/**
 * 绩效合约管理页面
 * 支持 L1/L2/L3 三种合约类型的管理
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  FileText,
  CheckCircle,
  Clock,
  TrendingUp,
  Users,
  Briefcase,
  User,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronUp,
  X,
  Save,
  Send,
  PenTool,
  Calculator,
  Filter,
  RefreshCw,
  Target,
  Award,
  Calendar,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Textarea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import {
  performanceContractApi,
  getStatusConfig,
  getCategoryLabel,
  getScoreColor,
} from "@/services/api/performanceContract";

// 指标类别选项
const CATEGORY_OPTIONS = [
  { value: "业绩指标", label: "业绩指标" },
  { value: "管理指标", label: "管理指标" },
  { value: "能力指标", label: "能力指标" },
  { value: "态度指标", label: "态度指标" },
];

// 合约类型选项
const CONTRACT_TYPE_OPTIONS = [
  { value: "L1", label: "公司级 (L1)", icon: Target },
  { value: "L2", label: "部门级 (L2)", icon: Users },
  { value: "L3", label: "个人级 (L3)", icon: User },
];

export default function PerformanceContract() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const [contracts, setContracts] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [expandedContractId, setExpandedContractId] = useState(null);

  // 弹窗状态
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isItemModalOpen, setIsItemModalOpen] = useState(false);
  const [isEvaluateModalOpen, setIsEvaluateModalOpen] = useState(false);
  const [selectedContract, setSelectedContract] = useState(null);
  const [editingItem, setEditingItem] = useState(null);

  // 表单数据
  const [createForm, setCreateForm] = useState({
    contract_type: "L1",
    year: new Date().getFullYear(),
    signer_name: "",
    signer_title: "",
    counterpart_name: "",
    counterpart_title: "",
    department_name: "",
    remarks: "",
  });

  const [itemForm, setItemForm] = useState({
    category: "业绩指标",
    indicator_name: "",
    indicator_description: "",
    weight: "",
    unit: "",
    target_value: "",
    challenge_value: "",
    baseline_value: "",
    scoring_rule: "",
    data_source: "",
    evaluation_method: "",
  });

  const [evaluations, setEvaluations] = useState([]);

  // 获取 Dashboard 数据
  const fetchDashboard = async () => {
    try {
      const { data } = await performanceContractApi.getDashboard({});
      setDashboard(data);
    } catch (error) {
      console.error("获取总览数据失败:", error);
    }
  };

  // 获取合约列表
  const fetchContracts = async (type = null) => {
    setLoading(true);
    try {
      const params = {};
      if (type && type !== "all") {
        params.contract_type = type;
      }
      const { data } = await performanceContractApi.list(params);
      setContracts(data.data?.items || data.items || []);
    } catch (error) {
      console.error("获取合约列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchContracts(activeTab === "all" ? null : activeTab);
  }, [activeTab]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    await fetchContracts(activeTab === "all" ? null : activeTab);
    setRefreshing(false);
  };

  const handleOpenCreate = () => {
    setCreateForm({
      contract_type: "L1",
      year: new Date().getFullYear(),
      signer_name: "",
      signer_title: "",
      counterpart_name: "",
      counterpart_title: "",
      department_name: "",
      remarks: "",
    });
    setIsCreateModalOpen(true);
  };

  const handleCreateContract = async () => {
    try {
      const contractNo = `PC-${createForm.contract_type}-${createForm.year}-${Date.now()}`;
      await performanceContractApi.create({
        ...createForm,
        contract_no: contractNo,
        status: "draft",
      });
      setIsCreateModalOpen(false);
      handleRefresh();
    } catch (error) {
      alert(`创建失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleExpandContract = async (contract) => {
    if (expandedContractId === contract.id) {
      setExpandedContractId(null);
      setSelectedContract(null);
    } else {
      const { data } = await performanceContractApi.get(contract.id);
      setSelectedContract(data.data || data);
      setExpandedContractId(contract.id);
    }
  };

  const handleOpenAddItem = (contract) => {
    setSelectedContract(contract);
    setEditingItem(null);
    setItemForm({
      category: "业绩指标",
      indicator_name: "",
      indicator_description: "",
      weight: "",
      unit: "",
      target_value: "",
      challenge_value: "",
      baseline_value: "",
      scoring_rule: "",
      data_source: "",
      evaluation_method: "",
    });
    setIsItemModalOpen(true);
  };

  const handleOpenEditItem = (contract, item) => {
    setSelectedContract(contract);
    setEditingItem(item);
    setItemForm({
      category: item.category,
      indicator_name: item.indicator_name,
      indicator_description: item.indicator_description || "",
      weight: item.weight?.toString() || "",
      unit: item.unit || "",
      target_value: item.target_value || "",
      challenge_value: item.challenge_value || "",
      baseline_value: item.baseline_value || "",
      scoring_rule: item.scoring_rule || "",
      data_source: item.data_source || "",
      evaluation_method: item.evaluation_method || "",
    });
    setIsItemModalOpen(true);
  };

  const handleSaveItem = async () => {
    try {
      if (editingItem) {
        await performanceContractApi.updateItem(
          selectedContract.id,
          editingItem.id,
          {
            ...itemForm,
            weight: parseFloat(itemForm.weight) || 0,
          }
        );
      } else {
        await performanceContractApi.addItem(selectedContract.id, {
          ...itemForm,
          sort_order: (selectedContract.items?.length || 0) + 1,
          weight: parseFloat(itemForm.weight) || 0,
        });
      }
      setIsItemModalOpen(false);
      // 刷新详情
      const { data } = await performanceContractApi.get(selectedContract.id);
      setSelectedContract(data.data || data);
      setExpandedContractId(selectedContract.id);
    } catch (error) {
      alert(`保存失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteItem = async (contractId, itemId) => {
    if (!confirm("确定删除该指标条目吗？")) return;
    try {
      await performanceContractApi.deleteItem(contractId, itemId);
      const { data } = await performanceContractApi.get(contractId);
      setSelectedContract(data.data || data);
      setExpandedContractId(contractId);
    } catch (error) {
      alert(`删除失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSubmitContract = async (contractId) => {
    if (!confirm("提交后合约将进入审核流程，确定提交吗？")) return;
    try {
      await performanceContractApi.submit(contractId);
      handleRefresh();
    } catch (error) {
      alert(`提交失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSignContract = async (contractId, signAs) => {
    try {
      await performanceContractApi.sign(contractId, signAs);
      handleRefresh();
    } catch (error) {
      alert(`签署失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const handleOpenEvaluate = (contract) => {
    setSelectedContract(contract);
    setEvaluations(
      contract.items?.map((item) => ({
        item_id: item.id,
        actual_value: item.actual_value || "",
        score: item.score || "",
        evaluator_comment: item.evaluator_comment || "",
      })) || []
    );
    setIsEvaluateModalOpen(true);
  };

  const handleSaveEvaluation = async () => {
    try {
      await performanceContractApi.evaluate(selectedContract.id, evaluations);
      setIsEvaluateModalOpen(false);
      handleRefresh();
    } catch (error) {
      alert(`评分失败：${error.response?.data?.detail || error.message}`);
    }
  };

  const updateEvaluation = (index, field, value) => {
    const newEvaluations = [...evaluations];
    newEvaluations[index] = { ...newEvaluations[index], [field]: value };
    setEvaluations(newEvaluations);
  };

  // 渲染统计卡片
  const renderStatCard = (title, value, Icon, color, subtitle) => (
    <motion.div variants={fadeIn} className="relative overflow-hidden rounded-xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-3xl font-bold text-white mt-1">{value || 0}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );

  // 渲染合约卡片
  const renderContractCard = (contract) => {
    const statusConfig = getStatusConfig(contract.status);
    const typeConfig = CONTRACT_TYPE_OPTIONS.find((t) => t.value === contract.contract_type);
    const TypeIcon = typeConfig?.icon || FileText;

    return (
      <motion.div key={contract.id} variants={fadeIn} className="mb-4">
        <Card className="bg-slate-800/50 border-slate-700/50 hover:border-slate-600 transition-colors">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                  <TypeIcon size={20} />
                </div>
                <div>
                  <CardTitle className="text-lg text-white flex items-center gap-2">
                    {contract.contract_no}
                    <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                  </CardTitle>
                  <p className="text-sm text-slate-400 mt-1">
                    {contract.year}年 {contract.department_name || "无部门"}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleExpandContract(contract)}
                className="text-slate-400 hover:text-white"
              >
                {expandedContractId === contract.id ? (
                  <ChevronUp size={18} />
                ) : (
                  <ChevronDown size={18} />
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-slate-500">签约人</p>
                <p className="text-white">{contract.signer_name}</p>
                <p className="text-xs text-slate-400">{contract.signer_title}</p>
              </div>
              <div>
                <p className="text-slate-500">对方/上级</p>
                <p className="text-white">{contract.counterpart_name}</p>
                <p className="text-xs text-slate-400">{contract.counterpart_title}</p>
              </div>
              <div>
                <p className="text-slate-500">权重总和</p>
                <p className={`font-medium ${contract.total_weight === 100 ? "text-emerald-400" : "text-amber-400"}`}>
                  {contract.total_weight?.toFixed(1) || 0}%
                </p>
              </div>
              <div>
                <p className="text-slate-500">签署日期</p>
                <p className="text-white">{contract.sign_date || "-"}</p>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex gap-2 mt-4 pt-4 border-t border-slate-700/50">
              {contract.status === "draft" && (
                <>
                  <Button
                    size="sm"
                    onClick={() => handleOpenAddItem(contract)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus size={16} className="mr-1" />
                    添加指标
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleSubmitContract(contract.id)}
                    className="border-emerald-600 text-emerald-400 hover:bg-emerald-600/20"
                  >
                    <Send size={16} className="mr-1" />
                    提交审批
                  </Button>
                </>
              )}
              {contract.status === "pending_sign" && (
                <>
                  <Button
                    size="sm"
                    onClick={() => handleSignContract(contract.id, "signer")}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <PenTool size={16} className="mr-1" />
                    签署确认
                  </Button>
                </>
              )}
              {contract.status === "active" && (
                <>
                  <Button
                    size="sm"
                    onClick={() => handleOpenEvaluate(contract)}
                    className="bg-amber-600 hover:bg-amber-700"
                  >
                    <Calculator size={16} className="mr-1" />
                    评分
                  </Button>
                </>
              )}
              {expandedContractId === contract.id && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleOpenAddItem(contract)}
                  className="border-blue-600 text-blue-400 hover:bg-blue-600/20"
                >
                  <Plus size={16} className="mr-1" />
                  添加指标
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 展开的详情 */}
        {expandedContractId === contract.id && selectedContract && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 p-4 rounded-lg bg-slate-900/50 border border-slate-700/50"
          >
            <h4 className="text-white font-medium mb-3 flex items-center gap-2">
              <Target size={18} className="text-blue-400" />
              指标条目 ({selectedContract.items?.length || 0})
            </h4>
            {selectedContract.items?.length > 0 ? (
              <div className="space-y-2">
                {selectedContract.items.map((item, _idx) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs border-slate-600 text-slate-300">
                            {getCategoryLabel(item.category)}
                          </Badge>
                          <span className="text-white font-medium">{item.indicator_name}</span>
                        </div>
                        {item.indicator_description && (
                          <p className="text-sm text-slate-400 mt-1">{item.indicator_description}</p>
                        )}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2 text-xs">
                          <div>
                            <span className="text-slate-500">权重：</span>
                            <span className="text-slate-300">{item.weight}%</span>
                          </div>
                          <div>
                            <span className="text-slate-500">目标值：</span>
                            <span className="text-slate-300">{item.target_value || "-"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500">实际值：</span>
                            <span className="text-slate-300">{item.actual_value || "-"}</span>
                          </div>
                          <div>
                            <span className="text-slate-500">得分：</span>
                            <span className={getScoreColor(item.score)}>{item.score || "-"}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleOpenEditItem(contract, item)}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-blue-400"
                        >
                          <Edit2 size={14} />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteItem(contract.id, item.id)}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm text-center py-4">暂无指标条目</p>
            )}
          </motion.div>
        )}
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="绩效合约管理"
        subtitle="L1/L2/L3 三级绩效合约体系"
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />

      <div className="container mx-auto px-4 py-6">
        {/* 统计卡片 */}
        {!loading && dashboard && (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
          >
            {renderStatCard(
              "总合约数",
              dashboard.summary?.total || 0,
              <FileText size={24} />,
              "bg-blue-500/20 text-blue-400",
              `${dashboard.summary?.active || 0} 执行中`
            )}
            {renderStatCard(
              "待签署",
              dashboard.summary?.pending_sign || 0,
              <Clock size={24} />,
              "bg-amber-500/20 text-amber-400"
            )}
            {renderStatCard(
              "执行中",
              dashboard.summary?.active || 0,
              <TrendingUp size={24} />,
              "bg-emerald-500/20 text-emerald-400"
            )}
            {renderStatCard(
              "已完成",
              dashboard.summary?.completed || 0,
              <CheckCircle size={24} />,
              "bg-purple-500/20 text-purple-400",
              dashboard.avg_score ? `平均分：${dashboard.avg_score.toFixed(1)}` : undefined
            )}
          </motion.div>
        )}

        {/* 统计卡片骨架屏 */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-28 rounded-xl bg-slate-800/50" />
            ))}
          </div>
        )}

        {/* 合约类型 Tab */}
        <Card className="bg-slate-800/30 border-slate-700/50 mb-6">
          <CardContent className="p-4">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-slate-900/50">
                <TabsTrigger value="all" className="data-[state=active]:bg-blue-600">
                  全部
                </TabsTrigger>
                <TabsTrigger value="L1" className="data-[state=active]:bg-blue-600">
                  <Target size={16} className="mr-1" />
                  公司级 (L1)
                </TabsTrigger>
                <TabsTrigger value="L2" className="data-[state=active]:bg-blue-600">
                  <Users size={16} className="mr-1" />
                  部门级 (L2)
                </TabsTrigger>
                <TabsTrigger value="L3" className="data-[state=active]:bg-blue-600">
                  <User size={16} className="mr-1" />
                  个人级 (L3)
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardContent>
        </Card>

        {/* 合约列表 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">
              合约列表 ({contracts.length})
            </h3>
            <Button onClick={handleOpenCreate} className="bg-blue-600 hover:bg-blue-700">
              <Plus size={18} className="mr-2" />
              创建合约
            </Button>
          </div>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-40 rounded-xl bg-slate-800/50" />
              ))}
            </div>
          ) : contracts.length > 0 ? (
            contracts.map(renderContractCard)
          ) : (
            <Card className="bg-slate-800/30 border-slate-700/50">
              <CardContent className="py-12 text-center">
                <FileText size={48} className="mx-auto text-slate-600 mb-4" />
                <p className="text-slate-400">暂无合约数据</p>
                <Button onClick={handleOpenCreate} variant="outline" className="mt-4 border-blue-600 text-blue-400">
                  <Plus size={16} className="mr-2" />
                  创建第一个合约
                </Button>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>

      {/* 创建合约弹窗 */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">创建绩效合约</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">合约类型</Label>
                <Select
                  value={createForm.contract_type}
                  onValueChange={(value) => setCreateForm({ ...createForm, contract_type: value })}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {CONTRACT_TYPE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">年度</Label>
                <Input
                  type="number"
                  value={createForm.year}
                  onChange={(e) => setCreateForm({ ...createForm, year: parseInt(e.target.value) })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">签约人姓名</Label>
                <Input
                  value={createForm.signer_name}
                  onChange={(e) => setCreateForm({ ...createForm, signer_name: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300">签约人职位</Label>
                <Input
                  value={createForm.signer_title}
                  onChange={(e) => setCreateForm({ ...createForm, signer_title: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">对方/上级姓名</Label>
                <Input
                  value={createForm.counterpart_name}
                  onChange={(e) => setCreateForm({ ...createForm, counterpart_name: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300">对方/上级职位</Label>
                <Input
                  value={createForm.counterpart_title}
                  onChange={(e) => setCreateForm({ ...createForm, counterpart_title: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div>
              <Label className="text-slate-300">部门名称</Label>
              <Input
                value={createForm.department_name}
                onChange={(e) => setCreateForm({ ...createForm, department_name: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">备注</Label>
              <Textarea
                value={createForm.remarks}
                onChange={(e) => setCreateForm({ ...createForm, remarks: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)} className="border-slate-700 text-slate-300">
              取消
            </Button>
            <Button onClick={handleCreateContract} className="bg-blue-600 hover:bg-blue-700">
              <Save size={16} className="mr-2" />
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 添加/编辑指标条目弹窗 */}
      <Dialog open={isItemModalOpen} onOpenChange={setIsItemModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingItem ? "编辑指标条目" : "添加指标条目"}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">指标类别</Label>
                <Select
                  value={itemForm.category}
                  onValueChange={(value) => setItemForm({ ...itemForm, category: value })}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    {CATEGORY_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value} className="text-white">
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">权重 (%)</Label>
                <Input
                  type="number"
                  value={itemForm.weight}
                  onChange={(e) => setItemForm({ ...itemForm, weight: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div>
              <Label className="text-slate-300">指标名称</Label>
              <Input
                value={itemForm.indicator_name}
                onChange={(e) => setItemForm({ ...itemForm, indicator_name: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div>
              <Label className="text-slate-300">指标描述</Label>
              <Textarea
                value={itemForm.indicator_description}
                onChange={(e) => setItemForm({ ...itemForm, indicator_description: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label className="text-slate-300">单位</Label>
                <Input
                  value={itemForm.unit}
                  onChange={(e) => setItemForm({ ...itemForm, unit: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300">目标值</Label>
                <Input
                  value={itemForm.target_value}
                  onChange={(e) => setItemForm({ ...itemForm, target_value: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300">挑战值</Label>
                <Input
                  value={itemForm.challenge_value}
                  onChange={(e) => setItemForm({ ...itemForm, challenge_value: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">底线值</Label>
                <Input
                  value={itemForm.baseline_value}
                  onChange={(e) => setItemForm({ ...itemForm, baseline_value: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <Label className="text-slate-300">数据来源</Label>
                <Input
                  value={itemForm.data_source}
                  onChange={(e) => setItemForm({ ...itemForm, data_source: e.target.value })}
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
            <div>
              <Label className="text-slate-300">评分规则</Label>
              <Textarea
                value={itemForm.scoring_rule}
                onChange={(e) => setItemForm({ ...itemForm, scoring_rule: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
                rows={2}
              />
            </div>
            <div>
              <Label className="text-slate-300">评估方式</Label>
              <Input
                value={itemForm.evaluation_method}
                onChange={(e) => setItemForm({ ...itemForm, evaluation_method: e.target.value })}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsItemModalOpen(false)} className="border-slate-700 text-slate-300">
              取消
            </Button>
            <Button onClick={handleSaveItem} className="bg-blue-600 hover:bg-blue-700">
              <Save size={16} className="mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 评分弹窗 */}
      <Dialog open={isEvaluateModalOpen} onOpenChange={setIsEvaluateModalOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">绩效评分</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {evaluations.map((evalItem, idx) => {
              const item = selectedContract?.items?.find((i) => i.id === evalItem.item_id);
              return (
                <div key={evalItem.item_id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline" className="border-slate-600 text-slate-300">
                      {getCategoryLabel(item?.category)}
                    </Badge>
                    <span className="text-white font-medium">{item?.indicator_name}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-400 text-sm">目标值</Label>
                      <p className="text-slate-300">{item?.target_value || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-slate-400 text-sm">权重</Label>
                      <p className="text-slate-300">{item?.weight}%</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div>
                      <Label className="text-slate-300 text-sm">实际值</Label>
                      <Input
                        value={evalItem.actual_value}
                        onChange={(e) => updateEvaluation(idx, "actual_value", e.target.value)}
                        className="bg-slate-800 border-slate-700 text-white mt-1"
                        placeholder="输入实际完成值"
                      />
                    </div>
                    <div>
                      <Label className="text-slate-300 text-sm">得分</Label>
                      <Input
                        type="number"
                        value={evalItem.score}
                        onChange={(e) => updateEvaluation(idx, "score", parseFloat(e.target.value) || 0)}
                        className="bg-slate-800 border-slate-700 text-white mt-1"
                        placeholder="0-100"
                        max="100"
                      />
                    </div>
                  </div>
                  <div className="mt-3">
                    <Label className="text-slate-300 text-sm">评估意见</Label>
                    <Textarea
                      value={evalItem.evaluator_comment}
                      onChange={(e) => updateEvaluation(idx, "evaluator_comment", e.target.value)}
                      className="bg-slate-800 border-slate-700 text-white mt-1"
                      rows={2}
                      placeholder="填写评估意见..."
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEvaluateModalOpen(false)} className="border-slate-700 text-slate-300">
              取消
            </Button>
            <Button onClick={handleSaveEvaluation} className="bg-blue-600 hover:bg-blue-700">
              <Save size={16} className="mr-2" />
              保存评分
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
