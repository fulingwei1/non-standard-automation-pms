/**
 * Qualification Management - 任职资格管理主页面
 * Features: 等级管理、能力模型管理、员工任职资格管理、评估记录
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Award,
  Plus,
  UserCheck,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import { qualificationApi } from "../../services/api";
import { toast } from "../../components/ui/toast";
import { formatDate } from "../../lib/utils";
import { confirmAction } from "@/lib/confirmAction";
import { StatsCards } from "./StatsCards";
import { LevelsTab } from "./LevelsTab";
import { ModelsTab } from "./ModelsTab";
import { EmployeesTab } from "./EmployeesTab";
import { EmployeeCharts } from "./EmployeeCharts";
import { PaginationControls } from "./PaginationControls";
import { compactQueryParams } from "./queryParams";

export default function QualificationManagement() {
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total: 0
  });
  const [selectedLevels, setSelectedLevels] = useState([]);
  const [modelSearch, setModelSearch] = useState("");
  const [qualificationSearch, _setQualificationSearch] = useState("");
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("levels");
  const [_loading, setLoading] = useState(false);

  // 等级管理
  const [levels, setLevels] = useState([]);
  const [levelFilter, setLevelFilter] = useState({
    role_type: "",
    is_active: true
  });

  // 能力模型管理
  const [models, setModels] = useState([]);
  const [modelFilter, setModelFilter] = useState({
    position_type: "",
    level_id: ""
  });

  // 员工任职资格
  const [qualifications, setQualifications] = useState([]);
  const [qualificationFilter, setQualificationFilter] = useState({
    position_type: "",
    status: ""
  });

  // 统计数据
  const [stats, setStats] = useState({
    total_levels: 0,
    total_models: 0,
    total_qualifications: 0,
    pending_certifications: 0
  });

  useEffect(() => {
    loadData();
  }, [
  activeTab,
  levelFilter,
  modelFilter,
  qualificationFilter,
  pagination.page]
  );

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "levels") {
        await loadLevels();
      } else if (activeTab === "models") {
        await loadModels();
      } else if (activeTab === "employees") {
        await loadQualifications();
      }
      await loadStats();
    } catch (error) {
      console.error("加载数据失败:", error);
      toast.error("加载数据失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  const loadLevels = async () => {
    try {
      const response = await qualificationApi.getLevels({
        page: 1,
        page_size: 100,
        ...levelFilter
      });
      if (response.data?.code === 200) {
        setLevels(response.data.data?.items || []);
      }
    } catch (error) {
      console.error("加载等级列表失败:", error);
    }
  };

  const loadModels = async () => {
    try {
      const params = compactQueryParams({
        page: pagination.page,
        page_size: pagination.page_size,
        ...modelFilter
      });
      if (modelSearch) {
        params.keyword = modelSearch;
      }
      const response = await qualificationApi.getModels(params);
      if (response.data?.code === 200) {
        setModels(response.data.data?.items || []);
        setPagination((prev) => ({
          ...prev,
          total: response.data.data?.total || 0
        }));
      }
    } catch (error) {
      console.error("加载能力模型失败:", error);
    }
  };

  const loadQualifications = async () => {
    try {
      const params = compactQueryParams({
        page: pagination.page,
        page_size: pagination.page_size,
        ...qualificationFilter
      });
      if (qualificationSearch) {
        params.keyword = qualificationSearch;
      }
      const response = await qualificationApi.getEmployeeQualifications(params);
      if (response.data?.code === 200) {
        setQualifications(response.data.data?.items || []);
        setPagination((prev) => ({
          ...prev,
          total: response.data.data?.total || 0
        }));
      }
    } catch (error) {
      console.error("加载员工任职资格失败:", error);
    }
  };

  const loadStats = async () => {
    try {
      // 加载统计数据
      const [levelsRes, modelsRes, qualificationsRes] = await Promise.all([
      qualificationApi.getLevels({ page: 1, page_size: 1 }),
      qualificationApi.getModels({ page: 1, page_size: 1 }),
      qualificationApi.getEmployeeQualifications({
        page: 1,
        page_size: 1,
        status: "PENDING"
      })]
      );

      setStats({
        total_levels: levelsRes.data?.data?.total || 0,
        total_models: modelsRes.data?.data?.total || 0,
        total_qualifications: qualificationsRes.data?.data?.total || 0,
        pending_certifications: qualificationsRes.data?.data?.total || 0
      });
    } catch (error) {
      console.error("加载统计数据失败:", error);
    }
  };

  const handleDeleteLevel = async (id) => {
    if (!await confirmAction("确定要删除该等级吗？")) {return;}

    try {
      await qualificationApi.deleteLevel(id);
      toast.success("等级删除成功");
      loadLevels();
    } catch (error) {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  };

  const handleExportModels = () => {
    try {
      const exportData = (models || []).map((model) => ({
        岗位类型: model.position_type,
        岗位子类型: model.position_subtype || "-",
        等级: model.level?.level_name || model.level_id,
        状态: model.is_active ? "启用" : "停用",
        创建时间: model.created_at ? formatDate(model.created_at) : "-"
      }));

      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
      headers.join(","),
      ...(exportData || []).map((row) =>
      (headers || []).map((header) => `"${row[header] || ""}"`).join(",")
      )].
      join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;"
      });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `能力模型列表_${new Date().toISOString().split("T")[0]}.csv`
      );
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success("导出成功");
    } catch (error) {
      console.error("导出失败:", error);
      toast.error("导出失败");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="任职资格管理"
        description="管理任职资格等级、能力模型和员工认证"
        icon={Award} />


      {/* 统计卡片 */}
      <StatsCards stats={stats} />

      {/* 主要内容区域 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>任职资格管理</CardTitle>
              <CardDescription>管理等级、能力模型和员工认证</CardDescription>
            </div>
            <div className="flex gap-2">
              {activeTab === "levels" &&
              <Button onClick={() => navigate("/qualifications/levels/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建等级
              </Button>
              }
              {activeTab === "models" &&
              <Button onClick={() => navigate("/qualifications/models/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建能力模型
              </Button>
              }
              {activeTab === "employees" &&
              <Button
                onClick={() => navigate("/qualifications/employees/certify")}>

                  <UserCheck className="h-4 w-4 mr-2" />
                  认证员工
              </Button>
              }
              {activeTab === "levels" &&
              <Button onClick={() => navigate("/qualifications/levels/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建等级
              </Button>
              }
              {activeTab === "models" &&
              <Button onClick={() => navigate("/qualifications/models/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建能力模型
              </Button>
              }
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full">

            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="levels">等级管理</TabsTrigger>
              <TabsTrigger value="models">能力模型</TabsTrigger>
              <TabsTrigger value="employees">员工认证</TabsTrigger>
            </TabsList>

            {/* 等级管理 */}
            <TabsContent value="levels" className="space-y-4">
              <LevelsTab
                levels={levels}
                levelFilter={levelFilter}
                setLevelFilter={setLevelFilter}
                selectedLevels={selectedLevels}
                setSelectedLevels={setSelectedLevels}
                onDeleteLevel={handleDeleteLevel}
              />
            </TabsContent>

            {/* 能力模型管理 */}
            <TabsContent value="models" className="space-y-4">
              <ModelsTab
                models={models}
                modelFilter={modelFilter}
                setModelFilter={setModelFilter}
                modelSearch={modelSearch}
                setModelSearch={setModelSearch}
                setPagination={setPagination}
                loadModels={loadModels}
                onExportModels={handleExportModels}
              />
            </TabsContent>

            {/* 员工认证管理 */}
            <TabsContent value="employees" className="space-y-4">
              <EmployeesTab
                qualifications={qualifications}
                qualificationFilter={qualificationFilter}
                setQualificationFilter={setQualificationFilter}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* 可视化图表区域 */}
      {activeTab === "employees" && qualifications.length > 0 &&
      <EmployeeCharts qualifications={qualifications} />
      }

      {/* 分页 */}
      <PaginationControls pagination={pagination} setPagination={setPagination} />
    </div>);

}
