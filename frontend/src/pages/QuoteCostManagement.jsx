import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Calculator,
  CheckCircle2,
  Layers,
  Search
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from "../components/ui";
import { staggerContainer } from "../lib/animations";
import { quoteApi, salesTemplateApi } from "../services/api";

import {
  CostOverview,
  CostBreakdown,
  CostCheck,
  CostApproval,
  ApplyTemplateDialog,
  SubmitApprovalDialog,
  CostSuggestionsDialog
} from "../components/quote-cost-management";

export default function QuoteCostManagement() {
  const [costSuggestions, setCostSuggestions] = useState(null);
  const [editedSuggestions, setEditedSuggestions] = useState({});
  const [showSuggestionsDialog, setShowSuggestionsDialog] = useState(false);
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [version, setVersion] = useState(null);
  const [items, setItems] = useState([]);
  const [costCheck, setCostCheck] = useState(null);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [costTemplates, setCostTemplates] = useState([]);

  // Dialog states
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Form states
  const [approvalData, setApprovalData] = useState({
    approval_level: 1,
    comment: ""
  });

  // Group items by category
  const groupedItems = useMemo(() => {
    const groups = {};
    items.forEach((item) => {
      const category = item.cost_category || "其他";
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(item);
    });
    return groups;
  }, [items]);

  // Calculate totals
  const totals = useMemo(() => {
    const totalPrice = items.reduce(
      (sum, item) =>
        sum + parseFloat(item.unit_price || 0) * parseFloat(item.qty || 0),
      0
    );
    const totalCost = items.reduce(
      (sum, item) =>
        sum + parseFloat(item.cost || 0) * parseFloat(item.qty || 0),
      0
    );
    const grossMargin =
      totalPrice > 0 ? ((totalPrice - totalCost) / totalPrice) * 100 : 0;
    return { totalPrice, totalCost, grossMargin };
  }, [items]);

  // Margin status
  const marginStatus = useMemo(() => {
    if (totals.grossMargin >= 20) {
      return {
        label: "正常",
        color: "bg-green-500",
        textColor: "text-green-400"
      };
    }
    if (totals.grossMargin >= 15) {
      return {
        label: "警告",
        color: "bg-amber-500",
        textColor: "text-amber-400"
      };
    }
    return { label: "风险", color: "bg-red-500", textColor: "text-red-400" };
  }, [totals.grossMargin]);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load quote
      const quoteRes = await quoteApi.get(id);
      setQuote(quoteRes.data?.data || quoteRes.data);

      // Load current version
      const quoteData = quoteRes.data?.data || quoteRes.data;
      if (quoteData.current_version_id) {
        const versionsRes = await quoteApi.getVersions(id);
        const versions = versionsRes.data?.data || versionsRes.data || [];
        const currentVersion =
          versions.find((v) => v.id === quoteData.current_version_id) ||
          versions[0];
        setVersion(currentVersion);

        // Load items from separate API
        try {
          const itemsRes = await quoteApi.getItems(id, currentVersion.id);
          const itemsList = itemsRes.data?.data || itemsRes.data || [];
          setItems(itemsList);
        } catch (_e) {
          // Fallback to version.items if API not available
          if (currentVersion.items) {
            setItems(currentVersion.items);
          }
        }
      }

      // Load cost check
      try {
        const checkRes = await quoteApi.checkCost(id);
        setCostCheck(checkRes.data?.data || checkRes.data);
      } catch (e) {
        console.log("Cost check not available:", e);
      }

      // Load approval history
      try {
        const historyRes = await quoteApi.getCostApprovalHistory(id);
        setApprovalHistory(historyRes.data?.data || historyRes.data || []);
      } catch (e) {
        console.log("Approval history not available:", e);
      }

      // Load cost templates
      try {
        const templatesRes = await salesTemplateApi.listCostTemplates({
          page: 1,
          page_size: 100,
          is_active: true
        });
        const templates =
          templatesRes.data?.data?.items || templatesRes.data?.items || [];
        setCostTemplates(templates);
      } catch (e) {
        console.log("Cost templates not available:", e);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate) {
      return;
    }

    try {
      setLoading(true);
      await quoteApi.applyCostTemplate(
        id,
        selectedTemplate.id,
        version?.id,
        {}
      );
      await loadData();
      setShowTemplateDialog(false);
      setSelectedTemplate(null);
    } catch (error) {
      console.error("应用模板失败:", error);
      alert("应用模板失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateCost = async () => {
    try {
      setLoading(true);
      await quoteApi.calculateCost(id, version?.id);
      await loadData();
    } catch (error) {
      console.error("计算成本失败:", error);
      alert("计算成本失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCheckCost = async () => {
    try {
      setLoading(true);
      const res = await quoteApi.checkCost(id, version?.id);
      setCostCheck(res.data?.data || res.data);
    } catch (error) {
      console.error("成本检查失败:", error);
      alert("成本检查失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitApproval = async () => {
    try {
      setLoading(true);
      await quoteApi.submitCostApproval(id, {
        quote_version_id: version?.id,
        ...approvalData
      });
      await loadData();
      setShowApprovalDialog(false);
      setApprovalData({ approval_level: 1, comment: "" });
    } catch (error) {
      console.error("提交审批失败:", error);
      alert("提交审批失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleItemChange = (itemId, field, value) => {
    setItems(
      items.map((item) =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    );
  };

  const handleAutoMatchCost = async () => {
    if (!version) {
      alert("请先选择报价版本");
      return;
    }

    try {
      setLoading(true);
      const res = await quoteApi.getCostMatchSuggestions(id, version.id);

      const suggestions = res.data?.data || res.data;
      if (suggestions) {
        setCostSuggestions(suggestions);
        // 初始化编辑状态
        const edited = {};
        suggestions.suggestions?.forEach((s) => {
          edited[s.item_id] = {
            cost: s.suggested_cost || s.current_cost,
            specification: s.suggested_specification,
            unit: s.suggested_unit,
            lead_time_days: s.suggested_lead_time_days,
            cost_category: s.suggested_cost_category
          };
        });
        setEditedSuggestions(edited);
        setShowSuggestionsDialog(true);
      }
    } catch (error) {
      console.error("获取成本建议失败:", error);
      alert(
        "获取成本建议失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApplySuggestions = async () => {
    if (!costSuggestions || !version) {
      return;
    }

    try {
      setLoading(true);

      // 准备应用数据
      const applyData = {
        suggestions: costSuggestions.suggestions.map((s) => ({
          item_id: s.item_id,
          cost:
            editedSuggestions[s.item_id]?.cost ||
            s.suggested_cost ||
            s.current_cost,
          specification:
            editedSuggestions[s.item_id]?.specification ||
            s.suggested_specification,
          unit: editedSuggestions[s.item_id]?.unit || s.suggested_unit,
          lead_time_days:
            editedSuggestions[s.item_id]?.lead_time_days ||
            s.suggested_lead_time_days,
          cost_category:
            editedSuggestions[s.item_id]?.cost_category ||
            s.suggested_cost_category
        }))
      };

      await quoteApi.applyCostSuggestions(id, version.id, applyData);

      setShowSuggestionsDialog(false);
      setCostSuggestions(null);
      setEditedSuggestions({});

      // 重新加载数据
      await loadData();

      alert("成本建议已应用！");
    } catch (error) {
      console.error("应用成本建议失败:", error);
      alert(
        "应用成本建议失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionChange = (itemId, field, value) => {
    setEditedSuggestions({
      ...editedSuggestions,
      [itemId]: {
        ...editedSuggestions[itemId],
        [field]: value
      }
    });
  };

  const handleSaveItems = async () => {
    if (!version) {
      alert("请先选择报价版本");
      return;
    }

    try {
      setLoading(true);

      // 准备批量更新数据
      const batchData = {
        items: items.map((item) => ({
          id: item.id,
          item_type: item.item_type,
          item_name: item.item_name,
          qty: item.qty ? parseFloat(item.qty) : null,
          unit_price: item.unit_price ? parseFloat(item.unit_price) : null,
          cost: item.cost ? parseFloat(item.cost) : null,
          lead_time_days: item.lead_time_days
            ? parseInt(item.lead_time_days)
            : null,
          remark: item.remark,
          cost_category: item.cost_category,
          cost_source: item.cost_source,
          specification: item.specification,
          unit: item.unit
        }))
      };

      const res = await quoteApi.batchUpdateItems(id, batchData, version.id);

      // 更新版本的成本数据
      if (res.data?.data) {
        const costData = res.data.data;
        if (version) {
          version.total_price = costData.total_price;
          version.cost_total = costData.total_cost;
          version.gross_margin = costData.gross_margin;
        }
      }

      // 重新加载数据
      await loadData();

      alert("保存成功！");
    } catch (error) {
      console.error("保存成本明细失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  if (loading && !quote) {
    return (
      <div className="flex items-center justify-center h-64">加载中...</div>
    );
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="报价成本管理"
        description={quote ? `报价编号: ${quote.quote_no || id}` : ""}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(`/sales/quotes`)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
            <Button variant="outline" onClick={handleCheckCost}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              成本检查
            </Button>
            <Button variant="outline" onClick={handleCalculateCost}>
              <Calculator className="h-4 w-4 mr-2" />
              重新计算
            </Button>
            <Button variant="outline" onClick={handleAutoMatchCost}>
              <Search className="h-4 w-4 mr-2" />
              自动匹配成本
            </Button>
            <Button onClick={() => setShowTemplateDialog(true)}>
              <Layers className="h-4 w-4 mr-2" />
              应用模板
            </Button>
          </div>
        }
      />

      <CostOverview totals={totals} marginStatus={marginStatus} />

      <Tabs defaultValue="breakdown" className="space-y-4">
        <TabsList>
          <TabsTrigger value="breakdown">成本明细</TabsTrigger>
          <TabsTrigger value="check">成本检查</TabsTrigger>
          <TabsTrigger value="approval">审批流程</TabsTrigger>
        </TabsList>

        <TabsContent value="breakdown" className="space-y-4">
          <CostBreakdown
            groupedItems={groupedItems}
            items={items}
            onSave={handleSaveItems}
            onItemChange={handleItemChange}
          />
        </TabsContent>

        <TabsContent value="check" className="space-y-4">
          <CostCheck costCheck={costCheck} />
        </TabsContent>

        <TabsContent value="approval" className="space-y-4">
          <CostApproval
            approvalHistory={approvalHistory}
            onSubmitApproval={() => setShowApprovalDialog(true)}
          />
        </TabsContent>
      </Tabs>

      <ApplyTemplateDialog
        open={showTemplateDialog}
        onOpenChange={setShowTemplateDialog}
        costTemplates={costTemplates}
        selectedTemplate={selectedTemplate}
        onTemplateSelect={setSelectedTemplate}
        onApply={handleApplyTemplate}
        loading={loading}
      />

      <SubmitApprovalDialog
        open={showApprovalDialog}
        onOpenChange={setShowApprovalDialog}
        approvalData={approvalData}
        onApprovalDataChange={setApprovalData}
        onSubmit={handleSubmitApproval}
        loading={loading}
      />

      <CostSuggestionsDialog
        open={showSuggestionsDialog}
        onOpenChange={setShowSuggestionsDialog}
        costSuggestions={costSuggestions}
        items={items}
        editedSuggestions={editedSuggestions}
        onSuggestionChange={handleSuggestionChange}
        onApply={handleApplySuggestions}
        loading={loading}
      />
    </motion.div>
  );
}
