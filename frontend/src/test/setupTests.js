/**
 * 测试环境配置文件
 * Vitest + React Testing Library 配置
 */

// 导入 jest-dom 扩展的 matchers
import '@testing-library/jest-dom';

// Mock window.getComputedStyle (jsdom 不支持，antd/rc-component 需要)
window.getComputedStyle = vi.fn().mockImplementation(() => ({
  display: 'block',
  visibility: 'visible',
  opacity: '1',
  width: '100px',
  height: '20px',
  overflow: 'visible',
  position: 'static',
  top: '0px',
  left: '0px',
  getPropertyValue: vi.fn().mockReturnValue(''),
}));

// Mock window.alert (jsdom 不支持)
window.alert = vi.fn();

// Mock window.confirm (jsdom 不支持)
window.confirm = vi.fn().mockReturnValue(true);

// Mock window.prompt (jsdom 不支持)
window.prompt = vi.fn().mockReturnValue(null);

// Mock window.print (jsdom 不支持)
window.print = vi.fn();

// Mock window.matchMedia (Ant Design 需要)
// 模拟大屏幕环境，使 lg: 断点的元素可见
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: true, // 模拟大屏幕
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
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock;
window.ResizeObserver = ResizeObserverMock;

// Mock localStorage / sessionStorage with real in-memory behavior
const createStorageMock = () => {
  let store = {};
  return {
    getItem: vi.fn((key) => (key in store ? store[key] : null)),
    setItem: vi.fn((key, value) => { store[key] = String(value); }),
    removeItem: vi.fn((key) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
};

const localStorageMock = createStorageMock();
global.localStorage = localStorageMock;
window.localStorage = localStorageMock;

const sessionStorageMock = createStorageMock();
global.sessionStorage = sessionStorageMock;
window.sessionStorage = sessionStorageMock;

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock react-router-dom (for useParams, useNavigate等)
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useParams: vi.fn(() => ({ 
      id: '1',
      projectId: '1',
      taskId: '1',
      customerId: '1',
      ecnId: '1',
      sourceType: 'project',
      sourceId: '1',
      department: 'engineering',
    })),
    useNavigate: vi.fn(() => vi.fn()),
    useLocation: vi.fn(() => ({ pathname: '/', search: '', hash: '', state: null })),
    useSearchParams: vi.fn(() => [new URLSearchParams(), vi.fn()]),
    useOutletContext: vi.fn(() => ({})),
    Router: ({ children }) => children,
    Routes: ({ children }) => children,
    Route: () => null,
    MemoryRouter: ({ children }) => children,
  };
});

// Mock API client globally with proper response structure
// 注意：这个 mock 会被 axios-mock-adapter 覆盖，所以需要返回正确的响应格式
vi.mock('../services/api/client', () => {
  const mockResponse = (data = {}, status = 200) => ({
    status,
    data: {
      success: true,
      data,
      items: Array.isArray(data) ? data : data.items || [],
      total: Array.isArray(data) ? data.length : data.total || 0,
      pending: 0,
      initiated_pending: 0,
      unread_cc: 0,
      urgent: 0,
    },
    headers: {},
    config: {},
  });

  const apiMock = {
    get: vi.fn().mockResolvedValue(mockResponse()),
    post: vi.fn().mockResolvedValue(mockResponse()),
    put: vi.fn().mockResolvedValue(mockResponse()),
    delete: vi.fn().mockResolvedValue(mockResponse()),
    patch: vi.fn().mockResolvedValue(mockResponse()),
    request: vi.fn().mockResolvedValue(mockResponse()),
    defaults: { baseURL: '/api/v1' },
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
  };

  return {
    default: apiMock,
    api: apiMock,
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
    return function MockChart({ data = [], ..._props }) {
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
