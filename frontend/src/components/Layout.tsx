import React, { useEffect, useState } from 'react';

import { BookOutlined, FilePdfOutlined, HomeOutlined, LogoutOutlined } from '@ant-design/icons';
import { Avatar, Button, Collapse, Drawer, Empty, Layout as AntLayout, List, Spin, Typography, message } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';

import { clearAccessToken, hasAccessToken } from '../modules/authToken';
import { DEFAULT_AVATAR_URL, me, type UserPublic } from '../modules/authService';
import type { KnowledgeBase, KnowledgeDocument } from '../modules/types';
import { listKnowledgeBases, listKnowledgeDocuments } from '../modules/kbService';

const { Header, Content } = AntLayout;
const { Title } = Typography;

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const [user, setUser] = useState<UserPublic | null>(null);
  const [isKbDrawerOpen, setIsKbDrawerOpen] = useState(false);
  const [kbList, setKbList] = useState<KnowledgeBase[]>([]);
  const [kbDocs, setKbDocs] = useState<Record<number, KnowledgeDocument[]>>({});
  const [isKbLoading, setIsKbLoading] = useState(false);

  useEffect(() => {
    const run = async () => {
      if (!hasAccessToken()) {
        setUser(null);
        return;
      }
      try {
        const profile = await me();
        setUser(profile);
      } catch {
        setUser(null);
      }
    };
    void run();
  }, []);

  const avatarSrc = user?.avatar_url || DEFAULT_AVATAR_URL;

  const loadKbOverview = async () => {
    setIsKbLoading(true);
    try {
      const bases = await listKnowledgeBases();
      setKbList(bases);
      const docsMap: Record<number, KnowledgeDocument[]> = {};
      for (const kb of bases) {
        try {
          docsMap[kb.id] = await listKnowledgeDocuments(kb.id);
        } catch {
          docsMap[kb.id] = [];
        }
      }
      setKbDocs(docsMap);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setIsKbLoading(false);
    }
  };

  const openKbDrawer = () => {
    setIsKbDrawerOpen(true);
    void loadKbOverview();
  };

  return (
    <AntLayout className="h-screen flex flex-col bg-gray-50">
      <Header 
        className="border-b px-6 flex items-center justify-between h-16 shadow-sm z-10"
        style={{ background: '#fff' }}
      >
        <div className="flex items-center gap-4">
          <Avatar size={32} src={avatarSrc} />
          {!isHome && (
            <Button
              icon={<HomeOutlined />}
              onClick={() => navigate('/')}
              type="text"
            >
              Back to Home
            </Button>
          )}
          <Title level={4} style={{ margin: 0 }}>
            {title || 'Multi-modal RAG System'}
          </Title>
        </div>

        <div className="flex items-center gap-2">
          {hasAccessToken() && (
            <>
              <Button icon={<BookOutlined />} onClick={openKbDrawer}>
                我的知识库
              </Button>
              <Button
                icon={<LogoutOutlined />}
                onClick={() => {
                  clearAccessToken();
                  navigate('/login', { replace: true });
                }}
              >
                Logout
              </Button>
            </>
          )}
        </div>
      </Header>
      <Drawer
        title="我的知识库"
        placement="right"
        width={480}
        open={isKbDrawerOpen}
        onClose={() => setIsKbDrawerOpen(false)}
      >
        {isKbLoading ? (
          <div className="py-10 flex justify-center">
            <Spin />
          </div>
        ) : kbList.length === 0 ? (
          <Empty description="暂无知识库" />
        ) : (
          <Collapse
            items={kbList.map((kb) => ({
              key: kb.id,
              label: (
                <div className="flex items-center justify-between w-full pr-2">
                  <span>{kb.name}</span>
                  {kb.is_default && <span className="text-xs text-gray-400">默认</span>}
                </div>
              ),
              children: (
                kbDocs[kb.id] && kbDocs[kb.id].length > 0 ? (
                  <List
                    size="small"
                    dataSource={kbDocs[kb.id]}
                    renderItem={(doc) => (
                      <List.Item className="flex items-center gap-2">
                        <FilePdfOutlined className="text-red-400" />
                        <span className="text-sm">{doc.filename}</span>
                      </List.Item>
                    )}
                  />
                ) : (
                  <div className="text-sm text-gray-500 py-2">暂无PDF文件</div>
                )
              ),
            }))}
          />
        )}
      </Drawer>
      <Content className="flex-1 overflow-hidden relative flex flex-col">
        <div className="flex-1 w-full max-w-5xl mx-auto p-4 h-full flex flex-col min-h-0">
          {children}
        </div>
      </Content>
    </AntLayout>
  );
};

export default Layout;
