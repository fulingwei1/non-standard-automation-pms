/**
 * useLocalStorage Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '../useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    // 清空 localStorage
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should initialize with initial value when localStorage is empty', () => {
    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    expect(result.current[0]).toBe('initialValue');
  });

  it('should initialize with value from localStorage if exists', () => {
    localStorage.setItem('testKey', JSON.stringify('storedValue'));

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    expect(result.current[0]).toBe('storedValue');
  });

  it('should update localStorage when value changes', () => {
    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    act(() => {
      result.current[1]('newValue');
    });

    expect(result.current[0]).toBe('newValue');
    expect(localStorage.getItem('testKey')).toBe(JSON.stringify('newValue'));
  });

  it('should support function updates', () => {
    const { result } = renderHook(() => 
      useLocalStorage('counter', 0)
    );

    act(() => {
      result.current[1](prev => prev + 1);
    });

    expect(result.current[0]).toBe(1);
    expect(localStorage.getItem('counter')).toBe(JSON.stringify(1));
  });

  it('should handle complex objects', () => {
    const complexObject = {
      id: 1,
      name: 'Test',
      nested: { value: 'nested' },
      array: [1, 2, 3]
    };

    const { result } = renderHook(() => 
      useLocalStorage('complexKey', null)
    );

    act(() => {
      result.current[1](complexObject);
    });

    expect(result.current[0]).toEqual(complexObject);
    expect(JSON.parse(localStorage.getItem('complexKey'))).toEqual(complexObject);
  });

  it('should remove value from localStorage', () => {
    localStorage.setItem('testKey', JSON.stringify('value'));

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    expect(result.current[0]).toBe('value');

    act(() => {
      result.current[2](); // removeValue
    });

    expect(result.current[0]).toBe('initialValue');
    expect(localStorage.getItem('testKey')).toBe(null);
  });

  it('should handle JSON parse errors gracefully', () => {
    // 设置无效的 JSON
    localStorage.setItem('badKey', 'invalid-json{');
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => 
      useLocalStorage('badKey', 'fallback')
    );

    expect(result.current[0]).toBe('fallback');
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should handle localStorage setItem errors', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // 模拟 localStorage.setItem 抛出错误
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('QuotaExceededError');
    });

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    act(() => {
      result.current[1]('newValue');
    });

    expect(consoleErrorSpy).toHaveBeenCalled();

    setItemSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it('should handle localStorage removeItem errors', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('RemoveError');
    });

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    act(() => {
      result.current[2](); // removeValue
    });

    expect(consoleErrorSpy).toHaveBeenCalled();

    removeItemSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it('should handle boolean values', () => {
    const { result } = renderHook(() => 
      useLocalStorage('boolKey', false)
    );

    act(() => {
      result.current[1](true);
    });

    expect(result.current[0]).toBe(true);
    expect(localStorage.getItem('boolKey')).toBe('true');
  });

  it('should handle null values', () => {
    const { result } = renderHook(() => 
      useLocalStorage('nullKey', null)
    );

    act(() => {
      result.current[1]({ value: 'test' });
    });

    expect(result.current[0]).toEqual({ value: 'test' });

    act(() => {
      result.current[1](null);
    });

    expect(result.current[0]).toBe(null);
    expect(localStorage.getItem('nullKey')).toBe('null');
  });

  it('should persist across re-renders', () => {
    const { result, rerender } = renderHook(() => 
      useLocalStorage('persistKey', 'initial')
    );

    act(() => {
      result.current[1]('updated');
    });

    rerender();

    expect(result.current[0]).toBe('updated');
  });
});
