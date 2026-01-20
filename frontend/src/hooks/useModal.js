import { useState, useCallback } from 'react';

/**
 * 模态框/对话框 Hook
 * 
 * @param {boolean} initialOpen - 初始状态
 * 
 * @example
 * const createModal = useModal();
 * const editModal = useModal();
 * 
 * // 打开对话框并传递数据
 * editModal.open({ id: 1, name: 'John' });
 * 
 * // 在组件中使用
 * <Dialog open={editModal.isOpen} onOpenChange={editModal.close}>
 *   <p>编辑: {editModal.data?.name}</p>
 * </Dialog>
 */
export function useModal(initialOpen = false) {
    const [isOpen, setIsOpen] = useState(initialOpen);
    const [data, setData] = useState(null);

    // 打开模态框
    const open = useCallback((modalData = null) => {
        setData(modalData);
        setIsOpen(true);
    }, []);

    // 关闭模态框
    const close = useCallback(() => {
        setIsOpen(false);
        // 延迟清除数据，等待关闭动画完成
        setTimeout(() => {
            setData(null);
        }, 200);
    }, []);

    // 切换状态
    const toggle = useCallback(() => {
        setIsOpen(prev => !prev);
    }, []);

    // 更新数据
    const updateData = useCallback((updates) => {
        setData(prev => ({
            ...prev,
            ...updates,
        }));
    }, []);

    return {
        isOpen,
        data,
        open,
        close,
        toggle,
        setData,
        updateData,
    };
}
