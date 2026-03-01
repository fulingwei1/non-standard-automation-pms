/**
 * 年度重点工作管理页面
 * 卡片列表展示、创建/编辑、进度更新
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Edit2,
  Trash2,
  ChevronRight,
  TrendingUp,
  DollarSign,
  Target,
  Calendar,
  X,
  Save,
  Sliders,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Textarea,
  Slider,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { annualWorkApi, strategyApi } from "@/services/api/strategy";

const PRIORITY_CONFIG = {
  HIGH: { label: "高优先级", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  MEDIUM: { label: "中优先级", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  LOW: { label: "低优先级", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
};

const STATUS_CONFIG = {
  PLANNED: { label: "计划中", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  DELAYED: { label: "已延期", color: "bg-red-500/20 text-red-400 border-red-500/30" },
};

export default function AnnualWorkList() {
  const [loading, setLoading] = useState(true);
  const [works, setWorks] = useState([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWork, setEditingWork] = useState(null);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [progressWork, setProgressWork] = useState(null);
  const [progressValue, setProgressValue] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    csf_id: "",
    priority: "MEDIUM",
    status: "PLANNED",
    budget: "",
    actual_cost: "",
    start_date: "",
    end_date: "",
    description: "",
  });

  // 获取战略列表
  useEffect(() => {
    fetchStrategies();
  }, []);

  // 获取年度重点工作列表
  useEffect(() => {
    if (selectedStrategyId != null) {
      fetchWorks();
    } else {
      setLoading(false);
    }
  }, [selectedStrategyId]);

  const fetchStrategies = async () => {
    try {
      const { data } = await strategyApi.list({});
      const list = data?.items ?? data ?? [];
      setStrategies(Array.isArray(list) ? list : []);
      const arr = Array.isArray(list) ? list : [];
      if (arr.length > 0 && !selectedStrategyId) {
        setSelectedStrategyId(arr[0].id);
      }
    } catch (error) {
      console.error("获取战略列表失败:", error);
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorks = async () => {
    setLoading(true);
    try {
      const { data } = await annualWorkApi.list({ strategy_id: selectedStrategyId });
      setWorks(data.items || data || []);
    } catch (error) {
      console.error("获取年度重点工作失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchWorks();
    setRefreshing(false);
  };

  const handleOpenCreate = () => {
    setEditingWork(null);
    setFormData({
      name: "",
      csf_id: "",
      priority: "MEDIUM",
      status: "PLANNED",
      budget: "",
      actual_cost: "",
      start_date: "",
      end_date: "",
      description: "",
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (work) => {
    setEditingWork(work);
    setFormData({
      name: work.name || "",
      csf_id: work.csf_id || "",
      priority: work.priority || "MEDIUM",
      status: work.status || "PLANNED",
      budget: work.budget?.toString() || "",
      actual_cost: work.actual_cost?.toString() || "",
      start_date: work.start_date || "",
      end_date: work.end_date || "",
      description: work.description || "",
    });
    setIsModalOpen(true);
  };

  const handleOpenProgress = (work) => {
    setProgressWork(work);
    setProgressValue(work.progress || 0);
    setIsProgressModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const submitData = {
        ...formData,
        strategy_id: selectedStrategyId,
        budget: formData.budget ? parseFloat(formData.budget) : null,
        actual_cost: formData.actual_cost ? parseFloat(formData.actual_cost) : null,
      };

      if (editingWork) {
        await annualWorkApi.update(editingWork.id, submitData);
      } else {
        await annualWorkApi.create(submitData);
      }

      setIsModalOpen(false);
      await fetchWorks();
    } catch (error) {
      console.error("保存失败:", error);
    }
  };

  const handleUpdateProgress = async () => {
    try {
      await annualWorkApi.updateProgress(progressWork.id, {
        progress: progressValue,
      });
      setIsProgressModalOpen(false);
      await fetchWorks();
    } catch (error) {
      console.error("更新进度失败:", error);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("确定要删除这项重点工作吗？")) return;
    try {
      await annualWorkApi.delete(id);
      await fetchWorks();
    } catch (error) {
      console.error("删除失败:", error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="年度重点工作"
        description="管理年度重点工作任务、追踪进度、监控成本"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Select
              value={selectedStrategyId != null ? selectedStrategyId.toString() : "__none__"}
              onValueChange={(val) => val !== "__none__" && setSelectedStrategyId(parseInt(val))}
            >
              <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="选择战略" />
              </SelectTrigger>
              <SelectContent>
                {strategies.length === 0 ? (
                  <SelectItem value="__none__">暂无战略，请先创建</SelectItem>
                ) : (
                  strategies.map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.name} ({s.year})
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <TrendingUp className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              刷新
            </Button>
            <Button onClick={handleOpenCreate}>
              <Plus className="w-4 h-4 mr-2" />
              新增重点工作
            </Button>
          </motion.div>
        }
      />

      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{works.length}</p>
                <p className="text-xs text-slate-400">重点工作总数</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {works.filter((w) => w.status === "COMPLETED").length}
                </p>
                <p className="text-xs text-slate-400">已完成</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Sliders className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {works.filter((w) => w.status === "IN_PROGRESS").length}
                </p>
                <p className="text-xs text-slate-400">进行中</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <Calendar className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {works.filter((w) => w.status === "DELAYED").length}
                </p>
                <p className="text-xs text-slate-400">已延期</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 重点工作卡片列表 */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {works.map((work) => {
          const priorityConfig = PRIORITY_CONFIG[work.priority] || PRIORITY_CONFIG.MEDIUM;
          const statusConfig = STATUS_CONFIG[work.status] || STATUS_CONFIG.PLANNED;
          const progress = work.progress || 0;

          return (
            <motion.div key={work.id} variants={fadeIn}>
              <Card className="bg-slate-800/40 border-slate-700/50 hover:border-primary/50 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base text-white mb-2">
                        {work.name}
                      </CardTitle>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="outline" className={priorityConfig.color}>
                          {priorityConfig.label}
                        </Badge>
                        <Badge variant="outline" className={statusConfig.color}>
                          {statusConfig.label}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* CSF 关联 */}
                  {work.csf_name && (
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <Target className="w-4 h-4" />
                      <span className="truncate">{work.csf_name}</span>
                    </div>
                  )}

                  {/* 进度条 */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">进度</span>
                      <span className="text-white font-medium">{progress}%</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          progress >= 100
                            ? "bg-emerald-500"
                            : progress >= 50
                            ? "bg-blue-500"
                            : "bg-amber-500"
                        }`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  {/* 成本信息 */}
                  {(work.budget || work.actual_cost) && (
                    <div className="flex items-center gap-4 text-sm">
                      {work.budget && (
                        <div className="flex items-center gap-1 text-slate-400">
                          <DollarSign className="w-4 h-4" />
                          <span>预算：¥{(work.budget / 10000).toFixed(1)}万</span>
                        </div>
                      )}
                      {work.actual_cost && (
                        <div className="flex items-center gap-1 text-slate-400">
                          <DollarSign className="w-4 h-4" />
                          <span>实际：¥{(work.actual_cost / 10000).toFixed(1)}万</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex gap-2 pt-2 border-t border-slate-700/50">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={() => handleOpenProgress(work)}
                    >
                      <Sliders className="w-3 h-3 mr-1" />
                      更新进度
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenEdit(work)}
                    >
                      <Edit2 className="w-3 h-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(work.id)}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {works.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-500">
            <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>暂无重点工作数据</p>
            <p className="text-sm">点击"新增重点工作"开始创建</p>
          </div>
        )}
      </motion.div>

      {/* 创建/编辑弹窗 */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingWork ? "编辑重点工作" : "新增重点工作"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2">
              <Label>工作名称</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="请输入工作名称"
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>优先级</Label>
              <Select
                value={formData.priority}
                onValueChange={(val) => setFormData({ ...formData, priority: val })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HIGH">高优先级</SelectItem>
                  <SelectItem value="MEDIUM">中优先级</SelectItem>
                  <SelectItem value="LOW">低优先级</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>状态</Label>
              <Select
                value={formData.status}
                onValueChange={(val) => setFormData({ ...formData, status: val })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PLANNED">计划中</SelectItem>
                  <SelectItem value="IN_PROGRESS">进行中</SelectItem>
                  <SelectItem value="COMPLETED">已完成</SelectItem>
                  <SelectItem value="DELAYED">已延期</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>预算 (元)</Label>
              <Input
                type="number"
                value={formData.budget}
                onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                placeholder="0"
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>实际成本 (元)</Label>
              <Input
                type="number"
                value={formData.actual_cost}
                onChange={(e) => setFormData({ ...formData, actual_cost: e.target.value })}
                placeholder="0"
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>开始日期</Label>
              <Input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>结束日期</Label>
              <Input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div className="col-span-2">
              <Label>描述</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="工作描述..."
                className="bg-slate-800 border-slate-700 min-h-[80px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSubmit}>
              <Save className="w-4 h-4 mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 进度更新弹窗 */}
      <Dialog open={isProgressModalOpen} onOpenChange={setIsProgressModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle>更新进度 - {progressWork?.name}</DialogTitle>
          </DialogHeader>
          <div className="py-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-400">当前进度</span>
              <span className="text-2xl font-bold text-white">{progressValue}%</span>
            </div>
            <Slider
              value={[progressValue]}
              onValueChange={(val) => setProgressValue(val[0])}
              min={0}
              max={100}
              step={1}
              className="mb-4"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsProgressModalOpen(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateProgress}>
              <Save className="w-4 h-4 mr-2" />
              确认更新
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
