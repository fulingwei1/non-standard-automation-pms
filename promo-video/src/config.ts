/**
 * 视频配置常量
 */
export const VIDEO_CONFIG = {
  // 视频尺寸
  width: 1920,
  height: 1080,
  fps: 30,

  // 总时长（帧数）= 90秒 * 30fps
  durationInFrames: 90 * 30, // 2700 frames

  // 场景时间点（帧数）
  scenes: {
    opening: { start: 0, duration: 5 * 30 },           // 0-5秒
    painPoints: { start: 5 * 30, duration: 15 * 30 },  // 5-20秒
    capabilities: { start: 20 * 30, duration: 40 * 30 }, // 20-60秒
    highlights: { start: 60 * 30, duration: 15 * 30 }, // 60-75秒
    ending: { start: 75 * 30, duration: 15 * 30 },     // 75-90秒
  },
};

/**
 * 颜色配置
 */
export const COLORS = {
  primary: '#1e3a5f',      // 深蓝
  secondary: '#3b82f6',    // 科技蓝
  accent: '#60a5fa',       // 亮蓝
  white: '#ffffff',
  lightGray: '#f1f5f9',
  darkGray: '#334155',
  success: '#10b981',      // 绿色
  warning: '#f59e0b',      // 橙色
  danger: '#ef4444',       // 红色
};

/**
 * 公司信息配置（可自定义）
 */
export const COMPANY_INFO = {
  name: '智测科技',
  slogan: '精准测试，智造未来',
  phone: '400-888-8888',
  email: 'contact@zhice-tech.com',
  website: 'www.zhice-tech.com',
};
