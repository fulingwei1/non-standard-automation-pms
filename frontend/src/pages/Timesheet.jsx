import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  Calendar,
  Plus,
  ChevronLeft,
  ChevronRight,
  Save,
  Send,
  Edit3,
  Trash2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Timer,
  Briefcase,
  Coffee,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { timesheetApi, projectApi } from "../services/api";
import { RefreshCw, Copy, FileText, Zap } from "lucide-react";

// Current week dates helper
const getWeekDates = (offset = 0) => {
  const today = new Date();
  const currentDay = today.getDay();
  const monday = new Date(today);
  monday.setDate(today.getDate() - currentDay + 1 + offset * 7);

  const dates = [];
  for (let i = 0; i < 7; i++) {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);
    dates.push(date);
  }
  return dates;
};

const formatDate = (date) => {
  return `${date.getMonth() + 1}/${date.getDate()}`;
};

const formatFullDate = (date) => {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
};

const dayNames = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

const getStatusBadge = (status) => {
  const statusUpper = status?.toUpperCase() || "DRAFT";
  const configs = {
    DRAFT: { label: "草稿", variant: "secondary", icon: Edit3 },
    PENDING: { label: "待审批", variant: "default", icon: AlertCircle },
    SUBMITTED: { label: "已提交", variant: "default", icon: AlertCircle },
    APPROVED: { label: "已审批", variant: "default", icon: CheckCircle2 },
    REJECTED: { label: "已退回", variant: "destructive", icon: XCircle },
  };
  const config = configs[statusUpper] || configs.DRAFT;
  return (
    <Badge variant={config.variant} className="gap-1">
      <config.icon className="w-3 h-3" />
      {config.label}
    </Badge>
  );
};

