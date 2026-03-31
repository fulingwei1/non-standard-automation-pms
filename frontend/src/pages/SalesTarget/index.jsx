/**
 * Sales Target Management Page
 * Features: Create sales targets (personal/team/department), Track progress, View target statistics
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { salesTargetApi, salesTeamApi } from "../../services/api";
import { toast } from "sonner";
import { parseMeta, buildDescriptionWithMeta, generatePeriodValue } from "./utils";
import TargetFilters from "./TargetFilters";
import SummaryCards from "./SummaryCards";
import AggregationView from "./AggregationView";
import TargetList from "./TargetList";
import CreateTargetDialog from "./CreateTargetDialog";
import EditTargetDialog from "./EditTargetDialog";

export default function SalesTarget() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    target_scope: "",
    target_type: "",
    target_period: "",
    status: "",
  });
  const [aggregationMode, setAggregationMode] = useState("organization");

  const currentUserId = useMemo(() => {
    try {
      const raw = localStorage.getItem("user");
      if (!raw) {return null;}
      const parsed = JSON.parse(raw);
      return parsed?.id ? Number(parsed.id) : null;
    } catch {
      return null;
    }
  }, []);

  // Form state
  const [formData, setFormData] = useState({
    target_scope: "PERSONAL",
    user_id: currentUserId,
    department_id: null,
    team_id: null,
    target_type: "CONTRACT_AMOUNT",
    target_period: "MONTHLY",
    period_value: "",
    target_value: "",
    manager_group: "",
    director_group: "",
    industry: "",
    region: "",
    target_customer: "",
    description: "",
  });

  // Fetch targets
  useEffect(() => {
    loadTargets();
  }, [filters]);

  const loadTargets = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 100,
        ...filters,
      };
      const res = await salesTargetApi.list(params);
      if (res.data?.items) {
        setTargets(res.data.items);
      }
    } catch (err) {
      console.error("Failed to load targets:", err);
      toast.error("加载目标列表失败");
    } finally {
      setLoading(false);
    }
  };

  // Load team members for selection
  const [teamMembers, setTeamMembers] = useState([]);
  useEffect(() => {
    const loadTeamMembers = async () => {
      try {
        const res = await salesTeamApi.getTeam();
        if (res.data?.team_members) {
          setTeamMembers(res.data.team_members);
        }
      } catch (err) {
        console.error("Failed to load team members:", err);
      }
    };
    loadTeamMembers();
  }, []);

  useEffect(() => {
    if (formData.target_scope !== "PERSONAL") {return;}
    if (formData.user_id) {return;}

    const firstMemberId = (teamMembers || [])[0]?.user_id;
    const fallbackId = firstMemberId || currentUserId;
    if (!fallbackId) {return;}

    setFormData((prev) => ({
      ...prev,
      user_id: Number(fallbackId),
    }));
  }, [formData.target_scope, formData.user_id, teamMembers, currentUserId]);

  // Update period value when period type changes
  useEffect(() => {
    if (formData.target_period) {
      setFormData((prev) => ({
        ...prev,
        period_value: generatePeriodValue(formData.target_period),
      }));
    }
  }, [formData.target_period]);

  const normalizedTargets = useMemo(() => (targets || []).map((t) => {
    const meta = parseMeta(t.description);
    const targetValue = Number(t.target_value || 0);
    const actualValue = Number(t.actual_value || meta.actual_value || 0);
    const completionRate = Number(t.completion_rate || (targetValue > 0 ? (actualValue / targetValue) * 100 : 0));
    return {
      ...t,
      meta,
      actual_value: actualValue,
      completion_rate: completionRate,
    };
  }), [targets]);

  const summaryCards = useMemo(() => {
    const sum = (arr, key) => arr.reduce((acc, cur) => acc + Number(cur[key] || 0), 0);
    const pick = (label, fn) => {
      const list = normalizedTargets.filter(fn);
      const targetValue = sum(list, "target_value");
      const actualValue = sum(list, "actual_value");
      const completion = targetValue > 0 ? (actualValue / targetValue) * 100 : 0;
      return { label, targetValue, actualValue, completion, count: list.length };
    };
    return [
      pick("个人", (t) => t.target_scope === "PERSONAL"),
      pick("项目经理组", (t) => (t.meta.manager_group || "") !== ""),
      pick("总监组", (t) => (t.meta.director_group || "") !== ""),
      pick("总目标", () => true),
    ];
  }, [normalizedTargets]);

  const aggregationRows = useMemo(() => {
    const grouped = new Map();
    const getKey = (t) => {
      if (aggregationMode === "organization") {
        return t.user_name || t.department_name || t.meta.manager_group || t.meta.director_group || "未分配";
      }
      if (aggregationMode === "industry") {return t.meta.industry || "未分类行业";}
      if (aggregationMode === "region") {return t.meta.region || "未分类大区";}
      if (aggregationMode === "target_customer") {return t.meta.target_customer || "未分类客户";}
      return "未分类";
    };

    normalizedTargets.forEach((t) => {
      const k = getKey(t);
      const prev = grouped.get(k) || {
        key: k,
        targetValue: 0,
        actualValue: 0,
        count: 0,
      };
      prev.targetValue += Number(t.target_value || 0);
      prev.actualValue += Number(t.actual_value || 0);
      prev.count += 1;
      grouped.set(k, prev);
    });

    return Array.from(grouped.values())
      .map((row) => ({
        ...row,
        completion: row.targetValue > 0 ? (row.actualValue / row.targetValue) * 100 : 0,
      }))
      .sort((a, b) => b.targetValue - a.targetValue);
  }, [aggregationMode, normalizedTargets]);

  const handleCreate = async () => {
    const normalizedTargetValue = Number(formData.target_value || 0);
    if (normalizedTargetValue <= 0) {
      toast.error("目标值必须大于 0");
      return;
    }

    if (formData.target_scope === "PERSONAL" && !formData.user_id) {
      toast.error("个人目标必须选择负责人");
      return;
    }

    if (formData.target_scope === "DEPARTMENT" && !formData.department_id) {
      toast.error("部门目标必须选择部门");
      return;
    }

    try {
      const payload = {
        ...formData,
        target_value: normalizedTargetValue,
        user_id:
          formData.target_scope === "PERSONAL"
            ? Number(formData.user_id)
            : formData.user_id,
        description: buildDescriptionWithMeta(formData.description, {
          manager_group: formData.manager_group,
          director_group: formData.director_group,
          industry: formData.industry,
          region: formData.region,
          target_customer: formData.target_customer,
        }),
      };
      await salesTargetApi.create(payload);
      toast.success("创建目标成功");
      setShowCreateDialog(false);
      resetForm();
      loadTargets();
    } catch (err) {
      console.error("Failed to create target:", err);
      const detail = err?.response?.data?.detail;
      toast.error(detail || err.response?.data?.message || "创建目标失败");
    }
  };

  const handleUpdate = async () => {
    if (!selectedTarget) {return;}
    try {
      await salesTargetApi.update(selectedTarget.id, {
        target_value: formData.target_value,
        description: formData.description,
        status: formData.status,
      });
      toast.success("更新目标成功");
      setShowEditDialog(false);
      setSelectedTarget(null);
      resetForm();
      loadTargets();
    } catch (err) {
      console.error("Failed to update target:", err);
      toast.error(err.response?.data?.message || "更新目标失败");
    }
  };

  const handleEdit = (target) => {
    setSelectedTarget(target);
    setFormData({
      target_scope: target.target_scope,
      user_id: target.user_id,
      department_id: target.department_id,
      team_id: target.team_id,
      target_type: target.target_type,
      target_period: target.target_period,
      period_value: target.period_value,
      target_value: target.target_value,
      manager_group: parseMeta(target.description).manager_group || "",
      director_group: parseMeta(target.description).director_group || "",
      industry: parseMeta(target.description).industry || "",
      region: parseMeta(target.description).region || "",
      target_customer: parseMeta(target.description).target_customer || "",
      description: (target.description || "").split("[meta]")[0].trim(),
      status: target.status,
    });
    setShowEditDialog(true);
  };

  const resetForm = () => {
    setFormData({
      target_scope: "PERSONAL",
      user_id: currentUserId,
      department_id: null,
      team_id: null,
      target_type: "CONTRACT_AMOUNT",
      target_period: "MONTHLY",
      period_value: generatePeriodValue("MONTHLY"),
      target_value: "",
      manager_group: "",
      director_group: "",
      industry: "",
      region: "",
      target_customer: "",
      description: "",
    });
  };

  const filteredTargets = useMemo(() => {
    let result = normalizedTargets;
    if (searchTerm) {
      result = (result || []).filter(
        (t) =>
          (t.user_name || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (t.department_name || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (t.period_value || "").includes(searchTerm),
      );
    }
    return result;
  }, [normalizedTargets, searchTerm]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="销售目标"
        description="创建和管理销售目标，跟踪目标完成进度"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button
              className="flex items-center gap-2"
              onClick={() => {
                resetForm();
                setShowCreateDialog(true);
              }}
            >
              <Plus className="w-4 h-4" />
              创建目标
            </Button>
          </motion.div>
        }
      />

      {/* Filters */}
      <TargetFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        filters={filters}
        setFilters={setFilters}
      />

      {/* Summary Cards */}
      <SummaryCards summaryCards={summaryCards} />

      {/* Aggregation View */}
      <AggregationView
        aggregationMode={aggregationMode}
        setAggregationMode={setAggregationMode}
        aggregationRows={aggregationRows}
      />

      {/* Targets List */}
      <TargetList
        filteredTargets={filteredTargets}
        loading={loading}
        onEdit={handleEdit}
      />

      {/* Create Dialog */}
      <CreateTargetDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        setFormData={setFormData}
        teamMembers={teamMembers}
        onCreate={handleCreate}
      />

      {/* Edit Dialog */}
      <EditTargetDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        setFormData={setFormData}
        onUpdate={handleUpdate}
      />
    </motion.div>
  );
}
