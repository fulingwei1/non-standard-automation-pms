import React from "react";
import {
  Card,
  CardContent,
  Button,
  Input,
  FormTextarea,
  FormSelect,
} from "../../ui";
import { Sparkles, Loader2, Layers } from "lucide-react";

const PROJECT_TYPES = [
  { value: "FIXED_PRICE", label: "固定价格" },
  { value: "TIME_MATERIAL", label: "工时材料" },
  { value: "COST_PLUS", label: "成本加成" },
];

/**
 * 基本信息步骤组件
 */
export const BasicInfoStep = ({
  formData,
  setFormData,
  recommendedTemplates = [],
  stageTemplates = [],
  currentStep,
  initialData,
  validatingCode,
  codeError,
  onCodeBlur,
  onApplyTemplate,
}) => {
  return (
    <div className="space-y-4">
      {/* 阶段模板选择 */}
      {stageTemplates.length > 0 && (
        <Card className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Layers className="h-4 w-4 text-blue-400" />
              <span className="text-sm font-medium text-blue-300">
                阶段模板 <span className="text-red-400">*</span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              选择项目生命周期模板，决定项目将经历哪些阶段
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {(stageTemplates || []).map((template) => (
                <div
                  key={template.id}
                  className={`flex items-start p-3 rounded-lg cursor-pointer transition-all ${
                    formData.stage_template_id === template.id
                      ? "bg-blue-500/20 border border-blue-500/50 ring-1 ring-blue-500/30"
                      : "bg-white/5 hover:bg-white/10 border border-transparent"
                  }`}
                  onClick={() =>
                    setFormData({ ...formData, stage_template_id: template.id })
                  }
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">
                        {template.template_name}
                      </span>
                      {template.is_default && (
                        <span className="px-1.5 py-0.5 text-xs bg-green-500/20 text-green-400 rounded">
                          默认
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {template.template_code} · {template.stage_count || 0} 个阶段
                    </div>
                    {template.description && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {template.description}
                      </p>
                    )}
                  </div>
                  {formData.stage_template_id === template.id && (
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center ml-2 shrink-0">
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 模板推荐 */}
      {recommendedTemplates.length > 0 && currentStep === 0 && (
        <Card className="bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border-violet-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-medium text-violet-300">
                推荐模板
              </span>
            </div>
            <div className="space-y-2">
              {recommendedTemplates.slice(0, 3).map((template) => (
                <div
                  key={template.template_id}
                  className="flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                  onClick={() => onApplyTemplate(template)}
                >
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white">
                      {template.template_name}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {template.reasons.join("、")}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onApplyTemplate(template);
                    }}
                  >
                    应用
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">
          项目编码 <span className="text-red-400">*</span>
        </label>
        <div className="relative">
          <Input
            value={formData.project_code}
            onChange={(e) => {
              setFormData({ ...formData, project_code: e.target.value });
            }}
            onBlur={onCodeBlur}
            placeholder="例如: PJ260104001"
            disabled={!!initialData.id}
            error={codeError}
          />
          {validatingCode && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-slate-400" />
          )}
        </div>
        {codeError && <p className="text-xs text-red-400">{codeError}</p>}
        {!initialData.id && !codeError && (
          <p className="text-xs text-slate-500">
            格式：PJ + 年月日(YYMMDD) + 序号(3位)
          </p>
        )}
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300">
          项目名称 <span className="text-red-400">*</span>
        </label>
        <Input
          value={formData.project_name}
          onChange={(e) =>
            setFormData({ ...formData, project_name: e.target.value })
          }
          placeholder="请输入项目全称"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">项目简称</label>
          <Input
            value={formData.short_name}
            onChange={(e) =>
              setFormData({ ...formData, short_name: e.target.value })
            }
            placeholder="项目简称（可选）"
          />
        </div>

        <FormSelect
          label="项目类型"
          name="project_type"
          value={formData.project_type}
          onChange={(e) =>
            setFormData({ ...formData, project_type: e.target.value })
          }
          required
        >
          <option value="">选择项目类型</option>
          {PROJECT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </FormSelect>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">产品类别</label>
          <Input
            value={formData.product_category}
            onChange={(e) =>
              setFormData({ ...formData, product_category: e.target.value })
            }
            placeholder="例如: ICT测试设备"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-300">行业</label>
          <Input
            value={formData.industry}
            onChange={(e) =>
              setFormData({ ...formData, industry: e.target.value })
            }
            placeholder="例如: 消费电子"
          />
        </div>
      </div>

      <FormTextarea
        label="项目描述"
        name="description"
        value={formData.description}
        onChange={(e) =>
          setFormData({ ...formData, description: e.target.value })
        }
        placeholder="请输入项目描述（可选）"
        rows={3}
      />
    </div>
  );
};
