/**
 * 技术参数模板管理
 * - 模板列表（按行业/测试类型分类）
 * - 模板 CRUD
 * - 基于模板的成本估算
 */

import { useState, useEffect } from "react";
import {
  Settings,
  FileText,
  Cpu,
  Factory,
  Beaker,
  Zap,
} from "lucide-react";
import { staggerContainer, fadeIn } from "../lib/animations";
import { technicalParameterApi } from "../services/api/technicalParameter";

// 行业选项
const INDUSTRIES = [
  { value: "AUTOMOTIVE", label: "汽车电子", icon: Factory },
  { value: "CONSUMER", label: "消费电子", icon: Cpu },
  { value: "MEDICAL", label: "医疗器械", icon: Beaker },
  { value: "INDUSTRIAL", label: "工业控制", icon: Settings },
  { value: "TELECOM", label: "通信设备", icon: Zap },
];

// 测试类型选项
const TEST_TYPES = [
  { value: "FCT", label: "功能测试 (FCT)" },
  { value: "ICT", label: "在线测试 (ICT)" },
  { value: "AGING", label: "老化测试" },
  { value: "AIRTIGHT", label: "气密测试" },
  { value: "VISION", label: "视觉检测" },
  { value: "EOL", label: "终检设备 (EOL)" },
];

