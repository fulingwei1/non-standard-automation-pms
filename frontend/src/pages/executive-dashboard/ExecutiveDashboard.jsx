import { motion } from "framer-motion";
import { LayoutDashboard, RefreshCw, Download } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";
import { ApiIntegrationError } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { timeRangeOptions } from "./constants";
import { useExecutiveDashboard } from "./useExecutiveDashboard";
import { KpiCard } from "./KpiCard";
import {
  OverviewTab,
  ProjectsTab,
  FinanceTab,
  ResourcesTab,
  SalesTab,
} from "./tabs";

export default function ExecutiveDashboard() {
  const {
    loading,
    refreshing,
    timeRange,
    setTimeRange,
    activeTab,
    setActiveTab,
    dashboardData,
    healthData,
    deliveryData,
    utilizationData,
    costData,
    trendData,
    milestoneData,
    salesFunnelData,
    error,
    setError,
    exporting,
    exportFormat,
    kpiCards,
    handleRefresh,
    handleExport,
  } = useExecutiveDashboard();

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader
          title="决策驾驶舱"
          description="企业运营数据全景视图"
          icon={LayoutDashboard}
        />
        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>
    );
  }

  if (error && !dashboardData.summary) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader
          title="决策驾驶舱"
          description="企业运营数据全景视图"
          icon={LayoutDashboard}
        />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/report-center/executive-dashboard"
          onRetry={() => {
            setError(null);
          }}
        />
      </div>
    );
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6 p-6"
    >
      <PageHeader
        title="决策驾驶舱"
        description="企业运营数据全景视图"
        icon={LayoutDashboard}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {timeRangeOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw
                className={cn("w-4 h-4", refreshing && "animate-spin")}
              />
              刷新
            </Button>
            <div className="relative inline-block">
              <select
                value={exportFormat}
                onChange={(e) => handleExport(e.target.value)}
                disabled={exporting}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary appearance-none pr-8 cursor-pointer disabled:opacity-50"
              >
                <option value="" disabled>
                  导出格式
                </option>
                <option value="xlsx">导出 Excel</option>
                <option value="pdf">导出 PDF</option>
                <option value="csv">导出 CSV</option>
                <option value="json">导出 JSON</option>
              </select>
              <Download
                className={cn(
                  "w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400",
                  exporting && "animate-pulse"
                )}
              />
            </div>
          </motion.div>
        }
      />

      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {kpiCards.map((kpi, index) => (
          <KpiCard key={index} kpi={kpi} />
        ))}
      </motion.div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 mb-4">
          <TabsTrigger value="overview">总览</TabsTrigger>
          <TabsTrigger value="projects">项目</TabsTrigger>
          <TabsTrigger value="finance">财务</TabsTrigger>
          <TabsTrigger value="resources">资源</TabsTrigger>
          <TabsTrigger value="sales">销售</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <OverviewTab
            healthData={healthData}
            deliveryData={deliveryData}
            trendData={trendData}
            costData={costData}
          />
        </TabsContent>

        <TabsContent value="projects" className="space-y-6">
          <ProjectsTab milestoneData={milestoneData} />
        </TabsContent>

        <TabsContent value="finance" className="space-y-6">
          <FinanceTab />
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <ResourcesTab utilizationData={utilizationData} />
        </TabsContent>

        <TabsContent value="sales" className="space-y-6">
          <SalesTab salesFunnelData={salesFunnelData} trendData={trendData} />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
