import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Save,
  Truck,
  Package,
  Plus,
  X,
  Calendar,
  Search,
  ChevronRight } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import { Badge } from "../components/ui/badge";
import { cn as _cn, formatCurrency, formatDate as _formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { purchaseApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { LoadingCard } from "../components/common";
import { ErrorMessage } from "../components/common";

export default function GoodsReceiptNew() {
  const navigate = useNavigate();
  const location = useLocation();
  const orderId =
  location.state?.orderId ||
  new URLSearchParams(location.search).get("order_id");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [order, setOrder] = useState(null);
  const [orderItems, setOrderItems] = useState([]);

  const [formData, setFormData] = useState({
    order_id: orderId ? parseInt(orderId) : null,
    receipt_date: new Date().toISOString().split("T")[0],
    receipt_type: "NORMAL",
    delivery_note_no: "",
    logistics_company: "",
    tracking_no: "",
    remark: ""
  });

  const [selectedItems, setSelectedItems] = useState([]);

  useEffect(() => {
    const targetOrderId = orderId || formData.order_id;
    if (targetOrderId) {
      loadOrder(targetOrderId);
    }
  }, [orderId, formData.order_id]);

  const loadOrder = async (targetOrderId) => {
    try {
      setLoading(true);
      setError(null);
      const orderIdToLoad = targetOrderId || orderId || formData.order_id;
      if (!orderIdToLoad) {
        return;
      }

      const [orderRes, itemsRes] = await Promise.all([
      purchaseApi.orders.get(orderIdToLoad),
      purchaseApi.orders.getItems(orderIdToLoad)]
      );
      setOrder(orderRes.data || orderRes);
      setOrderItems(itemsRes.data || itemsRes || []);
    } catch (err) {
      console.error("Failed to load order:", err);
      setError(err.response?.data?.detail || "加载采购订单失败");
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = (item) => {
    const remainingQty = item.quantity - (item.received_qty || 0);
    if (remainingQty <= 0) {
      toast.error("该物料已全部收货");
      return;
    }

    const exists = selectedItems.find((si) => si.order_item_id === item.id);
    if (exists) {
      toast.error("该物料已添加");
      return;
    }

    setSelectedItems([
    ...selectedItems,
    {
      order_item_id: item.id,
      material_code: item.material_code,
      material_name: item.material_name,
      specification: item.specification,
      unit: item.unit,
      order_qty: item.quantity,
      received_qty: item.received_qty || 0,
      remaining_qty: remainingQty,
      delivery_qty: remainingQty,
      received_qty_input: remainingQty,
      unit_price: item.unit_price,
      remark: ""
    }]
    );
  };

  const handleRemoveItem = (index) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  const handleUpdateItem = (index, field, value) => {
    const newItems = [...selectedItems];
    const item = newItems[index];

    if (field === "delivery_qty") {
      const qty = parseFloat(value) || 0;
      if (qty > item.remaining_qty) {
        toast.error(`送货数量不能超过剩余数量 ${item.remaining_qty}`);
        return;
      }
      item.delivery_qty = qty;
      item.received_qty_input = qty;
    } else if (field === "received_qty_input") {
      const qty = parseFloat(value) || 0;
      if (qty > item.delivery_qty) {
        toast.error(`实收数量不能超过送货数量 ${item.delivery_qty}`);
        return;
      }
      item.received_qty_input = qty;
    } else {
      item[field] = value;
    }

    setSelectedItems(newItems);
  };

  const handleSubmit = async () => {
    if (!formData.order_id) {
      toast.error("请选择采购订单");
      return;
    }

    if (selectedItems.length === 0) {
      toast.error("请至少添加一个物料");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const receiptData = {
        order_id: formData.order_id,
        receipt_date: formData.receipt_date,
        receipt_type: formData.receipt_type,
        delivery_note_no: formData.delivery_note_no || null,
        logistics_company: formData.logistics_company || null,
        tracking_no: formData.tracking_no || null,
        remark: formData.remark || null,
        items: selectedItems.map((item) => ({
          order_item_id: item.order_item_id,
          delivery_qty: item.delivery_qty,
          received_qty: item.received_qty_input,
          remark: item.remark || null
        }))
      };

      const res = await purchaseApi.receipts.create(receiptData);
      toast.success("收货单创建成功");
      navigate(`/purchases/receipts/${res.data?.id || res.id}`);
    } catch (err) {
      console.error("Failed to create receipt:", err);
      setError(err.response?.data?.detail || "创建收货单失败");
      toast.error(err.response?.data?.detail || "创建收货单失败");
    } finally {
      setLoading(false);
    }
  };

  const availableItems = orderItems.filter((item) => {
    const remainingQty = item.quantity - (item.received_qty || 0);
    return (
      remainingQty > 0 &&
      !selectedItems.find((si) => si.order_item_id === item.id));

  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="新建收货单"
          description="从采购订单创建收货单"
          actions={
          <Button
            variant="outline"
            onClick={() => navigate("/purchases/receipts")}>

              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          } />


        {error && <ErrorMessage message={error} />}

        {loading && !order ?
        <LoadingCard /> :
        !orderId ?
        <motion.div variants={fadeIn} className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">选择采购订单</CardTitle>
                <CardDescription className="text-slate-400">
                  请先选择要创建收货单的采购订单
                </CardDescription>
              </CardHeader>
              <CardContent>
                <OrderSelectionForm
                onSelect={(selectedOrder) => {
                  setFormData((prev) => ({
                    ...prev,
                    order_id: selectedOrder.id
                  }));
                  // loadOrder will be triggered by useEffect when formData.order_id changes
                }} />

              </CardContent>
            </Card>
          </motion.div> :

        <motion.div variants={fadeIn} className="space-y-6">
            {/* Order Info */}
            {order &&
          <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-slate-200">采购订单信息</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <Label className="text-slate-400">订单编号</Label>
                      <p className="text-slate-200 font-mono">
                        {order.order_no}
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">供应商</Label>
                      <p className="text-slate-200">{order.supplier_name}</p>
                    </div>
                    <div>
                      <Label className="text-slate-400">项目</Label>
                      <p className="text-slate-200">
                        {order.project_name || "-"}
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">订单状态</Label>
                      <Badge className="bg-emerald-500">{order.status}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
          }

            {/* Receipt Form */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">收货单信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">收货日期 *</Label>
                    <Input
                    type="date"
                    value={formData.receipt_date}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      receipt_date: e.target.value
                    })
                    }
                    className="bg-slate-900/50 border-slate-700 text-slate-200" />

                  </div>
                  <div>
                    <Label className="text-slate-400">收货类型</Label>
                    <Select
                    value={formData.receipt_type}
                    onValueChange={(val) =>
                    setFormData({ ...formData, receipt_type: val })
                    }>

                      <SelectTrigger className="bg-slate-900/50 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NORMAL">正常收货</SelectItem>
                        <SelectItem value="RETURN">退货</SelectItem>
                        <SelectItem value="EXCHANGE">换货</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-400">送货单号</Label>
                    <Input
                    value={formData.delivery_note_no}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      delivery_note_no: e.target.value
                    })
                    }
                    placeholder="送货单号（可选）"
                    className="bg-slate-900/50 border-slate-700 text-slate-200" />

                  </div>
                  <div>
                    <Label className="text-slate-400">物流公司</Label>
                    <Input
                    value={formData.logistics_company}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      logistics_company: e.target.value
                    })
                    }
                    placeholder="物流公司（可选）"
                    className="bg-slate-900/50 border-slate-700 text-slate-200" />

                  </div>
                  <div>
                    <Label className="text-slate-400">物流单号</Label>
                    <Input
                    value={formData.tracking_no}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      tracking_no: e.target.value
                    })
                    }
                    placeholder="物流单号（可选）"
                    className="bg-slate-900/50 border-slate-700 text-slate-200" />

                  </div>
                </div>
                <div>
                  <Label className="text-slate-400">备注</Label>
                  <Textarea
                  value={formData.remark}
                  onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                  }
                  placeholder="备注信息（可选）"
                  className="bg-slate-900/50 border-slate-700 text-slate-200"
                  rows={3} />

                </div>
              </CardContent>
            </Card>

            {/* Available Items */}
            {availableItems.length > 0 &&
          <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-slate-200">可收货物料</CardTitle>
                  <CardDescription className="text-slate-400">
                    点击物料添加到收货单
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {availableItems.map((item) => {
                  const remainingQty =
                  item.quantity - (item.received_qty || 0);
                  return (
                    <div
                      key={item.id}
                      className="p-3 border border-slate-700 rounded-lg bg-slate-900/30 flex items-center justify-between hover:bg-slate-900/50 cursor-pointer"
                      onClick={() => handleAddItem(item)}>

                          <div className="flex-1">
                            <p className="text-slate-200 font-mono text-sm">
                              {item.material_code}
                            </p>
                            <p className="text-slate-400 text-sm">
                              {item.material_name}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-slate-300">
                              订单: {item.quantity} {item.unit}
                            </p>
                            <p className="text-slate-400 text-sm">
                              已收: {item.received_qty || 0} | 剩余:{" "}
                              {remainingQty}
                            </p>
                          </div>
                          <Button size="sm" variant="ghost" className="ml-4">
                            <Plus className="w-4 h-4" />
                          </Button>
                        </div>);

                })}
                  </div>
                </CardContent>
              </Card>
          }

            {/* Selected Items */}
            {selectedItems.length > 0 &&
          <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-slate-200">收货明细</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-400">
                          物料编码
                        </TableHead>
                        <TableHead className="text-slate-400">
                          物料名称
                        </TableHead>
                        <TableHead className="text-slate-400">
                          剩余数量
                        </TableHead>
                        <TableHead className="text-slate-400">
                          送货数量 *
                        </TableHead>
                        <TableHead className="text-slate-400">
                          实收数量
                        </TableHead>
                        <TableHead className="text-slate-400">备注</TableHead>
                        <TableHead className="text-slate-400">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedItems.map((item, index) =>
                  <TableRow key={index} className="border-slate-700">
                          <TableCell className="font-mono text-sm text-slate-200">
                            {item.material_code}
                          </TableCell>
                          <TableCell className="text-slate-300">
                            {item.material_name}
                          </TableCell>
                          <TableCell className="text-slate-300">
                            {item.remaining_qty} {item.unit}
                          </TableCell>
                          <TableCell>
                            <Input
                        type="number"
                        value={item.delivery_qty}
                        onChange={(e) =>
                        handleUpdateItem(
                          index,
                          "delivery_qty",
                          e.target.value
                        )
                        }
                        min={0}
                        max={item.remaining_qty}
                        className="w-24 bg-slate-900/50 border-slate-700 text-slate-200" />

                          </TableCell>
                          <TableCell>
                            <Input
                        type="number"
                        value={item.received_qty_input}
                        onChange={(e) =>
                        handleUpdateItem(
                          index,
                          "received_qty_input",
                          e.target.value
                        )
                        }
                        min={0}
                        max={item.delivery_qty}
                        className="w-24 bg-slate-900/50 border-slate-700 text-slate-200" />

                          </TableCell>
                          <TableCell>
                            <Input
                        value={item.remark}
                        onChange={(e) =>
                        handleUpdateItem(
                          index,
                          "remark",
                          e.target.value
                        )
                        }
                        placeholder="备注"
                        className="w-32 bg-slate-900/50 border-slate-700 text-slate-200" />

                          </TableCell>
                          <TableCell>
                            <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRemoveItem(index)}>

                              <X className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                  )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
          }

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <Button
              variant="outline"
              onClick={() => navigate("/purchases/receipts")}>

                取消
              </Button>
              <Button
              onClick={handleSubmit}
              disabled={loading || selectedItems.length === 0}
              className="bg-blue-600 hover:bg-blue-700">

                {loading ? "创建中..." : "创建收货单"}
              </Button>
            </div>
          </motion.div>
        }
      </div>
    </div>);

}

