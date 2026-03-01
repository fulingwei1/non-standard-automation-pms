/**
 * AI 智能排计划页面
 * 功能：
 * - 生成正常/高强度两种模式计划
 * - 对比选择
 * - 可视化调整
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  Zap,
  TrendingUp,
  RefreshCw,
  Save,
  CheckCircle,
  AlertCircle,
  ChevronRight,
  Edit2,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Input,
  Label,
} from "../components/ui";
import { scheduleGenerationApi } from "../services/api";

export default function ScheduleGeneration() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [schedules, setSchedules] = useState(null);
  const [selectedMode, setSelectedMode] = useState("normal");
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const generateSchedules = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await scheduleGenerationApi.generateBothModes(projectId);
      setSchedules(res.data || res);
    } catch (error) {
      console.error("生成失败:", error);
      alert("生成失败：" + error.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    generateSchedules();
  }, [generateSchedules]);

  const handleSave = async (mode) => {
    try {
      const scheduleData = mode === 'normal' 
        ? schedules.normal_mode 
        : schedules.intensive_mode;
      
      await scheduleGenerationApi.saveSchedule(projectId, scheduleData);
      alert("计划已保存");
      navigate("/schedule-plans");
    } catch (error) {
      alert("保存失败：" + error.message);
    }
  };

  const handleAdjustTask = (task) => {
    setSelectedTask(task);
    setShowAdjustDialog(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Calendar className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
        <span className="text-slate-400">AI 生成计划中...</span>
      </div>
    );
  }

  if (!schedules) {
    return (
      <div className="text-center py-12 text-slate-400">
        生成失败
      </div>
    );
  }

  const currentSchedule = selectedMode === 'normal' 
    ? schedules.normal_mode 
    : schedules.intensive_mode;

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
            title="AI 智能排计划"
            description="基于历史数据生成项目计划，支持正常/高强度两种模式"
            actions={
              <div className="flex gap-2">
                <Button onClick={generateSchedules} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  重新生成
                </Button>
                <Button 
                  onClick={() => handleSave(selectedMode)}
                  variant="outline"
                >
                  <Save className="w-4 h-4 mr-2" />
                  保存此方案
                </Button>
              </div>
            }
          />

          {/* 模式对比 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card 
              className={`cursor-pointer transition-all ${
                selectedMode === 'normal' 
                  ? 'border-blue-500 ring-2 ring-blue-500' 
                  : 'border-slate-700'
              }`}
              onClick={() => setSelectedMode('normal')}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  正常强度模式
                </CardTitle>
                <CardDescription>
                  标准工期，质量保证
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">总工期</span>
                    <span className="text-2xl font-bold">
                      {schedules.normal_mode.total_days}天
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">效率系数</span>
                    <span className="text-lg">
                      {schedules.normal_mode.overall_efficiency}x
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">AI 提升</span>
                    <span className="text-lg">
                      +{(schedules.normal_mode.ai_boost_factor - 1) * 100}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card 
              className={`cursor-pointer transition-all ${
                selectedMode === 'intensive' 
                  ? 'border-orange-500 ring-2 ring-orange-500' 
                  : 'border-slate-700'
              }`}
              onClick={() => setSelectedMode('intensive')}
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-orange-500" />
                  高强度模式（加速）
                </CardTitle>
                <CardDescription>
                  工期缩短{schedules.comparison.time_saved_percentage}%，需更多资源
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">总工期</span>
                    <span className="text-2xl font-bold text-orange-500">
                      {schedules.intensive_mode.total_days}天
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-green-500">
                    <span className="text-sm">节省{schedules.comparison.time_saved}天</span>
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">效率要求</span>
                    <span className="text-lg">
                      {schedules.intensive_mode.overall_efficiency}x
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 计划详情 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{currentSchedule.mode_name} - 项目计划</CardTitle>
                  <CardDescription>
                    {currentSchedule.start_date} 至 {currentSchedule.end_date} 
                    （共{currentSchedule.total_days}天）
                  </CardDescription>
                </div>
                <Badge variant={selectedMode === 'intensive' ? 'destructive' : 'default'}>
                  {currentSchedule.mode_name}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {/* 阶段概览 */}
              <div className="grid grid-cols-5 gap-2 mb-6">
                {Object.entries(currentSchedule.phases || {}).map(([key, phase]) => (
                  <div key={key} className="p-3 rounded-lg border bg-slate-800/50">
                    <div className="text-xs text-slate-400 mb-1">{phase.name}</div>
                    <div className="text-lg font-bold">{phase.duration}天</div>
                    <div className="text-xs text-slate-500">{phase.tasks.length}任务</div>
                  </div>
                ))}
              </div>

              {/* 任务列表 */}
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>任务名称</TableHead>
                    <TableHead>阶段</TableHead>
                    <TableHead>工期</TableHead>
                    <TableHead>开始日期</TableHead>
                    <TableHead>结束日期</TableHead>
                    <TableHead>负责人</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(currentSchedule.tasks || []).map((task, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">
                        {task.task_name}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {task.phase_name}
                        </Badge>
                      </TableCell>
                      <TableCell>{task.duration}天</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span className="text-xs">
                            D+{task.start_day}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-xs">
                            D+{task.end_day}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>-</TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleAdjustTask(task)}
                        >
                          <Edit2 className="w-3 h-3" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 效率分析 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-8 h-8 text-green-500" />
                  <div>
                    <div className="text-sm text-slate-400">团队效率</div>
                    <div className="text-2xl font-bold">
                      {currentSchedule.team_efficiency_factor}x
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Zap className="w-8 h-8 text-purple-500" />
                  <div>
                    <div className="text-sm text-slate-400">AI 提升</div>
                    <div className="text-2xl font-bold">
                      {currentSchedule.ai_boost_factor}x
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-8 h-8 text-blue-500" />
                  <div>
                    <div className="text-sm text-slate-400">综合效率</div>
                    <div className="text-2xl font-bold">
                      {currentSchedule.overall_efficiency}x
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 调整任务对话框 */}
          <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>调整任务 - {selectedTask?.task_name}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>工期（天）</Label>
                  <Input
                    type="number"
                    defaultValue={selectedTask?.duration}
                    min="1"
                  />
                </div>
                <div>
                  <Label>开始日期</Label>
                  <Input
                    type="date"
                    defaultValue={selectedTask?.start_date}
                  />
                </div>
                <div>
                  <Label>负责人</Label>
                  <Input placeholder="选择工程师..." />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setShowAdjustDialog(false)}>取消</Button>
                <Button onClick={() => setShowAdjustDialog(false)}>保存</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
