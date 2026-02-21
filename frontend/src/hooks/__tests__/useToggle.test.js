/**
 * useToggle Hook 测试
 */

import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToggle } from '../useToggle';

describe('useToggle', () => {
  it('should initialize with false by default', () => {
    const { result } = renderHook(() => useToggle());

    expect(result.current[0]).toBe(false);
  });

  it('should initialize with custom initial value', () => {
    const { result } = renderHook(() => useToggle(true));

    expect(result.current[0]).toBe(true);
  });

  it('should toggle value', () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => {
      result.current[1]();
    });

    expect(result.current[0]).toBe(true);

    act(() => {
      result.current[1]();
    });

    expect(result.current[0]).toBe(false);
  });

  it('should set value using setValue', () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => {
      result.current[2].setValue(true);
    });

    expect(result.current[0]).toBe(true);

    act(() => {
      result.current[2].setValue(false);
    });

    expect(result.current[0]).toBe(false);
  });

  it('should set value to true using setTrue', () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => {
      result.current[2].setTrue();
    });

    expect(result.current[0]).toBe(true);

    // 再次调用应该保持为 true
    act(() => {
      result.current[2].setTrue();
    });

    expect(result.current[0]).toBe(true);
  });

  it('should set value to false using setFalse', () => {
    const { result } = renderHook(() => useToggle(true));

    act(() => {
      result.current[2].setFalse();
    });

    expect(result.current[0]).toBe(false);

    // 再次调用应该保持为 false
    act(() => {
      result.current[2].setFalse();
    });

    expect(result.current[0]).toBe(false);
  });

  it('should toggle multiple times correctly', () => {
    const { result } = renderHook(() => useToggle(false));

    for (let i = 0; i < 10; i++) {
      act(() => {
        result.current[1]();
      });
      expect(result.current[0]).toBe(i % 2 === 0);
    }
  });

  it('should maintain function references across re-renders', () => {
    const { result, rerender } = renderHook(() => useToggle());

    const firstToggle = result.current[1];
    const firstSetValue = result.current[2].setValue;
    const firstSetTrue = result.current[2].setTrue;
    const firstSetFalse = result.current[2].setFalse;

    rerender();

    expect(result.current[1]).toBe(firstToggle);
    expect(result.current[2].setValue).toBe(firstSetValue);
    expect(result.current[2].setTrue).toBe(firstSetTrue);
    expect(result.current[2].setFalse).toBe(firstSetFalse);
  });

  it('should work with all methods in sequence', () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => {
      result.current[2].setTrue();
    });
    expect(result.current[0]).toBe(true);

    act(() => {
      result.current[1]();
    });
    expect(result.current[0]).toBe(false);

    act(() => {
      result.current[2].setValue(true);
    });
    expect(result.current[0]).toBe(true);

    act(() => {
      result.current[2].setFalse();
    });
    expect(result.current[0]).toBe(false);
  });

  it('should handle rapid toggles', () => {
    const { result } = renderHook(() => useToggle(false));

    act(() => {
      result.current[1]();
      result.current[1]();
      result.current[1]();
    });

    // 应该切换 3 次：false -> true -> false -> true
    expect(result.current[0]).toBe(true);
  });

  it('should destructure correctly', () => {
    const { result } = renderHook(() => useToggle(false));

    const [value, toggle, { setValue, setTrue, setFalse }] = result.current;

    expect(value).toBe(false);
    expect(typeof toggle).toBe('function');
    expect(typeof setValue).toBe('function');
    expect(typeof setTrue).toBe('function');
    expect(typeof setFalse).toBe('function');
  });

  it('should accept boolean initial values', () => {
    const { result: result1 } = renderHook(() => useToggle(true));
    expect(result1.current[0]).toBe(true);

    const { result: result2 } = renderHook(() => useToggle(false));
    expect(result2.current[0]).toBe(false);
  });
});
