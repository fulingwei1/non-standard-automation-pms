/**
 * Mock API responses for testing
 * 为所有异步测试提供统一的API mock策略
 */

// 通用的成功响应
export const mockSuccessResponse = (data = {}) => ({
  data: {
    success: true,
    data,
    items: Array.isArray(data) ? data : data.items || [],
    total: Array.isArray(data) ? data.length : data.total || 0,
  },
});

// 通用的列表响应
export const mockListResponse = (items = []) => ({
  data: {
    success: true,
    items,
    total: items.length,
    page: 1,
    pageSize: 20,
  },
});

// 通用的详情响应
export const mockDetailResponse = (detail = {}) => ({
  data: {
    success: true,
    data: detail,
  },
});

// 创建一个完整的API mock对象
export const createMockApi = () => ({
  get: vi.fn().mockResolvedValue(mockSuccessResponse()),
  post: vi.fn().mockResolvedValue(mockSuccessResponse()),
  put: vi.fn().mockResolvedValue(mockSuccessResponse()),
  delete: vi.fn().mockResolvedValue(mockSuccessResponse()),
  patch: vi.fn().mockResolvedValue(mockSuccessResponse()),
  request: vi.fn().mockResolvedValue(mockSuccessResponse()),
});
