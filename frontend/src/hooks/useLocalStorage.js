import { useState, useEffect, useCallback } from 'react';

/**
 * LocalStorage Hook
 * 
 * 在localStorage中持久化状态
 * 
 * @param {string} key - localStorage键名
 * @param {any} initialValue - 初始值
 * 
 * @example
 * const [theme, setTheme] = useLocalStorage('theme', 'dark');
 */
export function useLocalStorage(key, initialValue) {
    // 获取初始值
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(`Error reading localStorage key "${key}":`, error);
            return initialValue;
        }
    });

    // 设置值
    const setValue = useCallback((value) => {
        try {
            // 允许传入函数
            const valueToStore = value instanceof Function ? value(storedValue) : value;
            setStoredValue(valueToStore);
            window.localStorage.setItem(key, JSON.stringify(valueToStore));
        } catch (error) {
            console.error(`Error setting localStorage key "${key}":`, error);
        }
    }, [key, storedValue]);

    // 删除值
    const removeValue = useCallback(() => {
        try {
            window.localStorage.removeItem(key);
            setStoredValue(initialValue);
        } catch (error) {
            console.error(`Error removing localStorage key "${key}":`, error);
        }
    }, [key, initialValue]);

    return [storedValue, setValue, removeValue];
}
