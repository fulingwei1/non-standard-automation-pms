import { Save } from "lucide-react";
import {
  Button,
  Input,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Textarea,
} from "@/components/ui";
import { getCategoryLabel } from "@/services/api/performanceContract";

export default function EvaluateDialog({
  open,
  onOpenChange,
  selectedContract,
  evaluations,
  updateEvaluation,
  onSaveEvaluation,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">绩效评分</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {evaluations.map((evalItem, idx) => {
            const item = selectedContract?.items?.find((i) => i.id === evalItem.item_id);
            return (
              <div key={evalItem.item_id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="outline" className="border-slate-600 text-slate-300">
                    {getCategoryLabel(item?.category)}
                  </Badge>
                  <span className="text-white font-medium">{item?.indicator_name}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400 text-sm">目标值</Label>
                    <p className="text-slate-300">{item?.target_value || "-"}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-sm">权重</Label>
                    <p className="text-slate-300">{item?.weight}%</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <Label className="text-slate-300 text-sm">实际值</Label>
                    <Input
                      value={evalItem.actual_value}
                      onChange={(e) => updateEvaluation(idx, "actual_value", e.target.value)}
                      className="bg-slate-800 border-slate-700 text-white mt-1"
                      placeholder="输入实际完成值"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300 text-sm">得分</Label>
                    <Input
                      type="number"
                      value={evalItem.score}
                      onChange={(e) => updateEvaluation(idx, "score", parseFloat(e.target.value) || 0)}
                      className="bg-slate-800 border-slate-700 text-white mt-1"
                      placeholder="0-100"
                      max="100"
                    />
                  </div>
                </div>
                <div className="mt-3">
                  <Label className="text-slate-300 text-sm">评估意见</Label>
                  <Textarea
                    value={evalItem.evaluator_comment}
                    onChange={(e) => updateEvaluation(idx, "evaluator_comment", e.target.value)}
                    className="bg-slate-800 border-slate-700 text-white mt-1"
                    rows={2}
                    placeholder="填写评估意见..."
                  />
                </div>
              </div>
            );
          })}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-slate-700 text-slate-300">
            取消
          </Button>
          <Button onClick={onSaveEvaluation} className="bg-blue-600 hover:bg-blue-700">
            <Save size={16} className="mr-2" />
            保存评分
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
