import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../components/ui";

const fieldSections = [
  {
    title: "技术维度",
    fields: [
      {
        key: "tech_maturity",
        label: "技术成熟度",
        options: [
          ["mature", "成熟"],
          ["medium", "一般"],
          ["low", "不成熟"],
        ],
      },
      {
        key: "process_difficulty",
        label: "工艺难度",
        options: [
          ["standard", "标准"],
          ["medium", "中等"],
          ["high", "复杂"],
        ],
      },
      {
        key: "precision_requirement",
        label: "精度要求",
        options: [
          ["normal", "常规"],
          ["high", "高精度"],
          ["extreme", "极高精度"],
        ],
      },
      {
        key: "sample_support",
        label: "样品支持",
        options: [
          ["available", "可提供"],
          ["limited", "有限"],
          ["none", "无"],
        ],
      },
    ],
  },
  {
    title: "商务维度",
    fields: [
      {
        key: "budget_status",
        label: "预算状态",
        options: [
          ["confirmed", "明确"],
          ["rough", "粗略"],
          ["unknown", "未知"],
        ],
      },
      {
        key: "price_sensitivity",
        label: "价格敏感度",
        options: [
          ["low", "低"],
          ["medium", "中"],
          ["high", "高"],
        ],
      },
      {
        key: "gross_margin_safety",
        label: "毛利安全性",
        options: [
          ["safe", "安全"],
          ["tight", "偏紧"],
          ["risk", "有风险"],
        ],
      },
      {
        key: "payment_terms",
        label: "付款条件",
        options: [
          ["good", "好"],
          ["normal", "一般"],
          ["poor", "差"],
        ],
      },
    ],
  },
  {
    title: "资源交付",
    fields: [
      {
        key: "resource_occupancy",
        label: "资源占用",
        options: [
          ["available", "可安排"],
          ["tight", "紧张"],
          ["unavailable", "不可安排"],
        ],
      },
      {
        key: "has_similar_case",
        label: "相似案例",
        options: [
          ["yes", "有"],
          ["partial", "部分"],
          ["no", "无"],
        ],
      },
      {
        key: "delivery_feasibility",
        label: "交付可行性",
        options: [
          ["feasible", "可交付"],
          ["tight", "偏紧"],
          ["risky", "风险高"],
        ],
      },
      {
        key: "delivery_months",
        label: "交付周期(月)",
        type: "number",
        min: 1,
        max: 24,
      },
      {
        key: "change_risk",
        label: "变更风险",
        options: [
          ["low", "低"],
          ["medium", "中"],
          ["high", "高"],
        ],
      },
    ],
  },
  {
    title: "客户关系",
    fields: [
      {
        key: "customer_nature",
        label: "客户性质",
        options: [
          ["strategic", "战略客户"],
          ["key", "重点客户"],
          ["normal", "普通客户"],
        ],
      },
      {
        key: "customer_potential",
        label: "客户潜力",
        options: [
          ["high", "高"],
          ["medium", "中"],
          ["low", "低"],
        ],
      },
      {
        key: "relationship_depth",
        label: "关系深度",
        options: [
          ["deep", "深"],
          ["normal", "一般"],
          ["new", "新接触"],
        ],
      },
      {
        key: "contact_level",
        label: "接触层级",
        options: [
          ["decision_maker", "决策层"],
          ["influencer", "影响者"],
          ["operator", "执行层"],
        ],
      },
      {
        key: "requirement_maturity",
        label: "需求成熟度",
        type: "number",
        min: 1,
        max: 5,
      },
    ],
  },
];

const checklistFields = [
  { key: "has_sow", label: "有客户SOW/URS" },
];

function normalizeNumberValue(value) {
  if (value === "") return "";
  const parsed = Number(value);
  return Number.isNaN(parsed) ? "" : parsed;
}

export function RequirementDataForm({
  requirementData,
  setRequirementData,
  enableAI,
  setEnableAI,
}) {
  const data = requirementData || {};

  const updateRequirementField = (key, value) => {
    const nextData = { ...data };
    if (value === "" || value === undefined || value === null) {
      delete nextData[key];
    } else {
      nextData[key] = value;
    }
    setRequirementData(nextData);
  };

  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardHeader>
        <CardTitle>需求数据</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {fieldSections.map((section) => (
              <section key={section.title} className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-200">
                  {section.title}
                </h4>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {section.fields.map((field) => {
                    const inputId = `requirement-${field.key}`;
                    const value = data[field.key] ?? "";
                    return (
                      <label key={field.key} htmlFor={inputId} className="space-y-1">
                        <span className="text-xs text-slate-400">{field.label}</span>
                        {field.type === "number" ? (
                          <input
                            id={inputId}
                            type="number"
                            min={field.min}
                            max={field.max}
                            value={value}
                            onChange={(event) =>
                              updateRequirementField(
                                field.key,
                                normalizeNumberValue(event.target.value),
                              )
                            }
                            className="h-10 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-white focus:border-blue-500 focus:outline-none"
                          />
                        ) : (
                          <select
                            id={inputId}
                            value={value}
                            onChange={(event) =>
                              updateRequirementField(field.key, event.target.value)
                            }
                            className="h-10 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-white focus:border-blue-500 focus:outline-none"
                          >
                            <option value="">未选择</option>
                            {field.options.map(([optionValue, optionLabel]) => (
                              <option key={optionValue} value={optionValue}>
                                {optionLabel}
                              </option>
                            ))}
                          </select>
                        )}
                      </label>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>

          <div className="flex flex-wrap gap-4">
            {checklistFields.map((field) => (
              <label key={field.key} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={Boolean(data[field.key])}
                  onChange={(event) =>
                    updateRequirementField(field.key, event.target.checked)
                  }
                />
                {field.label}
              </label>
            ))}
          </div>

          <div>
            <label htmlFor="requirement-json" className="block text-sm font-medium mb-2">
              JSON明细
            </label>
            <textarea
              id="requirement-json"
              className="h-40 w-full rounded-lg border border-slate-700 bg-slate-900 p-3 font-mono text-sm text-white focus:border-blue-500 focus:outline-none"
              value={JSON.stringify(data, null, 2)}
              onChange={(e) => {
                try {
                  setRequirementData(JSON.parse(e.target.value));
                } catch (_err) {
                  // 保留当前有效数据，避免半截 JSON 覆盖表单。
                }
              }}
            />
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={enableAI}
              onChange={(e) => setEnableAI(e.target.checked)}
            />
            启用AI分析
          </label>
        </div>
      </CardContent>
    </Card>
  );
}
