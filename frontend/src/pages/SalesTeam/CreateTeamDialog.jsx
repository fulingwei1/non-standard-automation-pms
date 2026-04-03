/**
 * Create Team Dialog component
 */

import { useState } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
} from "../../components/ui";
import { salesTeamApi } from "../../services/api";
import { toast } from "sonner";
import { DEFAULT_CREATE_TEAM_FORM, TEAM_TYPE_OPTIONS } from "./constants";
import { generateTeamCode } from "./utils";

export default function CreateTeamDialog({
  open,
  onOpenChange,
  departmentOptions,
  teamMembers,
  onTeamCreated,
}) {
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ ...DEFAULT_CREATE_TEAM_FORM });

  const resetForm = () => {
    setForm({ ...DEFAULT_CREATE_TEAM_FORM });
  };

  const handleCreate = async () => {
    if (!form.team_name?.trim()) {
      toast.error("团队名称不能为空");
      return;
    }

    const teamCode = (form.team_code || generateTeamCode())
      .toUpperCase()
      .replace(/\s+/g, "")
      .slice(0, 20);

    try {
      setCreating(true);
      await salesTeamApi.createTeam({
        team_code: teamCode,
        team_name: form.team_name.trim(),
        description: form.description?.trim() || undefined,
        team_type: form.team_type || "REGION",
        department_id: form.department_id
          ? Number(form.department_id)
          : undefined,
        leader_id: form.leader_id
          ? Number(form.leader_id)
          : undefined,
      });

      toast.success(`团队创建成功（${teamCode}）`);
      onOpenChange(false);
      resetForm();
      onTeamCreated?.();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(detail || "创建团队失败");
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>新建销售团队</DialogTitle>
          <DialogDescription>创建团队实体，用于目标分配与统计</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1">
            <label className="text-sm text-slate-300">团队名称 *</label>
            <Input
              placeholder="请输入团队名称"
              value={form.team_name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, team_name: e.target.value }))
              }
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm text-slate-300">团队编码</label>
            <Input
              placeholder="留空自动生成"
              value={form.team_code}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, team_code: e.target.value }))
              }
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-sm text-slate-300">团队类型</label>
              <select
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
                value={form.team_type}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, team_type: e.target.value }))
                }
              >
                {TEAM_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-sm text-slate-300">所属部门</label>
              <select
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
                value={form.department_id}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, department_id: e.target.value }))
                }
              >
                <option value="">不指定</option>
                {(departmentOptions || [])
                  .filter((d) => d.value !== "all")
                  .map((dept) => (
                    <option key={dept.value} value={dept.value}>
                      {dept.label}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm text-slate-300">负责人</label>
            <select
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
              value={form.leader_id}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, leader_id: e.target.value }))
              }
            >
              <option value="">不指定</option>
              {(teamMembers || []).map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.user_name || member.name || `用户${member.user_id}`}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm text-slate-300">描述</label>
            <Input
              placeholder="可选"
              value={form.description}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, description: e.target.value }))
              }
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            disabled={creating}
            onClick={() => {
              onOpenChange(false);
              resetForm();
            }}
          >
            取消
          </Button>
          <Button disabled={creating} onClick={handleCreate}>
            {creating ? "创建中..." : "创建团队"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