function AddEntryDialog({
  open,
  onOpenChange,
  onAdd,
  weekDates,
  projects,
  loading,
}) {
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [hours, setHours] = useState({});
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  const selectedProject = projects.find(
    (p) => p.id === Number(selectedProjectId),
  );

  // 当选择项目时，加载任务列表
  useEffect(() => {
    if (selectedProjectId) {
      loadTasks(Number(selectedProjectId));
    } else {
      setTasks([]);
      setSelectedTaskId("");
    }
  }, [selectedProjectId]);

  const loadTasks = async (projectId) => {
    setLoadingTasks(true);
    try {
      // 使用progressApi获取项目任务
      const { progressApi } = await import("../services/api");
      const response = await progressApi.tasks.list({
        project_id: projectId,
        page_size: 100,
      });
      const items =
        response.data?.items ||
        response.data?.data?.items ||
        response.items ||
        [];
      setTasks(items);
    } catch (error) {
      console.error("加载任务失败:", error);
      setTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  };

  const handleAdd = () => {
    if (selectedProjectId && selectedTaskId) {
      onAdd({
        project_id: Number(selectedProjectId),
        project_name: selectedProject?.project_name,
        task_id: Number(selectedTaskId),
        task_name: tasks.find((t) => t.id === Number(selectedTaskId))
          ?.task_name,
        hours,
      });
      setSelectedProjectId("");
      setSelectedTaskId("");
      setHours({});
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>添加工时记录</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {/* Project Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">项目</label>
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value);
                setSelectedTaskId("");
              }}
              disabled={loading}
              className="w-full h-10 px-3 rounded-lg bg-slate-700 border border-slate-600 text-white focus:border-blue-500 focus:outline-none disabled:opacity-50"
            >
              <option value="">选择项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.project_code} - {project.project_name}
                </option>
              ))}
            </select>
          </div>

          {/* Task Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">任务</label>
            <select
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
              disabled={!selectedProjectId || loadingTasks}
              className="w-full h-10 px-3 rounded-lg bg-slate-700 border border-slate-600 text-white focus:border-blue-500 focus:outline-none disabled:opacity-50"
            >
              <option value="">
                {loadingTasks ? "加载中..." : "选择任务（可选）"}
              </option>
              {tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {task.task_name || task.title}
                </option>
              ))}
            </select>
          </div>

          {/* Hours Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">工时</label>
            <div className="grid grid-cols-7 gap-2">
              {weekDates.map((date, index) => (
                <div key={index} className="text-center">
                  <div className="text-xs text-slate-500 mb-1">
                    {dayNames[index]}
                  </div>
                  <div className="text-xs text-slate-400 mb-1">
                    {formatDate(date)}
                  </div>
                  <Input
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    placeholder="0"
                    value={hours[formatFullDate(date)] || ""}
                    onChange={(e) =>
                      setHours({
                        ...hours,
                        [formatFullDate(date)]: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="text-center h-9 bg-slate-700 border-slate-600 text-white"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleAdd} disabled={!selectedProjectId}>
            添加
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Timesheet() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [entries, setEntries] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [projects, setProjects] = useState([]);
  const [weekData, setWeekData] = useState(null);

  const weekDates = getWeekDates(weekOffset);
  const isCurrentWeek = weekOffset === 0;
  const weekStart = formatFullDate(weekDates[0]);

  // 加载周工时数据
  const loadWeekTimesheet = useCallback(async () => {
    setLoading(true);
    try {
      const response = await timesheetApi.getWeek({
        week_start: weekStart,
      });
      const data = response.data?.data || response.data;

      // 转换数据格式：将API返回的timesheets转换为UI需要的格式
      const timesheets = data.timesheets || [];

      // 按项目和任务分组（同一项目+任务的多条记录合并为一行）
      const grouped = {};
      timesheets.forEach((ts) => {
        // 使用项目ID和任务ID作为分组键（如果没有任务ID，使用'none'）
        const key = `${ts.project_id || "none"}_${ts.task_id || "none"}`;

        if (!grouped[key]) {
          // 生成一个唯一的entry ID（使用第一个timesheet的ID）
          grouped[key] = {
            id: `entry_${ts.id}`, // 使用entry_前缀避免与timesheet ID冲突
            project_id: ts.project_id,
            project_code: ts.project_id
              ? `PJ${String(ts.project_id).padStart(9, "0")}`
              : "",
            project_name: ts.project_name || "未分配项目",
            task_id: ts.task_id,
            task_name: ts.task_name,
            hours: {},
            status: ts.status || "DRAFT",
            timesheet_ids: [], // 存储该entry对应的所有timesheet ID
            timesheet_map: {}, // 存储日期到timesheet ID的映射
          };
        }

        // 处理日期（可能是字符串或Date对象）
        const dateStr =
          typeof ts.work_date === "string"
            ? ts.work_date.split("T")[0] // 处理ISO格式日期
            : ts.work_date;

        grouped[key].hours[dateStr] = parseFloat(ts.work_hours || 0);
        grouped[key].timesheet_map[dateStr] = ts.id;

        if (!grouped[key].timesheet_ids.includes(ts.id)) {
          grouped[key].timesheet_ids.push(ts.id);
        }

        // 状态优先级：APPROVED > PENDING > DRAFT > REJECTED
        const statusPriority = {
          APPROVED: 3,
          PENDING: 2,
          SUBMITTED: 2,
          DRAFT: 1,
          REJECTED: 0,
        };
        const currentPriority = statusPriority[grouped[key].status] || 0;
        const newPriority = statusPriority[ts.status] || 0;
        if (newPriority > currentPriority) {
          grouped[key].status = ts.status;
        }
      });

      setEntries(Object.values(grouped));
      setWeekData(data);
    } catch (error) {
      console.error("加载周工时数据失败:", error);
      // 如果API失败，保持空数组
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [weekStart]);

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({
        page_size: 100,
        is_active: true,
      });
      const items = response.data?.items || response.data?.data?.items || [];
      setProjects(items);
    } catch (error) {
      console.error("加载项目列表失败:", error);
      setProjects([]);
    }
  }, []);

  // 初始化加载
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    loadWeekTimesheet();
  }, [loadWeekTimesheet]);

  // Calculate totals
  const dailyTotals = weekDates.reduce((acc, date) => {
    const dateStr = formatFullDate(date);
    acc[dateStr] = entries.reduce((sum, entry) => {
      const hours = entry.hours?.[dateStr] || 0;
      return sum + (typeof hours === "number" ? hours : parseFloat(hours) || 0);
    }, 0);
    return acc;
  }, {});

  const weeklyTotal = Object.values(dailyTotals).reduce((a, b) => a + b, 0);

  // 处理添加新记录
  const handleAddEntry = async (newEntry) => {
    if (!newEntry.project_id) return;

    setSaving(true);
    try {
      // 为本周的每一天创建工时记录（如果有工时）
      const timesheetsToCreate = [];

      weekDates.forEach((date) => {
        const dateStr = formatFullDate(date);
        const hours = newEntry.hours?.[dateStr];
        if (hours && parseFloat(hours) > 0) {
          timesheetsToCreate.push({
            project_id: newEntry.project_id,
            task_id: newEntry.task_id || null,
            work_date: dateStr,
            work_hours: parseFloat(hours),
            work_type: "NORMAL",
            description: newEntry.task_name || "",
          });
        }
      });

      if (timesheetsToCreate.length > 0) {
        const response = await timesheetApi.batchCreate({
          timesheets: timesheetsToCreate,
        });

        // 检查响应（batchCreate可能返回ResponseModel格式）
        if (
          response.data?.code === 200 ||
          response.data?.success !== false ||
          response.status === 201
        ) {
          // 重新加载数据
          await loadWeekTimesheet();
          setShowAddDialog(false);
        } else {
          throw new Error(
            response.data?.message || response.data?.detail || "创建失败",
          );
        }
      }
    } catch (error) {
      console.error("创建工时记录失败:", error);
      alert("创建工时记录失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  // 处理工时修改（防抖处理，避免频繁请求）
  const handleHoursChange = async (entryId, dateStr, value) => {
    const entry = entries.find((e) => e.id === entryId);
    if (!entry) return;

    const hours = parseFloat(value) || 0;

    // 更新本地状态（乐观更新）
    setEntries(
      entries.map((e) =>
        e.id === entryId
          ? { ...e, hours: { ...e.hours, [dateStr]: hours } }
          : e,
      ),
    );

    // 使用防抖，延迟500ms后执行实际保存
    if (handleHoursChange.timeout) {
      clearTimeout(handleHoursChange.timeout);
    }

    handleHoursChange.timeout = setTimeout(async () => {
      try {
        // 查找该日期是否已有记录（通过timesheet_map）
        const existingTimesheetId = entry.timesheet_map?.[dateStr];

        // 或者从weekData中查找
        let existingTimesheet = null;
        if (weekData?.timesheets) {
          existingTimesheet = weekData.timesheets.find((ts) => {
            const tsDate =
              typeof ts.work_date === "string"
                ? ts.work_date.split("T")[0]
                : ts.work_date;
            return (
              ts.id === existingTimesheetId ||
              (ts.project_id === entry.project_id &&
                ts.task_id === entry.task_id &&
                tsDate === dateStr)
            );
          });
        }

        if (hours > 0) {
          if (existingTimesheet) {
            // 更新现有记录
            await timesheetApi.update(existingTimesheet.id, {
              work_hours: hours,
            });
          } else {
            // 创建新记录
            await timesheetApi.create({
              project_id: entry.project_id,
              task_id: entry.task_id || null,
              work_date: dateStr,
              work_hours: hours,
              work_type: "NORMAL",
              description: entry.task_name || "",
            });
          }
        } else if (existingTimesheet) {
          // 删除记录（工时为0）
          await timesheetApi.delete(existingTimesheet.id);
        }

        // 重新加载数据
        await loadWeekTimesheet();
      } catch (error) {
        console.error("更新工时记录失败:", error);
        // 恢复原值
        await loadWeekTimesheet();
        alert("更新工时记录失败，请稍后重试");
      }
    }, 500); // 500ms防抖
  };

  // 处理删除记录
  const handleDeleteEntry = async (entryId) => {
    const entry = entries.find((e) => e.id === entryId);
    if (!entry || !confirm("确定要删除这条工时记录吗？")) return;

    try {
      // 删除该条目对应的所有工时记录
      if (entry.timesheet_ids && entry.timesheet_ids.length > 0) {
        for (const tsId of entry.timesheet_ids) {
          await timesheetApi.delete(tsId);
        }
      }
      // 重新加载数据
      await loadWeekTimesheet();
    } catch (error) {
      console.error("删除工时记录失败:", error);
      alert("删除工时记录失败，请稍后重试");
    }
  };

  // 处理提交审批
  const handleSubmit = async () => {
    // 收集所有草稿状态的工时记录ID
    const timesheetIds = [];
    entries.forEach((entry) => {
      if (entry.status === "DRAFT" && entry.timesheet_ids) {
        timesheetIds.push(...entry.timesheet_ids);
      }
    });

    if (timesheetIds.length === 0) {
      alert("没有可提交的记录（只有草稿状态的记录可以提交）");
      return;
    }

    if (!confirm(`确定要提交 ${timesheetIds.length} 条工时记录进行审批吗？`)) {
      return;
    }

    setSaving(true);
    try {
      const response = await timesheetApi.submit({
        timesheet_ids: timesheetIds,
      });

      if (response.data?.code === 200 || response.data?.message) {
        alert(
          response.data.message || `成功提交 ${timesheetIds.length} 条工时记录`,
        );
        // 重新加载数据
        await loadWeekTimesheet();
      } else {
        throw new Error(response.data?.message || "提交失败");
      }
    } catch (error) {
      console.error("提交工时记录失败:", error);
      alert(
        error.response?.data?.detail ||
          error.message ||
          "提交工时记录失败，请稍后重试",
      );
    } finally {
      setSaving(false);
    }
  };

  // 处理保存草稿（自动保存，无需额外操作）
  const handleSaveDraft = () => {
    // 工时记录在修改时已自动保存，这里只是提示
    alert("工时记录已自动保存为草稿");
  };

  // 复制上周的工时记录
  const handleCopyLastWeek = async () => {
    if (weekOffset === 0) {
      alert("当前是本周，无法复制上周数据");
      return;
    }

    if (!confirm("确定要复制上周的工时记录到本周吗？")) {
      return;
    }

    setSaving(true);
    try {
      // 获取上周的周开始日期
      const lastWeekStart = getWeekDates(weekOffset - 1)[0];
      const lastWeekStartStr = formatFullDate(lastWeekStart);

      // 获取上周的工时数据
      const lastWeekResponse = await timesheetApi.getWeek({
        week_start: lastWeekStartStr,
      });
      const lastWeekData = lastWeekResponse.data?.data || lastWeekResponse.data;
      const lastWeekTimesheets = lastWeekData.timesheets || [];

      if (lastWeekTimesheets.length === 0) {
        alert("上周没有工时记录可复制");
        return;
      }

      // 为本周创建对应的工时记录
      const timesheetsToCreate = [];
      const currentWeekStart = weekDates[0];

      lastWeekTimesheets.forEach((ts) => {
        // 计算对应的本周日期（保持星期几不变）
        const lastWeekDate = new Date(ts.work_date);
        const dayOfWeek =
          lastWeekDate.getDay() === 0 ? 7 : lastWeekDate.getDay(); // 转换为1-7（周一到周日）
        const currentWeekDate = new Date(currentWeekStart);
        currentWeekDate.setDate(currentWeekStart.getDate() + dayOfWeek - 1);

        // 检查本周该日期是否已有记录
        const dateStr = formatFullDate(currentWeekDate);
        const existing = entries.find(
          (e) =>
            e.project_id === ts.project_id &&
            e.task_id === ts.task_id &&
            e.hours?.[dateStr],
        );

        if (!existing && parseFloat(ts.work_hours || 0) > 0) {
          timesheetsToCreate.push({
            project_id: ts.project_id,
            rd_project_id: ts.rd_project_id,
            task_id: ts.task_id,
            work_date: dateStr,
            work_hours: parseFloat(ts.work_hours || 0),
            work_type: ts.work_type || "NORMAL",
            description: ts.description || "",
          });
        }
      });

      if (timesheetsToCreate.length > 0) {
        await timesheetApi.batchCreate({
          timesheets: timesheetsToCreate,
        });
        alert(`成功复制 ${timesheetsToCreate.length} 条工时记录`);
        // 重新加载数据
        await loadWeekTimesheet();
      } else {
        alert("本周已有对应日期的工时记录，无需复制");
      }
    } catch (error) {
      console.error("复制上周工时记录失败:", error);
      alert("复制上周工时记录失败，请稍后重试");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="工时填报"
            description="记录您的工作时间，便于项目成本核算与绩效统计"
          />

          {loading && (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
              <span className="text-slate-400">加载中...</span>
            </div>
          )}

          {/* Week Summary */}
          <motion.div
            variants={fadeIn}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {[
              {
                label: "本周工时",
                value: `${weeklyTotal}h`,
                icon: Clock,
                color: "text-blue-400",
                desc: `目标 40h`,
              },
              {
                label: "加班工时",
                value: `${Math.max(0, weeklyTotal - 40)}h`,
                icon: Timer,
                color: weeklyTotal > 40 ? "text-amber-400" : "text-slate-400",
                desc: "超出标准工时",
              },
              {
                label: "参与项目",
                value: new Set(entries.map((e) => e.project_id).filter(Boolean))
                  .size,
                icon: Briefcase,
                color: "text-emerald-400",
                desc: "个项目",
              },
              {
                label: "休息时间",
                value: `${Math.max(0, 168 - weeklyTotal - 56)}h`,
                icon: Coffee,
                color: "text-purple-400",
                desc: "本周剩余",
              },
            ].map((stat, index) => (
              <Card key={index} className="bg-surface-1/50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">{stat.label}</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {stat.value}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {stat.desc}
                      </p>
                    </div>
                    <stat.icon className={cn("w-8 h-8", stat.color)} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>

          {/* Week Navigation */}
          <motion.div variants={fadeIn}>
            <Card className="bg-surface-1/50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setWeekOffset(weekOffset - 1)}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <div className="flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-accent" />
                      <span className="font-medium text-white">
                        {formatFullDate(weekDates[0])} ~{" "}
                        {formatFullDate(weekDates[6])}
                      </span>
                      {isCurrentWeek && (
                        <Badge variant="secondary" className="ml-2">
                          本周
                        </Badge>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setWeekOffset(weekOffset + 1)}
                      disabled={weekOffset >= 0}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setShowAddDialog(true)}
                      disabled={loading}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      添加记录
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCopyLastWeek}
                      disabled={loading || weekOffset === 0}
                      title="复制上周的工时记录"
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      复制上周
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleSaveDraft}
                      disabled={loading || saving}
                    >
                      <Save className="w-4 h-4 mr-1" />
                      保存草稿
                    </Button>
                    <Button
                      onClick={handleSubmit}
                      disabled={
                        loading ||
                        saving ||
                        entries.filter((e) => e.status === "DRAFT").length === 0
                      }
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Send className="w-4 h-4 mr-1" />
                      {saving ? "提交中..." : "提交审批"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Timesheet Table */}
          <motion.div variants={fadeIn}>
            <Card className="bg-surface-1/50 overflow-hidden">
              <CardHeader className="pb-0">
                <CardTitle className="text-lg">工时明细</CardTitle>
                <CardDescription>
                  填写每天在各项目任务上投入的工时
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-4 text-sm font-medium text-slate-400 min-w-[200px]">
                          项目 / 任务
                        </th>
                        {weekDates.map((date, index) => {
                          const isToday =
                            formatFullDate(date) === formatFullDate(new Date());
                          const isWeekend = index >= 5;
                          return (
                            <th
                              key={index}
                              className={cn(
                                "text-center p-4 text-sm font-medium min-w-[80px]",
                                isWeekend ? "text-slate-500" : "text-slate-400",
                                isToday && "bg-accent/10",
                              )}
                            >
                              <div>{dayNames[index]}</div>
                              <div className="text-xs mt-0.5">
                                {formatDate(date)}
                              </div>
                            </th>
                          );
                        })}
                        <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[80px]">
                          小计
                        </th>
                        <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[100px]">
                          状态
                        </th>
                        <th className="text-center p-4 text-sm font-medium text-slate-400 w-[60px]">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {entries.length === 0 && !loading ? (
                        <tr>
                          <td
                            colSpan={10}
                            className="p-8 text-center text-slate-400"
                          >
                            暂无工时记录，点击"添加记录"开始填报
                          </td>
                        </tr>
                      ) : (
                        entries.map((entry) => {
                          const entryTotal = Object.values(
                            entry.hours || {},
                          ).reduce((a, b) => {
                            const val =
                              typeof b === "number" ? b : parseFloat(b) || 0;
                            return a + val;
                          }, 0);
                          const isEditable = entry.status === "DRAFT";

                          return (
                            <tr
                              key={entry.id}
                              className="border-b border-border/50 hover:bg-surface-2/30"
                            >
                              <td className="p-4">
                                <div>
                                  <div className="font-medium text-white text-sm">
                                    {entry.project_name || "未分配项目"}
                                  </div>
                                  <div className="text-xs text-slate-400">
                                    {entry.project_code || entry.project_id}{" "}
                                    {entry.task_name
                                      ? `· ${entry.task_name}`
                                      : ""}
                                  </div>
                                </div>
                              </td>
                              {weekDates.map((date, index) => {
                                const dateStr = formatFullDate(date);
                                const hoursValue = entry.hours?.[dateStr];
                                const hours =
                                  typeof hoursValue === "number"
                                    ? hoursValue
                                    : parseFloat(hoursValue) || 0;
                                const isToday =
                                  dateStr === formatFullDate(new Date());
                                const isWeekend = index >= 5;

                                return (
                                  <td
                                    key={index}
                                    className={cn(
                                      "p-2 text-center",
                                      isToday && "bg-blue-500/10",
                                      isWeekend && "bg-slate-700/30",
                                    )}
                                  >
                                    {isEditable ? (
                                      <Input
                                        type="number"
                                        min="0"
                                        max="24"
                                        step="0.5"
                                        value={hours > 0 ? hours : ""}
                                        onChange={(e) =>
                                          handleHoursChange(
                                            entry.id,
                                            dateStr,
                                            e.target.value,
                                          )
                                        }
                                        className="w-16 h-8 text-center mx-auto bg-slate-700 border-slate-600 text-white"
                                        placeholder="0"
                                      />
                                    ) : (
                                      <span
                                        className={cn(
                                          "text-sm",
                                          hours > 0
                                            ? "text-white"
                                            : "text-slate-500",
                                        )}
                                      >
                                        {hours > 0 ? hours : "-"}
                                      </span>
                                    )}
                                  </td>
                                );
                              })}
                              <td className="p-4 text-center">
                                <span className="font-medium text-white">
                                  {entryTotal}h
                                </span>
                              </td>
                              <td className="p-4 text-center">
                                {getStatusBadge(entry.status)}
                              </td>
                              <td className="p-4 text-center">
                                {isEditable && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteEntry(entry.id)}
                                    className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                )}
                              </td>
                            </tr>
                          );
                        })
                      )}

                      {/* Daily Totals Row */}
                      <tr className="bg-surface-2/50 border-t-2 border-border">
                        <td className="p-4 font-medium text-white">每日合计</td>
                        {weekDates.map((date, index) => {
                          const dateStr = formatFullDate(date);
                          const total = dailyTotals[dateStr] || 0;
                          const isToday =
                            dateStr === formatFullDate(new Date());
                          const isOvertime = total > 8;

                          return (
                            <td
                              key={index}
                              className={cn(
                                "p-4 text-center font-medium",
                                isToday && "bg-accent/10",
                                isOvertime ? "text-amber-400" : "text-white",
                              )}
                            >
                              {total}h
                            </td>
                          );
                        })}
                        <td className="p-4 text-center">
                          <span
                            className={cn(
                              "font-bold text-lg",
                              weeklyTotal > 40
                                ? "text-amber-400"
                                : "text-emerald-400",
                            )}
                          >
                            {weeklyTotal}h
                          </span>
                        </td>
                        <td colSpan={2}></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Add Entry Dialog */}
          <AddEntryDialog
            open={showAddDialog}
            onOpenChange={setShowAddDialog}
            onAdd={handleAddEntry}
            weekDates={weekDates}
            projects={projects}
            loading={loading}
          />
        </motion.div>
      </div>
    </div>
  );
}
