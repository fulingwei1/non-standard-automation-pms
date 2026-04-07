/**
 * 绩效合约管理页面
 * 支持 L1/L2/L3 三种合约类型的管理
 */
import { useState, useEffect } from "react";




import { staggerContainer } from "@/lib/animations";
import { performanceContractApi } from "@/services/api/performanceContract";
import { INITIAL_CREATE_FORM, INITIAL_ITEM_FORM } from "./constants";

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
  const [createForm, setCreateForm] = useState({ ...INITIAL_CREATE_FORM });
  const [itemForm, setItemForm] = useState({ ...INITIAL_ITEM_FORM });
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
    setCreateForm({ ...INITIAL_CREATE_FORM });
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
    setItemForm({ ...INITIAL_ITEM_FORM });
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
            <StatCard
              title="总合约数"
              value={dashboard.summary?.total || 0}
              icon={<FileText size={24} />}
              color="bg-blue-500/20 text-blue-400"
              subtitle={`${dashboard.summary?.active || 0} 执行中`}
            />
            <StatCard
              title="待签署"
              value={dashboard.summary?.pending_sign || 0}
              icon={<Clock size={24} />}
              color="bg-amber-500/20 text-amber-400"
            />
            <StatCard
              title="执行中"
              value={dashboard.summary?.active || 0}
              icon={<TrendingUp size={24} />}
              color="bg-emerald-500/20 text-emerald-400"
            />
            <StatCard
              title="已完成"
              value={dashboard.summary?.completed || 0}
              icon={<CheckCircle size={24} />}
              color="bg-purple-500/20 text-purple-400"
              subtitle={dashboard.avg_score ? `平均分：${dashboard.avg_score.toFixed(1)}` : undefined}
            />
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
            <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab}>
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
            contracts.map((contract) => (
              <ContractCard
                key={contract.id}
                contract={contract}
                expandedContractId={expandedContractId}
                selectedContract={selectedContract}
                onExpandContract={handleExpandContract}
                onOpenAddItem={handleOpenAddItem}
                onSubmitContract={handleSubmitContract}
                onSignContract={handleSignContract}
                onOpenEvaluate={handleOpenEvaluate}
                onOpenEditItem={handleOpenEditItem}
                onDeleteItem={handleDeleteItem}
              />
            ))
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
      <CreateContractDialog
        open={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        createForm={createForm}
        setCreateForm={setCreateForm}
        onCreateContract={handleCreateContract}
      />

      {/* 添加/编辑指标条目弹窗 */}
      <ItemFormDialog
        open={isItemModalOpen}
        onOpenChange={setIsItemModalOpen}
        editingItem={editingItem}
        itemForm={itemForm}
        setItemForm={setItemForm}
        onSaveItem={handleSaveItem}
      />

      {/* 评分弹窗 */}
      <EvaluateDialog
        open={isEvaluateModalOpen}
        onOpenChange={setIsEvaluateModalOpen}
        selectedContract={selectedContract}
        evaluations={evaluations}
        updateEvaluation={updateEvaluation}
        onSaveEvaluation={handleSaveEvaluation}
      />
    </div>
  );
}
