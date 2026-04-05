import { Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";

function ExistingItemCard({ item }) {
  return (
    <div className="border rounded-lg p-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="font-medium">{item.item_name}</div>
          <div className="text-xs text-slate-500 mt-1">
            {item.item_code}{" "}
            {item.category_name && `· ${item.category_name}`}
          </div>
          {item.acceptance_criteria && (
            <div className="text-xs text-slate-600 mt-1">
              验收标准: {item.acceptance_criteria}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {item.is_required && <Badge className="bg-blue-500">必检</Badge>}
          {item.is_key_item && <Badge variant="destructive">关键项</Badge>}
        </div>
      </div>
    </div>
  );
}

export default function TemplateItemsDialog({
  open,
  onOpenChange,
  selectedTemplate,
  templateItems,
  newItem,
  setNewItem,
  onAddItem,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedTemplate?.template_name} - 检查项管理
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Add item form */}
            <div>
              <h3 className="text-sm font-medium mb-2">添加检查项</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    检查项编码
                  </label>
                  <Input
                    value={newItem.item_code}
                    onChange={(e) =>
                      setNewItem({ ...newItem, item_code: e.target.value })
                    }
                    placeholder="检查项编码"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    检查项名称 *
                  </label>
                  <Input
                    value={newItem.item_name}
                    onChange={(e) =>
                      setNewItem({ ...newItem, item_name: e.target.value })
                    }
                    placeholder="检查项名称"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">分类</label>
                  <Input
                    value={newItem.category_name}
                    onChange={(e) =>
                      setNewItem({ ...newItem, category_name: e.target.value })
                    }
                    placeholder="分类名称"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">单位</label>
                  <Input
                    value={newItem.unit}
                    onChange={(e) =>
                      setNewItem({ ...newItem, unit: e.target.value })
                    }
                    placeholder="单位"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="text-sm font-medium mb-2 block">
                  验收标准
                </label>
                <Input
                  value={newItem.acceptance_criteria}
                  onChange={(e) =>
                    setNewItem({
                      ...newItem,
                      acceptance_criteria: e.target.value,
                    })
                  }
                  placeholder="验收标准"
                />
              </div>
              <div className="mt-4">
                <label className="text-sm font-medium mb-2 block">标准值</label>
                <Input
                  value={newItem.standard_value}
                  onChange={(e) =>
                    setNewItem({ ...newItem, standard_value: e.target.value })
                  }
                  placeholder="标准值"
                />
              </div>
              <div className="mt-4 flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newItem.is_required}
                    onChange={(e) =>
                      setNewItem({ ...newItem, is_required: e.target.checked })
                    }
                  />
                  <span className="text-sm">必检项</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newItem.is_key_item}
                    onChange={(e) =>
                      setNewItem({ ...newItem, is_key_item: e.target.checked })
                    }
                  />
                  <span className="text-sm">关键项</span>
                </label>
              </div>
              <Button onClick={onAddItem} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                添加检查项
              </Button>
            </div>

            {/* Existing items list */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-2">检查项列表</h3>
              <div className="space-y-2">
                {templateItems.length === 0 ? (
                  <div className="text-center py-4 text-slate-400">
                    暂无检查项
                  </div>
                ) : (
                  templateItems.map((item) => (
                    <ExistingItemCard key={item.id} item={item} />
                  ))
                )}
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
