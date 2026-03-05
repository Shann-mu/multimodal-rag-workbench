import { useCallback, useEffect, useMemo, useState } from 'react';
import type { FC } from 'react';
import { Alert, Button, Drawer, Spin, message, Select, Space, Modal, Input, Form, Upload, Tooltip, Divider } from 'antd';
import { PlusOutlined, UnorderedListOutlined, UploadOutlined, BookOutlined, FileTextOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';

import Layout from '../components/Layout';
import MessageList from '../components/MessageList';
import InputArea from '../components/InputArea';
import FileUploader from '../components/FileUploader';
import SessionList from '../components/SessionList';
import { useChat } from '../hooks/useChat';
import type { ChatSession, KnowledgeBase, KnowledgeDocument } from '../modules/types';
import { createSession, listMessages, listSessions } from '../modules/historyService';
import { listKnowledgeBases, listKnowledgeDocuments, createKnowledgeBase, uploadKnowledgeDocument } from '../modules/kbService';
import { DEFAULT_AVATAR_URL, me } from '../modules/authService';

interface ChatContainerProps {
  title: string;
  type: 'text' | 'image' | 'audio' | 'pdf';
  fileAccept?: string;
}

const ChatContainer: FC<ChatContainerProps> = ({ title, type, fileAccept }) => {
  const { sessionId, messages, sendMessage, isStreaming, error, loadMessages, resetChat, setSessionId } = useChat();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [userAvatarUrl, setUserAvatarUrl] = useState<string>(DEFAULT_AVATAR_URL);

  // 知识库相关的 state
  const [kbList, setKbList] = useState<KnowledgeBase[]>([]);
  const [activeKbId, setActiveKbId] = useState<number | null>(null);
  const [docList, setDocList] = useState<KnowledgeDocument[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([]);
  const [isKbModalOpen, setIsKbModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [form] = Form.useForm();

  // 加载知识库列表
  const refreshKbList = useCallback(async () => {
    try {
      const data = await listKnowledgeBases();
      setKbList(data);
      if (data.length > 0 && activeKbId === null) {
        const defaultKb = data.find(kb => kb.is_default) || data[0];
        setActiveKbId(defaultKb.id);
      }
    } catch (e) {
      console.error('Failed to load knowledge bases', e);
    }
  }, [activeKbId]);

  // 加载文档列表
  const refreshDocList = useCallback(async (kbId: number) => {
    try {
      const data = await listKnowledgeDocuments(kbId);
      setDocList(data);
    } catch (e) {
      console.error('Failed to load documents', e);
    }
  }, []);

  useEffect(() => {
    void refreshKbList();
  }, [refreshKbList]);

  useEffect(() => {
    const run = async () => {
      try {
        const profile = await me();
        setUserAvatarUrl(profile.avatar_url || DEFAULT_AVATAR_URL);
      } catch {
        setUserAvatarUrl(DEFAULT_AVATAR_URL);
      }
    };
    void run();
  }, []);

  useEffect(() => {
    if (activeKbId !== null) {
      void refreshDocList(activeKbId);
      setSelectedDocIds([]); // 切换知识库时清空已选文档
    } else {
      setDocList([]);
      setSelectedDocIds([]);
    }
  }, [activeKbId, refreshDocList]);

  const urlSessionId = useMemo(() => {
    const raw = new URLSearchParams(location.search).get('session_id');
    const n = raw ? Number(raw) : NaN;
    if (!Number.isFinite(n) || n <= 0) return null;
    return n;
  }, [location.search]);

  const activeSessionId = sessionId ?? urlSessionId ?? null;

  const refreshSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const data = await listSessions();
      setSessions(data);
      if (activeSessionId == null && urlSessionId == null) {
        const defaultSession = data.find((s) => s.is_default) || data[0];
        if (defaultSession) {
          setSessionId(defaultSession.id);
        }
      }
    } finally {
      setIsLoadingSessions(false);
    }
  }, [activeSessionId, setSessionId, urlSessionId]);

  useEffect(() => {
    if (sessionId == null && urlSessionId != null) {
      setSessionId(urlSessionId);
    }
  }, [sessionId, setSessionId, urlSessionId]);

  useEffect(() => {
    void refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    const run = async () => {
      if (activeSessionId == null) {
        resetChat();
        return;
      }
      setIsLoadingMessages(true);
      try {
        const records = await listMessages(activeSessionId);
        loadMessages([...records].reverse(), activeSessionId);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        message.error(msg);
        resetChat();
      } finally {
        setIsLoadingMessages(false);
      }
    };

    void run();
  }, [activeSessionId, loadMessages, resetChat]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);

    if (activeSessionId == null) {
      if (params.has('session_id')) {
        params.delete('session_id');
        const qs = params.toString();
        navigate({ pathname: location.pathname, search: qs ? `?${qs}` : '' }, { replace: true });
      }
      return;
    }

    const next = String(activeSessionId);
    if (params.get('session_id') !== next) {
      params.set('session_id', next);
      navigate({ pathname: location.pathname, search: `?${params.toString()}` }, { replace: true });
    }
  }, [activeSessionId, location.pathname, location.search, navigate]);

  const handleSend = (text: string) => {
    sendMessage(text, selectedFile || undefined, activeKbId, selectedDocIds);
    setSelectedFile(null);
  };

  const handleCreateKb = async (values: { name: string; description: string }) => {
    try {
      const newKb = await createKnowledgeBase(values);
      message.success(`知识库 "${newKb.name}" 创建成功`);
      setIsKbModalOpen(false);
      form.resetFields();
      await refreshKbList();
      setActiveKbId(newKb.id);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  const handleUploadDoc = async (file: File) => {
    if (!activeKbId) {
      message.warning('请先选择知识库');
      return false;
    }
    setIsUploading(true);
    try {
      await uploadKnowledgeDocument(activeKbId, file);
      message.success('文档上传成功');
      await refreshDocList(activeKbId);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setIsUploading(false);
    }
    return false; // 阻止 antd upload 默认行为
  };

  const handleNewSession = async () => {
    try {
      const now = new Date();
      const title = `会话 ${now.toLocaleString()}`;
      const next = await createSession({ title, mode: 'multimodal', is_default: false });
      setSessionId(next.id);
      setIsDrawerOpen(false);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  const sidebar = (
    <SessionList
      sessions={sessions}
      selectedSessionId={activeSessionId}
      loading={isLoadingSessions}
      onSelect={(id) => {
        setSessionId(id);
        setIsDrawerOpen(false);
      }}
      onNew={handleNewSession}
    />
  );

  const mobileHeaderActions = (
    <div className="flex gap-2">
      <Button icon={<UnorderedListOutlined />} onClick={() => setIsDrawerOpen(true)}>
        历史
      </Button>
      <Button type="primary" icon={<PlusOutlined />} onClick={handleNewSession}>
        新会话
      </Button>
    </div>
  );

  return (
    <Layout title={title}>
      <div className="flex-1 flex gap-4 min-h-0">
        <div className="hidden md:block w-72 shrink-0">{sidebar}</div>

        <Drawer
          title="历史会话"
          placement="left"
          width={320}
          open={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          bodyStyle={{ padding: 0 }}
        >
          {sidebar}
        </Drawer>

        <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden min-h-0">
          <div className="md:hidden px-3 py-2 border-b border-gray-200 bg-white flex justify-end">
            {mobileHeaderActions}
          </div>

          {error && (
            <Alert message="Error" description={error} type="error" showIcon closable className="m-2" />
          )}

          <div className="flex-1 overflow-hidden min-h-0">
            {isLoadingMessages ? (
              <div className="h-full flex items-center justify-center">
                <Spin />
              </div>
            ) : (
              <MessageList messages={messages} isStreaming={isStreaming} userAvatarUrl={userAvatarUrl} />
            )}
          </div>

          {/* 知识库工具栏 */}
          <div className="px-4 py-2 border-t border-gray-100 bg-white">
            <Space split={<Divider type="vertical" />} className="w-full justify-between overflow-x-auto flex-nowrap">
              <Space>
                <Tooltip title="选择知识库">
                  <Select
                    prefix={<BookOutlined className="text-gray-400" />}
                    value={activeKbId}
                    onChange={setActiveKbId}
                    placeholder="选择知识库"
                    className="w-40"
                    options={kbList.map(kb => ({ label: kb.name, value: kb.id }))}
                  />
                </Tooltip>
                
                <Tooltip title="选择参与检索的文档 (不选则全库检索)">
                  <Select
                    mode="multiple"
                    prefix={<FileTextOutlined className="text-gray-400" />}
                    value={selectedDocIds}
                    onChange={setSelectedDocIds}
                    placeholder="全部文档"
                    className="min-w-[160px] max-w-[300px]"
                    maxTagCount="responsive"
                    options={docList.map(doc => ({ label: doc.filename, value: doc.id }))}
                    allowClear
                  />
                </Tooltip>
              </Space>

              <Space>
                <Upload
                  beforeUpload={handleUploadDoc}
                  showUploadList={false}
                  accept=".pdf"
                >
                  <Button 
                    icon={<UploadOutlined />} 
                    loading={isUploading}
                    disabled={!activeKbId}
                  >
                    上传文档
                  </Button>
                </Upload>
                
                <Button 
                  icon={<PlusOutlined />} 
                  onClick={() => setIsKbModalOpen(true)}
                >
                  新知识库
                </Button>
              </Space>
            </Space>
          </div>

          <div className="bg-gray-50 border-t border-gray-200 p-2">
            {type !== 'text' && fileAccept && (
              <div className="px-4 pt-2">
                <FileUploader
                  accept={fileAccept}
                  onFileSelect={setSelectedFile}
                  selectedFile={selectedFile}
                  onClear={() => setSelectedFile(null)}
                  type={type === 'image' ? 'image' : type === 'audio' ? 'audio' : 'pdf'}
                />
              </div>
            )}
            <InputArea onSend={handleSend} disabled={isStreaming} />
          </div>
        </div>
      </div>

      <Modal
        title="创建新知识库"
        open={isKbModalOpen}
        onCancel={() => setIsKbModalOpen(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateKb}
          initialValues={{ name: '', description: '' }}
        >
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入知识库名称' }]}
          >
            <Input placeholder="例如：技术文档、项目资料" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="简要描述知识库内容" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default ChatContainer;
