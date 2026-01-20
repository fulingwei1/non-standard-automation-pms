/**
 * Service Ticket Assign Dialog Component
 * 服务工单分配对话框组件
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
import { User } from "lucide-react";

export function ServiceTicketAssignDialog({ ticketId, onClose, onSubmit, submitting = false }) {
  const [assignData, setAssignData] = useState({
    assignee_id: "",
    comment: "",
  });
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Load users for assignment
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
        
        const userList = response.data?.items || response.data || [];
        setUsers(
          userList.map((u) => ({
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

  const handleSubmit = async () => {
    if (!assignData.assignee_id) {
      toast.warning("请选择负责人");
      return;
    }

    if (submitting) {return;}

    try {
      await onSubmit({
        assignee_id: parseInt(assignData.assignee_id),
        comment: assignData.comment,
        assigned_time: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Assign failed:", error);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            分配工单
          </DialogTitle>
          <DialogDescription>
            将工单 #{ticketId} 分配给负责人
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">
                负责人 *
              </label>
              <select
                value={assignData.assignee_id}
                onChange={(e) =>
                  setAssignData({ ...assignData, assignee_id: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                disabled={loadingUsers}
              >
                <option value="">
                  {loadingUsers ? "加载中..." : "选择负责人"}
                </option>
                {users.map((user) => (
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
                value={assignData.comment}
                onChange={(e) =>
                  setAssignData({ ...assignData, comment: e.target.value })
                }
                placeholder="输入分配说明..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? "分配中..." : "确认分配"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
