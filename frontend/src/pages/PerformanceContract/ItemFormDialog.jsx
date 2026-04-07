

import { CATEGORY_OPTIONS } from "./constants";

export default function ItemFormDialog({
  open,
  onOpenChange,
  editingItem,
  itemForm,
  setItemForm,
  onSaveItem,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-900 border-slate-700 max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white">
            {editingItem ? "编辑指标条目" : "添加指标条目"}
          </DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">指标类别</Label>
              <Select
                value={itemForm.category}
                onValueChange={(value) => setItemForm({ ...itemForm, category: value })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {CATEGORY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-white">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">权重 (%)</Label>
              <Input
                type="number"
                value={itemForm.weight}
                onChange={(e) => setItemForm({ ...itemForm, weight: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div>
            <Label className="text-slate-300">指标名称</Label>
            <Input
              value={itemForm.indicator_name}
              onChange={(e) => setItemForm({ ...itemForm, indicator_name: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
          <div>
            <Label className="text-slate-300">指标描述</Label>
            <Textarea
              value={itemForm.indicator_description}
              onChange={(e) => setItemForm({ ...itemForm, indicator_description: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
              rows={2}
            />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label className="text-slate-300">单位</Label>
              <Input
                value={itemForm.unit}
                onChange={(e) => setItemForm({ ...itemForm, unit: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">目标值</Label>
              <Input
                value={itemForm.target_value}
                onChange={(e) => setItemForm({ ...itemForm, target_value: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">挑战值</Label>
              <Input
                value={itemForm.challenge_value}
                onChange={(e) => setItemForm({ ...itemForm, challenge_value: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-300">底线值</Label>
              <Input
                value={itemForm.baseline_value}
                onChange={(e) => setItemForm({ ...itemForm, baseline_value: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">数据来源</Label>
              <Input
                value={itemForm.data_source}
                onChange={(e) => setItemForm({ ...itemForm, data_source: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div>
            <Label className="text-slate-300">评分规则</Label>
            <Textarea
              value={itemForm.scoring_rule}
              onChange={(e) => setItemForm({ ...itemForm, scoring_rule: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
              rows={2}
            />
          </div>
          <div>
            <Label className="text-slate-300">评估方式</Label>
            <Input
              value={itemForm.evaluation_method}
              onChange={(e) => setItemForm({ ...itemForm, evaluation_method: e.target.value })}
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-slate-700 text-slate-300">
            取消
          </Button>
          <Button onClick={onSaveItem} className="bg-blue-600 hover:bg-blue-700">
            <Save size={16} className="mr-2" />
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
