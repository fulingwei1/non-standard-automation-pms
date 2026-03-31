/**
 * Acceptance Execution Page - 验收执行页面
 * Features: 验收检查项执行、问题管理、验收完成
 */
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, CheckCircle2 } from 'lucide-react';
import { PageHeader } from '../../components/layout';
import { Button } from '../../components/ui/button';

import { useAcceptanceExecutionPage } from './hooks/useAcceptanceExecutionPage';
import { ExecutionSummaryCards } from './ExecutionSummaryCards';
import { CheckItemsPanel } from './CheckItemsPanel';
import { IssuesPanel } from './IssuesPanel';
import { UpdateItemDialog } from './UpdateItemDialog';
import { CreateIssueDialog } from './CreateIssueDialog';
import { CompleteDialog } from './CompleteDialog';

export default function AcceptanceExecution() {
    const { id } = useParams();
    const navigate = useNavigate();

    const {
        loading,
        order,
        items,
        issues,
        itemsByCategory,
        passedCount,
        failedCount,
        totalChecked,

        showItemDialog,
        setShowItemDialog,
        showIssueDialog,
        setShowIssueDialog,
        showCompleteDialog,
        setShowCompleteDialog,
        selectedItem,

        itemResult,
        setItemResult,
        newIssue,
        setNewIssue,
        completeData,
        setCompleteData,

        refreshAll,
        openItemDialog,
        handleUpdateItem,
        handleCreateIssue,
        handleComplete,
    } = useAcceptanceExecutionPage(id);

    if (loading) {
        return (
            <div className="space-y-6 p-6">
                <div className="text-center py-8 text-slate-400">加载中...</div>
            </div>
        );
    }

    if (!order) {
        return (
            <div className="space-y-6 p-6">
                <div className="text-center py-8 text-slate-400">验收单不存在</div>
            </div>
        );
    }

    return (
        <div className="space-y-6 p-6">
            {/* Page header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/acceptance-orders')}
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        返回列表
                    </Button>
                    <PageHeader
                        title={`验收执行 - ${order.order_no}`}
                        description="验收检查项执行、问题管理"
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" onClick={refreshAll}>
                        <RefreshCw className="w-4 h-4 mr-2" />
                        刷新
                    </Button>
                    {order.status === 'IN_PROGRESS' && (
                        <Button onClick={() => setShowCompleteDialog(true)}>
                            <CheckCircle2 className="w-4 h-4 mr-2" />
                            完成验收
                        </Button>
                    )}
                </div>
            </div>

            {/* Summary stat cards */}
            <ExecutionSummaryCards
                totalItems={items?.length ?? 0}
                passedCount={passedCount}
                failedCount={failedCount}
                totalChecked={totalChecked}
            />

            {/* Main content: check items + issues sidebar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <CheckItemsPanel
                    itemsByCategory={itemsByCategory}
                    onItemClick={openItemDialog}
                    onAddIssue={() => setShowIssueDialog(true)}
                />
                <IssuesPanel issues={issues} />
            </div>

            {/* Dialogs */}
            <UpdateItemDialog
                open={showItemDialog}
                onOpenChange={setShowItemDialog}
                selectedItem={selectedItem}
                itemResult={itemResult}
                setItemResult={setItemResult}
                onSave={handleUpdateItem}
            />

            <CreateIssueDialog
                open={showIssueDialog}
                onOpenChange={setShowIssueDialog}
                items={items}
                newIssue={newIssue}
                setNewIssue={setNewIssue}
                onSubmit={handleCreateIssue}
            />

            <CompleteDialog
                open={showCompleteDialog}
                onOpenChange={setShowCompleteDialog}
                completeData={completeData}
                setCompleteData={setCompleteData}
                onComplete={handleComplete}
            />
        </div>
    );
}
