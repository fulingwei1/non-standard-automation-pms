import { useState } from "react";
import { ClipboardCheck, Minus, Plus, CheckCircle2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
} from "../../ui";
import { cn } from "../../../lib/utils";

export default function TaskCompleteDialog({ open, onClose, task, onComplete }) {
  const [hours, setHours] = useState(task?.actualHours || 0);
  const [notes, setNotes] = useState("");
  const [issues, setIssues] = useState([]);

  const remainingSteps = task?.steps?.filter((s) => !s.completed) || [];

  const handleSubmit = () => {
    onComplete && onComplete(task.id, hours);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-emerald-400" />
            确认完成任务
          </DialogTitle>
          <DialogDescription>确认任务完成并填报工时</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="p-3 rounded-lg bg-surface-2/50">
            <p className="font-medium text-white">{task?.title}</p>
            <p className="text-sm text-slate-400">
              {task?.machineNo} · {task?.workstation}
            </p>
          </div>

          {remainingSteps.length > 0 && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
              <p className="text-sm font-medium text-amber-400 mb-2">
                ⚠️ 以下步骤尚未完成：
              </p>
              <ul className="text-xs text-amber-300/80 space-y-1">
                {remainingSteps.map((step) => (
                  <li key={step.id}>• {step.title}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">实际工时</label>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setHours(Math.max(0.5, hours - 0.5))}
                >
                  <Minus className="w-4 h-4" />
                </Button>
                <div className="w-20 text-center">
                  <span className="text-2xl font-bold text-white">{hours}</span>
                  <span className="text-slate-400 ml-1">小时</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setHours(hours + 0.5)}
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              <div className="text-xs text-slate-400">
                预估 {task?.estimatedHours}h
                {hours > task?.estimatedHours && (
                  <span className="text-amber-400 ml-1">
                    (+{(hours - task.estimatedHours).toFixed(1)}h)
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">完工备注</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="记录完工情况、遇到的问题等..."
              className={cn(
                "w-full h-20 px-3 py-2 rounded-lg resize-none",
                "bg-surface-2 border border-border",
                "text-white placeholder:text-slate-500",
                "focus:outline-none focus:ring-2 focus:ring-primary/50"
              )}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">
              遗留问题 (可选)
            </label>
            <div className="flex flex-wrap gap-2">
              {["需要复检", "有轻微偏差", "待补充物料", "建议优化工艺"].map(
                (issue) => (
                  <button
                    key={issue}
                    onClick={() => {
                      if (issues.includes(issue)) {
                        setIssues(issues.filter((i) => i !== issue));
                      } else {
                        setIssues([...issues, issue]);
                      }
                    }}
                    className={cn(
                      "px-3 py-1 rounded-full text-xs font-medium transition-all",
                      issues.includes(issue)
                        ? "bg-primary text-white"
                        : "bg-surface-2 text-slate-400 hover:bg-surface-3"
                    )}
                  >
                    {issue}
                  </button>
                )
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            className="bg-emerald-500 hover:bg-emerald-600"
          >
            <CheckCircle2 className="w-4 h-4 mr-1" />
            确认完成
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
