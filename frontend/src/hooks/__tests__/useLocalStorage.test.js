/**
 * useLocalStorage Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from '../useLocalStorage';

describe('useLocalStorage', () => {
  // Use a real-ish storage map since global localStorage is mocked with vi.fn()
  let storageMap;

  beforeEach(() => {
    storageMap = {};
    vi.clearAllMocks();
    
    // Configure the global localStorage mock to behave like real localStorage
    localStorage.getItem.mockImplementation((key) => storageMap[key] ?? null);
    localStorage.setItem.mockImplementation((key, value) => {
      storageMap[key] = String(value);
    });
    localStorage.removeItem.mockImplementation((key) => {
      delete storageMap[key];
    });
    localStorage.clear.mockImplementation(() => {
      storageMap = {};
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with initial value when localStorage is empty', () => {
    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    expect(result.current[0]).toBe('initialValue');
  });

  it('should initialize with value from localStorage if exists', () => {
    storageMap['testKey'] = JSON.stringify('storedValue');

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
    expect(storageMap['testKey']).toBe(JSON.stringify('newValue'));
  });

  it('should support function updates', () => {
    const { result } = renderHook(() => 
      useLocalStorage('counter', 0)
    );

    act(() => {
      result.current[1](prev => prev + 1);
    });

    expect(result.current[0]).toBe(1);
    expect(storageMap['counter']).toBe(JSON.stringify(1));
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
    expect(JSON.parse(storageMap['complexKey'])).toEqual(complexObject);
  });

  it('should remove value from localStorage', () => {
    storageMap['testKey'] = JSON.stringify('value');

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    expect(result.current[0]).toBe('value');

    act(() => {
      result.current[2](); // removeValue
    });

    expect(result.current[0]).toBe('initialValue');
    expect(storageMap['testKey']).toBeUndefined();
  });

  it('should handle JSON parse errors gracefully', () => {
    storageMap['badKey'] = 'invalid-json{';
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
    
    localStorage.setItem.mockImplementation(() => {
      throw new Error('QuotaExceededError');
    });

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    act(() => {
      result.current[1]('newValue');
    });

    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should handle localStorage removeItem errors', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    localStorage.removeItem.mockImplementation(() => {
      throw new Error('RemoveError');
    });

    const { result } = renderHook(() => 
      useLocalStorage('testKey', 'initialValue')
    );

    act(() => {
      result.current[2](); // removeValue
    });

    expect(consoleErrorSpy).toHaveBeenCalled();

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
    expect(storageMap['boolKey']).toBe('true');
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
    expect(storageMap['nullKey']).toBe('null');
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
