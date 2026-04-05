/**
 * Quote Create/Edit Page - 报价创建/编辑页面
 * Features: 报价表单、成本拆解、版本管理、AI智能定价
 */
import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Save, RefreshCw, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import { quoteApi, opportunityApi } from "../../services/api";

import { DEFAULT_FORM_DATA, DEFAULT_VERSION_DATA, DEFAULT_ITEM, COST_LINKED_FIELDS, ITEM_SUBMIT_FIELDS } from "./constants";
import BasicInfoCard from "./BasicInfoCard";
import QuoteItemsTable from "./QuoteItemsTable";
import SummaryCards from "./SummaryCards";
import AdditionalInfoCard from "./AdditionalInfoCard";
import AiSidebarPanel from "./AiSidebarPanel";

export default function QuoteCreateEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [opportunities, setOpportunities] = useState([]);
  const [showAiPanel, setShowAiPanel] = useState(true); // AI面板显示状态

  // Form state
  const [formData, setFormData] = useState({ ...DEFAULT_FORM_DATA });
  const [versionData, setVersionData] = useState({ ...DEFAULT_VERSION_DATA });
  const [items, setItems] = useState([]);

  // 获取当前选中的商机对象
  const selectedOpportunity = useMemo(() => {
    if (!formData.opportunity_id) return null;
    return opportunities.find(opp => opp.id === formData.opportunity_id);
  }, [formData.opportunity_id, opportunities]);

  useEffect(() => {
    fetchOpportunities();
    if (isEdit) {
      fetchQuoteDetail();
    }
  }, [id]);

  const fetchOpportunities = async () => {
    try {
      const res = await opportunityApi.list({
        page_size: 1000,
        stage: "PROPOSING",
      });
      setOpportunities(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch opportunities:", error);
    }
  };

  const fetchQuoteDetail = async () => {
    try {
      setLoading(true);
      const res = await quoteApi.get(id);
      const quote = res.data || res;
      setFormData({
        opportunity_id: quote.opportunity_id,
        quote_code: quote.quote_code,
        quote_name: quote.quote_name || "",
        valid_days: quote.valid_days || 30,
        lead_time_days: quote.lead_time_days || 60,
        payment_terms: quote.payment_terms || "",
        delivery_terms: quote.delivery_terms || "",
        risk_terms: quote.risk_terms || "",
        note: quote.note || "",
      });
      const latestVersion =
        quote.current_version ||
        quote.currentVersion ||
        (quote.versions && quote.versions?.length > 0 ? quote.versions[0] : null);

      if (latestVersion) {
        setVersionData({
          version_no: latestVersion.version_no || "V1.0",
          total_price: latestVersion.total_price || 0,
          cost_total: latestVersion.cost_total || 0,
          tax_rate: latestVersion.tax_rate || 13,
          tax_amount: latestVersion.tax_amount || 0,
          amount_with_tax: latestVersion.amount_with_tax || 0,
          lead_time_days: latestVersion.lead_time_days || 60,
          risk_terms: latestVersion.risk_terms || "",
          note: latestVersion.note || "",
        });
        setItems(
          (latestVersion.items || []).map((item) => {
            const materialCost = Number(item.material_cost || 0);
            const laborCost = Number(item.labor_cost || 0);
            const overheadCost = Number(item.overhead_cost || 0);
            const totalCost = Number(
              item.total_cost || materialCost + laborCost + overheadCost || item.cost || 0,
            );
            const qty = Number(item.qty || 0);
            const unitPrice = Number(item.unit_price || 0);
            return {
              ...item,
              qty,
              unit_price: unitPrice,
              cost: Number(item.cost || totalCost || 0),
              amount: qty * unitPrice,
              cost_amount: qty * totalCost,
              station_count: Number(item.station_count || 0),
              ct_seconds: Number(item.ct_seconds || 0),
              uph: Number(item.uph || 0),
              fixture_qty: Number(item.fixture_qty || 0),
              camera_count: Number(item.camera_count || 0),
              light_count: Number(item.light_count || 0),
              operator_hours: Number(item.operator_hours || 0),
              engineering_hours: Number(item.engineering_hours || 0),
              material_cost: materialCost,
              labor_cost: laborCost,
              overhead_cost: overheadCost,
              total_cost: totalCost,
            };
          }),
        );
      }
    } catch (error) {
      console.error("Failed to fetch quote detail:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    setItems([...items, { ...DEFAULT_ITEM }]);
  };

  const handleRemoveItem = (index) => {
    setItems((items || []).filter((_, i) => i !== index));
    calculateTotals();
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;

    const item = newItems[index];
    const qty = Number(item.qty || 0);
    const unitPrice = Number(item.unit_price || 0);
    const materialCost = Number(item.material_cost || 0);
    const laborCost = Number(item.labor_cost || 0);
    const overheadCost = Number(item.overhead_cost || 0);

    // 成本字段联动
    if (COST_LINKED_FIELDS.includes(field)) {
      item.total_cost = materialCost + laborCost + overheadCost;
      item.cost = item.total_cost;
    }

    if (field === "total_cost") {
      item.cost = Number(item.total_cost || 0);
    }

    item.amount = qty * unitPrice;
    item.cost_amount = qty * Number(item.cost || 0);

    setItems(newItems);
    calculateTotals();
  };

  const calculateTotals = () => {
    const totalPrice = (items || []).reduce((sum, item) => sum + (item.amount || 0), 0);
    const totalCost = (items || []).reduce(
      (sum, item) => sum + (item.cost_amount || 0),
      0,
    );
    const taxAmount = totalPrice * (versionData.tax_rate / 100);
    const amountWithTax = totalPrice + taxAmount;
    setVersionData({
      ...versionData,
      total_price: totalPrice,
      cost_total: totalCost,
      tax_amount: taxAmount,
      amount_with_tax: amountWithTax,
    });
  };

  useEffect(() => {
    calculateTotals();
  }, [items, versionData.tax_rate]);

  const handleSave = async () => {
    if (!formData.opportunity_id) {
      alert("请选择商机");
      return;
    }
    if (items?.length === 0) {
      alert("请至少添加一条报价明细");
      return;
    }
    try {
      setLoading(true);
      const quoteData = {
        ...formData,
        version: {
          ...versionData,
          items: (items || []).map((item) => {
            const mapped = {};
            ITEM_SUBMIT_FIELDS.forEach((key) => {
              mapped[key] = item[key];
            });
            return mapped;
          }),
        },
      };
      if (isEdit) {
        await quoteApi.update(id, quoteData);
      } else {
        await quoteApi.create(quoteData);
      }
      alert(isEdit ? "保存成功" : "创建成功");
      navigate("/sales/quotes");
    } catch (error) {
      console.error("Failed to save quote:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    if (!isEdit) {
      calculateTotals();
      alert("已完成本地重算");
      return;
    }

    try {
      setLoading(true);
      const res = await quoteApi.recalculateCost(id);
      const data = res?.data?.data || res?.data || res;
      setVersionData((prev) => ({
        ...prev,
        total_price: Number(data.total_price || prev.total_price || 0),
        cost_total: Number(data.total_cost || prev.cost_total || 0),
      }));
      alert("成本重算完成");
    } catch (error) {
      console.error("Failed to recalculate quote cost:", error);
      alert("重算失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 应用AI推荐价格
  const handleApplyAiPrice = (recommendedPrice) => {
    if (!recommendedPrice || items.length === 0) return;

    // 按比例分配到各明细项
    const currentTotal = items.reduce((sum, item) => sum + (item.amount || 0), 0);
    if (currentTotal <= 0) {
      // 如果当前没有金额，平均分配
      const avgPrice = recommendedPrice / items.length;
      const newItems = items.map(item => ({
        ...item,
        unit_price: avgPrice / (item.qty || 1),
        amount: avgPrice,
      }));
      setItems(newItems);
    } else {
      // 按比例调整单价
      const ratio = recommendedPrice / currentTotal;
      const newItems = items.map(item => ({
        ...item,
        unit_price: (item.unit_price || 0) * ratio,
        amount: (item.amount || 0) * ratio,
      }));
      setItems(newItems);
    }

    // 重新计算汇总
    setTimeout(calculateTotals, 0);
  };

  const costStructure = {
    material: (items || []).reduce(
      (sum, item) => sum + Number(item.qty || 0) * Number(item.material_cost || 0),
      0,
    ),
    labor: (items || []).reduce(
      (sum, item) => sum + Number(item.qty || 0) * Number(item.labor_cost || 0),
      0,
    ),
    overhead: (items || []).reduce(
      (sum, item) => sum + Number(item.qty || 0) * Number(item.overhead_cost || 0),
      0,
    ),
  };

  const grossMargin =
    versionData.total_price > 0
      ? (
          ((versionData.total_price - versionData.cost_total) /
            versionData.total_price) *
          100
        ).toFixed(2)
      : 0;

  return (
    <div className="flex h-full">
      {/* 主内容区 */}
      <div className={cn(
        "flex-1 space-y-6 p-6 overflow-auto transition-all duration-300",
        showAiPanel ? "mr-80" : ""
      )}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/sales/quotes")}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回列表
            </Button>
            <PageHeader
              title={isEdit ? "编辑报价" : "创建报价"}
              description="报价表单、成本拆解、AI智能定价"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAiPanel(!showAiPanel)}
              className={cn(showAiPanel && "bg-purple-500/20 border-purple-500")}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              AI智能定价
              {showAiPanel ? <ChevronRight className="w-4 h-4 ml-1" /> : <ChevronLeft className="w-4 h-4 ml-1" />}
            </Button>
            <Button variant="outline" onClick={handleRecalculate} disabled={loading}>
              <RefreshCw className="w-4 h-4 mr-2" />
              重算成本
            </Button>
            <Button onClick={handleSave} disabled={loading}>
              <Save className="w-4 h-4 mr-2" />
              保存
            </Button>
          </div>
        </div>

        <BasicInfoCard
          formData={formData}
          setFormData={setFormData}
          opportunities={opportunities}
          isEdit={isEdit}
        />

        <QuoteItemsTable
          items={items}
          onAddItem={handleAddItem}
          onRemoveItem={handleRemoveItem}
          onItemChange={handleItemChange}
        />

        <SummaryCards
          versionData={versionData}
          setVersionData={setVersionData}
          costStructure={costStructure}
          grossMargin={grossMargin}
        />

        <AdditionalInfoCard
          formData={formData}
          setFormData={setFormData}
          versionData={versionData}
          setVersionData={setVersionData}
        />
      </div>

      {/* AI智能定价侧边栏 */}
      {showAiPanel && (
        <AiSidebarPanel
          selectedOpportunity={selectedOpportunity}
          currentPrice={versionData.total_price}
          currentCost={versionData.cost_total}
          onApplyPrice={handleApplyAiPrice}
          onClose={() => setShowAiPanel(false)}
        />
      )}
    </div>
  );
}
