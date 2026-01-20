/**
 * 装配技工专用任务中心
 * 核心功能：
 * 1. 工时填报
 * 2. 装配缺料反馈
 * 3. 零部件质量反馈
 * 4. 装配图纸查看
 * 5. 任务完成确认（含工时填报）
 */
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Wrench,
  AlertTriangle,
  FileWarning,
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  Button,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";

import MaterialShortageDialog from "../components/production/assembler/MaterialShortageDialog";
import QualityFeedbackDialog from "../components/production/assembler/QualityFeedbackDialog";
import DrawingViewerDialog from "../components/production/assembler/DrawingViewerDialog";
import TaskCompleteDialog from "../components/production/assembler/TaskCompleteDialog";
import AssemblyTaskCard from "../components/production/assembler/AssemblyTaskCard";

export default function AssemblerTaskCenter() {
  const [tasks, setTasks] = useState([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [shortageDialog, setShortageDialog] = useState({
    open: false,
    task: null,
    material: null
  });
  const [qualityDialog, setQualityDialog] = useState({
    open: false,
    task: null,
    material: null
  });
  const [drawingDialog, setDrawingDialog] = useState({
    open: false,
    task: null
  });
  const [completeDialog, setCompleteDialog] = useState({
    open: false,
    task: null
  });

  const filteredTasks = tasks.filter((task) => {
    if (statusFilter === "all") {return true;}
    return task.status === statusFilter;
  });

  const stats = {
    total: tasks.length,
    in_progress: tasks.filter((t) => t.status === "in_progress").length,
    pending: tasks.filter((t) => t.status === "pending").length,
    blocked: tasks.filter((t) => t.status === "blocked").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    shortage: tasks.filter((t) =>
    t.materials?.some((m) => m.status === "shortage")
    ).length
  };

  const handleAction = (action, task, material = null) => {
    switch (action) {
      case "shortage":
        setShortageDialog({ open: true, task, material });
        break;
      case "quality":
        setQualityDialog({ open: true, task, material });
        break;
      case "drawing":
        setDrawingDialog({ open: true, task });
        break;
      case "complete":
        setCompleteDialog({ open: true, task });
        break;
      case "start":
        setTasks((prev) =>
        prev.map((t) =>
        t.id === task.id ? { ...t, status: "in_progress" } : t
        )
        );
        break;
    }
  };

  const handleComplete = (taskId, hours) => {
    setTasks((prev) =>
    prev.map((t) =>
    t.id === taskId ?
    {
      ...t,
      status: "completed",
      actualHours: hours,
      progress: 100,
      completedDate: new Date().toISOString().split("T")[0]
    } :
    t
    )
    );
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="我的装配任务"
        description={`今日待完成 ${stats.in_progress} 项，共 ${stats.total} 项任务`}
        actions={
        <div className="flex gap-2">
            <Button
            variant="outline"
            onClick={() =>
            setShortageDialog({ open: true, task: null, material: null })
            }>

              <AlertTriangle className="w-4 h-4 mr-1" />
              反馈缺料
            </Button>
            <Button
            variant="outline"
            onClick={() =>
            setQualityDialog({ open: true, task: null, material: null })
            }>

              <FileWarning className="w-4 h-4 mr-1" />
              质量反馈
            </Button>
        </div>
        } />


      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-5 gap-4">

        {[
        {
          key: "in_progress",
          label: "进行中",
          icon: PlayCircle,
          color: "text-blue-400",
          value: stats.in_progress
        },
        {
          key: "pending",
          label: "待开始",
          icon: Circle,
          color: "text-slate-400",
          value: stats.pending
        },
        {
          key: "blocked",
          label: "已阻塞",
          icon: PauseCircle,
          color: "text-red-400",
          value: stats.blocked
        },
        {
          key: "completed",
          label: "已完成",
          icon: CheckCircle2,
          color: "text-emerald-400",
          value: stats.completed
        },
        {
          key: "shortage",
          label: "缺料任务",
          icon: AlertTriangle,
          color: "text-amber-400",
          value: stats.shortage
        }].
        map((stat) =>
        <Card key={stat.key} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stat.value}
                  </p>
                </div>
                <stat.icon className={cn("w-6 h-6", stat.color)} />
              </div>
            </CardContent>
        </Card>
        )}
      </motion.div>

      <motion.div variants={fadeIn} className="flex gap-2 flex-wrap">
        {[
        { value: "all", label: "全部任务" },
        { value: "in_progress", label: "进行中" },
        { value: "pending", label: "待开始" },
        { value: "blocked", label: "已阻塞" },
        { value: "completed", label: "已完成" }].
        map((filter) =>
        <Button
          key={filter.value}
          variant={statusFilter === filter.value ? "default" : "ghost"}
          size="sm"
          onClick={() => setStatusFilter(filter.value)}>

            {filter.label}
        </Button>
        )}
      </motion.div>

      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {filteredTasks.map((task) =>
        <AssemblyTaskCard key={task.id} task={task} onAction={handleAction} />
        )}
      </motion.div>

      {filteredTasks.length === 0 &&
      <motion.div variants={fadeIn} className="text-center py-16">
          <Wrench className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无任务</h3>
          <p className="text-sm text-slate-500 mt-1">
            {statusFilter !== "all" ?
          "没有符合条件的任务" :
          "当前没有分配给您的装配任务"}
          </p>
      </motion.div>
      }

      <MaterialShortageDialog
        open={shortageDialog.open}
        onClose={() =>
        setShortageDialog({ open: false, task: null, material: null })
        }
        task={shortageDialog.task}
        material={shortageDialog.material} />


      <QualityFeedbackDialog
        open={qualityDialog.open}
        onClose={() =>
        setQualityDialog({ open: false, task: null, material: null })
        }
        task={qualityDialog.task}
        material={qualityDialog.material} />


      <DrawingViewerDialog
        open={drawingDialog.open}
        onClose={() => setDrawingDialog({ open: false, task: null })}
        task={drawingDialog.task} />


      <TaskCompleteDialog
        open={completeDialog.open}
        onClose={() => setCompleteDialog({ open: false, task: null })}
        task={completeDialog.task}
        onComplete={handleComplete} />

    </motion.div>);

}