function StatCard({ icon: Icon, label, value, color = "text-white" }) {
  return (
    <div className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

export default function TechnicalParameterManagement() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterIndustry, setFilterIndustry] = useState("");
  const [filterTestType, setFilterTestType] = useState("");

  // 编辑/创建模态框
  const [editModal, setEditModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    industry: "",
    test_type: "",
    description: "",
    parameters: {},
    cost_factors: {},
    typical_labor_hours: {},
  });

  // 成本估算模态框
  const [estimateModal, setEstimateModal] = useState(false);
  const [estimateTemplate, setEstimateTemplate] = useState(null);
  const [estimateParams, setEstimateParams] = useState({});
  const [estimateResult, setEstimateResult] = useState(null);

  // 加载模板列表
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await technicalParameterApi.list({
          keyword: searchKeyword,
          industry: filterIndustry,
          test_type: filterTestType,
        });
        setTemplates(res.data || res.items || []);
      } catch (err) {
        console.error("Failed to load templates:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [searchKeyword, filterIndustry, filterTestType]);

  // 打开创建模态框
  const handleCreate = () => {
    setEditingTemplate(null);
    setFormData({
      name: "",
      code: "",
      industry: "",
      test_type: "",
      description: "",
      parameters: {},
      cost_factors: {},
      typical_labor_hours: {},
    });
    setEditModal(true);
  };

  // 打开编辑模态框
  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      code: template.code,
      industry: template.industry,
      test_type: template.test_type,
      description: template.description || "",
      parameters: template.parameters || {},
      cost_factors: template.cost_factors || {},
      typical_labor_hours: template.typical_labor_hours || {},
    });
    setEditModal(true);
  };

  // 保存模板
  const handleSave = async () => {
    try {
      if (editingTemplate) {
        await technicalParameterApi.update(editingTemplate.id, formData);
      } else {
        await technicalParameterApi.create(formData);
      }
      setEditModal(false);
      // 刷新列表
      const res = await technicalParameterApi.list({});
      setTemplates(res.data || res.items || []);
    } catch (err) {
      alert("保存失败: " + err.message);
    }
  };

  // 删除模板
  const handleDelete = async (id) => {
    if (!confirm("确定删除此模板？")) return;
    try {
      await technicalParameterApi.delete(id);
      setTemplates((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      alert("删除失败: " + err.message);
    }
  };

  // 打开成本估算
  const handleEstimate = (template) => {
    setEstimateTemplate(template);
    // 初始化参数
    const params = {};
    if (template.parameters) {
      Object.keys(template.parameters).forEach((key) => {
        const param = template.parameters[key];
        params[key] = param.default_value || 0;
      });
    }
    setEstimateParams(params);
    setEstimateResult(null);
    setEstimateModal(true);
  };

  // 执行成本估算
  const runEstimate = async () => {
    try {
      const res = await technicalParameterApi.estimateCost({
        template_id: estimateTemplate.id,
        parameters: estimateParams,
      });
      setEstimateResult(res.data || res);
    } catch (err) {
      alert("估算失败: " + err.message);
    }
  };

  // 统计
  const totalCount = templates.length;
  const industryGroups = INDUSTRIES.map((ind) => ({
    ...ind,
    count: templates.filter((t) => t.industry === ind.value).length,
  }));

  const getIndustryLabel = (value) => INDUSTRIES.find((i) => i.value === value)?.label || value;
  const getTestTypeLabel = (value) => TEST_TYPES.find((t) => t.value === value)?.label || value;

  return (
    <div className="space-y-6">
      <PageHeader title="技术参数模板" subtitle="模板管理 · 成本估算 · 行业分类" />

      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {/* 统计卡片 */}
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <StatCard icon={FileText} label="模板总数" value={totalCount} color="text-blue-400" />
            {industryGroups.map((ind) => (
              <StatCard
                key={ind.value}
                icon={ind.icon}
                label={ind.label}
                value={ind.count}
                color="text-slate-300"
              />
            ))}
          </motion.div>

          {/* 搜索和筛选 */}
          <motion.div variants={fadeIn} className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="搜索模板名称或编码..."
                className="w-full bg-surface-1/50 border border-white/5 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-300"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
              />
            </div>

            <select
              className="bg-surface-1/50 border border-white/5 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={filterIndustry}
              onChange={(e) => setFilterIndustry(e.target.value)}
            >
              <option value="">全部行业</option>
              {INDUSTRIES.map((ind) => (
                <option key={ind.value} value={ind.value}>{ind.label}</option>
              ))}
            </select>

            <select
              className="bg-surface-1/50 border border-white/5 rounded-lg px-3 py-2 text-sm text-slate-300"
              value={filterTestType}
              onChange={(e) => setFilterTestType(e.target.value)}
            >
              <option value="">全部测试类型</option>
              {TEST_TYPES.map((tt) => (
                <option key={tt.value} value={tt.value}>{tt.label}</option>
              ))}
            </select>

            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              新增模板
            </button>
          </motion.div>

          {/* 模板列表 */}
          <motion.div variants={fadeIn} className="grid gap-4">
            {templates.length === 0 ? (
              <div className="text-center text-slate-500 py-12 bg-surface-1/50 border border-white/5 rounded-xl">
                暂无模板数据
              </div>
            ) : (
              templates.map((template) => (
                <div
                  key={template.id}
                  className="bg-surface-1/50 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h4 className="text-white font-medium">{template.name}</h4>
                        <span className="text-xs text-slate-500 font-mono">{template.code}</span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">{template.description || "暂无描述"}</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleEstimate(template)}
                        className="p-2 hover:bg-white/5 rounded-lg text-purple-400"
                        title="成本估算"
                      >
                        <Calculator className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(template)}
                        className="p-2 hover:bg-white/5 rounded-lg text-blue-400"
                        title="编辑"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(template.id)}
                        className="p-2 hover:bg-white/5 rounded-lg text-red-400"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-3">
                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                      {getIndustryLabel(template.industry)}
                    </span>
                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded">
                      {getTestTypeLabel(template.test_type)}
                    </span>
                    {template.parameters && Object.keys(template.parameters).length > 0 && (
                      <span className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                        {Object.keys(template.parameters).length} 个参数
                      </span>
                    )}
                  </div>

                  {/* 参数预览 */}
                  {template.parameters && Object.keys(template.parameters).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/5">
                      <div className="text-xs text-slate-500 mb-2">参数列表:</div>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(template.parameters).slice(0, 5).map(([key, param]) => (
                          <span key={key} className="px-2 py-1 bg-slate-800 text-slate-400 text-xs rounded">
                            {param.label || key}: {param.default_value} {param.unit || ""}
                          </span>
                        ))}
                        {Object.keys(template.parameters).length > 5 && (
                          <span className="px-2 py-1 text-slate-500 text-xs">
                            +{Object.keys(template.parameters).length - 5} 更多
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </motion.div>
        </motion.div>
      )}

      {/* 编辑/创建模态框 */}
      {editModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-white mb-4">
              {editingTemplate ? "编辑模板" : "创建模板"}
            </h3>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">模板名称 *</label>
                  <input
                    type="text"
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">模板编码 *</label>
                  <input
                    type="text"
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    disabled={!!editingTemplate}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">行业 *</label>
                  <select
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  >
                    <option value="">请选择</option>
                    {INDUSTRIES.map((ind) => (
                      <option key={ind.value} value={ind.value}>{ind.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">测试类型 *</label>
                  <select
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={formData.test_type}
                    onChange={(e) => setFormData({ ...formData, test_type: e.target.value })}
                  >
                    <option value="">请选择</option>
                    {TEST_TYPES.map((tt) => (
                      <option key={tt.value} value={tt.value}>{tt.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 mb-1 block">描述</label>
                <textarea
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 resize-none"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 mb-1 block">参数定义 (JSON)</label>
                <textarea
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 font-mono resize-none"
                  rows={6}
                  value={JSON.stringify(formData.parameters, null, 2)}
                  onChange={(e) => {
                    try {
                      setFormData({ ...formData, parameters: JSON.parse(e.target.value) });
                    } catch { /* ignore */ }
                  }}
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 mb-1 block">成本因子 (JSON)</label>
                <textarea
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300 font-mono resize-none"
                  rows={4}
                  value={JSON.stringify(formData.cost_factors, null, 2)}
                  onChange={(e) => {
                    try {
                      setFormData({ ...formData, cost_factors: JSON.parse(e.target.value) });
                    } catch { /* ignore */ }
                  }}
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setEditModal(false)}
                className="flex-1 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 成本估算模态框 */}
      {estimateModal && estimateTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-lg">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-purple-400" />
              成本估算 - {estimateTemplate.name}
            </h3>

            <div className="space-y-4">
              {/* 参数输入 */}
              {estimateTemplate.parameters && Object.entries(estimateTemplate.parameters).map(([key, param]) => (
                <div key={key}>
                  <label className="text-xs text-slate-400 mb-1 block">
                    {param.label || key} {param.unit && `(${param.unit})`}
                  </label>
                  <input
                    type="number"
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={estimateParams[key] || ""}
                    onChange={(e) => setEstimateParams({
                      ...estimateParams,
                      [key]: parseFloat(e.target.value) || 0,
                    })}
                  />
                </div>
              ))}

              <button
                onClick={runEstimate}
                className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg flex items-center justify-center gap-2"
              >
                <Zap className="w-4 h-4" />
                计算成本
              </button>

              {/* 估算结果 */}
              {estimateResult && (
                <div className="bg-slate-800/50 rounded-lg p-4 space-y-3">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-emerald-400">
                      ¥{(estimateResult.total_cost / 10000).toFixed(2)}万
                    </div>
                    <div className="text-xs text-slate-500 mt-1">预估总成本</div>
                  </div>

                  {estimateResult.breakdown && (
                    <div className="pt-3 border-t border-white/5 space-y-2">
                      <div className="text-xs text-slate-400 font-medium">成本拆解:</div>
                      {Object.entries(estimateResult.breakdown).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-slate-400">{key}</span>
                          <span className="text-slate-300">¥{(value / 10000).toFixed(2)}万</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {estimateResult.labor_hours && (
                    <div className="pt-3 border-t border-white/5">
                      <div className="text-xs text-slate-400 font-medium mb-2">人工工时:</div>
                      <div className="text-sm text-slate-300">
                        预估 {estimateResult.labor_hours} 小时
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={() => {
                setEstimateModal(false);
                setEstimateTemplate(null);
                setEstimateResult(null);
              }}
              className="w-full mt-4 py-2 text-slate-400 hover:text-white text-sm"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
