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

  it('renders visible items with required props', () => {
    render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={300}
        renderItem={mockRenderItem}
      />
    );

    expect(mockRenderItem).toHaveBeenCalled();
    expect(screen.getByTestId('item-0')).toBeInTheDocument();
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
    expect(mockRenderItem).not.toHaveBeenCalled();
  });

  it('applies custom className to scroll container', () => {
    const { container } = render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={300}
        renderItem={mockRenderItem}
        className="custom-class"
      />
    );

    const scrollContainer = container.querySelector('.custom-class');
    expect(scrollContainer).toBeInTheDocument();
    expect(scrollContainer.className).toContain('custom-class');
  });

  it('renders fewer items than full list for virtualization', () => {
    render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={300}
        renderItem={mockRenderItem}
        overscan={0}
      />
    );

    expect(mockRenderItem.mock.calls.length).toBeLessThan(mockItems.length);
  });

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
    expect(screen.getByTestId('item-0')).toBeInTheDocument();
  });

  it('calls onScroll with new scrollTop', () => {
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

  it('renders different visible items after scrolling', () => {
    const { container } = render(
      <VirtualizedList
        items={mockItems}
        itemHeight={50}
        containerHeight={300}
        renderItem={mockRenderItem}
      />
    );

    const scrollContainer = container.querySelector('.overflow-auto');
    fireEvent.scroll(scrollContainer, { target: { scrollTop: 500 } });

    expect(screen.getByTestId('item-7')).toBeInTheDocument();
  });

  it('handles single item list', () => {
    render(
      <VirtualizedList
        items={[{ id: 0, name: 'Single Item' }]}
        itemHeight={50}
        containerHeight={300}
        renderItem={mockRenderItem}
      />
    );

    expect(mockRenderItem).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Single Item')).toBeInTheDocument();
  });
});
