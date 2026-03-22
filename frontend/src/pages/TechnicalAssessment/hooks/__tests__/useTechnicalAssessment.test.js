import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTechnicalAssessment } from '../useTechnicalAssessment';
import { presaleWorkbenchApi } from '../../../../services/api';

// Mock react-router-dom（hook 内部依赖 useParams / useSearchParams）
vi.mock('react-router-dom', () => ({
  useParams: () => ({ sourceType: 'lead', sourceId: '1' }),
  useSearchParams: () => [new URLSearchParams('')],
}));

// Mock API
vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    presaleWorkbenchApi: {
      loadContext: vi.fn(),
      loadAssessmentArtifacts: vi.fn(),
      applyAssessment: vi.fn(),
      evaluateAssessment: vi.fn(),
      saveRequirementDetail: vi.fn(),
      unwrapResponse: vi.fn((r) => r),
    },
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});

describe('useTechnicalAssessment Hook', () => {
  const mockWorkbench = {
    assessment: { items: [], current: null, requirementDetail: null, risks: { items: [], total: 0 }, versions: { items: [], total: 0 } },
    templates: { assessment: { items: [] }, technical: { items: [] } },
    solutions: { items: [] },
    funnel: { gateConfigs: { items: [] }, stages: { items: [] }, transitionLogs: { items: [] }, dwellAlerts: { items: [] } },
    meta: { failures: [] },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    presaleWorkbenchApi.loadContext.mockResolvedValue(mockWorkbench);
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useTechnicalAssessment());

    // 等待初始加载完成
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current).toBeDefined();
    expect(result.current.assessments).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
      sourceType: 'lead',
      sourceId: 1,
      presaleTicketId: null,
    });
  });
});
