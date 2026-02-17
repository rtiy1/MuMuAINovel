import { useEffect, useState } from 'react';
import { Alert, Button, Card, Form, Input, Space, Spin, Tabs, Typography, message } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AnnouncementModal from '../components/AnnouncementModal';
import { authApi } from '../services/api';

const { Title, Paragraph } = Typography;

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [localAuthEnabled, setLocalAuthEnabled] = useState(false);
  const [localRegistrationEnabled, setLocalRegistrationEnabled] = useState(false);
  const [showAnnouncement, setShowAnnouncement] = useState(false);
  const [form] = Form.useForm();
  const [registerForm] = Form.useForm();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await authApi.getCurrentUser();
        const redirect = searchParams.get('redirect') || '/';
        navigate(redirect);
      } catch {
        try {
          const config = await authApi.getAuthConfig();
          setLocalAuthEnabled(config.local_auth_enabled);
          setLocalRegistrationEnabled(!!config.local_auth_allow_registration);
        } catch (error) {
          console.error('获取认证配置失败:', error);
          setLocalAuthEnabled(false);
          setLocalRegistrationEnabled(false);
        }
        setChecking(false);
      }
    };

    checkAuth();
  }, [navigate, searchParams]);

  const handleLoginSuccess = () => {
    const hideForever = localStorage.getItem('announcement_hide_forever');
    const hideToday = localStorage.getItem('announcement_hide_today');
    const today = new Date().toDateString();

    if (hideForever === 'true' || hideToday === today) {
      const redirect = searchParams.get('redirect') || '/';
      navigate(redirect);
      return;
    }
    setShowAnnouncement(true);
  };

  const handleLocalLogin = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      const response = await authApi.localLogin(values.username, values.password);

      if (response.success) {
        message.success('登录成功！');
        handleLoginSuccess();
      }
    } catch (error) {
      console.error('本地登录失败:', error);
      setLoading(false);
    }
  };

  const handleLocalRegister = async (values: { username: string; displayName?: string; password: string }) => {
    try {
      setLoading(true);
      const response = await authApi.localRegister(values.username, values.password, values.displayName);

      if (response.success) {
        message.success('注册成功！');
        handleLoginSuccess();
      }
    } catch (error) {
      console.error('本地注册失败:', error);
      setLoading(false);
    }
  };

  const handleAnnouncementClose = () => {
    setShowAnnouncement(false);
    const redirect = searchParams.get('redirect') || '/';
    navigate(redirect);
  };

  const handleDoNotShowToday = () => {
    const today = new Date().toDateString();
    localStorage.setItem('announcement_hide_today', today);
  };

  const handleNeverShow = () => {
    localStorage.setItem('announcement_hide_forever', 'true');
  };

  const renderLocalLogin = () => (
    <Form
      form={form}
      onFinish={handleLocalLogin}
      size="large"
      style={{ marginTop: '24px' }}
    >
      <Form.Item
        name="username"
        rules={[{ required: true, message: '请输入用户名' }]}
      >
        <Input
          prefix={<UserOutlined style={{ color: '#999' }} />}
          placeholder="用户名"
          autoComplete="username"
        />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[{ required: true, message: '请输入密码' }]}
      >
        <Input.Password
          prefix={<LockOutlined style={{ color: '#999' }} />}
          placeholder="密码"
          autoComplete="current-password"
        />
      </Form.Item>
      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          block
          style={{
            height: 48,
            fontSize: 16,
            fontWeight: 600,
            background: 'var(--color-primary)',
            border: 'none',
            borderRadius: '12px',
            boxShadow: 'var(--shadow-primary)',
          }}
        >
          登录
        </Button>
      </Form.Item>
    </Form>
  );

  const renderLocalRegister = () => (
    <Form
      form={registerForm}
      onFinish={handleLocalRegister}
      size="large"
      style={{ marginTop: '24px' }}
    >
      <Form.Item
        name="username"
        rules={[
          { required: true, message: '请输入用户名' },
          { min: 3, message: '用户名至少 3 个字符' },
          { max: 32, message: '用户名最多 32 个字符' },
          { pattern: /^[a-zA-Z0-9_.-]+$/, message: '仅支持字母、数字、下划线、短横线、点' },
        ]}
      >
        <Input
          prefix={<UserOutlined style={{ color: '#999' }} />}
          placeholder="用户名"
          autoComplete="username"
        />
      </Form.Item>
      <Form.Item
        name="displayName"
        rules={[
          { min: 2, message: '显示名称至少 2 个字符' },
          { max: 50, message: '显示名称最多 50 个字符' },
        ]}
      >
        <Input
          prefix={<UserOutlined style={{ color: '#999' }} />}
          placeholder="显示名称（可选）"
          autoComplete="nickname"
        />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少 6 个字符' },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined style={{ color: '#999' }} />}
          placeholder="密码"
          autoComplete="new-password"
        />
      </Form.Item>
      <Form.Item
        name="confirmPassword"
        dependencies={['password']}
        rules={[
          { required: true, message: '请再次输入密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error('两次输入的密码不一致'));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined style={{ color: '#999' }} />}
          placeholder="确认密码"
          autoComplete="new-password"
        />
      </Form.Item>
      <Form.Item style={{ marginBottom: 0 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          block
          style={{
            height: 48,
            fontSize: 16,
            fontWeight: 600,
            background: 'var(--color-primary)',
            border: 'none',
            borderRadius: '12px',
            boxShadow: 'var(--shadow-primary)',
          }}
        >
          注册并登录
        </Button>
      </Form.Item>
    </Form>
  );

  const renderDisabledNotice = () => (
    <Alert
      type="warning"
      showIcon
      message="本地登录未启用"
      description="请联系管理员开启 LOCAL_AUTH_ENABLED 后再登录。"
      style={{ marginTop: '24px', textAlign: 'left' }}
    />
  );

  if (checking) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--color-bg-base)',
      }}>
        <Spin size="large" style={{ color: 'var(--color-primary)' }} />
      </div>
    );
  }

  return (
    <>
      <AnnouncementModal
        visible={showAnnouncement}
        onClose={handleAnnouncementClose}
        onDoNotShowToday={handleDoNotShowToday}
        onNeverShow={handleNeverShow}
      />
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--color-bg-base)',
        padding: '20px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          top: '-10%',
          right: '-5%',
          width: '400px',
          height: '400px',
          background: 'var(--color-primary)',
          opacity: 0.1,
          borderRadius: '50%',
          filter: 'blur(60px)',
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-10%',
          left: '-5%',
          width: '350px',
          height: '350px',
          background: 'var(--color-success)',
          opacity: 0.08,
          borderRadius: '50%',
          filter: 'blur(60px)',
        }} />

        <Card
          style={{
            width: '100%',
            maxWidth: 420,
            background: 'var(--color-bg-container)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            boxShadow: 'var(--shadow-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '16px',
            position: 'relative',
            zIndex: 1,
          }}
          bodyStyle={{
            padding: '40px 32px',
          }}
        >
          <Space direction="vertical" size="large" style={{ width: '100%', textAlign: 'center' }}>
            <div style={{ marginBottom: '8px' }}>
              <div style={{
                width: '72px',
                height: '72px',
                margin: '0 auto 20px',
                background: 'var(--color-primary)',
                borderRadius: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'var(--shadow-primary)',
              }}>
                <img
                  src="/logo.svg"
                  alt="Logo"
                  style={{
                    width: '48px',
                    height: '48px',
                    filter: 'brightness(0) invert(1)',
                  }}
                />
              </div>
              <Title level={2} style={{
                marginBottom: 8,
                color: 'var(--color-primary)',
                fontWeight: 700,
              }}>
                AI小说创作助手
              </Title>
              <Paragraph style={{
                color: 'var(--color-text-secondary)',
                fontSize: '14px',
                marginBottom: 0,
              }}>
                {localAuthEnabled ? '使用账户密码登录' : '本地登录未启用'}
              </Paragraph>
            </div>

            {localAuthEnabled ? (
              localRegistrationEnabled ? (
                <Tabs
                  defaultActiveKey="local"
                  centered
                  items={[
                    {
                      key: 'local',
                      label: '账户密码',
                      children: renderLocalLogin(),
                    },
                    {
                      key: 'register',
                      label: '注册账号',
                      children: renderLocalRegister(),
                    },
                  ]}
                />
              ) : (
                renderLocalLogin()
              )
            ) : (
              renderDisabledNotice()
            )}

            <div style={{
              padding: '16px',
              background: 'rgba(77, 128, 136, 0.08)',
              borderRadius: '12px',
              border: '1px solid var(--color-border)',
            }}>
              <Paragraph style={{
                fontSize: 13,
                color: 'var(--color-text-secondary)',
                marginBottom: 0,
                lineHeight: 1.6,
              }}>
                🎉 首次登录将自动创建账号
                <br />
                🔒 每个用户拥有独立的数据空间
              </Paragraph>
            </div>
          </Space>
        </Card>
      </div>
    </>
  );
}
