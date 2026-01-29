import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { COLORS } from '../config';

interface PainPoint {
  icon: React.ReactNode;
  title: string;
  stat: string;
}

const painPoints: PainPoint[] = [
  {
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="24" r="20" stroke={COLORS.warning} strokeWidth="3" />
        <path d="M24 14V26" stroke={COLORS.warning} strokeWidth="3" strokeLinecap="round" />
        <path d="M24 26L30 32" stroke={COLORS.warning} strokeWidth="3" strokeLinecap="round" />
      </svg>
    ),
    title: '测试效率低，产能受限',
    stat: '效率仅 60%',
  },
  {
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <path d="M24 8L4 40H44L24 8Z" stroke={COLORS.danger} strokeWidth="3" strokeLinejoin="round" />
        <path d="M24 20V28" stroke={COLORS.danger} strokeWidth="3" strokeLinecap="round" />
        <circle cx="24" cy="34" r="2" fill={COLORS.danger} />
      </svg>
    ),
    title: '漏测风险高，质量难保障',
    stat: '漏测率 5%↑',
  },
  {
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="16" r="8" stroke={COLORS.secondary} strokeWidth="3" />
        <path d="M12 40C12 32 17 28 24 28C31 28 36 32 36 40" stroke={COLORS.secondary} strokeWidth="3" />
        <path d="M32 20L40 28" stroke={COLORS.secondary} strokeWidth="3" strokeLinecap="round" />
        <path d="M40 20L32 28" stroke={COLORS.secondary} strokeWidth="3" strokeLinecap="round" />
      </svg>
    ),
    title: '人工成本高，依赖经验',
    stat: '成本 +30%',
  },
];

/**
 * 场景2：痛点引入
 * - 三个痛点依次滑入
 */
export const PainPointsScene: React.FC = () => {
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
        padding: 80,
      }}
    >
      {/* 标题 */}
      <h2
        style={{
          fontSize: 56,
          fontWeight: 700,
          color: COLORS.white,
          textAlign: 'center',
          marginBottom: 60,
          opacity: titleOpacity,
        }}
      >
        您是否面临这些挑战？
      </h2>

      {/* 痛点列表 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          gap: 60,
          marginTop: 40,
        }}
      >
        {painPoints.map((point, index) => {
          // 每个痛点延迟出现
          const delay = 60 + index * 90; // 2秒后开始，每个间隔3秒

          const slideX = interpolate(frame, [delay, delay + 30], [-100, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const opacity = interpolate(frame, [delay, delay + 30], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          // 数字动画
          const statScale = spring({
            frame: Math.max(0, frame - delay - 20),
            fps,
            config: { damping: 10, stiffness: 100 },
          });

          return (
            <div
              key={index}
              style={{
                width: 400,
                padding: 40,
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: 24,
                border: '1px solid rgba(255, 255, 255, 0.1)',
                opacity,
                transform: `translateX(${slideX}px)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              {/* 图标 */}
              <div style={{ marginBottom: 24 }}>{point.icon}</div>

              {/* 标题 */}
              <h3
                style={{
                  fontSize: 28,
                  fontWeight: 600,
                  color: COLORS.white,
                  textAlign: 'center',
                  marginBottom: 16,
                }}
              >
                {point.title}
              </h3>

              {/* 统计数字 */}
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: COLORS.danger,
                  transform: `scale(${statScale})`,
                }}
              >
                {point.stat}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
