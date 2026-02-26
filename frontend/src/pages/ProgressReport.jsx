/**
 * Progress Report Page - 进度填报页面
 * Features: 日报/周报填报，任务进度更新
 */
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  Plus,
  Save,
  FileText,
  AlertTriangle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate } from "../lib/utils";
import { progressApi, projectApi } from "../services/api";
import { Edit } from "lucide-react";
export default function ProgressReport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [reportType, setReportType] = useState("DAILY"); // DAILY or WEEKLY
  const [reportDate, setReportDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [reportContent, setReportContent] = useState("");
  const [taskProgress, setTaskProgress] = useState({});
  // Dialogs
  const [showTaskProgressDialog, setShowTaskProgressDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [progressValue, setProgressValue] = useState(0);
  const [progressNote, setProgressNote] = useState("");
  useEffect(() => {
    if (id) {
      fetchProject();
      fetchTasks();
    }
  }, [id]);
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id);
      setProject(res.data || res);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };
  const fetchTasks = async () => {
    try {
      setLoading(true);
      const res = await progressApi.tasks.list({ project_id: id });
      const taskList = res.data?.items || res.data || [];
      setTasks(taskList);
      // Initialize task progress
      const progressMap = {};
      taskList.forEach((task) => {
        progressMap[task.id] = task.progress || 0;
      });
      setTaskProgress(progressMap);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleUpdateTaskProgress = async () => {
    if (!selectedTask) {return;}
    try {
      await progressApi.tasks.updateProgress(selectedTask.id, {
        progress: progressValue,
        note: progressNote
      });
      setShowTaskProgressDialog(false);
      setProgressValue(0);
      setProgressNote("");
      fetchTasks();
    } catch (error) {
      console.error("Failed to update task progress:", error);
      alert("更新进度失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleSubmitReport = async () => {
    if (!reportContent.trim()) {
      alert("请填写报告内容");
      return;
    }
    try {
      await progressApi.reports.create({
        project_id: parseInt(id),
        report_type: reportType,
        report_date: reportDate,
        content: reportContent,
        task_progress: taskProgress
      });
      alert("提交成功");
      setReportContent("");
      setTaskProgress({});
    } catch (error) {
      console.error("Failed to submit report:", error);
      alert("提交失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const openTaskProgressDialog = (task) => {
    setSelectedTask(task);
    setProgressValue(taskProgress[task.id] || task.progress || 0);
    setProgressNote("");
    setShowTaskProgressDialog(true);
  };
  const getStatusColor = (status) => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-500";
      case "IN_PROGRESS":
        return "bg-blue-500";
      case "BLOCKED":
        return "bg-red-500";
      case "PENDING":
        return "bg-slate-300";
      default:
        return "bg-slate-300";
    }
  };
  const getStatusLabel = (status) => {
    switch (status) {
      case "COMPLETED":
        return "已完成";
      case "IN_PROGRESS":
        return "进行中";
      case "BLOCKED":
        return "阻塞";
      case "PENDING":
        return "待开始";
      default:
        return "未知";
    }
  };
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}>

            <ArrowLeft className="w-4 h-4 mr-2" />
            返回项目
          </Button>
          <PageHeader
            title={`${project?.project_name || "项目"} - 进度填报`}
            description="填写日报或周报，更新任务进度" />

        </div>
      </div>
      {/* Report Type Selection */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">报告类型</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DAILY">日报</SelectItem>
                  <SelectItem value="WEEKLY">周报</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">报告日期</label>
              <Input
                type="date"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)} />

            </div>
          </div>
        </CardContent>
      </Card>
      {/* Task Progress */}
      <Card>
        <CardHeader>
          <CardTitle>任务进度</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          tasks.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无任务</div> :

          <div className="space-y-3">
              {tasks.map((task) => {
              const progress = taskProgress[task.id] || task.progress || 0;
              return (
                <div
                  key={task.id}
                  className="border rounded-lg p-4 hover:bg-slate-50 transition-colors">

                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getStatusColor(task.status)}>
                            {getStatusLabel(task.status)}
                          </Badge>
                          <h3 className="font-medium">{task.task_name}</h3>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(task.planned_start_date)} -{" "}
                            {formatDate(task.planned_end_date)}
                          </div>
                          {task.assignee_name &&
                        <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {task.assignee_name}
                        </div>
                        }
                        </div>
                      </div>
                      <div className="text-right mr-4">
                        <div className="text-2xl font-bold text-slate-700">
                          {progress}%
                        </div>
                        <div className="text-xs text-slate-500">完成度</div>
                      </div>
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openTaskProgressDialog(task)}>

                        <Edit className="w-4 h-4 mr-2" />
                        更新进度
                      </Button>
                    </div>
                    <Progress value={progress} className="h-2" />
                </div>);

            })}
          </div>
          }
        </CardContent>
      </Card>
      {/* Report Content */}
      <Card>
        <CardHeader>
          <CardTitle>报告内容</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                今日/本周工作内容
              </label>
              <textarea
                className="w-full min-h-[120px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={reportContent}
                onChange={(e) => setReportContent(e.target.value)}
                placeholder="请填写工作内容、完成情况、遇到的问题等..." />

            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setReportContent("")}>
                清空
              </Button>
              <Button onClick={handleSubmitReport}>
                <Save className="w-4 h-4 mr-2" />
                提交报告
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Task Progress Dialog */}
      <Dialog
        open={showTaskProgressDialog}
        onOpenChange={setShowTaskProgressDialog}>

        <DialogContent>
          <DialogHeader>
            <DialogTitle>更新任务进度</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedTask &&
            <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">任务名称</div>
                  <div className="font-medium">{selectedTask.task_name}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    完成进度 (%)
                  </label>
                  <div className="space-y-2">
                    <Input
                    type="number"
                    min="0"
                    max="100"
                    value={progressValue}
                    onChange={(e) =>
                    setProgressValue(parseInt(e.target.value) || 0)
                    } />

                    <Progress value={progressValue} className="h-2" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    进度说明
                  </label>
                  <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={progressNote}
                  onChange={(e) => setProgressNote(e.target.value)}
                  placeholder="填写进度说明..." />

                </div>
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowTaskProgressDialog(false)}>

              取消
            </Button>
            <Button onClick={handleUpdateTaskProgress}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}