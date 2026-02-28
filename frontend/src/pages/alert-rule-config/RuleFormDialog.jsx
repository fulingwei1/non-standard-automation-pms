import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  DialogDescription,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Checkbox } from "../../components/ui/checkbox";
import {
  ruleTypeOptions,
  targetTypeOptions,
  conditionTypeOptions,
  operatorOptions,
  alertLevelOptions,
  frequencyOptions,
  channelOptions,
} from "./constants";

export function RuleFormDialog({
  open,
  onOpenChange,
  editingRule,
  formData,
  setFormData,
  templates,
  selectedTemplate,
  onTemplateSelect,
  onChannelToggle,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingRule ? "编辑预警规则" : "新建预警规则"}
          </DialogTitle>
          <DialogDescription>
            {editingRule
              ? "修改预警规则的配置信息"
              : "创建新的预警规则，配置触发条件和通知方式"}
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-6">
          {!editingRule && templates.length > 0 && (
            <div className="space-y-2">
              <Label>从模板创建（可选）</Label>
              <Select
                value={selectedTemplate?.id?.toString() || ""}
                onValueChange={(val) => onTemplateSelect(parseInt(val))}
              >
                <SelectTrigger className="bg-surface-2">
                  <SelectValue placeholder="选择模板..." />
                </SelectTrigger>
                <SelectContent>
                  {(templates || []).map((template) => (
                    <SelectItem
                      key={template.id}
                      value={template.id.toString()}
                    >
                      {template.template_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">基本信息</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rule_code">
                  规则编码 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="rule_code"
                  value={formData.rule_code}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      rule_code: e.target.value.toUpperCase(),
                    }))
                  }
                  placeholder="例如: PROJ_DELAY"
                  disabled={!!editingRule}
                  className="bg-surface-2"
                />
                <p className="text-xs text-slate-500">
                  只能包含字母、数字和下划线
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule_name">
                  规则名称 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="rule_name"
                  value={formData.rule_name}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      rule_name: e.target.value,
                    }))
                  }
                  placeholder="例如: 项目进度延期预警"
                  className="bg-surface-2"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rule_type">
                  规则类型 <span className="text-red-400">*</span>
                </Label>
                <Select
                  value={formData.rule_type}
                  onValueChange={(val) =>
                    setFormData((prev) => ({ ...prev, rule_type: val }))
                  }
                >
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue placeholder="选择规则类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {(ruleTypeOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="target_type">
                  监控对象类型 <span className="text-red-400">*</span>
                </Label>
                <Select
                  value={formData.target_type}
                  onValueChange={(val) =>
                    setFormData((prev) => ({ ...prev, target_type: val }))
                  }
                >
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue placeholder="选择监控对象" />
                  </SelectTrigger>
                  <SelectContent>
                    {(targetTypeOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 col-span-2">
                <Label htmlFor="description">规则描述</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder="描述规则的用途和触发条件"
                  className="bg-surface-2"
                  rows={2}
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">触发条件配置</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="condition_type">条件类型</Label>
                <Select
                  value={formData.condition_type}
                  onValueChange={(val) =>
                    setFormData((prev) => ({ ...prev, condition_type: val }))
                  }
                >
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(conditionTypeOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {formData.condition_type === "THRESHOLD" && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="condition_operator">条件运算符</Label>
                    <Select
                      value={formData.condition_operator}
                      onValueChange={(val) =>
                        setFormData((prev) => ({
                          ...prev,
                          condition_operator: val,
                        }))
                      }
                    >
                      <SelectTrigger className="bg-surface-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {(operatorOptions || []).map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {formData.condition_operator === "BETWEEN" ? (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="threshold_min">阈值下限</Label>
                        <Input
                          id="threshold_min"
                          type="number"
                          value={formData.threshold_min}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              threshold_min: e.target.value,
                            }))
                          }
                          placeholder="最小值"
                          className="bg-surface-2"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="threshold_max">阈值上限</Label>
                        <Input
                          id="threshold_max"
                          type="number"
                          value={formData.threshold_max}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              threshold_max: e.target.value,
                            }))
                          }
                          placeholder="最大值"
                          className="bg-surface-2"
                        />
                      </div>
                    </>
                  ) : (
                    <div className="space-y-2">
                      <Label htmlFor="threshold_value">阈值</Label>
                      <Input
                        id="threshold_value"
                        type="number"
                        value={formData.threshold_value}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            threshold_value: e.target.value,
                          }))
                        }
                        placeholder="例如: 3 (天) 或 0.1 (比例)"
                        className="bg-surface-2"
                      />
                    </div>
                  )}
                </>
              )}
              {formData.condition_type === "CUSTOM" && (
                <div className="space-y-2 col-span-2">
                  <Label htmlFor="condition_expr">自定义表达式</Label>
                  <Textarea
                    id="condition_expr"
                    value={formData.condition_expr}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        condition_expr: e.target.value,
                      }))
                    }
                    placeholder="例如: progress < 80 AND days_left < 7"
                    className="bg-surface-2"
                    rows={3}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">
              预警级别和检查频率
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="alert_level">预警级别</Label>
                <Select
                  value={formData.alert_level}
                  onValueChange={(val) =>
                    setFormData((prev) => ({ ...prev, alert_level: val }))
                  }
                >
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(alertLevelOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="check_frequency">检查频率</Label>
                <Select
                  value={formData.check_frequency}
                  onValueChange={(val) =>
                    setFormData((prev) => ({ ...prev, check_frequency: val }))
                  }
                >
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(frequencyOptions || []).map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="advance_days">提前预警天数</Label>
                <Input
                  id="advance_days"
                  type="number"
                  min="0"
                  value={formData.advance_days}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      advance_days: parseInt(e.target.value) || 0,
                    }))
                  }
                  placeholder="0"
                  className="bg-surface-2"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">通知配置</h3>
            <div className="space-y-3">
              <div>
                <Label>通知渠道</Label>
                <div className="flex flex-wrap gap-3 mt-2">
                  {(channelOptions || []).map((channel) => (
                    <div
                      key={channel.value}
                      className="flex items-center space-x-2"
                    >
                      <Checkbox
                        id={`channel-${channel.value}`}
                        checked={formData.notify_channels?.includes(
                          channel.value
                        )}
                        onCheckedChange={() => onChannelToggle(channel.value)}
                      />
                      <Label
                        htmlFor={`channel-${channel.value}`}
                        className="text-sm font-normal cursor-pointer"
                      >
                        {channel.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="solution_guide">处理指南</Label>
            <Textarea
              id="solution_guide"
              value={formData.solution_guide}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  solution_guide: e.target.value,
                }))
              }
              placeholder="提供预警触发后的处理建议和步骤"
              className="bg-surface-2"
              rows={3}
            />
          </div>

          {editingRule && (
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_enabled"
                checked={formData.is_enabled}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({ ...prev, is_enabled: checked }))
                }
              />
              <Label htmlFor="is_enabled" className="cursor-pointer">
                启用此规则
              </Label>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSave}>
            {editingRule ? "保存" : "创建"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
