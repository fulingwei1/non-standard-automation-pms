/**
 * useModal Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useModal } from '../useModal';

describe('useModal', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with default closed state', () => {
    const { result } = renderHook(() => useModal());

    expect(result.current.isOpen).toBe(false);
    expect(result.current.data).toBe(null);
  });

  it('should initialize with custom initial state', () => {
    const { result } = renderHook(() => useModal(true));

    expect(result.current.isOpen).toBe(true);
  });

  it('should open modal without data', () => {
    const { result } = renderHook(() => useModal());

    act(() => {
      result.current.open();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.data).toBe(null);
  });

  it('should open modal with data', () => {
    const { result } = renderHook(() => useModal());
    const testData = { id: 1, name: 'Test' };

    act(() => {
      result.current.open(testData);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.data).toEqual(testData);
  });

  it('should close modal', () => {
    const { result } = renderHook(() => useModal(true));

    act(() => {
      result.current.close();
    });

    expect(result.current.isOpen).toBe(false);
  });

  it('should clear data after close animation delay', () => {
    const { result } = renderHook(() => useModal());
    const testData = { id: 1, name: 'Test' };

    act(() => {
      result.current.open(testData);
    });

    expect(result.current.data).toEqual(testData);

    act(() => {
      result.current.close();
    });

    // 数据应该还在（延迟清除）
    expect(result.current.data).toEqual(testData);

    // 快进 200ms
    act(() => {
      vi.advanceTimersByTime(200);
    });

    // 现在数据应该被清除了
    expect(result.current.data).toBe(null);
  });

  it('should toggle modal state', () => {
    const { result } = renderHook(() => useModal(false));

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isOpen).toBe(true);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isOpen).toBe(false);
  });

  it('should set data directly', () => {
    const { result } = renderHook(() => useModal());
    const testData = { id: 1, name: 'Test' };

    act(() => {
      result.current.setData(testData);
    });

    expect(result.current.data).toEqual(testData);
  });

  it('should update data partially', () => {
    const { result } = renderHook(() => useModal());
    const initialData = { id: 1, name: 'Original', status: 'active' };

    act(() => {
      result.current.open(initialData);
    });

    act(() => {
      result.current.updateData({ name: 'Updated' });
    });

    expect(result.current.data).toEqual({
      id: 1,
      name: 'Updated',
      status: 'active'
    });
  });

  it('should handle multiple open calls', () => {
    const { result } = renderHook(() => useModal());
    
    act(() => {
      result.current.open({ id: 1 });
    });

    expect(result.current.data).toEqual({ id: 1 });

    act(() => {
      result.current.open({ id: 2 });
    });

    expect(result.current.data).toEqual({ id: 2 });
    expect(result.current.isOpen).toBe(true);
  });

  it('should handle complex data objects', () => {
    const { result } = renderHook(() => useModal());
    const complexData = {
      id: 1,
      user: { name: 'John', email: 'john@test.com' },
      tags: ['tag1', 'tag2'],
      metadata: { created: '2024-01-01' }
    };

    act(() => {
      result.current.open(complexData);
    });

    expect(result.current.data).toEqual(complexData);
  });

  it('should maintain data when toggling from open to close', () => {
    const { result } = renderHook(() => useModal(true));
    const testData = { id: 1 };

    act(() => {
      result.current.setData(testData);
    });

    act(() => {
      result.current.toggle();
    });

    // 立即检查，数据应该还在
    expect(result.current.data).toEqual(testData);
  });

  it('should return stable function references', () => {
    const { result, rerender } = renderHook(() => useModal());

    const firstOpen = result.current.open;
    const firstClose = result.current.close;
    const firstToggle = result.current.toggle;

    rerender();

    expect(result.current.open).toBe(firstOpen);
    expect(result.current.close).toBe(firstClose);
    expect(result.current.toggle).toBe(firstToggle);
  });
});
