import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { pmoApi, projectApi } from "../services/api";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Input,
} from "../components/ui";
import {
  Plus,
  Search,
  ArrowRight,
  XCircle,
} from "lucide-react";
import { staggerContainer } from "../lib/animations";
import {
  RiskList,
  CreateRiskDialog,
  AssessRiskDialog,
  ResponseRiskDialog,
  StatusRiskDialog,
  CloseRiskDialog,
  RiskDetailDialog
} from "../components/risk-management";

export default function RiskManagement() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [project, setProject] = useState(null);
  const [risks, setRisks] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(
    projectId ? parseInt(projectId) : null,
  );
  const [projectSearch, setProjectSearch] = useState("");
  const [projectList, setProjectList] = useState([]);
  const [showProjectSelect, setShowProjectSelect] = useState(!projectId);
  const [statusFilter, setStatusFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState("");

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [assessDialog, setAssessDialog] = useState({
    open: false,
    riskId: null,
  });
  const [responseDialog, setResponseDialog] = useState({
    open: false,
    riskId: null,
  });
  const [statusDialog, setStatusDialog] = useState({
    open: false,
    riskId: null,
  });
  const [closeDialog, setCloseDialog] = useState({ open: false, riskId: null });
  const [detailDialog, setDetailDialog] = useState({ open: false, risk: null });

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectData();
      fetchRisks();
    } else {
      fetchProjectList();
    }
  }, [selectedProjectId, statusFilter, levelFilter]);

  const fetchProjectData = async () => {
    if (!selectedProjectId) {
      return;
    }
    try {
      const res = await projectApi.get(selectedProjectId);
      const data = res.data || res;
      setProject(data);
    } catch (err) {
      console.error("Failed to fetch project:", err);
      setError(err.response?.data?.detail || err.message || "加载项目信息失败");
    }
  };

  const fetchRisks = async () => {
    if (!selectedProjectId) {
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter) {
        params.status = statusFilter;
      }
      if (levelFilter) {
        params.risk_level = levelFilter;
      }
      const res = await pmoApi.risks.list(selectedProjectId, params);
      const data = res.data || res;
      setRisks(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to fetch risks:", err);
      setError(err.response?.data?.detail || err.message || "加载风险数据失败");
      setRisks([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectList = async () => {
    try {
      const res = await projectApi.list({
        page: 1,
        page_size: 50,
        keyword: projectSearch,
      });
      const data = res.data || res;
      // Handle PaginatedResponse format
      if (data && typeof data === "object" && "items" in data) {
        setProjectList(data.items || []);
      } else if (Array.isArray(data)) {
        setProjectList(data);
      } else {
        setProjectList([]);
      }
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setProjectList([]);
    }
  };

  const handleCreate = async (formData) => {
    try {
      await pmoApi.risks.create(selectedProjectId, formData);
      setCreateDialogOpen(false);
      fetchRisks();
    } catch (err) {
      console.error("Failed to create risk:", err);
      alert("创建失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleAssess = async (riskId, data) => {
    try {
      await pmoApi.risks.assess(riskId, data);
      setAssessDialog({ open: false, riskId: null });
      fetchRisks();
    } catch (err) {
      console.error("Failed to assess risk:", err);
      alert("评估失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleResponse = async (riskId, data) => {
    try {
      await pmoApi.risks.response(riskId, data);
      setResponseDialog({ open: false, riskId: null });
      fetchRisks();
    } catch (err) {
      console.error("Failed to update response:", err);
      alert("更新失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleStatusUpdate = async (riskId, data) => {
    try {
      await pmoApi.risks.updateStatus(riskId, data);
      setStatusDialog({ open: false, riskId: null });
      fetchRisks();
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("更新失败: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleClose = async (riskId, data) => {
    try {
      await pmoApi.risks.close(riskId, data);
      setCloseDialog({ open: false, riskId: null });
      fetchRisks();
    } catch (err) {
      console.error("Failed to close risk:", err);
      alert("关闭失败: " + (err.response?.data?.detail || err.message));
    }
  };

  if (showProjectSelect) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
      >
        <PageHeader title="风险管理" description="选择项目以管理其风险" />

        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <div className="mb-4">
              <Input
                placeholder="搜索项目名称或编码..."
                value={projectSearch || "unknown"}
                onChange={(e) => {
                  setProjectSearch(e.target.value);
                  fetchProjectList();
                }}
                className="w-full"
                icon={Search}
              />
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(projectList || []).map((proj) => (
                <div
                  key={proj.id}
                  onClick={() => {
                    setSelectedProjectId(proj.id);
                    setShowProjectSelect(false);
                    navigate(`/pmo/risks/${proj.id}`);
                  }}
                  className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 cursor-pointer transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-white">
                        {proj.project_name}
                      </h3>
                      <p className="text-sm text-slate-400">
                        {proj.project_code}
                      </p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-500" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title="风险管理"
        description={
          project ? `${project.project_name} - 项目风险管理` : "项目风险管理"
        }
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowProjectSelect(true);
                navigate("/pmo/risks");
              }}
            >
              选择项目
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              新建风险
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={statusFilter || "unknown"}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部状态</option>
              <option value="IDENTIFIED">已识别</option>
              <option value="ANALYZING">分析中</option>
              <option value="RESPONDING">应对中</option>
              <option value="MONITORING">监控中</option>
              <option value="CLOSED">已关闭</option>
            </select>
            <select
              value={levelFilter || "unknown"}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部等级</option>
              <option value="CRITICAL">严重</option>
              <option value="HIGH">高</option>
              <option value="MEDIUM">中</option>
              <option value="LOW">低</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="mb-6 border-red-500/30 bg-red-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-400">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setError(null);
                  if (selectedProjectId) {
                    fetchProjectData();
                    fetchRisks();
                  }
                }}
                className="border-red-500/30 text-red-400 hover:bg-red-500/20"
              >
                重试
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <RiskList
        loading={loading}
        error={null}
        risks={risks}
        onRetry={() => {
          setError(null);
          if (selectedProjectId) {
            fetchProjectData();
            fetchRisks();
          }
        }}
        onAssess={(riskId) => setAssessDialog({ open: true, riskId })}
        onResponse={(riskId) => setResponseDialog({ open: true, riskId })}
        onStatusUpdate={(riskId) => setStatusDialog({ open: true, riskId })}
        onClose={(riskId) => setCloseDialog({ open: true, riskId })}
        onDetail={(risk) => setDetailDialog({ open: true, risk })}
      />

      {/* Create Dialog */}
      <CreateRiskDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate}
      />

      {/* Assess Dialog */}
      <AssessRiskDialog
        open={assessDialog.open}
        onOpenChange={(open) => setAssessDialog({ open, riskId: null })}
        onSubmit={(data) => handleAssess(assessDialog.riskId, data)}
      />

      {/* Response Dialog */}
      <ResponseRiskDialog
        open={responseDialog.open}
        onOpenChange={(open) => setResponseDialog({ open, riskId: null })}
        onSubmit={(data) => handleResponse(responseDialog.riskId, data)}
      />

      {/* Status Dialog */}
      <StatusRiskDialog
        open={statusDialog.open}
        onOpenChange={(open) => setStatusDialog({ open, riskId: null })}
        onSubmit={(data) => handleStatusUpdate(statusDialog.riskId, data)}
      />

      {/* Close Dialog */}
      <CloseRiskDialog
        open={closeDialog.open}
        onOpenChange={(open) => setCloseDialog({ open, riskId: null })}
        onSubmit={(data) => handleClose(closeDialog.riskId, data)}
      />

      {/* Detail Dialog */}
      <RiskDetailDialog
        open={detailDialog.open}
        onOpenChange={(open) => setDetailDialog({ open, risk: null })}
        risk={detailDialog.risk}
      />
    </motion.div>
  );
}
