import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import VirtualizedList from '../VirtualizedList';

describe('VirtualizedList', () => {
  const mockItems = Array.from({ length: 100 }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
  }));

  const mockRenderItem = vi.fn((item) => (
    <div data-testid={`item-${item.id}`}>{item.name}</div>
  ));

  beforeEach(() => {
    mockRenderItem.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders with required props', () => {
      render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('renders empty state when no items', () => {
      render(
        <VirtualizedList
          items={[]}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          className="custom-class"
        />
      );
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('sets container height correctly', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      const containerDiv = container.querySelector('div[style*="height"]');
      expect(containerDiv).toHaveStyle({ height: '300px' });
    });
  });

  describe('Virtualization', () => {
    it('only renders visible items initially', () => {
      render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          overscan={0}
        />
      );
      // Container height 300px / item height 50px = 6 visible items
      // Plus overscan items
      expect(mockRenderItem.mock.calls.length).toBeLessThan(mockItems.length);
    });

    it('renders with overscan buffer', () => {
      render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          overscan={3}
        />
      );
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('handles zero overscan', () => {
      render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          overscan={0}
        />
      );
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('calculates total height correctly', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      // Total height = 100 items * 50px = 5000px
      const innerDiv = container.querySelector('div[style*="height: 5000px"]');
      expect(innerDiv).toBeInTheDocument();
    });
  });

  describe('Dynamic Item Height', () => {
    it('supports function-based item height', () => {
      const getItemHeight = vi.fn((index) => (index % 2 === 0 ? 50 : 70));
      render(
        <VirtualizedList
          items={mockItems.slice(0, 10)}
          itemHeight={getItemHeight}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(getItemHeight).toHaveBeenCalled();
    });

    it('calculates correct total height with dynamic heights', () => {
      const getItemHeight = (index) => (index % 2 === 0 ? 50 : 70);
      const items = mockItems.slice(0, 10);
      const { container } = render(
        <VirtualizedList
          items={items}
          itemHeight={getItemHeight}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      // 5 items @ 50px + 5 items @ 70px = 600px
      const innerDiv = container.querySelector('div[style*="height: 600px"]');
      expect(innerDiv).toBeInTheDocument();
    });
  });

  describe('Scrolling Behavior', () => {
    it('handles scroll events', () => {
      const mockOnScroll = vi.fn();
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          onScroll={mockOnScroll}
        />
      );
      
      const scrollContainer = container.querySelector('.overflow-auto');
      fireEvent.scroll(scrollContainer, { target: { scrollTop: 100 } });
      
      expect(mockOnScroll).toHaveBeenCalledWith(100);
    });

    it('updates rendered items on scroll', () => {
      mockRenderItem.mockClear();
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      
      const _initialCallCount = mockRenderItem.mock.calls.length;
      mockRenderItem.mockClear();
      
      const scrollContainer = container.querySelector('.overflow-auto');
      fireEvent.scroll(scrollContainer, { target: { scrollTop: 500 } });
      
      // After scrolling, different items should be rendered
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('does not call onScroll when not provided', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      
      const scrollContainer = container.querySelector('.overflow-auto');
      expect(() => {
        fireEvent.scroll(scrollContainer, { target: { scrollTop: 100 } });
      }).not.toThrow();
    });
  });

  describe('Render Item Function', () => {
    it('passes correct item and index to renderItem', () => {
      render(
        <VirtualizedList
          items={mockItems.slice(0, 5)}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      
      expect(mockRenderItem).toHaveBeenCalledWith(
        expect.objectContaining({ id: 0, name: 'Item 0' }),
        0
      );
    });

    it('renders custom content from renderItem', () => {
      const customRender = (item) => (
        <div data-testid={`custom-${item.id}`}>
          Custom: {item.name}
        </div>
      );
      
      render(
        <VirtualizedList
          items={mockItems.slice(0, 5)}
          itemHeight={50}
          containerHeight={300}
          renderItem={customRender}
        />
      );
      
      expect(screen.getByTestId('custom-0')).toHaveTextContent('Custom: Item 0');
    });
  });

  describe('Edge Cases', () => {
    it('handles single item', () => {
      render(
        <VirtualizedList
          items={[{ id: 0, name: 'Single Item' }]}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(mockRenderItem).toHaveBeenCalledTimes(1);
    });

    it('handles container smaller than one item', () => {
      render(
        <VirtualizedList
          items={mockItems}
          itemHeight={100}
          containerHeight={50}
          renderItem={mockRenderItem}
        />
      );
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('handles container larger than all items', () => {
      render(
        <VirtualizedList
          items={mockItems.slice(0, 3)}
          itemHeight={50}
          containerHeight={1000}
          renderItem={mockRenderItem}
        />
      );
      expect(mockRenderItem).toHaveBeenCalledTimes(3);
    });

    it('handles zero item height', () => {
      render(
        <VirtualizedList
          items={mockItems.slice(0, 5)}
          itemHeight={0}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(mockRenderItem).toHaveBeenCalled();
    });

    it('handles very large lists', () => {
      const largeList = Array.from({ length: 10000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
      }));
      
      render(
        <VirtualizedList
          items={largeList}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      
      // Should only render visible items, not all 10000
      expect(mockRenderItem.mock.calls.length).toBeLessThan(100);
    });
  });

  describe('Performance', () => {
    it('does not re-render all items on scroll', () => {
      mockRenderItem.mockClear();
      const { container } = render(
        <VirtualizedList
          items={mockItems}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      
      const _initialCallCount = mockRenderItem.mock.calls.length;
      mockRenderItem.mockClear();
      
      const scrollContainer = container.querySelector('.overflow-auto');
      fireEvent.scroll(scrollContainer, { target: { scrollTop: 10 } });
      
      // Small scroll should not trigger full re-render
      const afterScrollCallCount = mockRenderItem.mock.calls.length;
      expect(afterScrollCallCount).toBeLessThanOrEqual(_initialCallCount);
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with items', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems.slice(0, 10)}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with empty state', () => {
      const { container } = render(
        <VirtualizedList
          items={[]}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with custom className', () => {
      const { container } = render(
        <VirtualizedList
          items={mockItems.slice(0, 5)}
          itemHeight={50}
          containerHeight={300}
          renderItem={mockRenderItem}
          className="custom-virtualized-list"
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
