import { useEffect, useState } from 'react';
import { Badge, Divider, Grid, Space, Typography } from 'antd';
import { ClockCircleOutlined, CopyrightOutlined, GithubOutlined, HeartFilled } from '@ant-design/icons';
import { VERSION_INFO, getVersionString } from '../config/version';
import { checkLatestVersion } from '../services/versionService';

const { Link, Text } = Typography;
const { useBreakpoint } = Grid;

interface AppFooterProps {
  sidebarWidth?: number;
}

export default function AppFooter({ sidebarWidth = 0 }: AppFooterProps) {
  const screens = useBreakpoint();
  const isMobile = !screens.md;
  const [hasUpdate, setHasUpdate] = useState(false);
  const [latestVersion, setLatestVersion] = useState('');
  const [releaseUrl, setReleaseUrl] = useState('');

  useEffect(() => {
    const checkVersion = async () => {
      try {
        const result = await checkLatestVersion();
        setHasUpdate(result.hasUpdate);
        setLatestVersion(result.latestVersion);
        setReleaseUrl(result.releaseUrl);
      } catch {
        // 版本检查失败时保持静默
      }
    };

    const timer = setTimeout(checkVersion, 3000);
    return () => clearTimeout(timer);
  }, []);

  const handleVersionClick = () => {
    if (hasUpdate && releaseUrl) {
      window.open(releaseUrl, '_blank');
    }
  };

  const leftOffset = isMobile ? 0 : sidebarWidth;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: leftOffset,
        right: 0,
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderTop: '1px solid var(--color-border)',
        padding: isMobile ? '8px 12px' : '10px 16px',
        zIndex: 100,
        boxShadow: 'var(--shadow-card)',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        transition: 'left 0.3s ease',
      }}
    >
      <div
        style={{
          maxWidth: 1400,
          margin: '0 auto',
          textAlign: 'center',
        }}
      >
        {isMobile ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 8,
            flexWrap: 'wrap',
          }}>
            <Badge dot={hasUpdate} offset={[-8, 2]}>
              <Text
                onClick={handleVersionClick}
                style={{
                  fontSize: 11,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  color: 'var(--color-primary)',
                  cursor: hasUpdate ? 'pointer' : 'default',
                }}
                title={hasUpdate ? `发现新版本 v${latestVersion}，点击查看` : '当前版本'}
              >
                <strong style={{ color: 'var(--color-text-primary)' }}>{VERSION_INFO.projectName}</strong>
                <span>{getVersionString()}</span>
              </Text>
            </Badge>
            <Divider type="vertical" style={{ margin: '0 4px', borderColor: 'var(--color-border)' }} />
            <Link
              href={VERSION_INFO.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 11,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: 'var(--color-text-secondary)',
              }}
            >
              <GithubOutlined style={{ fontSize: 12 }} />
            </Link>
            <Text
              style={{
                fontSize: 10,
                color: 'var(--color-text-tertiary)',
              }}
            >
              <ClockCircleOutlined style={{ fontSize: 10, marginRight: 4 }} />
              {VERSION_INFO.buildTime}
            </Text>
          </div>
        ) : (
          <Space
            direction="horizontal"
            size={12}
            split={<Divider type="vertical" style={{ borderColor: 'var(--color-border)' }} />}
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <Badge dot={hasUpdate} offset={[-8, 2]}>
              <Text
                onClick={handleVersionClick}
                style={{
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  color: 'var(--color-text-secondary)',
                  cursor: hasUpdate ? 'pointer' : 'default',
                  transition: 'all 0.3s',
                }}
                onMouseEnter={(e) => {
                  if (hasUpdate) {
                    e.currentTarget.style.transform = 'scale(1.05)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (hasUpdate) {
                    e.currentTarget.style.transform = 'scale(1)';
                  }
                }}
                title={hasUpdate ? `发现新版本 v${latestVersion}，点击查看` : '当前版本'}
              >
                <strong style={{ color: 'var(--color-text-primary)' }}>{VERSION_INFO.projectName}</strong>
                <span>{getVersionString()}</span>
              </Text>
            </Badge>

            <Link
              href={VERSION_INFO.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: 'var(--color-text-secondary)',
              }}
            >
              <GithubOutlined style={{ fontSize: 13 }} />
              <span>GitHub</span>
            </Link>

            <Link
              href={VERSION_INFO.licenseUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: 'var(--color-text-secondary)',
              }}
            >
              <CopyrightOutlined style={{ fontSize: 11 }} />
              <span>{VERSION_INFO.license}</span>
            </Link>

            <Text
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: 'var(--color-text-tertiary)',
              }}
            >
              <ClockCircleOutlined style={{ fontSize: 12 }} />
              <span>{VERSION_INFO.buildTime}</span>
            </Text>

            <Text
              style={{
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                color: 'var(--color-text-secondary)',
              }}
            >
              <span>Made with</span>
              <HeartFilled style={{ color: 'var(--color-error)', fontSize: 11 }} />
              <span>by {VERSION_INFO.author}</span>
            </Text>
          </Space>
        )}
      </div>
    </div>
  );
}
