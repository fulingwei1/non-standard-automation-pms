/**
 * MaterialSelectDialog - 采购物料选择对话框
 * 搜索并选择物料添加到采购订单
 */

import { useState, useMemo } from "react";
import { Search, Plus, Package, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../ui/dialog";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";

export default function MaterialSelectDialog({
  open,
  onOpenChange,
  materials = [],
  selectedItems = [],
  onAddItems,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [quantities, setQuantities] = useState({});

  // 过滤物料
  const filteredMaterials = useMemo(() => {
    if (!searchQuery) {return materials;}

    const query = searchQuery.toLowerCase();
    return materials.filter(
      (material) =>
        material.name?.toLowerCase().includes(query) ||
        material.code?.toLowerCase().includes(query) ||
        material.category?.toLowerCase().includes(query)
    );
  }, [materials, searchQuery]);

  // 已选择的物料ID集合
  const selectedIds = useMemo(
    () => new Set(selectedItems.map((item) => item.code || item.id)),
    [selectedItems]
  );

  // 更新数量
  const updateQuantity = (materialId, quantity) => {
    setQuantities((prev) => ({
      ...prev,
      [materialId]: Math.max(1, parseInt(quantity) || 1),
    }));
  };

  // 添加选中的物料
  const handleAddSelected = () => {
    const itemsToAdd = filteredMaterials
      .filter((material) => quantities[material.id])
      .map((material) => ({
        code: material.code || material.id,
        name: material.name,
        qty: quantities[material.id] || 1,
        price: material.purchase_price || material.price || 0,
        received: 0,
      }));

    if (itemsToAdd.length > 0) {
      onAddItems?.(itemsToAdd);
      setQuantities({});
      setSearchQuery("");
      onOpenChange(false);
    }
  };

  // 快速添加单个物料
  const handleQuickAdd = (material) => {
    const item = {
      code: material.code || material.id,
      name: material.name,
      qty: quantities[material.id] || 1,
      price: material.purchase_price || material.price || 0,
      received: 0,
    };
    onAddItems?.([item]);
    setQuantities((prev) => {
      const newQuantities = { ...prev };
      delete newQuantities[material.id];
      return newQuantities;
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">选择采购物料</DialogTitle>
        </DialogHeader>

        <DialogBody className="space-y-4">
          {/* 搜索框 */}
          <div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索物料编码、名称、类别..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-900 border-slate-700 text-white placeholder-slate-400"
              />
            </div>
          </div>

          {/* 已选物料提示 */}
          {selectedItems.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-slate-400">已选：</span>
              {selectedItems.map((item, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="bg-blue-500/20 text-blue-300 border border-blue-500/30"
                >
                  {item.name || item.code}
                  <span className="ml-1">×{item.qty}</span>
                </Badge>
              ))}
            </div>
          )}

          {/* 物料列表 */}
          <div className="max-h-96 overflow-y-auto">
            {filteredMaterials.length === 0 ? (
              <div className="text-center py-8">
                <Package className="h-12 w-12 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-400">
                  {searchQuery ? "未找到匹配的物料" : "暂无可用物料"}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredMaterials.map((material) => {
                  const isSelected = selectedIds.has(material.code || material.id);
                  const quantity = quantities[material.id] || 1;

                  return (
                    <div
                      key={material.id}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border transition-colors",
                        isSelected
                          ? "bg-blue-500/10 border-blue-500/30"
                          : "bg-slate-900/50 border-slate-700/50 hover:border-slate-600"
                      )}
                    >
                      {/* 物料信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-blue-400">
                            {material.code || material.id}
                          </span>
                          {isSelected && (
                            <Badge className="bg-blue-500 text-white text-xs">已添加</Badge>
                          )}
                        </div>
                        <p className="text-sm text-white truncate">{material.name}</p>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          {material.category && <span>{material.category}</span>}
                          {material.stock !== undefined && (
                            <span>库存：{material.stock}</span>
                          )}
                          {material.unit && <span>单位：{material.unit}</span>}
                        </div>
                      </div>

                      {/* 价格和数量 */}
                      <div className="flex items-center gap-3">
                        {material.purchase_price !== undefined && (
                          <div className="text-right">
                            <p className="text-sm text-white">
                              ¥{material.purchase_price.toFixed(2)}
                            </p>
                            <p className="text-xs text-slate-500">采购价</p>
                          </div>
                        )}

                        {!isSelected && (
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              min="1"
                              value={quantity}
                              onChange={(e) => updateQuantity(material.id, e.target.value)}
                              className="w-20 bg-slate-800 border-slate-600 text-white text-center"
                            />
                            <Button
                              size="sm"
                              onClick={() => handleQuickAdd(material)}
                              className="bg-blue-500 hover:bg-blue-600 text-white"
                            >
                              <Plus className="w-4 h-4" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 统计信息 */}
          {Object.keys(quantities).length > 0 && (
            <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
              <p className="text-sm text-slate-400">
                已选择 <span className="text-white font-semibold">{Object.keys(quantities).length}</span>{" "}
                种物料
              </p>
            </div>
          )}
        </DialogBody>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => {
              onOpenChange(false);
              setQuantities({});
              setSearchQuery("");
            }}
            className="bg-slate-700 border-slate-600 text-white"
          >
            取消
          </Button>
          <Button
            onClick={handleAddSelected}
            disabled={Object.keys(quantities).length === 0}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            添加选中物料
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
