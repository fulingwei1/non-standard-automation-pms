/**
 * 全局 mocks - 这个文件会在测试运行前被导入
 * 注意：vi.mock 需要在测试文件顶层使用才能正确 hoisted
 * 这里使用 vi.hoisted 来确保 mock 正确工作
 */

import { vi } from 'vitest';

// 使用 hoisted mock 确保在模块加载前生效
const { mockIcons } = vi.hoisted(() => {
  const React = require('react');
  const mockIcon = (name) => function MockIcon(props) {
    return React.createElement('svg', { 'data-testid': `icon-${name}`, ...props });
  };

  return {
    mockIcons: {
      User: mockIcon('user'),
      Lock: mockIcon('lock'),
      ArrowRight: mockIcon('arrow-right'),
      ArrowLeft: mockIcon('arrow-left'),
      Eye: mockIcon('eye'),
      EyeOff: mockIcon('eye-off'),
      Search: mockIcon('search'),
      Plus: mockIcon('plus'),
      Minus: mockIcon('minus'),
      Edit: mockIcon('edit'),
      Delete: mockIcon('delete'),
      Save: mockIcon('save'),
      Download: mockIcon('download'),
      Upload: mockIcon('upload'),
      RefreshCw: mockIcon('refresh-cw'),
      X: mockIcon('x'),
      Check: mockIcon('check'),
      AlertCircle: mockIcon('alert-circle'),
      AlertTriangle: mockIcon('alert-triangle'),
      Info: mockIcon('info'),
      BarChart3: mockIcon('bar-chart-3'),
      Clock: mockIcon('clock'),
      Users: mockIcon('users'),
      Settings: mockIcon('settings'),
      Menu: mockIcon('menu'),
      Bell: mockIcon('bell'),
      ChevronDown: mockIcon('chevron-down'),
      ChevronUp: mockIcon('chevron-up'),
      ChevronLeft: mockIcon('chevron-left'),
      ChevronRight: mockIcon('chevron-right'),
      MoreVertical: mockIcon('more-vertical'),
      Filter: mockIcon('filter'),
      Calendar: mockIcon('calendar'),
      FileText: mockIcon('file-text'),
      Folder: mockIcon('folder'),
      Home: mockIcon('home'),
      LogOut: mockIcon('log-out'),
      TrendingUp: mockIcon('trending-up'),
      TrendingDown: mockIcon('trending-down'),
      DollarSign: mockIcon('dollar-sign'),
      Percent: mockIcon('percent'),
      PieChart: mockIcon('pie-chart'),
      Activity: mockIcon('activity'),
      Zap: mockIcon('zap'),
      Layers: mockIcon('layers'),
      Box: mockIcon('box'),
      Package: mockIcon('package'),
      Truck: mockIcon('truck'),
      Factory: mockIcon('factory'),
      Wrench: mockIcon('wrench'),
      Cpu: mockIcon('cpu'),
      HardDrive: mockIcon('hard-drive'),
      Wifi: mockIcon('wifi'),
      Battery: mockIcon('battery'),
      Thermometer: mockIcon('thermometer'),
      Wind: mockIcon('wind'),
      Droplets: mockIcon('droplets'),
      Sun: mockIcon('sun'),
      Moon: mockIcon('moon'),
      Star: mockIcon('star'),
      Heart: mockIcon('heart'),
      ThumbUp: mockIcon('thumb-up'),
      Share2: mockIcon('share-2'),
      Copy: mockIcon('copy'),
      Link: mockIcon('link'),
      ExternalLink: mockIcon('external-link'),
      Print: mockIcon('print'),
      Mail: mockIcon('mail'),
      Phone: mockIcon('phone'),
      MapPin: mockIcon('map-pin'),
      Globe: mockIcon('globe'),
      Building: mockIcon('building'),
      Briefcase: mockIcon('briefcase'),
      GraduationCap: mockIcon('graduation-cap'),
      Award: mockIcon('award'),
      Target: mockIcon('target'),
      Compass: mockIcon('compass'),
      Shield: mockIcon('shield'),
      Unlock: mockIcon('unlock'),
      Key: mockIcon('key'),
    },
  };
});

// 导出 mock 供测试文件使用
export { mockIcons };