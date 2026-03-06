import React, { useEffect, useMemo, useState } from 'react';

import {
  AudioOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  MessageOutlined,
  PlusOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { Alert, Button, Card, Drawer, List, Spin, Typography, message } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';

import Layout from '../components/Layout';
import SessionList from '../components/SessionList';
import type { ChatSession } from '../modules/types';
import { createSession, listSessions } from '../modules/historyService';

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  const modules = [
    {
      title: 'Smart QA',
      description: 'Intelligent text-based question answering system.',
      icon: <MessageOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
      path: '/chat',
    },
    {
      title: 'Image Analysis',
      description: 'Upload images and ask questions about them.',
      icon: <FileImageOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
      path: '/image-analysis',
    },
    {
      title: 'Audio Transcribe',
      description: 'Transcribe audio and analyze content.',
      icon: <AudioOutlined style={{ fontSize: '32px', color: '#722ed1' }} />,
      path: '/audio-transcribe',
    },
    {
      title: 'PDF Parsing',
      description: 'Upload PDFs and ask questions based on content.',
      icon: <FilePdfOutlined style={{ fontSize: '32px', color: '#f5222d' }} />,
      path: '/pdf-qa',
    },
  ];

  useEffect(() => {
    const run = async () => {
      setIsLoadingSessions(true);
      setLoadError(null);
      try {
        const data = await listSessions();
        setSessions(data);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setLoadError(msg);
        message.error(msg);
      } finally {
        setIsLoadingSessions(false);
      }
    };

    void run();
  }, []);

  const defaultSession = useMemo(() => sessions.find((s) => s.is_default) || null, [sessions]);
  const recentSession = useMemo(() => sessions[0] || null, [sessions]);
  const recentSessions = useMemo(() => sessions.slice(0, 5), [sessions]);

  const urlSessionId = useMemo(() => {
    const raw = new URLSearchParams(location.search).get('session_id');
    const n = raw ? Number(raw) : NaN;
    if (!Number.isFinite(n) || n <= 0) return null;
    return n;
  }, [location.search]);

  useEffect(() => {
    if (urlSessionId != null) {
      setSelectedSessionId(urlSessionId);
    }
  }, [urlSessionId]);

  useEffect(() => {
    if (selectedSessionId != null || urlSessionId != null) return;
    const initial = defaultSession?.id ?? recentSession?.id ?? null;
    if (initial != null) {
      setSelectedSessionId(initial);
    }
  }, [defaultSession, recentSession, selectedSessionId, urlSessionId]);

  useEffect(() => {
    if (selectedSessionId == null) return;

    const params = new URLSearchParams(location.search);
    const next = String(selectedSessionId);
    if (params.get('session_id') !== next) {
      params.set('session_id', next);
      navigate({ pathname: location.pathname, search: `?${params.toString()}` }, { replace: true });
    }
  }, [location.pathname, location.search, navigate, selectedSessionId]);

  const openSession = (path: string, sessionId: number) => {
    navigate({ pathname: path, search: `?session_id=${sessionId}` });
  };

  const createNewSession = async (titlePrefix: string) => {
    const now = new Date();
    const title = `${titlePrefix} ${now.toLocaleString()}`;
    const session = await createSession({ title, mode: 'multimodal', is_default: false });
    const createdId = Number((session as unknown as { id?: unknown }).id);
    if (Number.isFinite(createdId) && createdId > 0) return createdId;

    const latest = await listSessions();
    const created = latest.find((s) => s.title === title) || latest.find((s) => !s.is_default) || latest[0];
    return created ? created.id : null;
  };

  const openWithSelectedOrNew = async (path: string, titlePrefix: string) => {
    try {
      // 总是进入新对话，而不是继续上次对话
      const createdId = await createNewSession(titlePrefix);
      if (createdId != null) {
        openSession(path, createdId);
        return;
      }
      navigate(path);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
      navigate(path);
    }
  };

  const handleNewSessionOnly = async () => {
    try {
      const createdId = await createNewSession('会话');
      if (createdId != null) {
        const data = await listSessions();
        setSessions(data);
        setSelectedSessionId(createdId);
      }
      setIsDrawerOpen(false);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <Layout title="Home">
      <div className="flex flex-col items-center justify-center min-h-full py-6 px-4">
        <div className="text-center mb-8 md:mb-12">
          <Title level={1} className="text-2xl md:text-4xl">Multi-modal RAG System</Title>
          <Paragraph className="text-base md:text-lg text-gray-500">
            Select a module to start your intelligent interaction journey
          </Paragraph>
        </div>

        <div className="w-full max-w-4xl mb-6">
          {loadError && (
            <Alert
              message="历史会话加载失败"
              description={loadError}
              type="warning"
              showIcon
              closable
              className="mb-4"
            />
          )}

          <Card className="border border-gray-200 shadow-sm" bodyStyle={{ padding: '12px md:padding-24px' }}>
            <Drawer
              title="历史会话"
              placement="left"
              width={280}
              open={isDrawerOpen}
              onClose={() => setIsDrawerOpen(false)}
              styles={{ body: { padding: 0 } }}
            >
              <SessionList
                sessions={sessions}
                selectedSessionId={selectedSessionId}
                loading={isLoadingSessions}
                onSelect={(id) => {
                  setSelectedSessionId(id);
                  setIsDrawerOpen(false);
                }}
                onNew={handleNewSessionOnly}
              />
            </Drawer>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  快捷入口
                </Title>
                <Paragraph type="secondary" style={{ marginBottom: 0 }} className="text-xs md:text-sm">
                  继续你的默认会话或最近会话
                </Paragraph>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button icon={<UnorderedListOutlined />} onClick={() => setIsDrawerOpen(true)} size="small">
                  历史
                </Button>
                <Button icon={<PlusOutlined />} onClick={handleNewSessionOnly} size="small">
                  新会话
                </Button>
                <Button
                  disabled={!defaultSession || isLoadingSessions}
                  onClick={() => defaultSession && openSession('/chat', defaultSession.id)}
                  size="small"
                  className="hidden sm:inline-flex"
                >
                  默认会话
                </Button>
                <Button
                  type="primary"
                  disabled={!recentSession || isLoadingSessions}
                  onClick={() => recentSession && openSession('/chat', recentSession.id)}
                  size="small"
                >
                  继续最近
                </Button>
              </div>
            </div>

            <div className="mt-4 px-1 md:px-2">
              {isLoadingSessions ? (
                <div className="py-6 flex justify-center">
                  <Spin />
                </div>
              ) : recentSessions.length > 0 ? (
                <List
                  size="small"
                  dataSource={recentSessions}
                  renderItem={(item) => (
                    <List.Item
                      className="cursor-pointer hover:bg-gray-50 transition-colors"
                      style={{ paddingInline: 8, md: 16 }}
                      onClick={() => openSession('/chat', item.id)}
                    >
                      <div className="w-full flex items-center justify-between gap-2">
                        <div className="truncate flex-1">
                          <div className="text-sm font-medium truncate">{item.title}</div>
                          <div className="text-[10px] md:text-xs text-gray-500 truncate">
                            {item.is_default ? '默认' : item.mode} · {new Date(item.updated_at).toLocaleDateString()}
                          </div>
                        </div>
                        <Button size="small" type="link">打开</Button>
                      </div>
                    </List.Item>
                  )}
                />
              ) : (
                <div className="text-sm text-gray-500 py-2">暂无历史会话</div>
              )}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 w-full max-w-4xl">
          {modules.map((module) => (
            <Card
              key={module.path}
              hoverable
              className="cursor-pointer transition-all hover:-translate-y-1 hover:shadow-md"
              bodyStyle={{ padding: '16px' }}
              onClick={() => {
                void openWithSelectedOrNew(module.path, module.title);
              }}
            >
              <div className="flex items-center gap-4">
                <div className="p-2 md:p-3 bg-gray-50 rounded-full shrink-0">
                  {React.cloneElement(module.icon as React.ReactElement, { style: { fontSize: '24px' } })}
                </div>
                <div className="min-w-0">
                  <Title level={5} style={{ margin: 0 }} className="truncate">{module.title}</Title>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }} className="text-xs md:text-sm truncate">
                    {module.description}
                  </Paragraph>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </Layout>
  );
};

export default Home;
