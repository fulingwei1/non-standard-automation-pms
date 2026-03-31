/**
 * Create/Edit template dialog component
 */

import { Plus, Trash2 } from "lucide-react";
import {
  Button,
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { TEMPLATE_TYPES } from "./constants";

export default function TemplateFormDialog({
  open,
  onOpenChange,
  selectedTemplate,
  formData,
  setFormData,
  onSave,
  onClose,
  addCategory,
  addItem,
  updateCategory,
  updateItem,
  removeCategory,
  removeItem,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedTemplate ? "编辑模板" : "新建模板"}
          </DialogTitle>
          <DialogDescription>创建或编辑成本模板</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>模板编码 *</Label>
              <Input
                value={formData.template_code}
                onChange={(e) =>
                  setFormData({ ...formData, template_code: e.target.value })
                }
                placeholder="TPL-ICT-001"
              />
            </div>
            <div>
              <Label>模板名称 *</Label>
              <Input
                value={formData.template_name}
                onChange={(e) =>
                  setFormData({ ...formData, template_name: e.target.value })
                }
                placeholder="ICT测试设备标准模板"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label>模板类型</Label>
              <Select
                value={formData.template_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, template_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>设备类型</Label>
              <Input
                value={formData.equipment_type}
                onChange={(e) =>
                  setFormData({ ...formData, equipment_type: e.target.value })
                }
                placeholder="ICT"
              />
            </div>
            <div>
              <Label>行业</Label>
              <Input
                value={formData.industry}
                onChange={(e) =>
                  setFormData({ ...formData, industry: e.target.value })
                }
                placeholder="消费电子"
              />
            </div>
          </div>

          <div>
            <Label>模板说明</Label>
            <Textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="模板说明..."
              rows={3}
            />
          </div>

          {/* Cost Structure */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>成本结构</Label>
              <Button variant="outline" size="sm" onClick={addCategory}>
                <Plus className="h-4 w-4 mr-1" />
                添加分类
              </Button>
            </div>

            <div className="space-y-4 border border-slate-700 rounded-lg p-4">
              {formData.cost_structure?.categories?.map(
                (category, catIndex) => (
                  <div
                    key={catIndex}
                    className="border border-slate-600 rounded-lg p-4"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <Input
                        value={category.category}
                        onChange={(e) =>
                          updateCategory(catIndex, "category", e.target.value)
                        }
                        placeholder="分类名称（如：硬件成本）"
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => addItem(catIndex)}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        添加项
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeCategory(catIndex)}
                        className="text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>

                    <div className="space-y-2">
                      {category.items?.map((item, itemIndex) => (
                        <div
                          key={itemIndex}
                          className="grid grid-cols-7 gap-2 items-end"
                        >
                          <Input
                            value={item.item_name}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "item_name",
                                e.target.value
                              )
                            }
                            placeholder="项目名称"
                          />
                          <Input
                            value={item.specification}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "specification",
                                e.target.value
                              )
                            }
                            placeholder="规格型号"
                          />
                          <Input
                            value={item.unit}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "unit",
                                e.target.value
                              )
                            }
                            placeholder="单位"
                          />
                          <Input
                            type="number"
                            value={item.default_qty}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "default_qty",
                                parseFloat(e.target.value) || 0
                              )
                            }
                            placeholder="数量"
                          />
                          <Input
                            type="number"
                            value={item.default_unit_price}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "default_unit_price",
                                parseFloat(e.target.value) || 0
                              )
                            }
                            placeholder="单价"
                          />
                          <Input
                            type="number"
                            value={item.default_cost}
                            onChange={(e) =>
                              updateItem(
                                catIndex,
                                itemIndex,
                                "default_cost",
                                parseFloat(e.target.value) || 0
                              )
                            }
                            placeholder="成本"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => removeItem(catIndex, itemIndex)}
                            className="text-red-400"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              )}

              {(!formData.cost_structure?.categories ||
                formData.cost_structure.categories?.length === 0) && (
                <div className="text-center py-8 text-slate-400">
                  点击"添加分类"开始构建成本结构
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={onSave}
            disabled={!formData.template_code || !formData.template_name}
          >
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
