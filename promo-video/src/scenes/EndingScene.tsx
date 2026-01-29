import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { COLORS, COMPANY_INFO } from '../config';

/**
 * 场景5：结尾
 * - Logo + 公司名称
 * - Slogan
 * - 联系方式
 * - CTA 按钮
 */
export const EndingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo 从上方滑入
  const logoY = interpolate(frame, [0, 45], [-100, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const logoOpacity = interpolate(frame, [0, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Slogan 淡入
  const sloganOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 联系信息依次淡入
  const contactDelay = 60;
  const contactOpacity = (index: number) =>
    interpolate(frame, [contactDelay + index * 20, contactDelay + index * 20 + 30], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

  // CTA 按钮脉冲效果
  const ctaDelay = 150;
  const ctaOpacity = interpolate(frame, [ctaDelay, ctaDelay + 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const ctaScale = spring({
    frame: Math.max(0, frame - ctaDelay),
    fps,
    config: { damping: 10, stiffness: 100 },
  });

  // 呼吸效果
  const breathe = Math.sin((frame - ctaDelay) * 0.08) * 0.05 + 1;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, ${COLORS.primary} 0%, #0f172a 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 30,
        }}
      >
        {/* Logo + 公司名称 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            opacity: logoOpacity,
            transform: `translateY(${logoY}px)`,
          }}
        >
          {/* Logo 图标 */}
          <div
            style={{
              width: 100,
              height: 100,
              borderRadius: 20,
              background: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.accent} 100%)`,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <svg width="60" height="60" viewBox="0 0 100 100">
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
              fontSize: 64,
              fontWeight: 700,
              color: COLORS.white,
              margin: 0,
              letterSpacing: 6,
            }}
          >
            {COMPANY_INFO.name}
          </h1>
        </div>

        {/* Slogan */}
        <p
          style={{
            fontSize: 36,
            color: COLORS.accent,
            margin: 0,
            opacity: sloganOpacity,
            letterSpacing: 4,
          }}
        >
          {COMPANY_INFO.slogan}
        </p>

        {/* 分隔线 */}
        <div
          style={{
            width: 200,
            height: 2,
            background: `linear-gradient(90deg, transparent, ${COLORS.secondary}, transparent)`,
            margin: '20px 0',
            opacity: sloganOpacity,
          }}
        />

        {/* 联系方式 */}
        <div
          style={{
            display: 'flex',
            gap: 60,
            marginTop: 10,
          }}
        >
          {[
            { icon: '📞', label: '电话', value: COMPANY_INFO.phone },
            { icon: '✉️', label: '邮箱', value: COMPANY_INFO.email },
            { icon: '🌐', label: '官网', value: COMPANY_INFO.website },
          ].map((item, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                opacity: contactOpacity(index),
              }}
            >
              <span style={{ fontSize: 32, marginBottom: 8 }}>{item.icon}</span>
              <span style={{ fontSize: 16, color: COLORS.lightGray, marginBottom: 4 }}>{item.label}</span>
              <span style={{ fontSize: 20, color: COLORS.white, fontWeight: 500 }}>{item.value}</span>
            </div>
          ))}
        </div>

        {/* CTA 按钮 */}
        <div
          style={{
            marginTop: 40,
            padding: '20px 60px',
            background: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.accent} 100%)`,
            borderRadius: 50,
            opacity: ctaOpacity,
            transform: `scale(${ctaScale * breathe})`,
            boxShadow: `0 0 30px ${COLORS.secondary}50`,
          }}
        >
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: COLORS.white,
              letterSpacing: 2,
            }}
          >
            立即咨询，获取定制方案
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
