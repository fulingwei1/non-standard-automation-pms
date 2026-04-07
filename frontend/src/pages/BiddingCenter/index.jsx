/**
 * 投标中心
 * 管理投标项目、技术标书、竞争分析
 */
import { useState, useEffect, useCallback } from "react";


import { fadeIn, staggerContainer } from "../../lib/animations";
import { presaleApi } from "../../services/api";
import { biddingStages, mapTenderStatus } from "./constants";

export default function BiddingCenter() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedBidding, setSelectedBidding] = useState(null);
  const [biddings, setBiddings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load tenders from API
  const loadTenders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (searchTerm) {
        params.keyword = searchTerm;
      }

      const response = await presaleApi.tenders.list(params);
      const tendersData = response.data?.items || response.data?.items || response.data || [];

      // Transform tenders
      const transformedTenders = (tendersData || []).map((tender) => {
        const deadline = tender.submission_deadline ?
        new Date(tender.submission_deadline) :
        null;
        const now = new Date();
        const daysLeft = deadline ?
        Math.ceil((deadline - now) / (1000 * 60 * 60 * 24)) :
        0;

        return {
          id: tender.id,
          code: tender.tender_no || `BID-${tender.id}`,
          name: tender.tender_name || tender.project_name || "",
          customer: tender.customer_name || "",
          customerId: tender.customer_id,
          stage: mapTenderStatus(tender.status),
          deadline: deadline ? deadline.toISOString().split("T")[0] : "",
          daysLeft: daysLeft > 0 ? daysLeft : 0,
          amount: tender.budget ? tender.budget / 10000 : 0,
          engineer: tender.responsible_name || "",
          salesPerson: tender.sales_person_name || "",
          progress: tender.progress || 0,
          solution: tender.solution_id ? `SOL-${tender.solution_id}` : null,
          solutionName: tender.solution_name || null,
          techRequirements:
          tender.tech_requirements || tender.description || "",
          competitors: [],
          documents: [],
          timeline: [],
          notes: tender.notes || "",
          costSupport: {
            status: "none",
            requestedAt: null,
            requestedBy: null,
            estimatedCost: null,
            submittedAt: null,
            submittedBy: null
          }
        };
      });

      setBiddings(transformedTenders);
    } catch (err) {
      console.error("Failed to load tenders:", err);
      setError(err.response?.data?.detail || err.message || "加载投标项目失败");
      setBiddings([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  useEffect(() => {
    loadTenders();
  }, [loadTenders]);

  // 筛选投标
  const filteredBiddings = (biddings || []).filter((bidding) => {
    const searchLower = searchTerm.toLowerCase();
    const name = (bidding.name || "").toLowerCase();
    const customer = (bidding.customer || "").toLowerCase();
    const code = (bidding.code || "").toLowerCase();

    return (
      name.includes(searchLower) ||
      customer.includes(searchLower) ||
      code.includes(searchLower));

  });

  // 按阶段分组（看板视图）
  const biddingsByStage = (biddingStages || []).map((stage) => ({
    ...stage,
    biddings: (filteredBiddings || []).filter((b) => b.stage === stage.id)
  }));

  // 统计数据
  const stats = {
    total: biddings.length,
    active: (biddings || []).filter((b) => !["won", "lost"].includes(b.stage)).length,
    won: (biddings || []).filter((b) => b.stage === "won").length,
    totalAmount: biddings.
    filter((b) => b.stage === "won").
    reduce((acc, b) => acc + b.amount, 0)
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      <PageHeader
        title="投标中心"
        description="管理投标项目、技术标书、竞争分析"
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建投标
            </Button>
        </motion.div>
        } />


      {/* 统计卡片 */}
      <StatsCards stats={stats} />

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4">

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索项目名称、客户、编号..."
              value={searchTerm || "unknown"}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full" />

          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading &&
      <div className="text-center py-16 text-slate-400">
          <Target className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
      </div>
      }

      {/* 错误提示 */}
      {error && !loading &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }

      {/* 看板视图 */}
      {!loading && !error &&
      <BiddingKanban
        biddingsByStage={biddingsByStage}
        onSelectBidding={setSelectedBidding} />

      }

      {/* 投标详情面板 */}
      {selectedBidding &&
      <BiddingDetailPanel
        bidding={selectedBidding}
        onClose={() => setSelectedBidding(null)} />

      }
    </motion.div>);

}
