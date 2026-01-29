import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { COLORS, COMPANY_INFO } from '../config';

/**
 * 场景1：开场动画
 * - Logo 缩放入场
 * - Slogan 淡入
 */
export const OpeningScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo 缩放动画 (spring)
  const logoScale = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 100,
    },
  });

  // Logo 发光效果
  const glowOpacity = interpolate(frame, [0, 60, 90, 150], [0, 0.8, 0.8, 0.3], {
    extrapolateRight: 'clamp',
  });

  // Slogan 淡入 (延迟 0.5 秒)
  const sloganOpacity = interpolate(frame, [15, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const sloganY = interpolate(frame, [15, 45], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${COLORS.primary} 0%, #0f172a 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Logo 容器 */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          transform: `scale(${logoScale})`,
        }}
      >
        {/* Logo 图标 (简化的测试设备图标) */}
        <div
          style={{
            width: 180,
            height: 180,
            borderRadius: 24,
            background: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.accent} 100%)`,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            boxShadow: `0 0 ${60 * glowOpacity}px ${30 * glowOpacity}px ${COLORS.secondary}40`,
            marginBottom: 30,
          }}
        >
          {/* 电路板图案 */}
          <svg width="100" height="100" viewBox="0 0 100 100">
            <rect x="20" y="20" width="60" height="60" rx="8" fill="none" stroke="white" strokeWidth="3" />
            <circle cx="35" cy="35" r="6" fill="white" />
            <circle cx="65" cy="35" r="6" fill="white" />
            <circle cx="35" cy="65" r="6" fill="white" />
            <circle cx="65" cy="65" r="6" fill="white" />
            <line x1="35" y1="41" x2="35" y2="59" stroke="white" strokeWidth="2" />
            <line x1="65" y1="41" x2="65" y2="59" stroke="white" strokeWidth="2" />
            <line x1="41" y1="50" x2="59" y2="50" stroke="white" strokeWidth="2" />
          </svg>
        </div>

        {/* 公司名称 */}
        <h1
          style={{
            fontSize: 72,
            fontWeight: 700,
            color: COLORS.white,
            margin: 0,
            letterSpacing: 8,
          }}
        >
          {COMPANY_INFO.name}
        </h1>

        {/* Slogan */}
        <p
          style={{
            fontSize: 32,
            color: COLORS.accent,
            margin: 0,
            marginTop: 20,
            opacity: sloganOpacity,
            transform: `translateY(${sloganY}px)`,
            letterSpacing: 4,
          }}
        >
          {COMPANY_INFO.slogan}
        </p>
      </div>
    </AbsoluteFill>
  );
};
