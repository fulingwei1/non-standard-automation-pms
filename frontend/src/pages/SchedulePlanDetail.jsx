import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ClipboardList, Edit2 } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Input,
  Label,
} from "../components/ui";
import { scheduleGenerationApi } from "../services/api";
import { toast } from "sonner";

export default function SchedulePlanDetail() {
  const { planId } = useParams();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [editForm, setEditForm] = useState({
    duration_days: "",
    planned_start_date: "",
    planned_end_date: "",
    status: "PLANNED",
  });

  const loadDetail = async () => {
    setLoading(true);
    try {
      const response = await scheduleGenerationApi.getSchedulePlan(planId);
      setDetail(response.data || response);
    } catch (error) {
      console.error("加载计划详情失败:", error);
      toast.error("加载计划详情失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [planId]);

  const plan = detail?.plan;
  const tasks = detail?.tasks || [];

  const openEditDialog = (task) => {
    setEditingTask(task);
    setEditForm({
      duration_days: String(task.duration_days ?? ""),
      planned_start_date: task.planned_start_date || "",
      planned_end_date: task.planned_end_date || "",
      status: task.status || "PLANNED",
    });
    setShowEditDialog(true);
  };

  const handleSaveTask = async () => {
    if (!editingTask) return;
    setSaving(true);
    try {
      const payload = {
        duration_days: Number(editForm.duration_days),
        status: editForm.status,
      };
      if (editForm.planned_start_date) {
        payload.planned_start_date = editForm.planned_start_date;
      }
      if (editForm.planned_end_date) {
        payload.planned_end_date = editForm.planned_end_date;
      }
      await scheduleGenerationApi.updateTask(editingTask.id, payload);
      toast.success("任务已更新");
      setShowEditDialog(false);
      await loadDetail();
    } catch (error) {
      console.error("更新任务失败:", error);
      toast.error(`更新任务失败：${error?.response?.data?.detail || error.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="计划方案详情"
          description={plan ? `${plan.plan_no} · ${plan.project_name}` : "加载中..."}
          actions={
            <Button asChild variant="outline">
              <Link to={plan?.project_id ? `/schedule-plans?project_id=${plan.project_id}` : "/schedule-plans"}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回列表
              </Link>
            </Button>
          }
        />

        {loading ? (
          <div className="py-8 text-center text-slate-400">加载中...</div>
        ) : !plan ? (
          <div className="py-8 text-center text-slate-400">计划不存在</div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card><CardContent className="pt-6"><div className="text-sm text-slate-400">计划编号</div><div className="text-lg font-semibold">{plan.plan_no}</div></CardContent></Card>
              <Card><CardContent className="pt-6"><div className="text-sm text-slate-400">计划模式</div><div className="text-lg font-semibold">{plan.mode_name || plan.schedule_mode}</div></CardContent></Card>
              <Card><CardContent className="pt-6"><div className="text-sm text-slate-400">总工期</div><div className="text-lg font-semibold">{plan.total_days}天</div></CardContent></Card>
              <Card><CardContent className="pt-6"><div className="text-sm text-slate-400">状态</div><div className="text-lg font-semibold"><Badge variant="outline">{plan.status}</Badge></div></CardContent></Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ClipboardList className="w-5 h-5 text-blue-500" />
                  任务明细
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>任务编号</TableHead>
                      <TableHead>任务名称</TableHead>
                      <TableHead>阶段</TableHead>
                      <TableHead>开始</TableHead>
                      <TableHead>结束</TableHead>
                      <TableHead>工期</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>{task.task_no}</TableCell>
                        <TableCell>{task.task_name}</TableCell>
                        <TableCell>{task.phase}</TableCell>
                        <TableCell>{task.planned_start_date || "-"}</TableCell>
                        <TableCell>{task.planned_end_date || "-"}</TableCell>
                        <TableCell>{task.duration_days}天</TableCell>
                        <TableCell><Badge variant="outline">{task.status}</Badge></TableCell>
                        <TableCell>
                          <Button variant="outline" size="sm" onClick={() => openEditDialog(task)}>
                            <Edit2 className="w-4 h-4 mr-1" />
                            编辑
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>编辑任务</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="planned_start_date">开始日期</Label>
                    <Input
                      id="planned_start_date"
                      type="date"
                      value={editForm.planned_start_date}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, planned_start_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="planned_end_date">结束日期</Label>
                    <Input
                      id="planned_end_date"
                      type="date"
                      value={editForm.planned_end_date}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, planned_end_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="duration_days">工期（天）</Label>
                    <Input
                      id="duration_days"
                      type="number"
                      value={editForm.duration_days}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, duration_days: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="status">状态</Label>
                    <select
                      id="status"
                      className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                      value={editForm.status}
                      onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))}
                    >
                      <option value="PLANNED">PLANNED</option>
                      <option value="IN_PROGRESS">IN_PROGRESS</option>
                      <option value="COMPLETED">COMPLETED</option>
                    </select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowEditDialog(false)}>取消</Button>
                  <Button onClick={handleSaveTask} disabled={saving}>{saving ? "保存中..." : "保存"}</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </>
        )}
      </div>
    </div>
  );
}
