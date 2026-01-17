import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Users,
  DollarSign,
  Filter,
  Calendar,
  Search,
  ChevronRight } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input } from
"../components/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  salesStatisticsApi,
  opportunityApi as _opportunityApi,
  customerApi as _customerApi } from
"../services/api";

const stages = [
{ key: "leads", label: "线索", color: "slate", backendKey: "leads" },
{
  key: "opportunities",
  label: "商机",
  color: "blue",
  backendKey: "opportunities"
},
{ key: "quotes", label: "报价", color: "amber", backendKey: "quotes" },
{ key: "contracts", label: "合同", color: "purple", backendKey: "contracts" }];


export default function SalesFunnel() {
  const [funnelData, setFunnelData] = useState([]);
  const [_loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("month"); // month, quarter, year
  const [ownerId, setOwnerId] = useState(null);
  const [customerId, setCustomerId] = useState(null);
  const [industry, setIndustry] = useState("");
  const [_selectedStage, setSelectedStage] = useState(null);

  useEffect(() => {
    loadFunnelData();
  }, []);

  const loadFunnelData = async () => {
    try {
      setLoading(true);

      // Calculate date range based on timeRange
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
        // year
        startDate = new Date(now.getFullYear(), 0, 1);
        endDate = new Date(now.getFullYear(), 11, 31);
      }

      const params = {
        start_date: startDate.toISOString().split("T")[0],
        end_date: endDate.toISOString().split("T")[0]
      };

      if (ownerId) params.owner_id = ownerId;
      if (customerId) params.customer_id = customerId;
      if (industry) params.industry = industry;

      const res = await salesStatisticsApi.funnel(params);
      const data = res.data || {};

      // Transform backend data to frontend format
      const transformedData = [
      {
        stage: "leads",
        label: "线索",
        count: data.leads || 0,
        value: 0,
        conversion: 100
      },
      {
        stage: "opportunities",
        label: "商机",
        count: data.opportunities || 0,
        value: data.total_opportunity_amount || 0,
        conversion:
        data.leads > 0 ?
        (data.opportunities / data.leads * 100).toFixed(1) :
        0
      },
      {
        stage: "quotes",
        label: "报价",
        count: data.quotes || 0,
        value: 0,
        conversion:
        data.opportunities > 0 ?
        (data.quotes / data.opportunities * 100).toFixed(1) :
        0
      },
      {
        stage: "contracts",
        label: "合同",
        count: data.contracts || 0,
        value: data.total_contract_amount || 0,
        conversion:
        data.quotes > 0 ?
        (data.contracts / data.quotes * 100).toFixed(1) :
        0
      }];


      // Calculate conversion rates from previous stage
      transformedData.forEach((item, index) => {
        if (index > 0) {
          const prevCount = transformedData[index - 1].count;
          item.conversion =
          prevCount > 0 ? (item.count / prevCount * 100).toFixed(1) : 0;
        }
      });

      setFunnelData(transformedData);
    } catch (error) {
      console.error("Failed to load funnel data:", error);
      // Mock data as fallback
      setFunnelData([
      {
        stage: "leads",
        label: "线索",
        count: 120,
        value: 0,
        conversion: 100
      },
      {
        stage: "opportunities",
        label: "商机",
        count: 80,
        value: 8000000,
        conversion: 66.7
      },
      {
        stage: "quotes",
        label: "报价",
        count: 45,
        value: 0,
        conversion: 56.3
      },
      {
        stage: "contracts",
        label: "合同",
        count: 25,
        value: 2500000,
        conversion: 55.6
      }]
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFunnelData();
  }, [timeRange, ownerId, customerId, industry]);

  const maxCount = Math.max(...funnelData.map((d) => d.count), 1);

  const handleStageClick = (stage) => {
    setSelectedStage(stage);
    // TODO: Navigate to detail page or show modal
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="销售漏斗"
        description="Issue 5.5: 销售漏斗可视化，支持筛选和钻取" />


      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Filters - Issue 5.5: 时间范围、销售、客户、行业筛选 */}
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
                  <label className="text-sm text-slate-400 mb-1 block">
                    时间范围
                  </label>
                  <Select value={timeRange} onValueChange={setTimeRange}>
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
                  <label className="text-sm text-slate-400 mb-1 block">
                    销售人员
                  </label>
                  <Select
                    value={ownerId || "all"}
                    onValueChange={(v) =>
                    setOwnerId(v === "all" ? null : parseInt(v))
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="全部" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部</SelectItem>
                      {/* TODO: Load from API */}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    客户
                  </label>
                  <Select
                    value={customerId || "all"}
                    onValueChange={(v) =>
                    setCustomerId(v === "all" ? null : parseInt(v))
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="全部" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部</SelectItem>
                      {/* TODO: Load from API */}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    行业
                  </label>
                  <Input
                    placeholder="输入行业关键词"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)} />

                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Funnel Visualization - Issue 5.5: 展示销售漏斗图表 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle>销售漏斗分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {funnelData.map((data, index) => {
                  const stageConfig =
                  stages.find((s) => s.key === data.stage) || stages[0];
                  const width = data.count / maxCount * 100;
                  const prevData = index > 0 ? funnelData[index - 1] : null;
                  const dropRate =
                  prevData && prevData.count > 0 ?
                  (
                  (prevData.count - data.count) / prevData.count *
                  100).
                  toFixed(1) :
                  0;
                  const conversionRate = parseFloat(data.conversion) || 0;

                  return (
                    <motion.div
                      key={data.stage}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      onClick={() => handleStageClick(data.stage)}
                      className="space-y-2 cursor-pointer hover:bg-surface-50/50 p-3 rounded-lg transition-colors">

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Badge
                            variant="outline"
                            className={cn(
                              `bg-${stageConfig.color}-500/10`,
                              `border-${stageConfig.color}-500/30`,
                              `text-${stageConfig.color}-400`
                            )}>

                            {data.label || stageConfig.label}
                          </Badge>
                          <span className="text-white font-medium">
                            {data.count}个
                          </span>
                          {data.value > 0 &&
                          <span className="text-slate-400 text-sm">
                              ¥{(data.value / 10000).toFixed(0)}万
                            </span>
                          }
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-slate-400">
                            转化率:{" "}
                            <span className="text-white">
                              {conversionRate}%
                            </span>
                          </span>
                          {prevData && dropRate > 0 &&
                          <span
                            className={cn(
                              "flex items-center gap-1",
                              dropRate > 50 ?
                              "text-red-400" :
                              "text-slate-400"
                            )}>

                              {dropRate > 50 ?
                            <TrendingDown className="w-4 h-4" /> :

                            <TrendingUp className="w-4 h-4" />
                            }
                              流失 {dropRate}%
                            </span>
                          }
                          <ChevronRight className="w-4 h-4 text-slate-500" />
                        </div>
                      </div>
                      <div className="relative">
                        <Progress
                          value={width}
                          className={cn(`bg-${stageConfig.color}-500/20`)} />

                      </div>
                    </motion.div>);

                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Statistics - Issue 5.5: 展示转化率和流失率 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-4 gap-4">

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">总线索数</p>
                    <p className="text-2xl font-bold text-white">
                      {funnelData[0]?.count || 0}
                    </p>
                  </div>
                  <Target className="w-8 h-8 text-blue-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">签约数</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {funnelData[funnelData.length - 1]?.count || 0}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-emerald-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">总签约额</p>
                    <p className="text-2xl font-bold text-purple-400">
                      ¥
                      {(
                      funnelData.reduce((sum, d) => sum + (d.value || 0), 0) /
                      10000).
                      toFixed(0)}
                      万
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-purple-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">整体转化率</p>
                    <p className="text-2xl font-bold text-amber-400">
                      {funnelData.length > 0 && funnelData[0].count > 0 ?
                      (
                      funnelData[funnelData.length - 1].count /
                      funnelData[0].count *
                      100).
                      toFixed(1) :
                      0}
                      %
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-amber-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>
    </div>);

}