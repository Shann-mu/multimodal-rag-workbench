import React, { useState } from 'react';

import { Avatar, Button, Card, Form, Input, Tabs, Typography, Upload, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';

import { DEFAULT_AVATAR_URL, login, register } from '../modules/authService';
import { setAccessToken } from '../modules/authToken';

const { Title, Paragraph } = Typography;

type LocationState = {
  from?: { pathname?: string };
};

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as LocationState;
  const redirectTo = state.from?.pathname || '/';

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  const readAsDataUrl = (file: File) => new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('读取头像失败'));
    reader.readAsDataURL(file);
  });

  const handleAvatarUpload = async (file: File) => {
    try {
      const dataUrl = await readAsDataUrl(file);
      setAvatarUrl(dataUrl);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
    return false;
  };

  const handleLogin = async (values: { username: string; password: string }) => {
    setIsSubmitting(true);
    try {
      const token = await login(values.username, values.password);
      setAccessToken(token.access_token);
      navigate(redirectTo, { replace: true });
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegister = async (values: { username: string; password: string; confirm: string }) => {
    setIsSubmitting(true);
    try {
      if (values.password !== values.confirm) {
        message.error('两次密码不一致');
        return;
      }
      await register(values.username, values.password, avatarUrl || undefined);
      const token = await login(values.username, values.password);
      setAccessToken(token.access_token);
      navigate('/', { replace: true });
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-screen w-full flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md shadow-sm">
        <Title level={3} style={{ marginBottom: 0 }}>
          多模态大模型RAG系统
        </Title>
        <Paragraph type="secondary" style={{ marginTop: 8 }}>
          登录后可使用问答并查看历史会话
        </Paragraph>

        <Tabs
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form layout="vertical" onFinish={handleLogin}>
                  <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
                    <Input autoComplete="username" />
                  </Form.Item>
                  <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                    <Input.Password autoComplete="current-password" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={isSubmitting} block>
                    登录
                  </Button>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form layout="vertical" onFinish={handleRegister}>
                  <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3 }]}>
                    <Input autoComplete="username" />
                  </Form.Item>
                  <Form.Item label="头像">
                    <div className="flex items-center gap-3">
                      <Avatar size={48} src={avatarUrl || DEFAULT_AVATAR_URL} />
                      <Upload accept="image/*" beforeUpload={handleAvatarUpload} showUploadList={false} maxCount={1}>
                        <Button icon={<UploadOutlined />}>选择头像</Button>
                      </Upload>
                      {avatarUrl && (
                        <Button onClick={() => setAvatarUrl(null)}>使用默认</Button>
                      )}
                    </div>
                  </Form.Item>
                  <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
                    <Input.Password autoComplete="new-password" />
                  </Form.Item>
                  <Form.Item
                    name="confirm"
                    label="确认密码"
                    rules={[{ required: true }]}
                  >
                    <Input.Password autoComplete="new-password" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={isSubmitting} block>
                    注册并登录
                  </Button>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default Login;