


export default function ItemsCard({
  items,
  onAddItem,
  onRemoveItem,
  onUpdateItem,
  onOpenMaterialDialog,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-slate-200">物料明细</CardTitle>
          <Button size="sm" onClick={onAddItem} variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            添加物料
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {items?.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>暂无物料，点击上方按钮添加</p>
          </div>
        ) : (
          <div className="space-y-3">
            {(items || []).map((item, index) => (
              <div
                key={index}
                className="p-4 border border-slate-700 rounded-lg bg-slate-900/30"
              >
                <div className="flex items-start justify-between mb-3">
                  <Badge className="bg-blue-500/20 text-blue-400">
                    物料 {index + 1}
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onRemoveItem(index)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="md:col-span-2">
                    <Label className="text-slate-400 text-xs">物料</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="物料编码"
                        value={item.material_code}
                        onChange={(e) =>
                          onUpdateItem(index, "material_code", e.target.value)
                        }
                        className="bg-slate-800 border-slate-700 text-slate-200"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onOpenMaterialDialog(index)}
                        className="whitespace-nowrap"
                      >
                        <Search className="w-4 h-4" />
                      </Button>
                    </div>
                    <Input
                      placeholder="物料名称 *"
                      value={item.material_name}
                      onChange={(e) =>
                        onUpdateItem(index, "material_name", e.target.value)
                      }
                      className="bg-slate-800 border-slate-700 text-slate-200 mt-2"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">数量 *</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.quantity}
                      onChange={(e) =>
                        onUpdateItem(
                          index,
                          "quantity",
                          parseFloat(e.target.value) || 0
                        )
                      }
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">单位</Label>
                    <Input
                      value={item.unit}
                      onChange={(e) =>
                        onUpdateItem(index, "unit", e.target.value)
                      }
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">单价</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={item.unit_price}
                      onChange={(e) =>
                        onUpdateItem(
                          index,
                          "unit_price",
                          parseFloat(e.target.value) || 0
                        )
                      }
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">金额</Label>
                    <Input
                      value={(
                        parseFloat(item.quantity || 0) *
                        parseFloat(item.unit_price || 0)
                      ).toFixed(2)}
                      disabled
                      className="bg-slate-800/50 border-slate-700 text-slate-300"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs">需求日期</Label>
                    <Input
                      type="date"
                      value={item.required_date}
                      onChange={(e) =>
                        onUpdateItem(index, "required_date", e.target.value)
                      }
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
