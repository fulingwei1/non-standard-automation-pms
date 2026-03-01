import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fieldCommissioningApi } from "../services/api/fieldCommissioning";
import { PageHeader } from "../components/layout/PageHeader";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Slider } from "../components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  ClipboardList,
  MapPin,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Calendar,
  User,
  FileText,
  Camera,
  Signature,
  X,
  RefreshCw,
} from "lucide-react";

// 状态配置
const statusConfig = {
  pending: { label: "待开始", color: "bg-gray-500/20 text-gray-400 border-gray-500/30" },
  in_progress: { label: "进行中", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  completed: { label: "已完成", color: "bg-green-500/20 text-green-400 border-green-500/30" },
  cancelled: { label: "已取消", color: "bg-red-500/20 text-red-400 border-red-500/30" },
};


export default function FieldCommissioning() {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showCheckinDialog, setShowCheckinDialog] = useState(false);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showIssueDialog, setShowIssueDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [checkinData, setCheckinData] = useState({ latitude: 31.2304, longitude: 121.4737 });
  const [progressData, setProgressData] = useState({ progress: 0, note: "" });
  const [issueData, setIssueData] = useState({ description: "", photo_url: "", severity: "medium" });
  const [completeData, setCompleteData] = useState({ signature: "", completion_note: "" });
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    fetchTasks();
    fetchStats();
  }, [statusFilter]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const params = statusFilter ? { status: statusFilter } : {};
      const response = await fieldCommissioningApi.list(params);
      setTasks(response.data || []);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fieldCommissioningApi.dashboard();
      setStats(response.data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const handleCheckin = async () => {
    try {
      await fieldCommissioningApi.checkin(selectedTask.id, checkinData);
      setShowCheckinDialog(false);
      fetchTasks();
      fetchStats();
      alert("签到成功！");
    } catch (error) {
      console.error("Checkin failed:", error);
      alert("签到失败，请重试");
    }
  };

  const handleUpdateProgress = async () => {
    try {
      await fieldCommissioningApi.updateProgress(selectedTask.id, {
        progress: progressData.progress,
        note: progressData.note,
      });
      setShowProgressDialog(false);
      fetchTasks();
      alert("进度更新成功！");
    } catch (error) {
      console.error("Update progress failed:", error);
      alert("更新失败，请重试");
    }
  };

  const handleReportIssue = async () => {
    try {
      await fieldCommissioningApi.reportIssue(selectedTask.id, issueData);
      setShowIssueDialog(false);
      fetchStats();
      alert("问题报告成功！");
    } catch (error) {
      console.error("Report issue failed:", error);
      alert("报告失败，请重试");
    }
  };

  const handleComplete = async () => {
    try {
      await fieldCommissioningApi.complete(selectedTask.id, completeData);
      setShowCompleteDialog(false);
      fetchTasks();
      fetchStats();
      alert("任务完成确认成功！");
    } catch (error) {
      console.error("Complete failed:", error);
      alert("确认失败，请重试");
    }
  };

  const simulateGPS = () => {
    // 模拟获取 GPS 坐标（以上海为中心随机偏移）
    const lat = 31.2304 + (Math.random() - 0.5) * 0.01;
    const lng = 121.4737 + (Math.random() - 0.5) * 0.01;
    setCheckinData({ latitude: parseFloat(lat.toFixed(6)), longitude: parseFloat(lng.toFixed(6)) });
  };

  const openProgressDialog = (task) => {
    setSelectedTask(task);
    setProgressData({ progress: task.progress || 0, note: task.progress_note || "" });
    setShowProgressDialog(true);
  };

  const openIssueDialog = (task) => {
    setSelectedTask(task);
    setIssueData({ description: "", photo_url: "", severity: "medium" });
    setShowIssueDialog(true);
  };

  const openCompleteDialog = (task) => {
    setSelectedTask(task);
    setCompleteData({ signature: "", completion_note: "" });
    setShowCompleteDialog(true);
  };

  return (
    <div className="p-4 md:p-6 space-y-4 md:space-y-6 bg-gray-950 min-h-screen">
      <PageHeader
        title="现场调试"
        description="移动端现场调试任务管理"
        icon={ClipboardList}
      />

      {loading && !tasks.length ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-gray-400">加载中...</div>
        </div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-4 md:space-y-6"
        >
          {/* 统计概览 */}
          {stats && (
            <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
              <Card className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-3 md:p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="h-4 w-4 text-blue-400" />
                    <p className="text-xs md:text-sm text-gray-400">今日任务</p>
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white">{stats.today_tasks || 0}</p>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-3 md:p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-blue-400" />
                    <p className="text-xs md:text-sm text-gray-400">进行中</p>
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white">{stats.in_progress || 0}</p>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-3 md:p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="h-4 w-4 text-green-400" />
                    <p className="text-xs md:text-sm text-gray-400">已完成</p>
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white">{stats.completed || 0}</p>
                </CardContent>
              </Card>
              <Card className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-3 md:p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    <p className="text-xs md:text-sm text-gray-400">问题</p>
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white">{stats.issue_count || 0}</p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 筛选工具栏 */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-3 md:p-4">
              <div className="flex flex-wrap gap-2 md:gap-3 items-center">
                <Select value={statusFilter === '' ? '__all__' : statusFilter} onValueChange={(v) => setStatusFilter(v === '__all__' ? '' : v)}>
                  <SelectTrigger className="w-full md:w-[140px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="状态筛选" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="__all__" className="text-white">全部状态</SelectItem>
                    <SelectItem value="pending" className="text-white">待开始</SelectItem>
                    <SelectItem value="in_progress" className="text-white">进行中</SelectItem>
                    <SelectItem value="completed" className="text-white">已完成</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  onClick={fetchTasks}
                  className="border-gray-700 text-gray-300 hover:bg-gray-800 ml-auto"
                >
                  <RefreshCw className="h-4 w-4 md:mr-2" />
                  <span className="hidden md:inline">刷新</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 任务列表 */}
          {tasks.length === 0 ? (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardContent className="p-8 md:p-12 text-center text-gray-400">
                <ClipboardList className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暂无现场调试任务</p>
              </CardContent>
            </Card>
          ) : (
            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4"
            >
              {tasks.map((task) => (
                <motion.div key={task.id} variants={fadeIn}>
                  <Card className="bg-gray-900/50 border-gray-800 hover:border-gray-700 transition-colors h-full">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className={statusConfig[task.status]?.color || "bg-gray-700"}>
                              {statusConfig[task.status]?.label || task.status}
                            </Badge>
                          </div>
                          <CardTitle className="text-base md:text-lg text-white line-clamp-2">
                            {task.project_name}
                          </CardTitle>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <User className="h-4 w-4" />
                        <span className="truncate">{task.customer_name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <MapPin className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate">{task.address}</span>
                      </div>
                      {task.scheduled_date && (
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                          <Calendar className="h-4 w-4" />
                          <span>{task.scheduled_date}</span>
                        </div>
                      )}
                      {task.progress > 0 && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-gray-400">
                            <span>进度</span>
                            <span>{task.progress}%</span>
                          </div>
                          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 transition-all"
                              style={{ width: `${task.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-800">
                        {task.status === "pending" && (
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedTask(task);
                              setShowCheckinDialog(true);
                            }}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-xs md:text-sm"
                          >
                            <MapPin className="h-3 w-3 md:mr-1" />
                            <span className="hidden md:inline">签到</span>
                          </Button>
                        )}
                        {task.status === "in_progress" && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => openProgressDialog(task)}
                              className="flex-1 bg-green-600 hover:bg-green-700 text-xs md:text-sm"
                            >
                              <TrendingUp className="h-3 w-3 md:mr-1" />
                              <span className="hidden md:inline">进度</span>
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openIssueDialog(task)}
                              className="flex-1 border-amber-600 text-amber-400 hover:bg-amber-600/20 text-xs md:text-sm"
                            >
                              <AlertTriangle className="h-3 w-3 md:mr-1" />
                              <span className="hidden md:inline">问题</span>
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => openCompleteDialog(task)}
                              className="flex-1 bg-purple-600 hover:bg-purple-700 text-xs md:text-sm"
                            >
                              <Signature className="h-3 w-3 md:mr-1" />
                              <span className="hidden md:inline">完成</span>
                            </Button>
                          </>
                        )}
                        {task.status === "completed" && (
                          <Badge className="w-full justify-center bg-green-500/20 text-green-400 border-green-500/30">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            已完成
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* 签到对话框 */}
      <Dialog open={showCheckinDialog} onOpenChange={setShowCheckinDialog}>
        <DialogContent className="max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">现场签到</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedTask && (
              <div className="text-sm text-gray-400">
                <p className="font-medium text-white">{selectedTask.project_name}</p>
                <p>{selectedTask.address}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label className="text-gray-300">GPS 坐标</Label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Input
                    type="number"
                    step="0.000001"
                    value={checkinData.latitude}
                    onChange={(e) => setCheckinData({ ...checkinData, latitude: parseFloat(e.target.value) })}
                    className="bg-gray-800 border-gray-700 text-white"
                    placeholder="纬度"
                  />
                  <p className="text-xs text-gray-500 mt-1">纬度</p>
                </div>
                <div>
                  <Input
                    type="number"
                    step="0.000001"
                    value={checkinData.longitude}
                    onChange={(e) => setCheckinData({ ...checkinData, longitude: parseFloat(e.target.value) })}
                    className="bg-gray-800 border-gray-700 text-white"
                    placeholder="经度"
                  />
                  <p className="text-xs text-gray-500 mt-1">经度</p>
                </div>
              </div>
              <Button
                variant="outline"
                onClick={simulateGPS}
                className="w-full border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                <MapPin className="h-4 w-4 mr-2" />
                模拟获取 GPS
              </Button>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCheckinDialog(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleCheckin} className="bg-blue-600 hover:bg-blue-700">
                确认签到
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 进度更新对话框 */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent className="max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">更新进度</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedTask && (
              <div className="text-sm text-gray-400">
                <p className="font-medium text-white">{selectedTask.project_name}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label className="text-gray-300">进度：{progressData.progress}%</Label>
              <Slider
                value={[progressData.progress]}
                onValueChange={(v) => setProgressData({ ...progressData, progress: v[0] })}
                max={100}
                step={5}
                className="py-2"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-300">备注</Label>
              <Textarea
                value={progressData.note}
                onChange={(e) => setProgressData({ ...progressData, note: e.target.value })}
                className="bg-gray-800 border-gray-700 text-white min-h-[80px]"
                placeholder="输入进度说明..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowProgressDialog(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleUpdateProgress} className="bg-green-600 hover:bg-green-700">
                更新进度
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 问题报告对话框 */}
      <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
        <DialogContent className="max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">报告问题</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedTask && (
              <div className="text-sm text-gray-400">
                <p className="font-medium text-white">{selectedTask.project_name}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label className="text-gray-300">严重程度</Label>
              <Select value={issueData.severity} onValueChange={(v) => setIssueData({ ...issueData, severity: v })}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                  <SelectValue placeholder="选择严重程度" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  <SelectItem value="low" className="text-white">低</SelectItem>
                  <SelectItem value="medium" className="text-white">中</SelectItem>
                  <SelectItem value="high" className="text-white">高</SelectItem>
                  <SelectItem value="critical" className="text-white">严重</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-gray-300">问题描述 *</Label>
              <Textarea
                value={issueData.description}
                onChange={(e) => setIssueData({ ...issueData, description: e.target.value })}
                className="bg-gray-800 border-gray-700 text-white min-h-[100px]"
                placeholder="详细描述遇到的问题..."
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-300">照片 URL（可选）</Label>
              <div className="flex gap-2">
                <Input
                  value={issueData.photo_url}
                  onChange={(e) => setIssueData({ ...issueData, photo_url: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-white flex-1"
                  placeholder="https://..."
                />
                <Button variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800">
                  <Camera className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowIssueDialog(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleReportIssue} className="bg-amber-600 hover:bg-amber-700">
                提交报告
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 完成任务对话框 */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="max-w-md bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">完成任务</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedTask && (
              <div className="text-sm text-gray-400">
                <p className="font-medium text-white">{selectedTask.project_name}</p>
              </div>
            )}
            <div className="space-y-2">
              <Label className="text-gray-300">电子签名 *</Label>
              <Input
                value={completeData.signature}
                onChange={(e) => setCompleteData({ ...completeData, signature: e.target.value })}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="输入您的姓名作为签名"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-300">完成备注（可选）</Label>
              <Textarea
                value={completeData.completion_note}
                onChange={(e) => setCompleteData({ ...completeData, completion_note: e.target.value })}
                className="bg-gray-800 border-gray-700 text-white min-h-[80px]"
                placeholder="输入完成情况说明..."
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCompleteDialog(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleComplete} className="bg-purple-600 hover:bg-purple-700">
                确认完成
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
