import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { acceptanceApi } from '../../../services/api';
import {
    defaultItemResult,
    defaultNewIssue,
    defaultCompleteData,
} from '../constants';

/**
 * Page-level state and action hook for the AcceptanceExecution page.
 * Manages order detail, check items, issues, dialog visibility, and
 * all form submissions for a single acceptance order identified by `id`.
 */
export function useAcceptanceExecutionPage(id) {
    const navigate = useNavigate();

    // Data
    const [loading, setLoading] = useState(true);
    const [order, setOrder] = useState(null);
    const [items, setItems] = useState([]);
    const [issues, setIssues] = useState([]);

    // Dialog visibility
    const [showItemDialog, setShowItemDialog] = useState(false);
    const [showIssueDialog, setShowIssueDialog] = useState(false);
    const [showCompleteDialog, setShowCompleteDialog] = useState(false);

    // Selected item for the update dialog
    const [selectedItem, setSelectedItem] = useState(null);

    // Form states
    const [itemResult, setItemResult] = useState(defaultItemResult);
    const [newIssue, setNewIssue] = useState(defaultNewIssue);
    const [completeData, setCompleteData] = useState(defaultCompleteData);

    // ── Fetchers ────────────────────────────────────────────────────────────

    const fetchOrderDetail = async () => {
        try {
            const res = await acceptanceApi.orders.get(id);
            setOrder(res.data || res);
        } catch (error) {
            console.error('Failed to fetch order detail:', error);
        }
    };

    const fetchItems = async () => {
        try {
            const res = await acceptanceApi.orders.getItems(id);
            setItems(res.data || res || []);
        } catch (error) {
            console.error('Failed to fetch items:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchIssues = async () => {
        try {
            const res = await acceptanceApi.issues.list(id);
            setIssues(res.data || res || []);
        } catch (error) {
            console.error('Failed to fetch issues:', error);
        }
    };

    const refreshAll = () => {
        fetchOrderDetail();
        fetchItems();
        fetchIssues();
    };

    useEffect(() => {
        if (id) {
            fetchOrderDetail();
            fetchItems();
            fetchIssues();
        }
    }, [id]);  

    // ── Actions ─────────────────────────────────────────────────────────────

    const openItemDialog = (item) => {
        setSelectedItem(item);
        setItemResult({
            result_status: item.result_status || 'PASSED',
            actual_value: item.actual_value || '',
            deviation: item.deviation || '',
            remark: item.remark || '',
        });
        setShowItemDialog(true);
    };

    const handleUpdateItem = async () => {
        if (!selectedItem) return;
        try {
            await acceptanceApi.orders.updateItem(selectedItem.id, itemResult);
            setShowItemDialog(false);
            setSelectedItem(null);
            setItemResult(defaultItemResult);
            fetchItems();
            fetchOrderDetail();
        } catch (error) {
            console.error('Failed to update item:', error);
            alert('更新检查项失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleCreateIssue = async () => {
        if (!newIssue.description) {
            alert('请填写问题描述');
            return;
        }
        try {
            await acceptanceApi.issues.create(id, newIssue);
            setShowIssueDialog(false);
            setNewIssue(defaultNewIssue);
            fetchIssues();
        } catch (error) {
            console.error('Failed to create issue:', error);
            alert('创建问题失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleComplete = async () => {
        if (!completeData.overall_result) {
            alert('请选择总体结果');
            return;
        }
        try {
            await acceptanceApi.orders.complete(id, completeData);
            alert('验收完成');
            navigate('/acceptance-orders');
        } catch (error) {
            console.error('Failed to complete acceptance:', error);
            alert('完成验收失败: ' + (error.response?.data?.detail || error.message));
        }
    };

    // ── Derived values ───────────────────────────────────────────────────────

    const itemsByCategory = (items || []).reduce((acc, item) => {
        const category = item.category_name || '其他';
        if (!acc[category]) acc[category] = [];
        acc[category].push(item);
        return acc;
    }, {});

    const passedCount = (items || []).filter((i) => i.result_status === 'PASSED').length;
    const failedCount = (items || []).filter((i) => i.result_status === 'FAILED').length;
    const pendingCount = (items || []).filter((i) => i.result_status === 'PENDING').length;
    const totalChecked = (items?.length ?? 0) - pendingCount;

    return {
        // Data
        loading,
        order,
        items,
        issues,
        itemsByCategory,
        passedCount,
        failedCount,
        pendingCount,
        totalChecked,

        // Dialog state
        showItemDialog,
        setShowItemDialog,
        showIssueDialog,
        setShowIssueDialog,
        showCompleteDialog,
        setShowCompleteDialog,
        selectedItem,

        // Form state
        itemResult,
        setItemResult,
        newIssue,
        setNewIssue,
        completeData,
        setCompleteData,

        // Actions
        refreshAll,
        openItemDialog,
        handleUpdateItem,
        handleCreateIssue,
        handleComplete,
    };
}
