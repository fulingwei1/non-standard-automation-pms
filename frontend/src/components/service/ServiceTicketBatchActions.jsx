/**
 * Service Ticket Batch Actions Component
 * 服务工单批量操作组件
 */

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
import { toast } from "../../components/ui/toast";
import DeleteConfirmDialog from "../../components/common/DeleteConfirmDialog";
import { Users, Download, Trash2, AlertTriangle, CheckCircle2 } from "lucide-react";

export function ServiceTicketBatchActions({
  selectedTickets,
  tickets,
  onClearSelection,
  onBatchAssign,
  onBatchExport,
  onBatchDelete,
}) {
  const [showBatchAssignDialog, setShowBatchAssignDialog] = useState(false);
  const [showBatchDeleteDialog, setShowBatchDeleteDialog] = useState(false);
  const [batchAssignData, setBatchAssignData] = useState({
    assignee_id: "",
    comment: "",
  });
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Load users for batch assignment
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoadingUsers(true);
        const response = await fetch('/api/v1/users/', {
          headers: { 
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          method: 'POST',
          body: JSON.stringify({
            is_active: true,
            page_size: 100,
          })
        });
        
        const userList = response.data?.items || response.data?.items || response.data || [];
        setUsers(
          (userList || []).map((u) => ({
            id: u.id,
            name: u.real_name || u.username,
            role: u.position || u.roles?.[0] || "工程师",
          })),
        );
      } catch (err) {
        console.error("Failed to load users:", err);
        setUsers([]);
      } finally {
        setLoadingUsers(false);
      }
    };
    loadUsers();
  }, []);

  const handleBatchAssign = async () => {
    if (!batchAssignData.assignee_id) {
      toast.warning("请选择负责人");
      return;
    }

    if (submitting) {return;}

    try {
      setSubmitting(true);
      await onBatchAssign({
        ticket_ids: selectedTickets,
        assignee_id: parseInt(batchAssignData.assignee_id),
        comment: batchAssignData.comment,
      });
      setShowBatchAssignDialog(false);
      setBatchAssignData({ assignee_id: "", comment: "" });
      onClearSelection();
    } catch (error) {
      console.error("Batch assign failed:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleBatchDelete = async () => {
    if (submitting) {return;}

    try {
      setSubmitting(true);
      await onBatchDelete(selectedTickets);
      setShowBatchDeleteDialog(false);
      onClearSelection();
    } catch (error) {
      console.error("Batch delete failed:", error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExport = async () => {
    try {
      setSubmitting(true);
      const ticketsToExport = (tickets || []).filter(ticket => 
        selectedTickets.includes(ticket.id)
      );
      await onBatchExport(ticketsToExport);
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setSubmitting(false);
    }
  };

  if (selectedTickets.length === 0) {
    return null;
  }

  return (
    <>
      {/* Batch Actions Bar */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl p-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
            <span className="text-white font-medium">
              已选择 {selectedTickets.length} 个工单
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Batch Assign */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowBatchAssignDialog(true)}
              disabled={submitting}
              className="flex items-center gap-2"
            >
              <Users className="w-4 h-4" />
              批量分配
            </Button>

            {/* Export */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={submitting}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              导出选中
            </Button>

            {/* Batch Delete */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowBatchDeleteDialog(true)}
              disabled={submitting}
              className="flex items-center gap-2 text-red-400 border-red-400 hover:bg-red-400 hover:text-white"
            >
              <Trash2 className="w-4 h-4" />
              批量删除
            </Button>

            {/* Clear Selection */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearSelection}
              className="text-slate-400"
            >
              清除选择
            </Button>
          </div>
        </div>
      </div>

      {/* Batch Assign Dialog */}
      {showBatchAssignDialog && (
        <Dialog open onOpenChange={() => setShowBatchAssignDialog(false)}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                批量分配工单
              </DialogTitle>
              <DialogDescription>
                将 {selectedTickets.length} 个工单分配给负责人
              </DialogDescription>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    负责人 *
                  </label>
                  <select
                    value={batchAssignData.assignee_id}
                    onChange={(e) =>
                      setBatchAssignData({ ...batchAssignData, assignee_id: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                    disabled={loadingUsers}
                  >
                    <option value="">
                      {loadingUsers ? "加载中..." : "选择负责人"}
                    </option>
                    {(users || []).map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name} ({user.role})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    分配说明
                  </label>
                  <Textarea
                    value={batchAssignData.comment}
                    onChange={(e) =>
                      setBatchAssignData({ ...batchAssignData, comment: e.target.value })
                    }
                    placeholder="输入分配说明（将应用于所有选中的工单）..."
                    rows={3}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowBatchAssignDialog(false)} disabled={submitting}>
                取消
              </Button>
              <Button onClick={handleBatchAssign} disabled={submitting}>
                {submitting ? "分配中..." : "确认分配"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Batch Delete Dialog */}
      {showBatchDeleteDialog && (
        <DeleteConfirmDialog
          open
          onOpenChange={() => setShowBatchDeleteDialog(false)}
          title="批量删除工单"
          description={`您确定要删除选中的 ${selectedTickets.length} 个工单吗？此操作不可撤销。`}
          confirmText={submitting ? "删除中..." : "确认删除"}
          confirmDisabled={submitting}
          onConfirm={handleBatchDelete}
          contentClassName="max-w-md bg-slate-900 border-slate-700"
          titleClassName="text-red-400"
          descriptionClassName="text-slate-300"
          cancelButtonClassName="border-slate-700"
          confirmButtonClassName="bg-red-600 hover:bg-red-700"
        >
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 font-medium">警告</span>
            </div>
            <ul className="text-sm text-slate-300 space-y-1">
              <li>• 删除后的工单无法恢复</li>
              <li>• 所有相关数据将被永久删除</li>
              <li>• 建议先导出数据作为备份</li>
            </ul>
          </div>
        </DeleteConfirmDialog>
      )}
    </>
  );
}
