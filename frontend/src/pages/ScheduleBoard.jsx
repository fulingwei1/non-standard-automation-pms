import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  projectApi,
  milestoneApi,
  progressApi
} from "../services/api";
import {
  StatsCards,
  ViewControls,
  StageColumn,
  ScheduleGanttView,
  ScheduleCalendarView,
  ResourceHeatMap
} from "../components/schedule-board";

export default function ScheduleBoard() {
  const [viewMode, setViewMode] = useState("kanban"); // kanban | gantt | calendar
  const [projects, setProjects] = useState([]);
  const [_loading, setLoading] = useState(true);

  const stages = [
    { stage: "S3", name: "采购备料" },
    { stage: "S4", name: "加工制造" },
    { stage: "S5", name: "装配调试" },
    { stage: "S6", name: "FAT验收" }
  ];

  const getStageName = (stage) => {
    const stageNames = {
      S1: "需求进入",
      S2: "方案设计",
      S3: "采购备料",
      S4: "加工制造",
      S5: "装配调试",
      S6: "FAT验收",
      S7: "包装发运",
      S8: "SAT验收",
      S9: "质保结项"
    };
    return stageNames[stage] || stage;
  };

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        const response = await projectApi.list({ page_size: 100 });
        // Handle PaginatedResponse format
        const data = response.data || response;
        const projectList = data.items || data || [];

        // Transform backend project format to frontend format and load milestones/resources
        const transformedProjects = await Promise.all(
          projectList.map(async (p) => {
            const projectId = p.id || p.project_code;

            // Load milestones for this project
            let milestones = [];
            try {
              const milestonesRes = await milestoneApi.list(projectId);
              const milestonesData = milestonesRes.data || milestonesRes || [];
              milestones = milestonesData.map((m) => ({
                name: m.milestone_name || m.name || "",
                date: m.plan_date || m.planned_date || "",
                status:
                  m.status === "COMPLETED"
                    ? "completed"
                    : m.status === "IN_PROGRESS"
                    ? "in_progress"
                    : "pending"
              }));
            } catch (err) {
              console.error(
                `Failed to load milestones for project ${projectId}:`,
                err
              );
            }

            // Load resources/workload for this project
            let resources = [];
            try {
              // Try to get project progress summary which may include resource info
              const progressRes = await progressApi.reports
                .getSummary(projectId)
                .catch(() => null);
              if (progressRes?.data) {
                // Extract resource info if available
                // This is a placeholder - adjust based on actual API response structure
                resources = [];
              }
            } catch (err) {
              console.error(
                `Failed to load resources for project ${projectId}:`,
                err
              );
            }

            return {
              id: p.project_code || p.id,
              name: p.project_name,
              customer: p.customer_name || "未知客户",
              stage: p.stage || "S1",
              stageName: getStageName(p.stage),
              progress: p.progress_pct || 0,
              health: p.health || "H1",
              planStart: p.planned_start_date || "",
              planEnd: p.planned_end_date || "",
              daysRemaining: p.planned_end_date
                ? Math.ceil(
                    (new Date(p.planned_end_date) - new Date()) /
                      (1000 * 60 * 60 * 24)
                  )
                : 0,
              milestones,
              resources
            };
          })
        );

        setProjects(transformedProjects);
      } catch (err) {
        console.error("Failed to fetch projects:", err);
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const totalProjects = projects.length;
  const atRiskProjects = projects.filter((p) => p.health === "H2").length;
  const blockedProjects = projects.filter((p) => p.health === "H3").length;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="排期看板"
        description="PMC视角的项目进度与资源协调中心"
      />

      {/* Summary Stats */}
      <StatsCards
        totalProjects={totalProjects}
        atRiskProjects={atRiskProjects}
        blockedProjects={blockedProjects}
      />

      {/* View Controls */}
      <ViewControls viewMode={viewMode} setViewMode={setViewMode} />

      {/* Kanban Board */}
      {viewMode === "kanban" && (
        <motion.div variants={fadeIn} className="overflow-x-auto pb-4">
          <div className="flex gap-6 min-w-max">
            {stages.map(({ stage, name }) => (
              <StageColumn
                key={stage}
                stage={stage}
                stageName={name}
                projects={projects}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Gantt View */}
      {viewMode === "gantt" && (
        <motion.div variants={fadeIn}>
          <ScheduleGanttView
            projects={projects}
            onProjectClick={(task) => {
              if (task.project_id) {
                window.open(`/projects/${task.project_id}`, "_blank");
              }
            }}
          />
        </motion.div>
      )}

      {/* Calendar View */}
      {viewMode === "calendar" && (
        <motion.div variants={fadeIn}>
          <ScheduleCalendarView
            projects={projects}
            onProjectClick={(event) => {
              if (event.plan_id) {
                // Navigate to production plan or project
                console.log("Clicked plan:", event);
              }
            }}
          />
        </motion.div>
      )}

      {/* Resource Heat Map */}
      <ResourceHeatMap />
    </motion.div>
  );
}
