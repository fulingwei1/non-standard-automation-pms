/**
 * Quote Create/Edit Page - 报价创建/编辑页面
 * Features: 报价表单、成本拆解、版本管理、AI智能定价
 */
import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { cn, formatCurrency } from "../lib/utils";
import { quoteApi, opportunityApi } from "../services/api";

export default function QuoteCreateEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = !!id;
  const [loading, setLoading] = useState(false);
  const [opportunities, setOpportunities] = useState([]);
  const [showAiPanel, setShowAiPanel] = useState(true); // AI面板显示状态

  // Form state
  const [formData, setFormData] = useState({
    opportunity_id: null,
    quote_code: "",
    quote_name: "",
    valid_days: 30,
    lead_time_days: 60,
    payment_terms: "",
    delivery_terms: "",
    risk_terms: "",
    note: "",
  });
  const [versionData, setVersionData] = useState({
    version_no: "V1.0",
    total_price: 0,
    cost_total: 0,
    tax_rate: 13,
    tax_amount: 0,
    amount_with_tax: 0,
    lead_time_days: 60,
    risk_terms: "",
    note: "",
  });
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
    } catch (_error) {
      // 非关键操作失败时静默降级
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
    } catch (_error) {
      // 非关键操作失败时静默降级
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    setItems([
      ...items,
      {
        item_name: "",
        item_code: "",
        specification: "",
        qty: 1,
        unit: "套",
        unit_price: 0,
        cost: 0,
        amount: 0,
        cost_amount: 0,
        station_count: 1,
        ct_seconds: 0,
        uph: 0,
        fixture_qty: 0,
        camera_count: 0,
        light_count: 0,
        operator_hours: 0,
        engineering_hours: 0,
        material_cost: 0,
        labor_cost: 0,
        overhead_cost: 0,
        total_cost: 0,
        remark: "",
      },
    ]);
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
    if (["material_cost", "labor_cost", "overhead_cost"].includes(field)) {
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
          items: (items || []).map((item) => ({
            item_name: item.item_name,
            item_code: item.item_code,
            specification: item.specification,
            qty: item.qty,
            unit: item.unit,
            unit_price: item.unit_price,
            cost: item.cost,
            station_count: item.station_count,
            ct_seconds: item.ct_seconds,
            uph: item.uph,
            fixture_qty: item.fixture_qty,
            camera_count: item.camera_count,
            light_count: item.light_count,
            operator_hours: item.operator_hours,
            engineering_hours: item.engineering_hours,
            material_cost: item.material_cost,
            labor_cost: item.labor_cost,
            overhead_cost: item.overhead_cost,
            total_cost: item.total_cost,
            remark: item.remark,
          })),
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

        {/* 基本信息 */}
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">商机 *</label>
                <Select
                  value={formData.opportunity_id?.toString() || ""}
                  onValueChange={(val) =>
                    setFormData({
                      ...formData,
                      opportunity_id: val ? parseInt(val) : null,
                    })
                  }
                  disabled={isEdit}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择商机" />
                  </SelectTrigger>
                  <SelectContent>
                    {(opportunities || []).map((opp) => (
                      <SelectItem key={opp.id} value={opp.id.toString()}>
                        {opp.opp_code} - {opp.opp_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">报价编码</label>
                <Input
                  value={formData.quote_code}
                  onChange={(e) =>
                    setFormData({ ...formData, quote_code: e.target.value })
                  }
                  placeholder="自动生成"
                  disabled={isEdit}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">报价名称</label>
                <Input
                  value={formData.quote_name}
                  onChange={(e) =>
                    setFormData({ ...formData, quote_name: e.target.value })
                  }
                  placeholder="报价名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  有效期(天)
                </label>
                <Input
                  type="number"
                  value={formData.valid_days}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      valid_days: parseInt(e.target.value) || 30,
                    })
                  }
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 报价明细 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>报价明细</CardTitle>
              <Button variant="outline" size="sm" onClick={handleAddItem}>
                <Plus className="w-4 h-4 mr-2" />
                添加明细
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {items?.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Button variant="outline" onClick={handleAddItem}>
                  <Plus className="w-4 h-4 mr-2" />
                  添加第一条明细
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>序号</TableHead>
                      <TableHead>物料编码</TableHead>
                      <TableHead>物料名称</TableHead>
                      <TableHead>规格</TableHead>
                      <TableHead>数量</TableHead>
                      <TableHead>单位</TableHead>
                      <TableHead>单价</TableHead>
                      <TableHead>金额</TableHead>
                      <TableHead>成本</TableHead>
                      <TableHead>成本金额</TableHead>
                      <TableHead>材料成本</TableHead>
                      <TableHead>人工成本</TableHead>
                      <TableHead>制造费用</TableHead>
                      <TableHead>备注</TableHead>
                      <TableHead>操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(items || []).map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{index + 1}</TableCell>
                        <TableCell>
                          <Input
                            value={item.item_code}
                            onChange={(e) =>
                              handleItemChange(index, "item_code", e.target.value)
                            }
                            placeholder="编码"
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            value={item.item_name}
                            onChange={(e) =>
                              handleItemChange(index, "item_name", e.target.value)
                            }
                            placeholder="名称"
                            className="w-32"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            value={item.specification}
                            onChange={(e) =>
                              handleItemChange(index, "specification", e.target.value)
                            }
                            placeholder="规格"
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.qty}
                            onChange={(e) =>
                              handleItemChange(index, "qty", parseFloat(e.target.value) || 0)
                            }
                            className="w-20"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            value={item.unit}
                            onChange={(e) =>
                              handleItemChange(index, "unit", e.target.value)
                            }
                            placeholder="单位"
                            className="w-16"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.unit_price}
                            onChange={(e) =>
                              handleItemChange(index, "unit_price", parseFloat(e.target.value) || 0)
                            }
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(item.amount || 0)}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.cost}
                            onChange={(e) =>
                              handleItemChange(index, "cost", parseFloat(e.target.value) || 0)
                            }
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(item.cost_amount || 0)}
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.material_cost || 0}
                            onChange={(e) =>
                              handleItemChange(index, "material_cost", parseFloat(e.target.value) || 0)
                            }
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.labor_cost || 0}
                            onChange={(e) =>
                              handleItemChange(index, "labor_cost", parseFloat(e.target.value) || 0)
                            }
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            value={item.overhead_cost || 0}
                            onChange={(e) =>
                              handleItemChange(index, "overhead_cost", parseFloat(e.target.value) || 0)
                            }
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            value={item.remark}
                            onChange={(e) =>
                              handleItemChange(index, "remark", e.target.value)
                            }
                            placeholder="备注"
                            className="w-24"
                          />
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveItem(index)}
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 汇总 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>价格汇总</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">总价:</span>
                  <span className="font-bold text-lg">
                    {formatCurrency(versionData.total_price || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">税率:</span>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      value={versionData.tax_rate}
                      onChange={(e) => {
                        const rate = parseFloat(e.target.value) || 0;
                        setVersionData({
                          ...versionData,
                          tax_rate: rate,
                          tax_amount: versionData.total_price * (rate / 100),
                          amount_with_tax: versionData.total_price * (1 + rate / 100),
                        });
                      }}
                      className="w-20"
                    />
                    <span>%</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">税额:</span>
                  <span className="font-medium">
                    {formatCurrency(versionData.tax_amount || 0)}
                  </span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span className="text-slate-500">含税总额:</span>
                  <span className="font-bold text-xl text-emerald-600">
                    {formatCurrency(versionData.amount_with_tax || 0)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>成本汇总</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">总成本:</span>
                  <span className="font-bold text-lg">
                    {formatCurrency(versionData.cost_total || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">材料成本:</span>
                  <span>{formatCurrency(costStructure.material)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">人工成本:</span>
                  <span>{formatCurrency(costStructure.labor)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">制造费用:</span>
                  <span>{formatCurrency(costStructure.overhead)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>利润分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">毛利:</span>
                  <span className="font-medium">
                    {formatCurrency(
                      (versionData.total_price || 0) - (versionData.cost_total || 0),
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">毛利率:</span>
                  <Badge
                    className={cn(
                      parseFloat(grossMargin) >= 20 && "bg-emerald-500",
                      parseFloat(grossMargin) >= 15 &&
                        parseFloat(grossMargin) < 20 &&
                        "bg-amber-500",
                      parseFloat(grossMargin) < 15 && "bg-red-500",
                      "bg-slate-500",
                    )}
                  >
                    {grossMargin}%
                  </Badge>
                </div>
                {parseFloat(grossMargin) < 15 && (
                  <div className="text-xs text-red-600 mt-2">
                    ⚠️ 毛利率低于15%，存在盈利风险
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 其他信息 */}
        <Card>
          <CardHeader>
            <CardTitle>其他信息</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">交期(天)</label>
                <Input
                  type="number"
                  value={versionData.lead_time_days}
                  onChange={(e) =>
                    setVersionData({
                      ...versionData,
                      lead_time_days: parseInt(e.target.value) || 60,
                    })
                  }
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">付款条件</label>
                <Input
                  value={formData.payment_terms}
                  onChange={(e) =>
                    setFormData({ ...formData, payment_terms: e.target.value })
                  }
                  placeholder="付款条件"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">交付条件</label>
                <Input
                  value={formData.delivery_terms}
                  onChange={(e) =>
                    setFormData({ ...formData, delivery_terms: e.target.value })
                  }
                  placeholder="交付条件"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">风险条款</label>
                <Input
                  value={versionData.risk_terms}
                  onChange={(e) =>
                    setVersionData({ ...versionData, risk_terms: e.target.value })
                  }
                  placeholder="风险条款"
                />
              </div>
              <div className="md:col-span-2">
                <label className="text-sm font-medium mb-2 block">备注</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-transparent"
                  value={formData.note}
                  onChange={(e) =>
                    setFormData({ ...formData, note: e.target.value })
                  }
                  placeholder="备注..."
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI智能定价侧边栏 */}
      {showAiPanel && (
        <div className="fixed right-0 top-0 h-full w-80 bg-slate-950 border-l border-slate-800 overflow-y-auto p-4 pt-20">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              AI智能定价
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAiPanel(false)}
              className="h-6 w-6 p-0"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          <IntelligentQuoteSidebar
            opportunity={selectedOpportunity}
            currentPrice={versionData.total_price}
            currentCost={versionData.cost_total}
            onApplyPrice={handleApplyAiPrice}
          />
        </div>
      )}
    </div>
  );
}
