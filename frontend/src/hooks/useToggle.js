import { useState, useCallback } from 'react';

/**
 * 切换状态 Hook
 * 
 * @param {boolean} initialValue - 初始值
 * 
 * @example
 * const [isOpen, toggle, setIsOpen] = useToggle(false);
 * 
 * <button onClick={toggle}>切换</button>
 * <button onClick={() => setIsOpen(true)}>打开</button>
 */
export function useToggle(initialValue = false) {
    const [value, setValue] = useState(initialValue);

    const toggle = useCallback(() => {
        setValue(prev => !prev);
    }, []);

    const setTrue = useCallback(() => {
        setValue(true);
    }, []);

    const setFalse = useCallback(() => {
        setValue(false);
    }, []);

    return [value, toggle, { setValue, setTrue, setFalse }];
}
