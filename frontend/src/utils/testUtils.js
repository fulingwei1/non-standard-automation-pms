/**
 * 测试辅助工具 - 统一 Mock 配置
 * 用于批量修复前端测试的 Mock 数据格式问题
 */

import { vi } from 'vitest';

/**
 * 创建带 mock 方法的 API 对象
 * @param {Object} methods - API 方法，如 { list: true, get: true, query: true }
 */
export const createMockApi = (methods = {}) => {
  const api = {};
  Object.keys(methods).forEach(key => {
    api[key] = vi.fn();
  });
  return api;
};

/**
 * 创建完整的 API mock 配置
 * 包含常用的 CRUD 方法
 */
export const createApiMock = () => ({
  list: vi.fn(),
  get: vi.fn(),
  query: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  aiMatch: vi.fn(),
  exportData: vi.fn(),
  importData: vi.fn(),
  submit: vi.fn(),
  approve: vi.fn(),
  reject: vi.fn(),
});

/**
 * 为 API 对象设置 mockResolvedValue
 * @param {Object} api - API 对象
 * @param {Object} mockData - mock 数据
 * @param {Object} options - 选项 { listData, getData, queryData }
 */
export const setupApiMocks = (api, mockData = {}, options = {}) => {
  const defaultResponse = { data: { items: [], total: 0 }, items: [] };
  
  if (api.list) {
    api.list.mockResolvedValue(options.listData || mockData.list || defaultResponse);
  }
  if (api.get) {
    api.get.mockResolvedValue(options.getData || mockData.get || { data: { items: [] } });
  }
  if (api.query) {
    api.query.mockResolvedValue(options.queryData || mockData.query || defaultResponse);
  }
  if (api.aiMatch) {
    api.aiMatch.mockResolvedValue(options.aiMatchData || mockData.aiMatch || defaultResponse);
  }
  if (api.exportData) {
    api.exportData.mockResolvedValue({ data: null });
  }
  if (api.importData) {
    api.importData.mockResolvedValue({ success: true });
  }
};

/**
 * 创建标准的 vi.mock 配置生成器
 * @param {Object} apiExports - 导出的 API 对象
 * @param {Object} customMocks - 自定义 mock 方法
 */
export const createMockConfig = (apiExports = {}, customMocks = {}) => {
  const mocks = {};
  
  Object.entries(apiExports).forEach(([key, value]) => {
    if (typeof value === 'object' && value !== null) {
      mocks[key] = createMockApi({
        list: true,
        get: true,
        query: true,
        ...customMocks[key]
      });
    }
  });
  
  return mocks;
};