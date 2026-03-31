import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { rdProjectApi, projectApi } from "../../services/api";
import { formatCurrency } from "../../lib/utils";
import {
  Button,
  Skeleton,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../../components/ui";
import {
  DollarSign,
  Clock,
  Users,
  Calculator,
  AlertCircle,
} from "lucide-react";
import { fadeIn, tabs, statusMap, categoryTypeMap } from "./constants";
import ProjectHeader from "./ProjectHeader";
import StatCards from "./StatCards";
import OverviewTab from "./OverviewTab";
import CostsTab from "./CostsTab";
import TimesheetTab from "./TimesheetTab";
import WorklogsTab from "./WorklogsTab";
import DocumentsTab from "./DocumentsTab";
import ReportsTab from "./ReportsTab";

export default function RdProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [costs, setCosts] = useState([]);
  const [costSummary, setCostSummary] = useState(null);
  const [timesheetSummary, setTimesheetSummary] = useState(null);
  const [linkedProject, setLinkedProject] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    if (id) {
      fetchProject();
      if (activeTab === "costs") {
        fetchCosts();
        fetchCostSummary();
      } else if (activeTab === "timesheet") {
        fetchTimesheetSummary();
      }
    }
  }, [id, activeTab]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const response = await rdProjectApi.get(id);
      const projectData = response.data?.data || response.data || response;
      setProject(projectData);

      // 如果有关联的非标项目，获取项目信息
      if (projectData.linked_project_id) {
        try {
          const linkedRes = await projectApi.get(projectData.linked_project_id);
          setLinkedProject(linkedRes.data?.data || linkedRes.data || linkedRes);
        } catch (err) {
          console.error("Failed to fetch linked project:", err);
        }
      }
    } catch (err) {
      console.error("Failed to fetch project:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCosts = async () => {
    try {
      const response = await rdProjectApi.getCosts({
        rd_project_id: id,
        page_size: 100,
      });
      const data = response.data || response;
      setCosts(data.items || data || []);
    } catch (err) {
      console.error("Failed to fetch costs:", err);
      setCosts([]);
    }
  };

  const fetchCostSummary = async () => {
    try {
      const response = await rdProjectApi.getCostSummary(id);
      const data = response.data?.data || response.data || response;
      setCostSummary(data);
    } catch (err) {
      console.error("Failed to fetch cost summary:", err);
    }
  };

  const fetchTimesheetSummary = async () => {
    try {
      const response = await rdProjectApi.getTimesheetSummary(id);
      const data = response.data?.data || response.data || response;
      setTimesheetSummary(data);
    } catch (err) {
      console.error("Failed to fetch timesheet summary:", err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">研发项目不存在</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/rd-projects")}
        >
          返回列表
        </Button>
      </div>
    );
  }

  const status = statusMap[project.status] || statusMap.DRAFT;
  const categoryType =
    categoryTypeMap[project.category_type] || categoryTypeMap.SELF;

  // Stat cards for overview
  const statCards = [
    {
      label: "预算金额",
      value: formatCurrency(project.budget_amount || 0),
      icon: DollarSign,
      color: "primary",
    },
    {
      label: "已归集费用",
      value: formatCurrency(project.total_cost || 0),
      icon: Calculator,
      color: "emerald",
      subtext: costSummary
        ? `人工: ${formatCurrency(costSummary.labor_cost || 0)}`
        : undefined,
    },
    {
      label: "总工时",
      value: project.total_hours
        ? `${project.total_hours.toFixed(1)} 小时`
        : "0 小时",
      icon: Clock,
      color: "indigo",
      subtext: timesheetSummary
        ? `${timesheetSummary.total_participants || 0} 人参与`
        : undefined,
    },
    {
      label: "参与人数",
      value: project.participant_count || 0,
      icon: Users,
      color: "amber",
    },
  ];

  return (
    <motion.div initial="hidden" animate="visible" variants={fadeIn}>
      <ProjectHeader
        project={project}
        status={status}
        categoryType={categoryType}
      />

      <StatCards statCards={statCards} />

      {/* Tabs */}
      <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-6">
          {(tabs || []).map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className="flex items-center gap-2"
            >
              <tab.icon className="h-4 w-4"  />
              {tab.name}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <OverviewTab
            project={project}
            linkedProject={linkedProject}
            status={status}
            categoryType={categoryType}
            id={id}
          />
        </TabsContent>

        <TabsContent value="costs" className="space-y-6">
          <CostsTab id={id} costs={costs} costSummary={costSummary} />
        </TabsContent>

        <TabsContent value="timesheet" className="space-y-6">
          <TimesheetTab project={project} timesheetSummary={timesheetSummary} />
        </TabsContent>

        <TabsContent value="worklogs" className="space-y-6">
          <WorklogsTab id={id} />
        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          <DocumentsTab id={id} />
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          <ReportsTab id={id} />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
