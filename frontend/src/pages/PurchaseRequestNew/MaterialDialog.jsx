import { Search, AlertCircle } from "lucide-react";
import { Input } from "../../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
} from "../../components/ui/dialog";

export default function MaterialDialog({
  open,
  onOpenChange,
  searchQuery,
  onSearchChange,
  filteredMaterials,
  onSelectMaterial,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">选择物料</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <Input
              placeholder="搜索物料编码或名称..."
              value={searchQuery || "unknown"}
              onChange={(e) => onSearchChange(e.target.value)}
              icon={Search}
              className="bg-slate-800 border-slate-700"
            />
            <div className="max-h-96 overflow-y-auto space-y-2">
              {filteredMaterials.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>未找到物料</p>
                </div>
              ) : (
                (filteredMaterials || []).map((material) => (
                  <div
                    key={material.id}
                    onClick={() => onSelectMaterial(material)}
                    className="p-3 border border-slate-700 rounded-lg hover:border-blue-500 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-200 font-medium">
                          {material.material_code}
                        </p>
                        <p className="text-slate-400 text-sm">
                          {material.material_name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-300">
                          ¥
                          {material.standard_price ||
                            material.last_price ||
                            0}
                        </p>
                        <p className="text-slate-500 text-xs">
                          {material.unit || "件"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
