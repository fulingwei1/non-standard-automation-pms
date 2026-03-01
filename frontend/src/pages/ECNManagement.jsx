import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import { staggerContainer, fadeIn } from "../lib/animations";
import { ecnBomApi } from "../services/api/ecnBom";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  FileText,
  Plus,
  Search,
  Filter,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
  BarChart3,
  Layers,
  DollarSign,
  Package,
} from "lucide-react";

// 变更类型配置
const changeTypeConfig = {
  "材料替换": { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", label: "材料替换" },
  "设计变更": { color: "bg-purple-500/20 text-purple-400 border-purple-500/30", label: "设计变更" },
  "工艺优化": { color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30", label: "工艺优化" },
};

// 状态配置
const statusConfig = {
  draft: { color: "bg-slate-500/20 text-slate-400 border-slate-500/30", label: "草稿", icon: FileText },
  reviewing: { color: "bg-amber-500/20 text-amber-400 border-amber-500/30", label: "审核中", icon: Clock },
  approved: { color: "bg-green-500/20 text-green-400 border-green-500/30", label: "已批准", icon: CheckCircle },
  implemented: { color: "bg-blue-500/20 text-blue-400 border-blue-500/30", label: "已实施", icon: CheckCircle },
  closed: { color: "bg-slate-500/20 text-slate-400 border-slate-500/30", label: "已关闭", icon: CheckCircle },
};

// 优先级配置
const priorityConfig = {
  low: { color: "text-slate-400", label: "低", bg: "bg-slate-500/20" },
  medium: { color: "text-blue-400", label: "中", bg: "bg-blue-500/20" },
  high: { color: "text-amber-400", label: "高", bg: "bg-amber-500/20" },
  urgent: { color: "text-red-400", label: "紧急", bg: "bg-red-500/20" },
};

const changeTypeOptions = [
  { value: "", label: "全部类型" },
  { value: "材料替换", label: "材料替换" },
  { value: "设计变更", label: "设计变更" },
  { value: "工艺优化", label: "工艺优化" },
];

const statusOptions = [
  { value: "", label: "全部状态" },
  { value: "draft", label: "草稿" },
  { value: "reviewing", label: "审核中" },
  { value: "approved", label: "已批准" },
  { value: "implemented", label: "已实施" },
  { value: "closed", label: "已关闭" },
];

export default function ECNManagement() {
  const [loading, setLoading] = useState(true);
  const [ecns, setEcns] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState("");
  const [changeTypeFilter, setChangeTypeFilter] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showImpactDialog, setShowImpactDialog] = useState(false);
  const [selectedEcn, setSelectedEcn] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [formData, setFormData] = useState({
    ecn_no: "",
    title: "",
    description: "",
    change_type: "",
    affected_projects: [],
    priority: "medium",
    created_by: null,
  });
  const [projectInput, setProjectInput] = useState("");

  useEffect(() => {
    fetchEcns();
  }, [page, statusFilter, changeTypeFilter]);

  const fetchEcns = async () => {
    try {
      setLoading(true);
      const params = {
        status: statusFilter || undefined,
        change_type: changeTypeFilter || undefined,
        page,
        page_size: pageSize,
      };
      const response = await ecnBomApi.list(params);
      setEcns(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error("Failed to load ECNs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setFormData({
      ecn_no: "",
      title: "",
      description: "",
      change_type: "",
      affected_projects: [],
      priority: "medium",
      created_by: null,
    });
    setProjectInput("");
    setShowCreateDialog(true);
  };

  const handleAddProject = () => {
    const projectId = parseInt(projectInput);
    if (projectId && !formData.affected_projects.includes(projectId)) {
      setFormData((prev) => ({
        ...prev,
        affected_projects: [...prev.affected_projects, projectId],
      }));
      setProjectInput("");
    }
  };

  const handleRemoveProject = (projectId) => {
    setFormData((prev) => ({
      ...prev,
      affected_projects: prev.affected_projects.filter((id) => id !== projectId),
    }));
  };

  const handleSubmit = async () => {
    if (!formData.title || !formData.change_type || formData.affected_projects.length === 0) {
      alert("请填写必填项：标题、变更类型、受影响项目");
      return;
    }

    try {
      await ecnBomApi.create(formData);
      setShowCreateDialog(false);
      fetchEcns();
    } catch (error) {
      console.error("Failed to create ECN:", error);
      alert("创建失败，请重试");
    }
  };

  const handleViewImpact = async (ecn) => {
    try {
      setSelectedEcn(ecn);
      const response = await ecnBomApi.getImpact(ecn.id);
      setImpactData(response.data);
      setShowImpactDialog(true);
    } catch (error) {
      console.error("Failed to load impact:", error);
      alert("加载影响分析失败");
    }
  };

  const handleApplyToBom = async (ecn) => {
    if (!window.confirm(`确定要将 ECN ${ecn.ecn_no} 应用到 BOM 吗？此操作不可逆。`)) {
      return;
    }

    try {
      await ecnBomApi.applyToBom(ecn.id);
      alert("成功应用到 BOM");
      fetchEcns();
    } catch (error) {
      console.error("Failed to apply to BOM:", error);
      alert("应用失败：" + (error.response?.data?.detail || error.message));
    }
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleResetFilters = () => {
    setStatusFilter("");
    setChangeTypeFilter("");
    setPage(1);
  };

  return (
    <div className="p-6 space-y-6 bg-gray-950 min-h-screen">
      <PageHeader
        title="ECN 工程变更管理"
        description="工程变更通知与 BOM 联动管理"
        icon={FileText}
      />

      {loading && !ecns.length ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-gray-400">加载中...</div>
        </div>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* 筛选工具栏 */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-3 items-center">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Input
                      placeholder="搜索 ECN 编号或标题..."
                      className="bg-gray-800 border-gray-700 text-white pl-10"
                    />
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  </div>
                </div>
                <Select value={statusFilter || "unknown"} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="状态" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {statusOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={changeTypeFilter || "unknown"} onValueChange={setChangeTypeFilter}>
                  <SelectTrigger className="w-[120px] bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="变更类型" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {changeTypeOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleResetFilters} variant="outline" className="border-gray-700 text-gray-300 hover:bg-gray-800">
                  <X className="h-4 w-4 mr-2" />
                  重置
                </Button>
                <Button onClick={handleCreate} className="bg-green-600 hover:bg-green-700 ml-auto">
                  <Plus className="h-4 w-4 mr-2" />
                  新建 ECN
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* ECN 列表 */}
          {ecns.length === 0 ? (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardContent className="p-12 text-center text-gray-400">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暂无 ECN 数据</p>
                <p className="text-sm mt-2">点击右上角"新建 ECN"添加第一条工程变更</p>
              </CardContent>
            </Card>
          ) : (
            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {ecns.map((ecn) => {
                const StatusIcon = statusConfig[ecn.status]?.icon || FileText;
                return (
                  <motion.div key={ecn.id} variants={fadeIn}>
                    <Card className="bg-gray-900/50 border-gray-800 hover:border-gray-700 transition-colors h-full">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={changeTypeConfig[ecn.change_type]?.color || "bg-gray-700"}>
                                {ecn.change_type}
                              </Badge>
                              <Badge className={priorityConfig[ecn.priority]?.bg + " " + priorityConfig[ecn.priority]?.color}>
                                {priorityConfig[ecn.priority]?.label}
                              </Badge>
                            </div>
                            <CardTitle className="text-lg text-white line-clamp-2">
                              {ecn.ecn_no} - {ecn.title}
                            </CardTitle>
                          </div>
                          <StatusIcon className={`h-5 w-5 ${statusConfig[ecn.status]?.color.split(" ")[1]}`} />
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <p className="text-sm text-gray-300 line-clamp-2">
                          {ecn.description}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                          <Layers className="h-3 w-3" />
                          <span>影响 {ecn.affected_projects_count || 0} 个项目</span>
                        </div>
                        <div className="flex items-center justify-between pt-3 border-t border-gray-800">
                          <Badge className={statusConfig[ecn.status]?.color}>
                            {statusConfig[ecn.status]?.label}
                          </Badge>
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewImpact(ecn)}
                              className="text-gray-400 hover:text-white h-7 text-xs"
                            >
                              <BarChart3 className="h-3 w-3 mr-1" />
                              影响分析
                            </Button>
                            {ecn.status === "approved" && (
                              <Button
                                size="sm"
                                onClick={() => handleApplyToBom(ecn)}
                                className="bg-blue-600 hover:bg-blue-700 h-7 text-xs"
                              >
                                <Package className="h-3 w-3 mr-1" />
                                应用到 BOM
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>
          )}

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex items-center justify-between pt-4 border-t border-gray-800">
              <span className="text-sm text-gray-400">
                共 {total} 条，第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="border-gray-700 text-gray-300 hover:bg-gray-800 disabled:opacity-50"
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(Math.min(Math.ceil(total / pageSize), page + 1))}
                  disabled={page >= Math.ceil(total / pageSize)}
                  className="border-gray-700 text-gray-300 hover:bg-gray-800 disabled:opacity-50"
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* 创建 ECN 对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">新建 ECN 工程变更</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-300">ECN 编号</Label>
                <Input
                  value={formData.ecn_no}
                  onChange={(e) => handleInputChange("ecn_no", e.target.value)}
                  className="bg-gray-800 border-gray-700 text-white"
                  placeholder="留空自动生成"
                />
              </div>
              <div>
                <Label className="text-gray-300">优先级</Label>
                <Select value={formData.priority} onValueChange={(v) => handleInputChange("priority", v)}>
                  <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="选择优先级" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {Object.entries(priorityConfig).map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"} className="text-white">
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-gray-300">标题 *</Label>
              <Input
                value={formData.title}
                onChange={(e) => handleInputChange("title", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
                placeholder="简要描述变更内容"
              />
            </div>
            <div>
              <Label className="text-gray-300">变更类型 *</Label>
              <Select value={formData.change_type} onValueChange={(v) => handleInputChange("change_type", v)}>
                <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                  <SelectValue placeholder="选择变更类型" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {changeTypeOptions.slice(1).map((opt) => (
                    <SelectItem key={opt.value} value={opt.value} className="text-white">
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300">变更描述</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => handleInputChange("description", e.target.value)}
                className="bg-gray-800 border-gray-700 text-white min-h-[100px]"
                placeholder="详细描述变更原因、内容和范围"
              />
            </div>
            <div>
              <Label className="text-gray-300">受影响项目 *</Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={projectInput || "unknown"}
                  onChange={(e) => setProjectInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddProject())}
                  className="bg-gray-800 border-gray-700 text-white flex-1"
                  placeholder="输入项目 ID 后按回车添加"
                  type="number"
                />
                <Button onClick={handleAddProject} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.affected_projects.map((projectId) => (
                  <Badge
                    key={projectId}
                    className="bg-blue-500/20 text-blue-400 border-blue-500/30 cursor-pointer"
                    onClick={() => handleRemoveProject(projectId)}
                  >
                    项目 {projectId} <X className="h-3 w-3 ml-1" />
                  </Badge>
                ))}
              </div>
              {formData.affected_projects.length === 0 && (
                <p className="text-xs text-gray-500">至少添加一个受影响项目</p>
              )}
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                className="border-gray-700 text-gray-300 hover:bg-gray-800"
              >
                取消
              </Button>
              <Button onClick={handleSubmit} className="bg-green-600 hover:bg-green-700">
                创建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 影响分析对话框 */}
      <Dialog open={showImpactDialog} onOpenChange={setShowImpactDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">
              变更影响分析 - {selectedEcn?.ecn_no}
            </DialogTitle>
          </DialogHeader>
          {impactData && (
            <div className="space-y-6 py-4">
              {/* 影响摘要 */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Layers className="h-4 w-4 text-blue-400" />
                      <span className="text-xs text-gray-400">受影响项目</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {impactData.impact_summary.affected_projects_count}
                    </p>
                  </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Package className="h-4 w-4 text-purple-400" />
                      <span className="text-xs text-gray-400">BOM 变更项</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {impactData.impact_summary.affected_bom_items_count}
                    </p>
                  </CardContent>
                </Card>
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <DollarSign className="h-4 w-4 text-green-400" />
                      <span className="text-xs text-gray-400">预估成本影响</span>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      ¥{(impactData.impact_summary.estimated_cost_impact / 10000).toFixed(2)}万
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* 项目影响详情 */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  项目影响详情
                </h4>
                <div className="space-y-2">
                  {impactData.impact_details.projects.map((proj, i) => (
                    <div key={i} className="flex items-center justify-between bg-gray-800/30 rounded px-3 py-2">
                      <span className="text-sm text-gray-300">项目 {proj.project_id}</span>
                      <Badge className="bg-blue-500/20 text-blue-400">
                        {proj.bom_changes_count} 个 BOM 变更
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* 成本分解 */}
              <div>
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  成本分解
                </h4>
                <div className="space-y-2">
                  {Object.entries(impactData.impact_details.cost_breakdown).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">
                        {key === "material_replacement" && "材料替换"}
                        {key === "design_change" && "设计变更"}
                        {key === "process_optimization" && "工艺优化"}
                        {key === "labor" && "人工成本"}
                        {key === "overhead" && "管理费用"}
                      </span>
                      <span className="text-white font-mono">
                        ¥{(value / 10000).toFixed(2)}万
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 建议 */}
              {impactData.recommendations?.length > 0 && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded p-4">
                  <h4 className="text-sm font-bold text-amber-400 mb-2 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    建议
                  </h4>
                  <ul className="space-y-1">
                    {impactData.recommendations.map((rec, i) => (
                      <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                        <span className="text-amber-400 mt-0.5">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex justify-end pt-4">
                <Button
                  onClick={() => setShowImpactDialog(false)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  关闭
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
