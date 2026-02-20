/**
 * 测试环境配置文件
 * Vitest + React Testing Library 配置
 */

// 导入 jest-dom 扩展的 matchers
import '@testing-library/jest-dom';

// Mock window.matchMedia (Ant Design 需要)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock window.ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock API client globally with proper response structure
vi.mock('../services/api/client', () => {
  const mockResponse = (data = {}) => ({
    data: {
      success: true,
      data,
      items: Array.isArray(data) ? data : data.items || [],
      total: Array.isArray(data) ? data.length : data.total || 0,
      pending: 0,
      initiated_pending: 0,
      unread_cc: 0,
      urgent: 0,
      total: 0,
    },
  });

  return {
    api: {
      get: vi.fn().mockResolvedValue(mockResponse()),
      post: vi.fn().mockResolvedValue(mockResponse()),
      put: vi.fn().mockResolvedValue(mockResponse()),
      delete: vi.fn().mockResolvedValue(mockResponse()),
      patch: vi.fn().mockResolvedValue(mockResponse()),
      request: vi.fn().mockResolvedValue(mockResponse()),
    },
  };
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};

// Mock recharts 图表库
vi.mock('recharts', () => {
  const React = require('react');
  
  const MockComponent = ({ children, ...props }) => {
    return React.createElement('div', { className: 'recharts-wrapper', ...props }, children);
  };

  return {
    LineChart: MockComponent,
    BarChart: MockComponent,
    AreaChart: MockComponent,
    PieChart: MockComponent,
    Line: () => null,
    Bar: () => null,
    Area: () => null,
    Pie: () => null,
    Cell: () => null,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    ResponsiveContainer: ({ children }) => React.createElement('div', null, children),
  };
});

// Mock @ant-design/plots 图表库
vi.mock('@ant-design/plots', () => {
  const React = require('react');
  
  const createMockChart = (chartType) => {
    return function MockChart({ data = [], ...props }) {
      return React.createElement('div', {
        'data-testid': `${chartType}-chart`,
        'data-chart-type': chartType,
        'data-points': data.length,
      }, `${chartType} Chart (${data.length} data points)`);
    };
  };

  return {
    Line: createMockChart('line'),
    Bar: createMockChart('bar'),
    Area: createMockChart('area'),
    Pie: createMockChart('pie'),
    Column: createMockChart('column'),
    Scatter: createMockChart('scatter'),
    Rose: createMockChart('rose'),
    Radar: createMockChart('radar'),
    DualAxes: createMockChart('dual-axes'),
    Gauge: createMockChart('gauge'),
    Liquid: createMockChart('liquid'),
    Bullet: createMockChart('bullet'),
    Funnel: createMockChart('funnel'),
    Waterfall: createMockChart('waterfall'),
    WordCloud: createMockChart('word-cloud'),
    Sunburst: createMockChart('sunburst'),
    Treemap: createMockChart('treemap'),
    Heatmap: createMockChart('heatmap'),
    Box: createMockChart('box'),
    Violin: createMockChart('violin'),
    Stock: createMockChart('stock'),
  };
});

// 抑制 console 警告（可选）
// global.console = {
//   ...console,
//   warn: vi.fn(),
//   error: vi.fn(),
// };
