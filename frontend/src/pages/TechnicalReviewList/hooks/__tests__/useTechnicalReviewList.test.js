import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSearchParams } from 'react-router-dom';
import { useTechnicalReviewList } from '../useTechnicalReviewList';
import { projectApi, technicalReviewApi } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    projectApi: {
    list: vi.fn(),
    get: vi.fn(),
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    aiMatch: vi.fn(),
    getOverdue: vi.fn(),
    getAging: vi.fn(),
    getSummary: vi.fn(),
    batch: vi.fn(),
    export: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    start: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
  },
  technicalReviewApi: {
    list: vi.fn(),
    get: vi.fn(),
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    aiMatch: vi.fn(),
    getOverdue: vi.fn(),
    getAging: vi.fn(),
    getSummary: vi.fn(),
    batch: vi.fn(),
    export: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    start: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
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

describe('useTechnicalReviewList Hook', () => {
  const mockReviews = [
    {
      id: 1,
      review_no: 'TR-PDR-001',
      review_name: '合同转项目 PDR',
      project_id: 42,
    },
  ];
  const mockProjects = [
    { id: 42, project_code: 'PRJ-42', project_name: '合同转项目' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([
      new URLSearchParams('project_id=42'),
      vi.fn(),
    ]);
    technicalReviewApi.list.mockResolvedValue({
      data: { items: mockReviews, total: 1 },
    });
    projectApi.list.mockResolvedValue({
      data: { items: mockProjects, total: 1 },
    });
  });

  it('scopes technical reviews by project context from the URL', async () => {
    const { result } = renderHook(() => useTechnicalReviewList());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.projectId).toBe('42');
    expect(technicalReviewApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      project_id: '42',
    });
    expect(result.current.reviews).toEqual(mockReviews);
  });
});
