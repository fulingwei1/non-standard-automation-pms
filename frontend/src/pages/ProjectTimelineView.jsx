/**
 * Project Timeline View - 项目时间轴视图
 *
 * 使用可拖拽时间轴展示项目进度
 * 支持拖拽调整项目/阶段的起止日期
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, List, Calendar } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ProjectTimeline } from "@/components/project/timeline";
import { projectApi, stageApi } from "@/services/api";

export default function ProjectTimelineView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [viewMode, setViewMode] = useState("timeline"); // "timeline" | "list"

  // 获取项目列表（带阶段和里程碑）
  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);

      // 如果有项目 ID，只获取单个项目
      if (id) {
        const projectRes = await projectApi.get(id);
        const project = projectRes.data || projectRes;

        // 获取项目阶段
        const stagesRes = await stageApi.list(id);
        project.stages = stagesRes.data?.items || stagesRes.items || [];

        // 获取里程碑（如果有 API）
        // const milestonesRes = await milestoneApi.list(id);
        // project.milestones = milestonesRes.data?.items || [];

        setProjects([project]);
      } else {
        // 获取所有项目
        const res = await projectApi.list({ page_size: 50 });
        const projectList = res.data?.items || res.items || [];

        // 为每个项目获取阶段数据
        const projectsWithDetails = await Promise.all(
          projectList.map(async (project) => {
            try {
              const stagesRes = await stageApi.list(project.id);
              project.stages = stagesRes.data?.items || stagesRes.items || [];
            } catch {
              project.stages = [];
            }
            return project;
          })
        );

        setProjects(projectsWithDetails);
      }
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      toast.error("加载项目数据失败");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 处理项目日期更新
  const handleProjectUpdate = async (projectId, updates) => {
    try {
      await projectApi.update(projectId, {
        planned_start_date: updates.start_date?.toISOString().split("T")[0],
        planned_end_date: updates.end_date?.toISOString().split("T")[0],
      });

      toast.success("项目日期已更新");

      // 更新本地状态
      setProjects((prev) =>
        prev.map((p) =>
          p.id === projectId
            ? {
                ...p,
                planned_start_date: updates.start_date,
                planned_end_date: updates.end_date,
              }
            : p
        )
      );
    } catch (error) {
      console.error("Failed to update project:", error);
      toast.error("更新项目日期失败");
    }
  };

  // 处理阶段日期更新
  const handleStageUpdate = async (projectId, stageId, updates) => {
    try {
      await stageApi.update(projectId, stageId, {
        planned_start_date: updates.start_date?.toISOString().split("T")[0],
        planned_end_date: updates.end_date?.toISOString().split("T")[0],
      });

      toast.success("阶段日期已更新");

      // 更新本地状态
      setProjects((prev) =>
        prev.map((p) =>
          p.id === projectId
            ? {
                ...p,
                stages: p.stages.map((s) =>
                  s.id === stageId
                    ? {
                        ...s,
                        planned_start_date: updates.start_date,
                        planned_end_date: updates.end_date,
                      }
                    : s
                ),
              }
            : p
        )
      );
    } catch (error) {
      console.error("Failed to update stage:", error);
      toast.error("更新阶段日期失败");
    }
  };

  // 处理双击事件（打开详情）
  const handleItemDoubleClick = (type, item, project) => {
    if (type === "project") {
      navigate(`/projects/${item.id}`);
    } else if (type === "stage") {
      navigate(`/projects/${project.id}/stages/${item.id}`);
    } else if (type === "milestone") {
      // 打开里程碑详情
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* 页头 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {id && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/projects/${id}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
          )}
          <PageHeader
            title={id ? "项目时间轴" : "项目总览时间轴"}
            description="可拖拽调整项目和阶段的时间安排"
          />
        </div>

        <div className="flex items-center gap-2">
          {/* 视图切换 */}
          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
            <Button
              variant={viewMode === "timeline" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("timeline")}
            >
              <Calendar className="w-4 h-4 mr-1" />
              时间轴
            </Button>
            <Button
              variant={viewMode === "list" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
            >
              <List className="w-4 h-4 mr-1" />
              列表
            </Button>
          </div>

          <Button variant="outline" onClick={fetchProjects}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 内容区 */}
      {loading ? (
        <Card>
          <CardContent className="py-16">
            <div className="text-center text-slate-400">加载中...</div>
          </CardContent>
        </Card>
      ) : viewMode === "timeline" ? (
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <ProjectTimeline
              projects={projects}
              onProjectUpdate={handleProjectUpdate}
              onStageUpdate={handleStageUpdate}
              onItemDoubleClick={handleItemDoubleClick}
              showStages={true}
              showMilestones={true}
              className="h-[calc(100vh-200px)]"
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>项目列表</CardTitle>
          </CardHeader>
          <CardContent>
            {/* 列表视图内容 - 可以使用现有的 ProjectList 组件 */}
            <div className="text-slate-400">列表视图</div>
          </CardContent>
        </Card>
      )}

      {/* 使用说明 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">操作说明</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-500 space-y-1">
          <p>• <strong>拖拽中间</strong>：整体移动项目/阶段时间（保持工期不变）</p>
          <p>• <strong>拖拽左边缘</strong>：调整开始日期</p>
          <p>• <strong>拖拽右边缘</strong>：调整结束日期</p>
          <p>• <strong>双击</strong>：打开详情页面</p>
          <p>• <strong>滚轮 + 鼠标移动</strong>：左右滚动时间轴</p>
        </CardContent>
      </Card>
    </div>
  );
}
