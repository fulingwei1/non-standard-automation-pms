import { useState, useEffect, useMemo } from "react";
import { useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import {
  projectApi,
  milestoneApi,
} from "../services/api";
import {
  StatsCards,
  ViewControls,
  StageColumn,
  ScheduleGanttView,
  ScheduleCalendarView,
  ResourceHeatMap
} from "../components/schedule-board";
import { mergeProjectContextFilters } from "../lib/projectContext";

const MILESTONE_HYDRATION_PROJECT_LIMIT = 12;

export default function ScheduleBoard() {
  const location = useLocation();
  const [viewMode, setViewMode] = useState("kanban"); // kanban | gantt | calendar
  const [projects, setProjects] = useState([]);
  const [_loading, setLoading] = useState(true);
  const projectListParams = useMemo(
    () => mergeProjectContextFilters(new URLSearchParams(location.search), { page_size: 100 }),
    [location.search],
  );

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
        const response = await projectApi.list(projectListParams);
        // Handle PaginatedResponse format
        const data = response.data || response;
        const projectList = data.items || data || [];
        const shouldLoadMilestones =
          Array.isArray(projectList) &&
          projectList.length <= MILESTONE_HYDRATION_PROJECT_LIMIT;

        // Transform backend project format to frontend format and load milestones/resources
        const transformedProjects = await Promise.all(
          (projectList || []).map(async (p) => {
            const projectId = p.id || p.project_code;

            // Load milestones for this project
            let milestones = [];
            if (shouldLoadMilestones) {
              try {
                const milestonesRes = await milestoneApi.list(projectId);
                const milestonesPayload = milestonesRes.data || milestonesRes || [];
                const milestonesData = Array.isArray(milestonesPayload)
                  ? milestonesPayload
                  : milestonesPayload.items || [];
                milestones = (milestonesData || []).map((m) => ({
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
            }

            // Load resources/workload for this project
            let resources = [];

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
  }, [projectListParams]);

  const totalProjects = projects?.length;
  const atRiskProjects = (projects || []).filter((p) => p.health === "H2").length;
  const blockedProjects = (projects || []).filter((p) => p.health === "H3").length;

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
            {(stages || []).map(({ stage, name }) => (
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
