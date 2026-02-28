import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import {
  Target,
  TrendingUp,
  MapPin,
  CheckCircle2,
  Route,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
} from "lucide-react";
import { cn } from "../lib/utils";
import { managementRhythmApi } from "../services/api";

const layerConfig = {
  vision: {
    label: "使命/愿景",
    icon: Target,
    color: "bg-purple-500",
    description: "看见远方的意义 - 我们要成为什么？",
  },
  opportunity: {
    label: "战略机会",
    icon: TrendingUp,
    color: "bg-blue-500",
    description: "做出判断与选择 - 我们凭什么能赢？",
  },
  positioning: {
    label: "战略定位",
    icon: MapPin,
    color: "bg-green-500",
    description: "选择在哪个结构里赢 - 我们在哪个战场打，用什么方式取胜？",
  },
  goals: {
    label: "战略目标",
    icon: CheckCircle2,
    color: "bg-orange-500",
    description: "让逻辑可以被验证 - 我们要实现什么结果？",
  },
  path: {
    label: "战略路径",
    icon: Route,
    color: "bg-red-500",
    description: "让战略能走通 - 我们怎么实现？",
  },
};

export default function StrategicStructureEditor({
  initialData,
  onSave,
  readOnly = false,
}) {
  const [structure, setStructure] = useState(initialData || {});
  const [expandedLayers, setExpandedLayers] = useState({
    vision: true,
    opportunity: false,
    positioning: false,
    goals: false,
    path: false,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setStructure(initialData);
    } else {
      // 加载模板
      loadTemplate();
    }
  }, [initialData]);

  const loadTemplate = async () => {
    try {
      const res = await managementRhythmApi.getStrategicStructureTemplate();
      const template = res.data || res;
      if (template && (template.vision || template.opportunity)) {
        setStructure(template);
      } else {
        // 使用默认结构
        setStructure({
          vision: {},
          opportunity: {},
          positioning: {},
          goals: {},
          path: {},
        });
      }
    } catch (err) {
      console.error("Failed to load template:", err);
      // 使用默认结构
      setStructure({
        vision: {},
        opportunity: {},
        positioning: {},
        goals: {},
        path: {},
      });
    }
  };

  const toggleLayer = (layer) => {
    setExpandedLayers((prev) => ({
      ...prev,
      [layer]: !prev[layer],
    }));
  };

  const updateLayer = (layer, field, value) => {
    setStructure((prev) => ({
      ...prev,
      [layer]: {
        ...prev[layer],
        [field]: value,
      },
    }));
  };

  const updateNestedField = (layer, path, value) => {
    setStructure((prev) => {
      const newStructure = { ...prev };
      const keys = path.split(".");
      let current = newStructure[layer] || {};

      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
          current[keys[i]] = {};
        }
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;

      return {
        ...newStructure,
        [layer]: newStructure[layer] ? { ...newStructure[layer] } : {},
      };
    });
  };

  const handleSave = async () => {
    if (onSave) {
      setLoading(true);
      try {
        await onSave(structure);
      } finally {
        setLoading(false);
      }
    }
  };

  const renderVisionLayer = () => {
    const config = layerConfig.vision;
    const Icon = config.icon;
    const data = structure.vision || {};

    return (
      <Card className="mb-4">
        <CardHeader
          className={cn("cursor-pointer", config.color, "text-white")}
          onClick={() => !readOnly && toggleLayer("vision")}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <div>
                <CardTitle className="text-white">{config.label}</CardTitle>
                <p className="text-sm text-white/80">{config.description}</p>
              </div>
            </div>
            {expandedLayers.vision ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </CardHeader>
        {expandedLayers.vision && (
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">使命</label>
              <Textarea
                value={data.mission || ""}
                onChange={(e) =>
                  updateLayer("vision", "mission", e.target.value)
                }
                placeholder="我们希望通过____，让____变得更好"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">愿景</label>
              <Textarea
                value={data.vision || ""}
                onChange={(e) =>
                  updateLayer("vision", "vision", e.target.value)
                }
                placeholder="最终成为一家怎样的公司"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                存在的意义
              </label>
              <Textarea
                value={data.why_exist || ""}
                onChange={(e) =>
                  updateLayer("vision", "why_exist", e.target.value)
                }
                placeholder="我们为什么存在？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                三年后希望被怎么记住
              </label>
              <Textarea
                value={data.three_years_later || ""}
                onChange={(e) =>
                  updateLayer("vision", "three_years_later", e.target.value)
                }
                placeholder="如果三年后只剩一句话，我们希望被怎么记住？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                为谁创造长期价值
              </label>
              <Textarea
                value={data.long_term_value || ""}
                onChange={(e) =>
                  updateLayer("vision", "long_term_value", e.target.value)
                }
                placeholder="我们希望为谁创造长期价值？"
                disabled={readOnly}
                rows={2}
              />
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  const renderOpportunityLayer = () => {
    const config = layerConfig.opportunity;
    const Icon = config.icon;
    const data = structure.opportunity || {};

    return (
      <Card className="mb-4">
        <CardHeader
          className={cn("cursor-pointer", config.color, "text-white")}
          onClick={() => !readOnly && toggleLayer("opportunity")}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <div>
                <CardTitle className="text-white">{config.label}</CardTitle>
                <p className="text-sm text-white/80">{config.description}</p>
              </div>
            </div>
            {expandedLayers.opportunity ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </CardHeader>
        {expandedLayers.opportunity && (
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">市场趋势</label>
              <Textarea
                value={data.market_trend || ""}
                onChange={(e) =>
                  updateLayer("opportunity", "market_trend", e.target.value)
                }
                placeholder="未来三年的行业关键趋势"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                客户需求本质
              </label>
              <Textarea
                value={data.customer_demand || ""}
                onChange={(e) =>
                  updateLayer("opportunity", "customer_demand", e.target.value)
                }
                placeholder="客户最根本的需求是什么？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">竞争空位</label>
              <Textarea
                value={data.competitive_gap || ""}
                onChange={(e) =>
                  updateLayer("opportunity", "competitive_gap", e.target.value)
                }
                placeholder="竞争中的空隙在哪里？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                我们的优势
              </label>
              <Textarea
                value={data.our_advantage || ""}
                onChange={(e) =>
                  updateLayer("opportunity", "our_advantage", e.target.value)
                }
                placeholder="我们凭什么能赢？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div className="border-t pt-4">
              <label className="block text-sm font-medium mb-3">
                四点合一分析
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    行业是否有增长
                  </label>
                  <Textarea
                    value={data.four_in_one?.industry_growth || ""}
                    onChange={(e) =>
                      updateNestedField(
                        "opportunity",
                        "four_in_one.industry_growth",
                        e.target.value,
                      )
                    }
                    disabled={readOnly}
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    竞争是否有空隙
                  </label>
                  <Textarea
                    value={data.four_in_one?.competitive_gap || ""}
                    onChange={(e) =>
                      updateNestedField(
                        "opportunity",
                        "four_in_one.competitive_gap",
                        e.target.value,
                      )
                    }
                    disabled={readOnly}
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    客户是否有需求
                  </label>
                  <Textarea
                    value={data.four_in_one?.customer_demand || ""}
                    onChange={(e) =>
                      updateNestedField(
                        "opportunity",
                        "four_in_one.customer_demand",
                        e.target.value,
                      )
                    }
                    disabled={readOnly}
                    rows={2}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    我们是否有优势
                  </label>
                  <Textarea
                    value={data.four_in_one?.our_advantage || ""}
                    onChange={(e) =>
                      updateNestedField(
                        "opportunity",
                        "four_in_one.our_advantage",
                        e.target.value,
                      )
                    }
                    disabled={readOnly}
                    rows={2}
                  />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                凭什么能赢的逻辑
              </label>
              <Textarea
                value={data.why_we_win || ""}
                onChange={(e) =>
                  updateLayer("opportunity", "why_we_win", e.target.value)
                }
                placeholder="总结：我们凭什么能赢？"
                disabled={readOnly}
                rows={3}
              />
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  const renderPositioningLayer = () => {
    const config = layerConfig.positioning;
    const Icon = config.icon;
    const data = structure.positioning || {};

    return (
      <Card className="mb-4">
        <CardHeader
          className={cn("cursor-pointer", config.color, "text-white")}
          onClick={() => !readOnly && toggleLayer("positioning")}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <div>
                <CardTitle className="text-white">{config.label}</CardTitle>
                <p className="text-sm text-white/80">{config.description}</p>
              </div>
            </div>
            {expandedLayers.positioning ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </CardHeader>
        {expandedLayers.positioning && (
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                聚焦的赛道/细分市场
              </label>
              <Textarea
                value={data.market_segment || ""}
                onChange={(e) =>
                  updateLayer("positioning", "market_segment", e.target.value)
                }
                placeholder="我们要在哪个细分市场建立主阵地？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                差异化方式
              </label>
              <Textarea
                value={data.differentiation || ""}
                onChange={(e) =>
                  updateLayer("positioning", "differentiation", e.target.value)
                }
                placeholder="我们打算通过什么样的差异化来形成势能？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                核心客户群体
              </label>
              <Textarea
                value={data.target_customers || ""}
                onChange={(e) =>
                  updateLayer("positioning", "target_customers", e.target.value)
                }
                placeholder="我们的核心客户是谁？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                独特价值主张
              </label>
              <Textarea
                value={data.value_proposition || ""}
                onChange={(e) =>
                  updateLayer(
                    "positioning",
                    "value_proposition",
                    e.target.value,
                  )
                }
                placeholder="我们为客户提供什么独特价值？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">竞争壁垒</label>
              <Textarea
                value={data.competitive_barrier || ""}
                onChange={(e) =>
                  updateLayer(
                    "positioning",
                    "competitive_barrier",
                    e.target.value,
                  )
                }
                placeholder="我们的竞争壁垒是什么？"
                disabled={readOnly}
                rows={2}
              />
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  const renderGoalsLayer = () => {
    const config = layerConfig.goals;
    const Icon = config.icon;
    const data = structure.goals || {};

    return (
      <Card className="mb-4">
        <CardHeader
          className={cn("cursor-pointer", config.color, "text-white")}
          onClick={() => !readOnly && toggleLayer("goals")}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <div>
                <CardTitle className="text-white">{config.label}</CardTitle>
                <p className="text-sm text-white/80">{config.description}</p>
              </div>
            </div>
            {expandedLayers.goals ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </CardHeader>
        {expandedLayers.goals && (
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">战略假设</label>
              <Textarea
                value={data.strategic_hypothesis || ""}
                onChange={(e) =>
                  updateLayer("goals", "strategic_hypothesis", e.target.value)
                }
                placeholder="我们的战略假设是什么？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">年度目标</label>
              <Textarea
                value={data.annual_goals || ""}
                onChange={(e) =>
                  updateLayer("goals", "annual_goals", e.target.value)
                }
                placeholder="年度目标"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">季度目标</label>
              <Textarea
                value={data.quarterly_goals || ""}
                onChange={(e) =>
                  updateLayer("goals", "quarterly_goals", e.target.value)
                }
                placeholder="季度目标"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">月度目标</label>
              <Textarea
                value={data.monthly_goals || ""}
                onChange={(e) =>
                  updateLayer("goals", "monthly_goals", e.target.value)
                }
                placeholder="月度目标"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-3">关键指标</label>
              <div className="space-y-2">
                {(data.key_metrics || []).map((metric, index) => (
                  <div
                    key={index}
                    className="flex gap-2 items-start p-3 border rounded-lg"
                  >
                    <div className="flex-1 grid grid-cols-3 gap-2">
                      <Input
                        value={metric.name || ""}
                        onChange={(e) => {
                          const newMetrics = [...(data.key_metrics || [])];
                          newMetrics[index] = {
                            ...newMetrics[index],
                            name: e.target.value,
                          };
                          updateLayer("goals", "key_metrics", newMetrics);
                        }}
                        placeholder="指标名称"
                        disabled={readOnly}
                      />
                      <Input
                        value={metric.target || ""}
                        onChange={(e) => {
                          const newMetrics = [...(data.key_metrics || [])];
                          newMetrics[index] = {
                            ...newMetrics[index],
                            target: e.target.value,
                          };
                          updateLayer("goals", "key_metrics", newMetrics);
                        }}
                        placeholder="目标值"
                        disabled={readOnly}
                      />
                      <Input
                        value={metric.purpose || ""}
                        onChange={(e) => {
                          const newMetrics = [...(data.key_metrics || [])];
                          newMetrics[index] = {
                            ...newMetrics[index],
                            purpose: e.target.value,
                          };
                          updateLayer("goals", "key_metrics", newMetrics);
                        }}
                        placeholder="验证目的"
                        disabled={readOnly}
                      />
                    </div>
                    {!readOnly && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newMetrics = (data.key_metrics || []).filter(
                            (_, i) => i !== index,
                          );
                          updateLayer("goals", "key_metrics", newMetrics);
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
                {!readOnly && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newMetrics = [
                        ...(data.key_metrics || []),
                        { name: "", target: "", purpose: "" },
                      ];
                      updateLayer("goals", "key_metrics", newMetrics);
                    }}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    添加指标
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  const renderPathLayer = () => {
    const config = layerConfig.path;
    const Icon = config.icon;
    const data = structure.path || {};

    return (
      <Card className="mb-4">
        <CardHeader
          className={cn("cursor-pointer", config.color, "text-white")}
          onClick={() => !readOnly && toggleLayer("path")}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Icon className="w-6 h-6" />
              <div>
                <CardTitle className="text-white">{config.label}</CardTitle>
                <p className="text-sm text-white/80">{config.description}</p>
              </div>
            </div>
            {expandedLayers.path ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        </CardHeader>
        {expandedLayers.path && (
          <CardContent className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                客户需求本质
              </label>
              <Textarea
                value={data.customer_need_essence || ""}
                onChange={(e) =>
                  updateLayer("path", "customer_need_essence", e.target.value)
                }
                placeholder="客户需求本质是什么？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">产品方案</label>
              <Textarea
                value={data.product_solution || ""}
                onChange={(e) =>
                  updateLayer("path", "product_solution", e.target.value)
                }
                placeholder="我们在客户需求本质上应该提供什么产品？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">服务体验</label>
              <Textarea
                value={data.service_experience || ""}
                onChange={(e) =>
                  updateLayer("path", "service_experience", e.target.value)
                }
                placeholder="我们在客户需求本质上应该创造什么体验？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">复购机制</label>
              <Textarea
                value={data.repurchase_mechanism || ""}
                onChange={(e) =>
                  updateLayer("path", "repurchase_mechanism", e.target.value)
                }
                placeholder="我们在客户需求本质上如何让客户持续复购？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">执行次序</label>
              <Textarea
                value={data.execution_order || ""}
                onChange={(e) =>
                  updateLayer("path", "execution_order", e.target.value)
                }
                placeholder="执行的先后顺序是什么？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">节奏</label>
              <Textarea
                value={data.rhythm || ""}
                onChange={(e) => updateLayer("path", "rhythm", e.target.value)}
                placeholder="节奏(周执行/月验证/季校准/年复盘)"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">兵力投入</label>
              <Textarea
                value={data.resources || ""}
                onChange={(e) =>
                  updateLayer("path", "resources", e.target.value)
                }
                placeholder="在哪些领域投入主要资源？"
                disabled={readOnly}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">战役系统</label>
              <Textarea
                value={data.campaigns || ""}
                onChange={(e) =>
                  updateLayer("path", "campaigns", e.target.value)
                }
                placeholder="关键战役和里程碑"
                disabled={readOnly}
                rows={2}
              />
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">五层战略结构</h3>
          <p className="text-sm text-gray-500">
            从愿景、机会、定位，到目标、路径，从看见到走通
          </p>
        </div>
        {!readOnly && (
          <Button onClick={handleSave} disabled={loading}>
            {loading ? "保存中..." : "保存结构"}
          </Button>
        )}
      </div>

      {renderVisionLayer()}
      {renderOpportunityLayer()}
      {renderPositioningLayer()}
      {renderGoalsLayer()}
      {renderPathLayer()}
    </div>
  );
}
