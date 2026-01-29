import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig, Sequence } from 'remotion';
import { COLORS } from '../config';

/**
 * 数字滚动动画组件
 */
const AnimatedNumber: React.FC<{
  value: string;
  frame: number;
  delay: number;
  fps: number;
}> = ({ value, frame, delay, fps }) => {
  const progress = interpolate(frame, [delay, delay + 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 解析数字部分
  const numMatch = value.match(/[\d.]+/);
  const numValue = numMatch ? parseFloat(numMatch[0]) : 0;
  const prefix = value.slice(0, value.indexOf(numMatch?.[0] || ''));
  const suffix = value.slice((value.indexOf(numMatch?.[0] || '') || 0) + (numMatch?.[0]?.length || 0));

  const displayNum = (numValue * progress).toFixed(value.includes('.') ? 2 : 0);

  return (
    <span>
      {prefix}
      {displayNum}
      {suffix}
    </span>
  );
};

/**
 * 测试类型卡片
 */
const TestTypeCard: React.FC<{
  title: string;
  items: string[];
  color: string;
  icon: React.ReactNode;
  frame: number;
  delay: number;
}> = ({ title, items, color, icon, frame, delay }) => {
  const opacity = interpolate(frame, [delay, delay + 20], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(frame, [delay, delay + 20], [0.8, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 脉冲光效
  const pulseFrame = Math.max(0, frame - delay - 20);
  const pulse = Math.sin(pulseFrame * 0.1) * 0.3 + 0.7;

  return (
    <div
      style={{
        width: 500,
        padding: 32,
        background: 'rgba(255, 255, 255, 0.03)',
        borderRadius: 20,
        border: `2px solid ${color}40`,
        opacity,
        transform: `scale(${scale})`,
        boxShadow: `0 0 ${30 * pulse}px ${color}30`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 12,
            background: `${color}20`,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {icon}
        </div>
        <h3 style={{ fontSize: 32, fontWeight: 700, color: COLORS.white, margin: 0 }}>
          {title}
        </h3>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        {items.map((item, i) => (
          <span
            key={i}
            style={{
              padding: '8px 16px',
              background: `${color}15`,
              borderRadius: 8,
              fontSize: 18,
              color: color,
            }}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
};

/**
 * 场景3：核心能力展示
 * 分为三个子场景：测试项目、测试精度、测试速度
 */
export const CapabilitiesScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 子场景时间划分 (40秒 = 1200帧)
  // 3.1 测试项目: 0-450帧 (15秒)
  // 3.2 测试精度: 450-750帧 (10秒)
  // 3.3 测试速度: 750-1200帧 (15秒)

  const subScene = frame < 450 ? 1 : frame < 750 ? 2 : 3;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${COLORS.primary} 0%, #0f172a 100%)`,
      }}
    >
      {/* 子场景 3.1: 测试项目展示 */}
      {subScene === 1 && (
        <div style={{ padding: 60 }}>
          <h2
            style={{
              fontSize: 48,
              fontWeight: 700,
              color: COLORS.white,
              textAlign: 'center',
              marginBottom: 50,
              opacity: interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            全面的测试能力
          </h2>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 40, flexWrap: 'wrap' }}>
            <TestTypeCard
              title="ICT 在线测试"
              items={['开短路检测', '电阻测量', '电容测量', '二极管测试']}
              color={COLORS.secondary}
              icon={
                <svg width="32" height="32" viewBox="0 0 32 32" fill={COLORS.secondary}>
                  <path d="M4 16H12L14 8L18 24L20 16H28" stroke={COLORS.secondary} strokeWidth="2" fill="none" />
                </svg>
              }
              frame={frame}
              delay={60}
            />

            <TestTypeCard
              title="FCT 功能测试"
              items={['电压测试', '电流测试', '通讯协议', '逻辑功能']}
              color={COLORS.success}
              icon={
                <svg width="32" height="32" viewBox="0 0 32 32" fill={COLORS.success}>
                  <path d="M16 4V12M16 12L20 8M16 12L12 8" stroke={COLORS.success} strokeWidth="2" fill="none" />
                  <path d="M16 28V20M16 20L20 24M16 20L12 24" stroke={COLORS.success} strokeWidth="2" fill="none" />
                </svg>
              }
              frame={frame}
              delay={150}
            />

            <TestTypeCard
              title="EOL 终检测试"
              items={['整机性能', '老化筛选', '可靠性验证', '出厂检验']}
              color={COLORS.accent}
              icon={
                <svg width="32" height="32" viewBox="0 0 32 32" fill={COLORS.accent}>
                  <circle cx="16" cy="16" r="10" stroke={COLORS.accent} strokeWidth="2" fill="none" />
                  <path d="M12 16L15 19L21 13" stroke={COLORS.accent} strokeWidth="2" fill="none" />
                </svg>
              }
              frame={frame}
              delay={240}
            />
          </div>
        </div>
      )}

      {/* 子场景 3.2: 测试精度展示 */}
      {subScene === 2 && (
        <div style={{ padding: 60, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <h2
            style={{
              fontSize: 48,
              fontWeight: 700,
              color: COLORS.white,
              textAlign: 'center',
              marginBottom: 60,
              opacity: interpolate(frame - 450, [0, 30], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            极致的测试精度
          </h2>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 80 }}>
            {[
              { label: '电压精度', value: '±0.01%', color: COLORS.secondary },
              { label: '电流精度', value: '±0.05%', color: COLORS.success },
              { label: '测量重复性', value: '99.99%', color: COLORS.accent },
            ].map((item, index) => {
              const delay = 450 + 30 + index * 45;
              const opacity = interpolate(frame, [delay, delay + 30], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });

              return (
                <div
                  key={index}
                  style={{
                    textAlign: 'center',
                    opacity,
                  }}
                >
                  <div
                    style={{
                      fontSize: 72,
                      fontWeight: 800,
                      color: item.color,
                      marginBottom: 16,
                      textShadow: `0 0 30px ${item.color}50`,
                    }}
                  >
                    <AnimatedNumber value={item.value} frame={frame} delay={delay} fps={fps} />
                  </div>
                  <div style={{ fontSize: 28, color: COLORS.lightGray }}>{item.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 子场景 3.3: 测试速度展示 */}
      {subScene === 3 && (
        <div style={{ padding: 60 }}>
          <h2
            style={{
              fontSize: 48,
              fontWeight: 700,
              color: COLORS.white,
              textAlign: 'center',
              marginBottom: 50,
              opacity: interpolate(frame - 750, [0, 30], [0, 1], { extrapolateRight: 'clamp' }),
            }}
          >
            卓越的测试效率
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 40, maxWidth: 1200, margin: '0 auto' }}>
            {[
              { label: '单板测试时间', ours: '3秒/片', theirs: '15秒', improvement: '提升 5x' },
              { label: '日产能', ours: '10,000+ 片', theirs: '2,000 片', improvement: '提升 5x' },
              { label: '换线时间', ours: '5分钟', theirs: '30分钟', improvement: '节省 83%' },
            ].map((item, index) => {
              const delay = 750 + 60 + index * 90;
              const progress = interpolate(frame, [delay, delay + 60], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });

              return (
                <div key={index} style={{ opacity: progress }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                    <span style={{ fontSize: 24, color: COLORS.white }}>{item.label}</span>
                    <span style={{ fontSize: 24, color: COLORS.success, fontWeight: 700 }}>{item.improvement}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                    {/* 我们的进度条 */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, color: COLORS.accent, marginBottom: 8 }}>我们: {item.ours}</div>
                      <div style={{ height: 24, background: 'rgba(255,255,255,0.1)', borderRadius: 12, overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${progress * 100}%`,
                            height: '100%',
                            background: `linear-gradient(90deg, ${COLORS.secondary}, ${COLORS.accent})`,
                            borderRadius: 12,
                          }}
                        />
                      </div>
                    </div>
                    {/* 传统方案进度条 */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, color: COLORS.darkGray, marginBottom: 8 }}>传统: {item.theirs}</div>
                      <div style={{ height: 24, background: 'rgba(255,255,255,0.1)', borderRadius: 12, overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${progress * 20}%`,
                            height: '100%',
                            background: COLORS.darkGray,
                            borderRadius: 12,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
