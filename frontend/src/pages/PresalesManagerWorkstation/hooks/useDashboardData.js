import { useState, useEffect, useCallback } from "react";
import { presaleApi, userApi } from "../../../services/api";
import {
  extractItems,
  formatDateLabel,
  formatDateTimeLabel,
  getDaysLeft,
  normalizeSolutionStatus,
  mapSolutionDisplayStatus,
  getSolutionStatusColor,
  getSolutionProgress,
  mapTenderStatus,
} from "../utils";

const INITIAL_STATS = {
  teamSize: 0,
  activeSolutions: 0,
  pendingReview: 0,
  activeBids: 0,
  urgentBids: 0,
  monthlyOutput: 0,
  monthlyTarget: 0,
  achievementRate: 0,
  avgSolutionTime: 0,
  solutionQuality: 0,
};

export function useDashboardData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overallStats, setOverallStats] = useState(INITIAL_STATS);
  const [teamPerformance, setTeamPerformance] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [ongoingSolutions, setOngoingSolutions] = useState([]);
  const [biddingProjects, setBiddingProjects] = useState([]);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load solutions
      const solutionsResponse = await presaleApi.solutions.list({
        page: 1,
        page_size: 100,
      });
      const solutions = extractItems(solutionsResponse);
      const ongoingSolutionsData = (solutions || [])
        .map((solution) => {
          const normalizedStatus = normalizeSolutionStatus(
            solution.status,
            solution.review_status
          );

          return {
            id: solution.id,
            name: solution.name || "未命名方案",
            customer:
              solution.customer_name ||
              (solution.customer_id ? `客户 #${solution.customer_id}` : "待关联客户"),
            author: solution.author_name || "待分配",
            version: solution.version || "V1.0",
            status: mapSolutionDisplayStatus(normalizedStatus),
            statusColor: getSolutionStatusColor(normalizedStatus),
            progress: getSolutionProgress(normalizedStatus),
            amount: Number(solution.estimated_cost || solution.suggested_price || 0),
            deadline:
              solution.estimated_duration
                ? `${solution.estimated_duration} 天`
                : formatDateLabel(solution.updated_at || solution.created_at),
            normalizedStatus,
            submitTime: solution.review_time || solution.updated_at || solution.created_at,
          };
        })
        .filter((solution) =>
          ["DRAFT", "SUBMITTED", "REVIEWING"].includes(solution.normalizedStatus)
        );
      setOngoingSolutions(ongoingSolutionsData);
      const activeSolutions = ongoingSolutionsData.length;
      const pendingReview = ongoingSolutionsData.filter(
        (solution) => solution.normalizedStatus === "REVIEWING"
      ).length;

      // Load tenders
      const tendersResponse = await presaleApi.tenders.list({
        page: 1,
        page_size: 100,
      });
      const tenders = extractItems(tendersResponse);
      const biddingProjectsData = (tenders || []).map((tender) => {
        const tenderStatus = mapTenderStatus(tender.result);
        return {
          id: tender.id,
          name: tender.tender_name || "未命名投标",
          customer: tender.customer_name || "待确认客户",
          daysLeft: getDaysLeft(tender.deadline),
          status: tenderStatus.label,
          statusColor: tenderStatus.color,
          amount: Number(tender.budget_amount || tender.budget || 0),
          responsible: tender.leader_id ? `负责人 #${tender.leader_id}` : "待分配",
          progress: tenderStatus.progress,
        };
      });
      setBiddingProjects(biddingProjectsData);
      const activeBids = biddingProjectsData.length;
      const urgentBids = biddingProjectsData.filter(
        (bid) => bid.daysLeft !== null && bid.daysLeft <= 7 && bid.daysLeft > 0
      ).length;

      // Calculate monthly output (sum of estimated values)
      const monthlyOutput = ongoingSolutionsData.reduce(
        (sum, solution) => sum + (solution.amount || 0),
        0
      );
      const monthlyTarget = monthlyOutput * 1.15;
      const achievementRate =
        monthlyTarget > 0 ? (monthlyOutput / monthlyTarget) * 100 : 0;

      // Get pending reviews
      const reviews = ongoingSolutionsData
        .filter((solution) => solution.normalizedStatus === "REVIEWING")
        .map((solution) => {
          const submitDate = new Date(solution.submitTime || 0);
          const daysWaiting = Number.isNaN(submitDate.getTime())
            ? 0
            : Math.max(
                0,
                Math.floor((new Date() - submitDate) / (1000 * 60 * 60 * 24))
              );

          return {
            id: solution.id,
            title: solution.name,
            customer: solution.customer,
            author: solution.author,
            version: solution.version,
            submitTimeLabel: formatDateTimeLabel(solution.submitTime),
            amount: solution.amount,
            priority: daysWaiting > 3 ? "high" : "medium",
            daysWaiting,
          };
        })
        .sort((a, b) => b.daysWaiting - a.daysWaiting);

      // Get team size
      let teamSize = 12;
      try {
        const usersResponse = await userApi
          .list({
            department: "售前技术部",
            is_active: true,
            page_size: 100,
          })
          .catch(() => null);
        if (usersResponse?.data?.total) {
          teamSize = usersResponse.data.total;
        }
      } catch (err) {
        console.error("Failed to get team size:", err);
      }

      // Get response time stats
      let avgSolutionTime = 5.2;
      try {
        const responseTimeResponse = await presaleApi.statistics
          .responseTime({})
          .catch(() => null);
        if (
          responseTimeResponse?.data?.data?.completion_time?.avg_completion_hours
        ) {
          avgSolutionTime = parseFloat(
            responseTimeResponse.data.data.completion_time.avg_completion_hours.toFixed(1)
          );
        }
      } catch (err) {
        console.error("Failed to get response time stats:", err);
      }

      // Calculate solution quality
      let solutionQuality = 92.5;
      try {
        const allSolutionsResponse = await presaleApi.solutions
          .list({
            page: 1,
            page_size: 100,
          })
          .catch(() => null);
        const allSolutions = extractItems(allSolutionsResponse);
        if (allSolutions.length > 0) {
          const approvedSolutions = (allSolutions || []).filter(
            (s) => normalizeSolutionStatus(s.status, s.review_status) === "APPROVED"
          ).length;
          const reviewedSolutions = (allSolutions || []).filter(
            (s) => normalizeSolutionStatus(s.status, s.review_status) !== "DRAFT"
          ).length;
          if (reviewedSolutions > 0) {
            solutionQuality = parseFloat(
              ((approvedSolutions / reviewedSolutions) * 100).toFixed(1)
            );
          }
        }
      } catch (err) {
        console.error("Failed to calculate solution quality:", err);
      }

      // Load team performance
      let teamPerformanceData = [];
      try {
        const performanceResponse = await presaleApi.statistics
          .performance({})
          .catch(() => null);
        if (performanceResponse?.data?.data?.performance) {
          teamPerformanceData = (performanceResponse.data.data.performance || []).map(
            (p) => ({
              id: p.user_id,
              name: p.user_name,
              role: "售前技术工程师",
              activeSolutions: p.solutions_count || 0,
              completedThisMonth: p.completed_tickets || 0,
              pendingReview: 0,
              avgQuality: p.avg_satisfaction
                ? parseFloat((p.avg_satisfaction * 20).toFixed(0))
                : 0,
              status:
                p.avg_satisfaction >= 4.5
                  ? "excellent"
                  : p.avg_satisfaction >= 4.0
                  ? "good"
                  : "warning",
            })
          );
        }
      } catch (err) {
        console.error("Failed to load team performance:", err);
      }

      setOverallStats({
        teamSize,
        activeSolutions,
        pendingReview,
        activeBids,
        urgentBids,
        monthlyOutput,
        monthlyTarget,
        achievementRate,
        avgSolutionTime,
        solutionQuality,
      });
      setPendingReviews(reviews);
      setTeamPerformance(
        teamPerformanceData.length > 0 ? teamPerformanceData : []
      );
    } catch (err) {
      console.error("Failed to load dashboard:", err);
      setError(
        err.response?.data?.detail || err.message || "加载工作台数据失败"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    loading,
    error,
    overallStats,
    teamPerformance,
    pendingReviews,
    ongoingSolutions,
    biddingProjects,
  };
}
