import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { COLORS } from '../config';

interface Highlight {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const highlights: Highlight[] = [
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <rect x="4" y="8" width="32" height="24" rx="4" stroke={COLORS.secondary} strokeWidth="2" />
        <path d="M12 16H28M12 22H24" stroke={COLORS.secondary} strokeWidth="2" strokeLinecap="round" />
        <circle cx="32" cy="8" r="4" fill={COLORS.success} />
      </svg>
    ),
    title: '自研测试平台',
    description: '软硬件一体化，稳定可靠',
  },
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <circle cx="20" cy="20" r="14" stroke={COLORS.secondary} strokeWidth="2" />
        <circle cx="20" cy="20" r="6" stroke={COLORS.secondary} strokeWidth="2" />
        <path d="M20 6V10M20 30V34M6 20H10M30 20H34" stroke={COLORS.secondary} strokeWidth="2" />
      </svg>
    ),
    title: '智能诊断',
    description: 'AI 辅助故障定位，快速排查',
  },
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <path d="M8 20C8 20 14 8 20 8C26 8 32 20 32 20C32 20 26 32 20 32C14 32 8 20 8 20Z" stroke={COLORS.secondary} strokeWidth="2" />
        <path d="M20 8V32" stroke={COLORS.secondary} strokeWidth="2" strokeDasharray="4 4" />
      </svg>
    ),
    title: '柔性兼容',
    description: '一机多用，快速换型',
  },
  {
    icon: (
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <rect x="6" y="6" width="12" height="12" rx="2" stroke={COLORS.secondary} strokeWidth="2" />
        <rect x="22" y="6" width="12" height="12" rx="2" stroke={COLORS.secondary} strokeWidth="2" />
        <rect x="6" y="22" width="12" height="12" rx="2" stroke={COLORS.secondary} strokeWidth="2" />
        <rect x="22" y="22" width="12" height="12" rx="2" stroke={COLORS.secondary} strokeWidth="2" />
        <path d="M18 12H22M12 18V22M28 18V22M18 28H22" stroke={COLORS.secondary} strokeWidth="2" />
      </svg>
    ),
    title: '数据追溯',
    description: '全流程数据记录，质量可追溯',
  },
];

/**
 * 场景4：技术亮点
 * - 2x2 网格布局
 * - 依次点亮
 */
export const HighlightsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 标题动画
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, #0f172a 0%, ${COLORS.primary} 100%)`,
        padding: 60,
      }}
    >
      {/* 标题 */}
      <h2
        style={{
          fontSize: 48,
          fontWeight: 700,
          color: COLORS.white,
          textAlign: 'center',
          marginBottom: 60,
          opacity: titleOpacity,
        }}
      >
        核心技术优势
      </h2>

      {/* 2x2 网格 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 40,
          maxWidth: 1200,
          margin: '0 auto',
        }}
      >
        {highlights.map((item, index) => {
          const delay = 60 + index * 60;

          const opacity = interpolate(frame, [delay, delay + 30], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const scale = spring({
            frame: Math.max(0, frame - delay),
            fps,
            config: { damping: 12, stiffness: 100 },
          });

          // 图标旋转动画
          const rotation = interpolate(frame, [delay, delay + 30], [-180, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          // 发光效果
          const glowIntensity = Math.sin((frame - delay) * 0.1) * 0.3 + 0.7;

          return (
            <div
              key={index}
              style={{
                padding: 40,
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 20,
                border: `1px solid ${COLORS.secondary}30`,
                opacity,
                transform: `scale(${scale})`,
                boxShadow: frame > delay ? `0 0 ${20 * glowIntensity}px ${COLORS.secondary}20` : 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 24,
              }}
            >
              {/* 图标容器 */}
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: 16,
                  background: `${COLORS.secondary}15`,
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  transform: `rotate(${rotation}deg)`,
                  flexShrink: 0,
                }}
              >
                {item.icon}
              </div>

              {/* 文字内容 */}
              <div>
                <h3
                  style={{
                    fontSize: 28,
                    fontWeight: 700,
                    color: COLORS.white,
                    margin: 0,
                    marginBottom: 8,
                  }}
                >
                  {item.title}
                </h3>
                <p
                  style={{
                    fontSize: 20,
                    color: COLORS.lightGray,
                    margin: 0,
                  }}
                >
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
