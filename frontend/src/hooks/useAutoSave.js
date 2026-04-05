import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * 表单自动保存 Hook
 *
 * 自动将表单数据保存到 localStorage，防止意外丢失。
 * 支持防抖保存、状态指示、手动恢复和清除。
 *
 * @param {string} key - localStorage 存储键名
 * @param {Object} data - 要自动保存的表单数据
 * @param {Object} options
 * @param {number} options.delay - 防抖延迟(ms)，默认 2000
 * @param {boolean} options.enabled - 是否启用自动保存，默认 true
 *
 * @returns {{ status, lastSavedAt, restore, clear, hasDraft }}
 *
 * @example
 * const { status, restore, clear, hasDraft } = useAutoSave('project_form', formData);
 *
 * // status: 'idle' | 'saving' | 'saved'
 * // restore() -> returns saved data or null
 * // clear() -> removes the draft
 * // hasDraft -> boolean
 */
export function useAutoSave(key, data, options = {}) {
  const { delay = 2000, enabled = true } = options;
  const [status, setStatus] = useState('idle'); // 'idle' | 'saving' | 'saved'
  const [lastSavedAt, setLastSavedAt] = useState(null);
  const timerRef = useRef(null);
  const initialDataRef = useRef(data);
  const isFirstRender = useRef(true);

  // Check if draft exists
  const hasDraft = (() => {
    try {
      return localStorage.getItem(key) !== null;
    } catch {
      return false;
    }
  })();

  // Auto-save with debounce
  useEffect(() => {
    // Skip saving on first render to avoid saving initial empty data
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (!enabled) return;

    // Don't save if data hasn't changed from initial
    if (JSON.stringify(data) === JSON.stringify(initialDataRef.current)) {
      return;
    }

    setStatus('saving');

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      try {
        const savePayload = {
          data,
          savedAt: new Date().toISOString(),
        };
        localStorage.setItem(key, JSON.stringify(savePayload));
        setStatus('saved');
        setLastSavedAt(new Date());

        // Reset to idle after 3s
        setTimeout(() => setStatus('idle'), 3000);
      } catch (err) {
        console.error('Auto-save failed:', err);
        setStatus('idle');
      }
    }, delay);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [key, data, delay, enabled]);

  // Restore saved data
  const restore = useCallback(() => {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed.data || parsed;
    } catch {
      return null;
    }
  }, [key]);

  // Clear saved draft
  const clear = useCallback(() => {
    try {
      localStorage.removeItem(key);
      setStatus('idle');
      setLastSavedAt(null);
    } catch (err) {
      console.error('Failed to clear draft:', err);
    }
  }, [key]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return {
    status,
    lastSavedAt,
    restore,
    clear,
    hasDraft,
  };
}
