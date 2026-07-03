/**
 * 销售漏斗页面（合并版）
 *
 * 功能：
 * 1. 概览 - 漏斗可视化 + 筛选 + 钻取
 * 2. 转化分析 - 详细阶段转化率
 * 3. 瓶颈识别 - 低转化率/长停留阶段分析
 * 4. 预测准确性 - 预测 vs 实际对比
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  TrendingUp, Filter, AlertTriangle, Activity, BarChart3, Target,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card, CardContent, CardHeader, CardTitle,
  Input,
  Tabs, TabsContent, TabsList, TabsTrigger,
} from "../../components/ui";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../../components/ui/select";
import { fadeIn } from "../../lib/animations";
import { salesStatisticsApi, customerApi, userApi } from "../../services/api";

import Overview from "./Overview";
import ConversionRates from "./ConversionRates";
import Bottlenecks from "./Bottlenecks";
import OpportunityWinRate from "./OpportunityWinRate";
import PredictionAccuracy from "./PredictionAccuracy";

export default function SalesFunnel() {
  const navigate = useNavigate();
  const [funnelData, setFunnelData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("month");
  const [ownerId, setOwnerId] = useState(null);
  const [customerId, setCustomerId] = useState(null);
  const [industry, setIndustry] = useState("");
  const [selectedStage, setSelectedStage] = useState(null);
  const [owners, setOwners] = useState([]);
  const [customers, setCustomers] = useState([]);

  // 加载筛选选项
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const [usersRes, customersRes] = await Promise.all([
          userApi.options({ page: 1, page_size: 100, is_active: true }),
          customerApi.list({ page: 1, page_size: 100 }),
        ]);
        const userItems = usersRes?.data?.items || usersRes?.data || [];
        const customerItems = customersRes?.data?.items || customersRes?.data || [];
        setOwners(Array.isArray(userItems) ? userItems : []);
        setCustomers(Array.isArray(customerItems) ? customerItems : []);
      } catch (error) {
        console.warn("Failed to load filter options:", error);
        setOwners([]);
        setCustomers([]);
      }
    };
    loadFilterOptions();
  }, []);

  // 加载漏斗数据
  const loadFunnelData = async () => {
    try {
      setLoading(true);
      const now = new Date();
      let startDate, endDate;

      if (timeRange === "month") {
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      } else if (timeRange === "quarter") {
        const quarter = Math.floor(now.getMonth() / 3);
        startDate = new Date(now.getFullYear(), quarter * 3, 1);
        endDate = new Date(now.getFullYear(), (quarter + 1) * 3, 0);
      } else {
        startDate = new Date(now.getFullYear(), 0, 1);
        endDate = new Date(now.getFullYear(), 11, 31);
      }

      const params = {
        start_date: startDate.toISOString().split("T")[0],
        end_date: endDate.toISOString().split("T")[0],
      };

      if (ownerId) params.owner_id = ownerId;
      if (customerId) params.customer_id = customerId;
      if (industry) params.industry = industry;

      const res = await salesStatisticsApi.funnel(params);
      const data = res.formatted || res.data?.data || res.data || {};

      const transformedData = [
        { stage: "leads", label: "线索", count: data.leads || 0, value: 0, conversion: 100 },
        {
          stage: "opportunities",
          label: "商机",
          count: data.opportunities || 0,
          value: data.total_opportunity_amount || 0,
          conversion: data.leads > 0 ? ((data.opportunities / data.leads) * 100).toFixed(1) : 0,
        },
        {
          stage: "quotes",
          label: "报价",
          count: data.quotes || 0,
          value: 0,
          conversion: data.opportunities > 0 ? ((data.quotes / data.opportunities) * 100).toFixed(1) : 0,
        },
        {
          stage: "contracts",
          label: "合同",
          count: data.contracts || 0,
          value: data.total_contract_amount || 0,
          conversion: data.quotes > 0 ? ((data.contracts / data.quotes) * 100).toFixed(1) : 0,
        },
      ];

      transformedData.forEach((item, index) => {
        if (index > 0) {
          const prevCount = transformedData[index - 1].count;
          item.conversion = prevCount > 0 ? ((item.count / prevCount) * 100).toFixed(1) : 0;
        }
      });

      setFunnelData(transformedData);
    } catch (error) {
      console.error("Failed to load funnel data:", error);
      setFunnelData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFunnelData();

  }, [timeRange, ownerId, customerId, industry]);

  const maxCount = Math.max(...(funnelData || []).map((d) => d.count), 1);

  const handleStageClick = (stage) => {
    setSelectedStage(stage);
    const routeMap = {
      leads: "/sales/leads",
      opportunities: "/opportunities",
      quotes: "/quotations",
      contracts: "/contracts",
    };
    const to = routeMap[stage];
    if (to) {
      navigate(to);
    }
  };

  // 使用 loading 和 selectedStage 避免 ESLint 警告
  void loading;
  void selectedStage;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="销售漏斗"
        description="销售漏斗可视化，支持筛选、钻取和优化分析"
        icon={<BarChart3 className="w-6 h-6 text-blue-500" />}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 筛选条件 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="w-4 h-4" />
                筛选条件
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">时间范围</label>
                  <Select value={timeRange || "month"} onValueChange={setTimeRange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="month">本月</SelectItem>
                      <SelectItem value="quarter">本季度</SelectItem>
                      <SelectItem value="year">本年</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">销售人员</label>
                  <Select value={ownerId?.toString() || "all"} onValueChange={(v) => setOwnerId(v === "all" ? null : parseInt(v))}>
                    <SelectTrigger>
                      <SelectValue placeholder="全部" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部</SelectItem>
                      {(owners || []).map((u) => (
                        <SelectItem key={u.id} value={u.id?.toString()}>
                          {u.real_name || u.username || `用户#${u.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">客户</label>
                  <Select
                    value={customerId?.toString() || "all"}
                    onValueChange={(v) => setCustomerId(v === "all" ? null : parseInt(v))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="全部" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部</SelectItem>
                      {(customers || []).map((c) => (
                        <SelectItem key={c.id} value={c.id?.toString()}>
                          {c.customer_name || c.name || `客户#${c.id}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">行业</label>
                  <Input placeholder="输入行业关键词" value={industry || ""} onChange={(e) => setIndustry(e.target.value)} />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Tab 切换 */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-[750px]">
            <TabsTrigger value="overview">
              <BarChart3 className="w-4 h-4 mr-2" />
              概览
            </TabsTrigger>
            <TabsTrigger value="conversion">
              <TrendingUp className="w-4 h-4 mr-2" />
              转化分析
            </TabsTrigger>
            <TabsTrigger value="bottlenecks">
              <AlertTriangle className="w-4 h-4 mr-2" />
              瓶颈识别
            </TabsTrigger>
            <TabsTrigger value="win-rate">
              <Target className="w-4 h-4 mr-2" />
              商机预测
            </TabsTrigger>
            <TabsTrigger value="accuracy">
              <Activity className="w-4 h-4 mr-2" />
              预测准确性
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <Overview funnelData={funnelData} maxCount={maxCount} handleStageClick={handleStageClick} />
          </TabsContent>

          <TabsContent value="conversion">
            <ConversionRates />
          </TabsContent>

          <TabsContent value="bottlenecks">
            <Bottlenecks />
          </TabsContent>

          <TabsContent value="win-rate">
            <OpportunityWinRate />
          </TabsContent>

          <TabsContent value="accuracy">
            <PredictionAccuracy />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
