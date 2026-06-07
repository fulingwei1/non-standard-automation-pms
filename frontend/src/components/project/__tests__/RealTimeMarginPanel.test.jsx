import { render, waitFor } from '@testing-library/react';
import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import RealTimeMarginPanel from '../RealTimeMarginPanel';
import { api } from '../../../services/api/client';

vi.mock('../../../hooks/usePermission', () => ({
  PERMISSIONS: {
    MARGIN: { READ: 'margin:read', READ_ALL: 'margin:read:all' },
    FINANCE: { REPORT_READ: 'finance:report:read' },
  },
  usePermission: () => ({
    hasAnyPermission: vi.fn(() => true),
  }),
}));

describe('RealTimeMarginPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads presale estimates through the registered solution proposal routes', async () => {
    api.get.mockImplementation((url, config) => {
      if (url === '/projects/7/costs/summary') {
        return Promise.resolve({
          data: {
            total_cost: 50000,
            by_type: { MECHANICAL: 30000, ELECTRICAL: 20000 },
          },
        });
      }

      if (url === '/projects/7/cost-estimate') {
        return Promise.reject(new Error('cost estimate endpoint unavailable'));
      }

      if (url === '/presale/proposals/solutions' && config?.params?.project_id === 7) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 55,
                name: '项目关联方案',
                project_id: 7,
                opportunity_id: 90,
                estimated_cost: 80000,
                suggested_price: 120000,
                review_status: 'APPROVED',
                created_at: '2026-06-01T00:00:00',
              },
            ],
            total: 1,
          },
        });
      }

      if (url === '/presale/proposals/solutions' && config?.params?.opportunity_id === 90) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 55,
                name: '项目关联方案',
                project_id: 7,
                opportunity_id: 90,
                estimated_cost: 80000,
                suggested_price: 120000,
                review_status: 'APPROVED',
              },
            ],
            total: 1,
          },
        });
      }

      if (url === '/presale/proposals/solutions/55/cost') {
        return Promise.resolve({
          data: {
            solution_id: 55,
            total_cost: 80000,
            breakdown: [
              { category: 'MECHANICAL', amount: 50000 },
              { category: 'ELECTRICAL', amount: 30000 },
            ],
          },
        });
      }

      return Promise.reject(new Error(`unexpected request: ${url}`));
    });

    render(
      React.createElement(RealTimeMarginPanel, {
        project: {
          id: 7,
          opportunity_id: 90,
          contract_amount: 120000,
          budget_amount: 90000,
        },
      }),
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/presale/proposals/solutions', {
        params: { project_id: 7 },
      });
      expect(api.get).toHaveBeenCalledWith('/presale/proposals/solutions', {
        params: { opportunity_id: 90 },
      });
      expect(api.get).toHaveBeenCalledWith('/presale/proposals/solutions/55/cost');
    });
  });
});
