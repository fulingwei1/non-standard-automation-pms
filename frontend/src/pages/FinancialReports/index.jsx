/**
 * Financial Reports Page - Financial reports and analysis
 * Features: Financial statements, Profit & loss, Cash flow, Budget analysis, Export reports
 */

import { useState, useEffect } from "react";
import {
  BarChart3,
} from "lucide-react";


import { fadeIn, staggerContainer } from "../../lib/animations";
import { financialReportApi } from "../../services/api";

import { reportTypes } from "./constants";

export default function FinancialReports() {
  const [selectedPeriod, setSelectedPeriod] = useState("month"); // month, quarter, year
  const [selectedReport, setSelectedReport] = useState("profit-loss");
  const [dateRange, setDateRange] = useState("2024-07");
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);

  // State initialized with empty data
  const [monthlyFinancials, setMonthlyFinancials] = useState([]);
  const [costBreakdown, setCostBreakdown] = useState([]);
  const [projectProfitability, setProjectProfitability] = useState([]);
  const [cashFlowData, setCashFlowData] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, costRes, projectRes, cashFlowRes] =
        await Promise.allSettled([
        financialReportApi.getMonthlyTrend({
          period: selectedPeriod,
          year: dateRange.split("-")[0]
        }),
        financialReportApi.getCostAnalysis({ period: selectedPeriod }),
        financialReportApi.getProjectProfitability({ limit: 10 }),
        financialReportApi.getCashFlow({ period: selectedPeriod })]
        );

        if (summaryRes.status === "fulfilled" && summaryRes.value.data) {
          const data = summaryRes.value.data;
          setMonthlyFinancials(Array.isArray(data) ? data : []);
        }
        if (costRes.status === "fulfilled" && costRes.value.data) {
          const cbd = costRes.value.data?.items || costRes.value.data;
          setCostBreakdown(Array.isArray(cbd) ? cbd : []);
        }
        if (projectRes.status === "fulfilled" && projectRes.value.data) {
          const data = projectRes.value.data;
          setProjectProfitability(Array.isArray(data) ? data : []);
        }
        if (cashFlowRes.status === "fulfilled" && cashFlowRes.value.data) {
          const data = cashFlowRes.value.data;
          setCashFlowData(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error("Failed to load financial reports:", err);
        setError("加载财务报表失败");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedPeriod, dateRange]);

  const currentData = monthlyFinancials[monthlyFinancials.length - 1] || { cashFlow: 0, revenue: 0, cost: 0, profit: 0 };
  const totalRevenue = (monthlyFinancials || []).reduce((sum, m) => sum + m.revenue, 0);
  const totalCost = (monthlyFinancials || []).reduce((sum, m) => sum + m.cost, 0);
  const totalProfit = (monthlyFinancials || []).reduce((sum, m) => sum + m.profit, 0);
  const avgMargin = totalProfit / totalRevenue * 100;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="财务报表"
        description="财务数据统计、分析和报表导出"
        icon={BarChart3}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
        </motion.div>
        } />

      {/* Period Selector */}
      <PeriodSelector
        selectedPeriod={selectedPeriod}
        setSelectedPeriod={setSelectedPeriod}
        dateRange={dateRange}
        setDateRange={setDateRange}
      />

      {/* Summary Statistics */}
      <SummaryStatistics
        totalRevenue={totalRevenue}
        totalCost={totalCost}
        totalProfit={totalProfit}
        avgMargin={avgMargin}
        currentData={currentData}
      />

      {/* Report Tabs */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <Tabs value={selectedReport || "unknown"} onValueChange={setSelectedReport}>
              <TabsList className="grid w-full grid-cols-5">
                {(reportTypes || []).map((type) => {
                  const Icon = type.icon;
                  return (
                    <TabsTrigger
                      key={type.id}
                      value={type.id}
                      className="flex items-center gap-2">
                      <Icon className="w-4 h-4" />
                      {type.label}
                    </TabsTrigger>);
                })}
              </TabsList>

              <ProfitLossTab currentData={currentData} monthlyFinancials={monthlyFinancials} />
              <CashFlowTab cashFlowData={cashFlowData} />
              <BudgetTab costBreakdown={costBreakdown} />
              <CostAnalysisTab costBreakdown={costBreakdown} />
              <ProjectProfitabilityTab projectProfitability={projectProfitability} />
            </Tabs>
          </CardHeader>
        </Card>
      </motion.div>
    </motion.div>);
}
