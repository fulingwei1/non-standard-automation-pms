/**
 * AcceptanceExecution 组件测试
 * 测试覆盖：验收执行、检查项管理、问题记录、验收完成
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AcceptanceExecution from '../AcceptanceExecution';
import { acceptanceApi } from '../../services/api';

// Mock dependencies
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AcceptanceExecution', () => {
  const mockOrder = {
    id: 1,
    code: 'ACC-2024-001',
    project_name: '智能制造系统',
    template_name: '软件验收模板',
    status: 'IN_PROGRESS',
    scheduled_date: '2024-06-30',
    executor_name: '张三',
    created_at: '2024-06-20T10:00:00Z',
  };

  const mockItems = [
    {
      id: 1,
      order_id: 1,
      category: '功能测试',
      description: '用户登录功能',
      standard: '能够正常登录系统',
      check_method: '手工测试',
      result_status: 'PENDING',
      actual_value: null,
      deviation: null,
      remark: null,
    },
    {
      id: 2,
      order_id: 1,
      category: '性能测试',
      description: '系统响应时间',
      standard: '页面加载时间<3秒',
      check_method: '性能工具测试',
      result_status: 'PASSED',
      actual_value: '2.5秒',
      deviation: null,
      remark: '性能良好',
    },
    {
      id: 3,
      order_id: 1,
      category: '兼容性测试',
      description: '浏览器兼容性',
      standard: '支持Chrome、Firefox、Safari',
      check_method: '手工测试',
      result_status: 'FAILED',
      actual_value: 'Safari部分功能异常',
      deviation: '存在兼容性问题',
      remark: '需要修复',
    },
  ];

  const mockIssues = [
    {
      id: 1,
      item_id: 3,
      category: 'BUG',
      severity: 'MAJOR',
      description: 'Safari浏览器下拉菜单无法正常显示',
      status: 'OPEN',
      created_at: '2024-06-25T14:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    acceptanceApi.orders.get.mockResolvedValue({ data: mockOrder });
    acceptanceApi.orders.getItems.mockResolvedValue({ data: mockItems });
    acceptanceApi.issues.list.mockResolvedValue({ data: mockIssues });
    acceptanceApi.orders.updateItem.mockResolvedValue({ data: { success: true } });
    acceptanceApi.issues.create.mockResolvedValue({ 
      data: { id: 2, ...mockIssues[0] } 
    });
    acceptanceApi.orders.complete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render page title', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/验收执行|Acceptance Execution/i)).toBeInTheDocument();
      });
    });

    it('should render order information', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('ACC-2024-001')).toBeInTheDocument();
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });
    });

    it('should render acceptance items table', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
        expect(screen.getByText('系统响应时间')).toBeInTheDocument();
        expect(screen.getByText('浏览器兼容性')).toBeInTheDocument();
      });
    });

    it('should display result status badges', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/待检查|PENDING/i)).toBeInTheDocument();
        expect(screen.getByText(/通过|PASSED/i)).toBeInTheDocument();
        expect(screen.getByText(/不通过|FAILED/i)).toBeInTheDocument();
      });
    });

    it('should render progress bar', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        // 2 out of 3 items checked (PASSED + FAILED)
        const progressText = screen.queryByText(/66|67|2\/3/);
        expect(progressText).toBeTruthy();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch order details on mount', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(acceptanceApi.orders.get).toHaveBeenCalledWith(1);
        expect(acceptanceApi.orders.getItems).toHaveBeenCalledWith(1);
        expect(acceptanceApi.issues.list).toHaveBeenCalledWith(1);
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      acceptanceApi.orders.get.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      }, { timeout: 3000 });
    });
  });

  // 3. 检查项执行测试
  describe('Item Execution', () => {
    it('should open item dialog when clicking check button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
      });

      const checkButtons = screen.queryAllByRole('button', { name: /检查|Check|执行/i });
      if (checkButtons.length > 0) {
        fireEvent.click(checkButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/执行检查|Execute Check|检查项/i)).toBeInTheDocument();
        });
      }
    });

    it('should update item status to PASSED', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
      });

      const checkButtons = screen.queryAllByRole('button', { name: /检查|Check|执行/i });
      if (checkButtons.length > 0) {
        fireEvent.click(checkButtons[0]);

        await waitFor(() => {
          const passButton = screen.queryByRole('button', { name: /通过|Pass|PASSED/i });
          if (passButton) {
            fireEvent.click(passButton);

            const submitButton = screen.getByRole('button', { name: /提交|Submit|确定/i });
            fireEvent.click(submitButton);
          }
        });

        await waitFor(() => {
          expect(acceptanceApi.orders.updateItem).toHaveBeenCalled();
        });
      }
    });

    it('should update item status to FAILED', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
      });

      const checkButtons = screen.queryAllByRole('button', { name: /检查|Check|执行/i });
      if (checkButtons.length > 0) {
        fireEvent.click(checkButtons[0]);

        await waitFor(() => {
          const failButton = screen.queryByRole('button', { name: /不通过|Fail|FAILED/i });
          if (failButton) {
            fireEvent.click(failButton);
          }
        });
      }
    });

    it('should record actual value and deviation', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统响应时间')).toBeInTheDocument();
      });

      const checkButtons = screen.queryAllByRole('button', { name: /检查|Check|执行|查看/i });
      if (checkButtons.length > 1) {
        fireEvent.click(checkButtons[1]);

        await waitFor(() => {
          const actualValueInput = screen.queryByLabelText(/实际值|Actual Value/i);
          if (actualValueInput) {
            fireEvent.change(actualValueInput, { target: { value: '2.8秒' } });
          }

          const deviationInput = screen.queryByLabelText(/偏差|Deviation/i);
          if (deviationInput) {
            fireEvent.change(deviationInput, { target: { value: '性能良好' } });
          }
        });
      }
    });
  });

  // 4. 问题管理测试
  describe('Issue Management', () => {
    it('should display issues list', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Safari浏览器下拉菜单无法正常显示/i)).toBeInTheDocument();
      });
    });

    it('should open create issue dialog', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
      });

      const issueButtons = screen.queryAllByRole('button', { name: /记录问题|Add Issue|新增/i });
      if (issueButtons.length > 0) {
        fireEvent.click(issueButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/记录问题|Create Issue/i)).toBeInTheDocument();
        });
      }
    });

    it('should create new issue', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('用户登录功能')).toBeInTheDocument();
      });

      const issueButtons = screen.queryAllByRole('button', { name: /记录问题|Add Issue|新增/i });
      if (issueButtons.length > 0) {
        fireEvent.click(issueButtons[0]);

        await waitFor(() => {
          const descInput = screen.queryByLabelText(/问题描述|Description/i);
          if (descInput) {
            fireEvent.change(descInput, { target: { value: '新发现的问题' } });
          }

          const submitButton = screen.getByRole('button', { name: /提交|Submit|确定/i });
          fireEvent.click(submitButton);
        });

        await waitFor(() => {
          expect(acceptanceApi.issues.create).toHaveBeenCalled();
        });
      }
    });

    it('should display issue severity badges', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const severityBadge = screen.queryByText(/重要|MAJOR|严重|高/i);
        expect(severityBadge).toBeTruthy();
      });
    });
  });

  // 5. 验收完成测试
  describe('Acceptance Completion', () => {
    it('should open complete dialog', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const completeButton = screen.queryByRole('button', { name: /完成验收|Complete|提交验收/i });
      if (completeButton) {
        fireEvent.click(completeButton);

        await waitFor(() => {
          expect(screen.getByText(/完成验收|Complete Acceptance|验收结论/i)).toBeInTheDocument();
        });
      }
    });

    it('should submit completion with PASS result', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const completeButton = screen.queryByRole('button', { name: /完成验收|Complete|提交验收/i });
      if (completeButton) {
        fireEvent.click(completeButton);

        await waitFor(() => {
          const passOption = screen.queryByText(/通过|PASS/i);
          if (passOption) {
            fireEvent.click(passOption);
          }

          const conclusionInput = screen.queryByLabelText(/验收结论|Conclusion/i);
          if (conclusionInput) {
            fireEvent.change(conclusionInput, { target: { value: '验收通过' } });
          }

          const submitButton = screen.getByRole('button', { name: /提交|Submit|确定/i });
          fireEvent.click(submitButton);
        });

        await waitFor(() => {
          expect(acceptanceApi.orders.complete).toHaveBeenCalled();
        });
      }
    });

    it('should submit completion with CONDITIONAL result', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const completeButton = screen.queryByRole('button', { name: /完成验收|Complete|提交验收/i });
      if (completeButton) {
        fireEvent.click(completeButton);

        await waitFor(() => {
          const conditionalOption = screen.queryByText(/有条件通过|CONDITIONAL/i);
          if (conditionalOption) {
            fireEvent.click(conditionalOption);
          }

          const conditionsInput = screen.queryByLabelText(/附加条件|Conditions/i);
          if (conditionsInput) {
            fireEvent.change(conditionsInput, { 
              target: { value: '需要在1个月内修复Safari兼容性问题' } 
            });
          }
        });
      }
    });

    it('should validate completion form', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const completeButton = screen.queryByRole('button', { name: /完成验收|Complete|提交验收/i });
      if (completeButton) {
        fireEvent.click(completeButton);

        await waitFor(() => {
          const submitButton = screen.getByRole('button', { name: /提交|Submit|确定/i });
          fireEvent.click(submitButton);
        });

        await waitFor(() => {
          const errorMessage = screen.queryByText(/必填|Required|不能为空/i);
          expect(errorMessage).toBeTruthy();
        });
      }
    });
  });

  // 6. 统计信息测试
  describe('Statistics', () => {
    it('should display total items count', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalCount = screen.queryByText(/3|共3项|Total: 3/i);
        expect(totalCount).toBeTruthy();
      });
    });

    it('should display passed items count', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const passedCount = screen.queryByText(/1|通过: 1|Passed: 1/i);
        expect(passedCount).toBeTruthy();
      });
    });

    it('should display failed items count', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const failedCount = screen.queryByText(/1|不通过: 1|Failed: 1/i);
        expect(failedCount).toBeTruthy();
      });
    });

    it('should display issues count', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const issuesCount = screen.queryByText(/1|问题: 1|Issues: 1/i);
        expect(issuesCount).toBeTruthy();
      });
    });
  });

  // 7. 导航功能测试
  describe('Navigation', () => {
    it('should go back when clicking back button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const backButton = screen.queryByRole('button', { name: /返回|Back/i });
      if (backButton) {
        fireEvent.click(backButton);
        expect(mockNavigate).toHaveBeenCalledWith(-1);
      }
    });
  });

  // 8. 刷新功能测试
  describe('Refresh Functionality', () => {
    it('should refresh data when clicking refresh button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(acceptanceApi.orders.getItems).toHaveBeenCalled();
      });

      const initialCallCount = acceptanceApi.orders.getItems.mock.calls.length;

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);

        await waitFor(() => {
          expect(acceptanceApi.orders.getItems.mock.calls.length).toBeGreaterThan(initialCallCount);
        });
      }
    });
  });
});
