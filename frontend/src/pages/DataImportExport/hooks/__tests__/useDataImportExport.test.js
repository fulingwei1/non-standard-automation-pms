import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDataImportExport } from '../useDataImportExport';
import { dataImportExportApi } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', () => {
  return {
    dataImportExportApi: {
      getTemplateTypes: vi.fn(),
      downloadTemplate: vi.fn(),
      previewImport: vi.fn(),
      uploadImport: vi.fn(),
      exportProjectList: vi.fn()
    }
  };
});

describe('useDataImportExport Hook', () => {
  const mockTemplateTypes = { types: [{ type: 'project', name: 'Project' }] };

  beforeEach(() => {
    vi.clearAllMocks();
    dataImportExportApi.getTemplateTypes.mockResolvedValue({ data: { data: mockTemplateTypes } });
  });

  it('should load template types on mount', async () => {
    const { result } = renderHook(() => useDataImportExport());

    // The hook calls loadTemplateTypes inside useEffect
    // Since it's async but doesn't set loading state for this specific call in useEffect (only sets templateTypes),
    // we wait for the state update.
    await waitFor(() => {
      expect(result.current.templateTypes).toEqual(mockTemplateTypes.types);
    });
    expect(dataImportExportApi.getTemplateTypes).toHaveBeenCalled();
  });

  it('handlePreviewImport should call api', async () => {
    const { result } = renderHook(() => useDataImportExport());

    act(() => {
      result.current.setImportFile(new File([''], 'test.xlsx'));
      result.current.setSelectedTemplateType('project');
    });

    dataImportExportApi.previewImport.mockResolvedValue({ data: { data: { total_rows: 10, valid_rows: 10 } } });

    await act(async () => {
      await result.current.handlePreviewImport();
    });

    expect(result.current.previewData).toEqual({ total_rows: 10, valid_rows: 10 });
    expect(result.current.success).toContain('预览成功');
  });
});