// Order Selection Component
function OrderSelectionForm({ onSelect }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const loadOrders = async () => {
      try {
        setLoading(true);
        const res = await purchaseApi.orders.list({
          page: 1,
          page_size: 100,
          status: "APPROVED" // Only show approved orders
        });
        const data = res.data?.items || res.data || [];
        setOrders(data);
      } catch (err) {
        console.error("Failed to load orders:", err);
      } finally {
        setLoading(false);
      }
    };
    loadOrders();
  }, []);

  const filteredOrders = orders.filter((order) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        order.order_no?.toLowerCase().includes(query) ||
        order.supplier_name?.toLowerCase().includes(query) ||
        order.project_name?.toLowerCase().includes(query));

    }
    return true;
  });

  if (loading) {
    return <LoadingCard />;
  }

  if (filteredOrders.length === 0) {
    return (
      <EmptyState
        icon={Package}
        title="暂无可收货的采购订单"
        description="请先创建并审批通过采购订单" />);


  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="搜索订单号、供应商、项目..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-slate-900/50 border-slate-700 text-slate-200" />

      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredOrders.map((order) =>
        <div
          key={order.id}
          className="p-4 border border-slate-700 rounded-lg bg-slate-900/30 hover:bg-slate-900/50 cursor-pointer transition-colors"
          onClick={() => onSelect(order)}>

            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-slate-200 font-mono font-semibold">
                  {order.order_no}
                </p>
                <p className="text-slate-400 text-sm mt-1">
                  {order.supplier_name}
                </p>
                {order.project_name &&
              <p className="text-slate-500 text-xs mt-1">
                    {order.project_name}
                  </p>
              }
              </div>
              <div className="text-right">
                <p className="text-slate-200 font-semibold">
                  ¥{formatCurrency(order.total_amount || 0)}
                </p>
                <Badge className="bg-emerald-500 mt-1">{order.status}</Badge>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-400 ml-4" />
            </div>
          </div>
        )}
      </div>
    </div>);

}