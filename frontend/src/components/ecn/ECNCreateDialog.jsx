/**
 * ECN Create Dialog Component
 * ECN创建对话框组件
 */
import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { 
  typeConfigs, 
  priorityConfigs,
  defaultECNForm,
  getTypesByCategory 
} from "./ecnManagementConstants";

export function ECNCreateDialog({
  open = false,
  onOpenChange,
  projects = [],
  machines = [],
  onCreateECN,
  loading = false,
}) {
  const [formData, setFormData] = useState(defaultECNForm);
  const [errors, setErrors] = useState({});

  // 根据选择的项目过滤设备
  const filteredMachines = formData.project_id
    ? machines.filter(m => m.project_id === formData.project_id)
    : machines;

  // 重置表单
  const resetForm = () => {
    setFormData(defaultECNForm);
    setErrors({});
  };

  // 对话框关闭时重置表单
  useEffect(() => {
    if (!open) {
      resetForm();
    }
  }, [open]);

  // 项目变化时，清空设备选择（如果设备不属于新项目）
  useEffect(() => {
    if (formData.project_id && formData.machine_id) {
      const machineInProject = machines.find(
        m => m.id === formData.machine_id && m.project_id === formData.project_id
      );
      if (!machineInProject) {
        setFormData(prev => ({ ...prev, machine_id: null }));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.project_id]);

  // 表单验证
  const validateForm = () => {
    const newErrors = {};

    if (!formData.ecn_title.trim()) {
      newErrors.ecn_title = "请输入ECN标题";
    }

    if (!formData.ecn_type) {
      newErrors.ecn_type = "请选择ECN类型";
    }

    if (!formData.change_reason.trim()) {
      newErrors.change_reason = "请输入变更原因";
    }

    if (!formData.change_description.trim()) {
      newErrors.change_description = "请输入变更描述";
    }

    if (!formData.priority) {
      newErrors.priority = "请选择优先级";
    }

    if (!formData.project_id) {
      newErrors.project_id = "请选择关联项目";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 处理表单提交
  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      await onCreateECN({
        ...formData,
        project_id: formData.project_id || null,
        machine_id: formData.machine_id || null,
      });
      
      if (onOpenChange) {
        onOpenChange(false);
      }
    } catch (error) {
      console.error("创建ECN失败:", error);
    }
  };

  // 获取类型分类
  const typesByCategory = getTypesByCategory();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建ECN变更申请</DialogTitle>
        </DialogHeader>
        
        <DialogBody>
          <div className="space-y-6">
            {/* 基本信息 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">基本信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* ECN标题 */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    ECN标题 <span className="text-red-500">*</span>
                  </label>
                  <Input
                    value={formData.ecn_title}
                    onChange={(e) =>
                      setFormData({ ...formData, ecn_title: e.target.value })
                    }
                    placeholder="请输入ECN变更标题"
                    className={errors.ecn_title ? "border-red-500" : ""}
                  />
                  {errors.ecn_title && (
                    <p className="text-sm text-red-500 mt-1">{errors.ecn_title}</p>
                  )}
                </div>

                {/* ECN类型 */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    ECN类型 <span className="text-red-500">*</span>
                  </label>
                  <Select
                    value={formData.ecn_type}
                    onValueChange={(value) =>
                      setFormData({ ...formData, ecn_type: value })
                    }
                  >
                    <SelectTrigger className={errors.ecn_type ? "border-red-500" : ""}>
                      <SelectValue placeholder="选择ECN类型" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typesByCategory).map(([category, types]) => (
                        <div key={category}>
                          <div className="px-2 py-1 text-xs font-semibold text-slate-500 bg-slate-100 dark:bg-slate-800 sticky top-0">
                            {category}
                          </div>
                          {types.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded ${type.color}`} />
                                {type.label}
                              </div>
                            </SelectItem>
                          ))}
                        </div>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.ecn_type && (
                    <p className="text-sm text-red-500 mt-1">{errors.ecn_type}</p>
                  )}
                </div>

                {/* 项目和机器 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      关联项目
                    </label>
                    <Select
                      value={formData.project_id?.toString() || ""}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          project_id: value ? parseInt(value) : null,
                        })
                      }
                    >
                      <SelectTrigger className={errors.project_id ? "border-red-500" : ""}>
                        <SelectValue placeholder="选择项目（必选）" />
                      </SelectTrigger>
                      <SelectContent>
                        {projects.map((project) => (
                          <SelectItem key={project.id} value={project.id.toString()}>
                            {project.project_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.project_id && (
                      <p className="text-sm text-red-500 mt-1">{errors.project_id}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      关联设备
                    </label>
                    <Select
                      value={formData.machine_id?.toString() || ""}
                      onValueChange={(value) =>
                        setFormData({
                          ...formData,
                          machine_id: value ? parseInt(value) : null,
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择设备（可选）" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">无关联设备</SelectItem>
                        {filteredMachines.map((machine) => (
                          <SelectItem key={machine.id} value={machine.id.toString()}>
                            {machine.machine_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* 优先级和紧急程度 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      优先级 <span className="text-red-500">*</span>
                    </label>
                    <Select
                      value={formData.priority}
                      onValueChange={(value) =>
                        setFormData({ ...formData, priority: value })
                      }
                    >
                      <SelectTrigger className={errors.priority ? "border-red-500" : ""}>
                        <SelectValue placeholder="选择优先级" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(priorityConfigs).map(([value, config]) => (
                          <SelectItem key={value} value={value}>
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="secondary"
                                className={`${config.color} text-white`}
                              >
                                {config.label}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {errors.priority && (
                      <p className="text-sm text-red-500 mt-1">{errors.priority}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      紧急程度
                    </label>
                    <Select
                      value={formData.urgency}
                      onValueChange={(value) =>
                        setFormData({ ...formData, urgency: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择紧急程度" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NORMAL">一般</SelectItem>
                        <SelectItem value="URGENT">紧急</SelectItem>
                        <SelectItem value="CRITICAL">关键</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 变更信息 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">变更信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 变更原因 */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    变更原因 <span className="text-red-500">*</span>
                  </label>
                  <Textarea
                    value={formData.change_reason}
                    onChange={(e) =>
                      setFormData({ ...formData, change_reason: e.target.value })
                    }
                    placeholder="请详细描述变更的原因和背景..."
                    rows={3}
                    className={errors.change_reason ? "border-red-500" : ""}
                  />
                  {errors.change_reason && (
                    <p className="text-sm text-red-500 mt-1">{errors.change_reason}</p>
                  )}
                </div>

                {/* 变更描述 */}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    变更描述 <span className="text-red-500">*</span>
                  </label>
                  <Textarea
                    value={formData.change_description}
                    onChange={(e) =>
                      setFormData({ ...formData, change_description: e.target.value })
                    }
                    placeholder="请详细描述变更的具体内容..."
                    rows={5}
                    className={errors.change_description ? "border-red-500" : ""}
                  />
                  {errors.change_description && (
                    <p className="text-sm text-red-500 mt-1">{errors.change_description}</p>
                  )}
                </div>

                {/* 变更范围和来源 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      变更范围
                    </label>
                    <Select
                      value={formData.change_scope}
                      onValueChange={(value) =>
                        setFormData({ ...formData, change_scope: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择变更范围" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PARTIAL">局部变更</SelectItem>
                        <SelectItem value="MODULE">模块变更</SelectItem>
                        <SelectItem value="SYSTEM">系统变更</SelectItem>
                        <SelectItem value="GLOBAL">全局变更</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      变更来源
                    </label>
                    <Select
                      value={formData.source_type}
                      onValueChange={(value) =>
                        setFormData({ ...formData, source_type: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择变更来源" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MANUAL">手动录入</SelectItem>
                        <SelectItem value="CUSTOMER">客户反馈</SelectItem>
                        <SelectItem value="INTERNAL">内部需求</SelectItem>
                        <SelectItem value="REGULATION">法规要求</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 类型信息展示 */}
            {formData.ecn_type && typeConfigs[formData.ecn_type] && (
              <Card className="bg-slate-50 dark:bg-slate-900/50">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded ${typeConfigs[formData.ecn_type].color}`} />
                    <div>
                      <div className="font-medium">{typeConfigs[formData.ecn_type].label}</div>
                      <div className="text-sm text-slate-500">
                        分类：{typeConfigs[formData.ecn_type].category}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </DialogBody>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange?.(false)}
            disabled={loading}
          >
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "创建中..." : "创建ECN"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
