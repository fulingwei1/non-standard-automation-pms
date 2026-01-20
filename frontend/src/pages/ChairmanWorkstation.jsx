/**
 * Chairman Workstation - Executive dashboard for chairman
 * Features: Strategic overview, Financial metrics, Company performance, Key decisions
 * Core Functions: Strategic decision-making, Major approvals, Overall monitoring
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button, ApiIntegrationError } from "../components/ui";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  pmoApi,
  salesStatisticsApi,
  projectApi,
  reportCenterApi
} from "../services/api";
import CultureWallCarousel from "../components/culture/CultureWallCarousel";
import {
  FinancialMetricsGrid,
  StrategicTargetCard,
  OperatingTargetCard,
  RevenueTrendCard,
  ProjectHealthCard,
  RiskProjectsCard,
  DepartmentPerformanceCard,
  KeyDecisionsCard,
  PendingApprovalsCard,
  RecentProjectsCard,
  OperationalOverviewCard,
  formatCurrency
} from "../components/chairman-workstation";

export default function ChairmanWorkstation() {
  const [_loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [companyStats, setCompanyStats] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [keyProjects, setKeyProjects] = useState([]);
  const [departmentPerformance, setDepartmentPerformance] = useState([]);
  const [monthlyRevenue, setMonthlyRevenue] = useState([]);
  const [riskProjects, setRiskProjects] = useState([]);
  const [projectHealthDistribution, setProjectHealthDistribution] = useState(
    []
  );

  // Load data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 获取基础仪表板数据
        const [dashboardRes, projectsRes] = await Promise.all([
        pmoApi.dashboard(),
        projectApi.list({ page: 1, page_size: 10 })]
        );

        if (dashboardRes.data) {
          setCompanyStats(dashboardRes.data);
        }
        if (projectsRes.data?.items) {
          setKeyProjects(projectsRes.data.items.slice(0, 5));

          // 筛选风险项目（健康度为 H2 或 H3）
          const riskProjectsData = projectsRes.data.items.filter(
            (p) => p.health === "H2" || p.health === "H3"
          );
          setRiskProjects(riskProjectsData);
        }

        // 获取项目健康度分布
        try {
          const healthRes = await reportCenterApi.getHealthDistribution();
          if (healthRes.data) {
            setProjectHealthDistribution(healthRes.data);
          }
        } catch (err) {
          console.error("Failed to load health distribution:", err);
        }

        // 获取风险墙数据
        try {
          const riskWallRes = await pmoApi.riskWall();
          if (riskWallRes.data?.projects) {
            setRiskProjects(riskWallRes.data.projects);
          }
        } catch (err) {
          console.error("Failed to load risk wall:", err);
        }

        // 获取月度营收数据（从销售统计 API）
        try {
          const now = new Date();
          const startDate = new Date(now.getFullYear(), now.getMonth() - 5, 1);
          const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
          const salesRes = await salesStatisticsApi.performance({
            start_date: startDate.toISOString().split("T")[0],
            end_date: endDate.toISOString().split("T")[0]
          });
          if (salesRes.data?.monthly_data) {
            setMonthlyRevenue(salesRes.data.monthly_data);
          }
        } catch (err) {
          console.error("Failed to load monthly revenue:", err);
        }

        // 获取部门绩效数据（从 PMO dashboard）
        if (dashboardRes.data?.departments) {
          setDepartmentPerformance(dashboardRes.data.departments);
        }
      } catch (err) {
        console.error("Failed to load chairman dashboard:", err);
        setError(err);
        setCompanyStats(null);
        setKeyProjects([]);
        setPendingApprovals([]);
        setDepartmentPerformance([]);
        setMonthlyRevenue([]);
        setRiskProjects([]);
        setProjectHealthDistribution([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Show error state
  if (error && !companyStats) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="董事长工作台"
          description="企业战略总览、经营决策支持" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/pmo/dashboard"
          onRetry={() => {
            const fetchData = async () => {
              try {
                setLoading(true);
                setError(null);
                const dashboardRes = await pmoApi.dashboard();
                if (dashboardRes.data) {
                  setCompanyStats(dashboardRes.data);
                }
              } catch (err) {
                setError(err);
              } finally {
                setLoading(false);
              }
            };
            fetchData();
          }} />

      </div>);

  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="董事长工作台"
        description={
        companyStats ?
        `年度营收目标: ${formatCurrency(companyStats.yearTarget || 0)} | 已完成: ${formatCurrency(companyStats.totalRevenue || 0)} (${(companyStats.yearProgress || 0).toFixed(1)}%)` :
        "企业战略总览、经营决策支持"
        }
        actions={
        <motion.div variants={fadeIn}>
            <Button className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              战略分析
            </Button>
        </motion.div>
        } />


      {/* 文化墙滚动播放 */}
      <motion.div variants={fadeIn}>
        <CultureWallCarousel
          autoPlay
          interval={5000}
          showControls
          showIndicators
          height="400px"
          onItemClick={(item) => {
            if (item.category === "GOAL") {
              window.location.href = "/personal-goals";
            } else {
              window.location.href = `/culture-wall?item=${item.id}`;
            }
          }} />

      </motion.div>

      {/* Key Financial Metrics */}
      {companyStats &&
        <FinancialMetricsGrid companyStats={companyStats} />
      }

      {/* Main Content Grid */}
      {companyStats &&
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Strategic Target & Operating Target */}
          <div className="lg:col-span-2 space-y-6">
            <StrategicTargetCard />
            <OperatingTargetCard companyStats={companyStats} />
            <RevenueTrendCard monthlyRevenue={monthlyRevenue} />
            <ProjectHealthCard projectHealthDistribution={projectHealthDistribution} />
            <RiskProjectsCard riskProjects={riskProjects} />
            <DepartmentPerformanceCard departmentPerformance={departmentPerformance} />
          </div>

          {/* Right Column - Key Decisions, Approvals & Recent Projects */}
          <div className="space-y-6">
            <KeyDecisionsCard />
            <PendingApprovalsCard pendingApprovals={pendingApprovals} />
            <RecentProjectsCard projects={keyProjects} />
            <OperationalOverviewCard companyStats={companyStats} />
          </div>
      </div>
      }
    </motion.div>);

}
