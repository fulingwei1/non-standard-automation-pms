import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import ChartContainer, { useChartData } from '../ChartContainer';

describe('ChartContainer', () => {
  describe('Basic Rendering', () => {
    it('renders children when no loading or error', () => {
      render(
        <ChartContainer>
          <div data-testid="chart-content">图表内容</div>
        </ChartContainer>
      );

      expect(screen.getByTestId('chart-content')).toBeInTheDocument();
    });

    it('renders with title', () => {
      render(
        <ChartContainer title="销售趋势">
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('销售趋势')).toBeInTheDocument();
    });

    it('renders with description', () => {
      render(
        <ChartContainer
          title="销售趋势"
          description="过去30天的销售数据"
        >
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('过去30天的销售数据')).toBeInTheDocument();
    });

    it('renders header actions', () => {
      const actions = <button>导出</button>;
      render(
        <ChartContainer title="图表" headerActions={actions}>
          <div>内容</div>
        </ChartContainer>
      );

      expect(screen.getByText('导出')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading state', () => {
      render(
        <ChartContainer loading={true}>
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('shows spinner in loading state', () => {
      const { container } = render(
        <ChartContainer loading={true}>
          <div>图表</div>
        </ChartContainer>
      );

      expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('displays title in loading state', () => {
      render(
        <ChartContainer loading={true} title="数据图表">
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('数据图表')).toBeInTheDocument();
    });

    it('does not render children in loading state', () => {
      render(
        <ChartContainer loading={true}>
          <div data-testid="chart">图表</div>
        </ChartContainer>
      );

      expect(screen.queryByTestId('chart')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error message', () => {
      render(
        <ChartContainer error="数据加载失败">
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('数据加载失败')).toBeInTheDocument();
    });

    it('shows error icon', () => {
      const { container } = render(
        <ChartContainer error="错误">
          <div>图表</div>
        </ChartContainer>
      );

      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('displays retry button when onRetry is provided', () => {
      render(
        <ChartContainer error="错误" onRetry={() => {}}>
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('重试')).toBeInTheDocument();
    });

    it('does not show retry button when onRetry is not provided', () => {
      render(
        <ChartContainer error="错误">
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.queryByText('重试')).not.toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', () => {
      const handleRetry = vi.fn();
      render(
        <ChartContainer error="错误" onRetry={handleRetry}>
          <div>图表</div>
        </ChartContainer>
      );

      const retryButton = screen.getByText('重试');
      fireEvent.click(retryButton);

      expect(handleRetry).toHaveBeenCalledTimes(1);
    });

    it('does not render children in error state', () => {
      render(
        <ChartContainer error="错误">
          <div data-testid="chart">图表</div>
        </ChartContainer>
      );

      expect(screen.queryByTestId('chart')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays default empty text', () => {
      render(
        <ChartContainer empty={true}>
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });

    it('displays custom empty text', () => {
      render(
        <ChartContainer empty={true} emptyText="没有找到数据">
          <div>图表</div>
        </ChartContainer>
      );

      expect(screen.getByText('没有找到数据')).toBeInTheDocument();
    });

    it('shows empty icon', () => {
      const { container } = render(
        <ChartContainer empty={true}>
          <div>图表</div>
        </ChartContainer>
      );

      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('does not render children in empty state', () => {
      render(
        <ChartContainer empty={true}>
          <div data-testid="chart">图表</div>
        </ChartContainer>
      );

      expect(screen.queryByTestId('chart')).not.toBeInTheDocument();
    });
  });

  describe('Height Customization', () => {
    it('uses default height', () => {
      const { container } = render(
        <ChartContainer loading={true}>
          <div>图表</div>
        </ChartContainer>
      );

      const loadingContainer = container.querySelector(
        '.flex.flex-col.items-center'
      );
      expect(loadingContainer).toHaveStyle({ height: '300px' });
    });

    it('uses custom height', () => {
      const { container } = render(
        <ChartContainer loading={true} height={500}>
          <div>图表</div>
        </ChartContainer>
      );

      const loadingContainer = container.querySelector(
        '.flex.flex-col.items-center'
      );
      expect(loadingContainer).toHaveStyle({ height: '500px' });
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <ChartContainer className="custom-chart">
          <div>图表</div>
        </ChartContainer>
      );

      expect(container.querySelector('.custom-chart')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for normal state', () => {
      const { container } = render(
        <ChartContainer title="销售图表">
          <div>图表内容</div>
        </ChartContainer>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for loading state', () => {
      const { container } = render(
        <ChartContainer loading={true} title="加载中">
          <div>图表</div>
        </ChartContainer>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for error state', () => {
      const { container } = render(
        <ChartContainer error="加载失败" onRetry={() => {}}>
          <div>图表</div>
        </ChartContainer>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for empty state', () => {
      const { container } = render(
        <ChartContainer empty={true} emptyText="无数据">
          <div>图表</div>
        </ChartContainer>
      );
      expect(container).toMatchSnapshot();
    });
  });
});

describe('useChartData Hook', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  describe('Basic Functionality', () => {
    it('fetches data on mount', async () => {
      const fetchFn = vi.fn().mockResolvedValue({ data: 'test' });
      const { result } = renderHook(() => useChartData(fetchFn));

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(fetchFn).toHaveBeenCalledTimes(1);
      expect(result.current.data).toEqual({ data: 'test' });
    });

    it('handles errors', async () => {
      const fetchFn = vi.fn().mockRejectedValue(new Error('加载失败'));
      const { result } = renderHook(() => useChartData(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('加载失败');
      expect(result.current.data).toBe(null);
    });

    it('transforms data', async () => {
      const fetchFn = vi.fn().mockResolvedValue([1, 2, 3]);
      const transform = (data) => data.map((x) => x * 2);

      const { result } = renderHook(() =>
        useChartData(fetchFn, [], { transform })
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual([2, 4, 6]);
    });
  });

  describe('Caching', () => {
    it.skip('caches data when cacheKey is provided', async () => {
      const fetchFn = vi.fn().mockResolvedValue({ value: 100 });
      const { result } = renderHook(() =>
        useChartData(fetchFn, [], { cacheKey: 'test-cache' })
      );

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const cached = sessionStorage.getItem('test-cache');
      expect(cached).toBeTruthy();

      const parsed = JSON.parse(cached);
      expect(parsed.data).toEqual({ value: 100 });
      expect(parsed.timestamp).toBeDefined();
    });

    it.skip('uses cached data within cache duration', async () => {
      const fetchFn = vi.fn().mockResolvedValue({ value: 100 });

      // First render - should fetch
      const { result: result1, unmount } = renderHook(() =>
        useChartData(fetchFn, [], {
          cacheKey: 'test-cache',
          cacheDuration: 10000,
        })
      );

      await waitFor(() => {
        expect(result1.current.loading).toBe(false);
      });

      expect(fetchFn).toHaveBeenCalledTimes(1);
      unmount();

      // Second render - should use cache
      const { result: result2 } = renderHook(() =>
        useChartData(fetchFn, [], {
          cacheKey: 'test-cache',
          cacheDuration: 10000,
        })
      );

      await waitFor(() => {
        expect(result2.current.loading).toBe(false);
      });

      // Should still be called only once (used cache)
      expect(fetchFn).toHaveBeenCalledTimes(1);
      expect(result2.current.data).toEqual({ value: 100 });
    });
  });

  describe('Refetch', () => {
    it('refetches data when refetch is called', async () => {
      const fetchFn = vi.fn().mockResolvedValue({ count: 1 });
      const { result } = renderHook(() => useChartData(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      fetchFn.mockResolvedValue({ count: 2 });

      act(() => {
        result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(fetchFn).toHaveBeenCalledTimes(2);
      expect(result.current.data).toEqual({ count: 2 });
    });
  });

  describe('SetData', () => {
    it('allows manual data update', async () => {
      const fetchFn = vi.fn().mockResolvedValue({ value: 1 });
      const { result } = renderHook(() => useChartData(fetchFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      act(() => {
        result.current.setData({ value: 999 });
      });

      expect(result.current.data).toEqual({ value: 999 });
    });
  });
});
