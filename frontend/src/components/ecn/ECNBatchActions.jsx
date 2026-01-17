/**
 * ECN Batch Actions Component
 * ECN批量操作组件
 */
import { useState } from "react";
import { 
  CheckCircle2, 
  X, 
  Download,
  ArrowRight,
  AlertTriangle
} from "lucide-react";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../ui/dialog";
import { Textarea } from "../ui/textarea";
import { Badge } from "../ui/badge";
import { batchOperations } from "./ecnManagementConstants";

export function ECNBatchActions({
  selectedECNIds = new Set(),
  ecns = [],
  onBatchSubmit,
  onBatchClose,
  onBatchExport,
  onClearSelection,
}) {
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [batchOperation, setBatchOperation] = useState("");
  const [batchComment, setBatchComment] = useState("");
  const [processing, setProcessing] = useState(false);

  // 获取选中的ECN详细信息
  const selectedECNs = ecns.filter(ecn => selectedECNIds.has(ecn.id));

  // 获取批量操作信息
  const getOperationInfo = (operation) => {
    return batchOperations.find(op => op.value === operation);
  };

  // 获取操作图标
  const getOperationIcon = (operation) => {
    const iconMap = {
      batch_submit: CheckCircle2,
      batch_close: X,
      batch_export: Download,
    };
    
    const IconComponent = iconMap[operation] || ArrowRight;
    return <IconComponent className="w-4 h-4" />;
  };

  // 处理批量操作
  const handleBatchOperation = async (operation) => {
    if (selectedECNIds.size === 0) {
      alert("请先选择要操作的ECN");
      return;
    }

    setBatchOperation(operation);
    const operationInfo = getOperationInfo(operation);
    if (!operationInfo) return;

    // 导出操作不需要确认
    if (operation === "batch_export") {
      setProcessing(true);
      try {
        await onBatchExport(selectedECNIds);
      } catch (error) {
        console.error("批量导出失败:", error);
      } finally {
        setProcessing(false);
      }
      return;
    }

    // 其他操作需要确认对话框
    setShowBatchDialog(true);
  };

  // 确认批量操作
  const confirmBatchOperation = async () => {
    if (!batchOperation) return;

    setProcessing(true);
    try {
      switch (batchOperation) {
        case "batch_submit":
          await onBatchSubmit(selectedECNIds, batchComment);
          break;
        case "batch_close":
          await onBatchClose(selectedECNIds, batchComment);
          break;
      }

      setShowBatchDialog(false);
      setBatchOperation("");
      setBatchComment("");
      onClearSelection();
    } catch (error) {
      console.error("批量操作失败:", error);
    } finally {
      setProcessing(false);
    }
  };

  // 如果没有选中项，不显示组件
  if (selectedECNIds.size === 0) {
    return null;
  }

  return (
    <>
      {/* 批量操作栏 */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* 选中信息 */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Badge variant="default" className="bg-blue-600">
                已选择 {selectedECNIds.size} 个ECN
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearSelection}
                className="text-blue-600 hover:text-blue-700"
              >
                清除选择
              </Button>
            </div>
          </div>

        {/* 批量操作按钮 */}
        <div className="flex items-center gap-2 flex-wrap">
          {batchOperations.map((operation) => (
            <Button
              key={operation.value}
              variant="outline"
              size="sm"
              onClick={() => {
                  handleBatchOperation(operation.value);
                }}
              className="flex items-center gap-2"
              disabled={processing}
            >
              {getOperationIcon(operation.value)}
                {operation.label}
            </Button>
            ))}
        </div>
        </div>

        {/* 选中ECN列表预览 */}
        <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
          <div className="text-sm text-blue-700 dark:text-blue-300 mb-2">
            选中的ECN：
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedECNs.slice(0, 10).map((ecn) => (
              <Badge
                key={ecn.id}
                variant="secondary"
                className="text-xs"
              >
                {ecn.ecn_no || `ECN-${String(ecn.id).padStart(6, '0')}`}
              </Badge>
            ))}
            {selectedECNs.length > 10 && (
              <Badge variant="outline" className="text-xs">
                +{selectedECNs.length - 10} 更多
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* 批量操作确认对话框 */}
      <Dialog open={showBatchDialog} onOpenChange={setShowBatchDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {getOperationIcon(batchOperation)}
              {getOperationInfo(batchOperation)?.label || "批量操作"}
            </DialogTitle>
          </DialogHeader>
          
          <DialogBody>
            <div className="space-y-4">
              {/* 操作说明 */}
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm">
                  此操作将影响 {selectedECNIds.size} 个ECN，请谨慎操作
                </span>
              </div>

              {/* 选中的ECN列表 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  将要操作的ECN：
                </label>
                <div className="max-h-32 overflow-y-auto border rounded-md p-2 bg-slate-50 dark:bg-slate-900">
                  <div className="space-y-1">
                    {selectedECNs.map((ecn) => (
                      <div key={ecn.id} className="text-xs flex items-center gap-2">
                        <span className="font-mono">
                          {ecn.ecn_no || `ECN-${String(ecn.id).padStart(6, '0')}`}
                        </span>
                        <span className="text-slate-500">-</span>
                        <span className="truncate">{ecn.ecn_title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 操作备注 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  操作备注（可选）
                </label>
                <Textarea
                  value={batchComment}
                  onChange={(e) => setBatchComment(e.target.value)}
                  placeholder="请输入操作说明或备注..."
                  rows={3}
                />
              </div>
            </div>
          </DialogBody>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowBatchDialog(false);
                setBatchOperation("");
                setBatchComment("");
              }}
              disabled={processing}
            >
              取消
            </Button>
            <Button
              onClick={confirmBatchOperation}
              disabled={processing}
              className="min-w-20"
            >
              {processing ? "处理中..." : "确认"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
