import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useMaterialReadiness } from '../useMaterialReadiness';

// Mock API
vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    defaults: { baseURL: '/api' },
  },
  materialApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    search: vi.fn(),
    warehouse: {
      statistics: vi.fn(),
    },
    categories: {
      list: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
  supplierApi: {
    list: vi.fn(),
  },
  };
});

describe('useMaterialReadiness Hook', () => {
  // 导入已 mock 的模块
  let materialApi;
  let projectApi;
  let supplierApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    
    // 动态导入 mock 的模块
    const api = await import('../../../../services/api');
    materialApi = api.materialApi;
    projectApi = api.projectApi;
    supplierApi = api.supplierApi;

    // Mock 数据 - 返回物料数组
    const mockMaterials = [
      { id: 1, code: 'MAT-001', name: '钢板', status: 'AVAILABLE', quantity: 100, required_quantity: 100, type: 'RAW_MATERIAL', priority: 'HIGH', project_id: 1 },
      { id: 2, code: 'MAT-002', name: '螺栓', status: 'OUT_OF_STOCK', quantity: 50, required_quantity: 100, type: 'RAW_MATERIAL', priority: 'URGENT', project_id: 1 },
    ];
    
    const mockProjects = [
      { id: 1, name: '项目A' }
    ];

    // 设置 mock 返回值
    materialApi.list.mockResolvedValue({ data: mockMaterials });
    projectApi.list.mockResolvedValue({ data: mockProjects });
    supplierApi.list.mockResolvedValue({ data: [] });
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useMaterialReadiness());

    // 等待 loading 变为 false
    await waitFor(() => expect(result.current.loading).toBe(false));

    // 验证数据已加载
    expect(result.current.materials).toBeDefined();
    expect(Array.isArray(result.current.materials)).toBe(true);
  });
});