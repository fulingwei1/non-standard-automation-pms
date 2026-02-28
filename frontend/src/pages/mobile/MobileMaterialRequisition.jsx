/**
 * Mobile Material Requisition - 移动端领料申请
 * 功能：移动端申请领料
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  Plus,
  X,
  CheckCircle2,
  AlertCircle } from
"lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import { cn as _cn } from "../../lib/utils";
import { productionApi, materialApi } from "../../services/api";

export default function MobileMaterialRequisition() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workOrderId = searchParams.get("workOrderId");

  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [items, setItems] = useState([
  { material_id: "", material_code: "", material_name: "", qty: 1, unit: "" }]
  );

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder();
    }
    fetchMaterials();
  }, [workOrderId]);

  const fetchWorkOrder = async () => {
    try {
      const res = await productionApi.workOrders.get(workOrderId);
      setWorkOrder(res.data);
    } catch (error) {
      console.error("Failed to fetch work order:", error);
    }
  };

  const fetchMaterials = async () => {
    try {
      const res = await materialApi.list({ page: 1, page_size: 100 });
      const materialsList = res.data?.items || res.data?.items || res.data || [];
      setMaterials(materialsList);
    } catch (error) {
      console.error("Failed to fetch materials:", error);
    }
  };

  const handleMaterialChange = (index, materialId) => {
    const material = materials.find((m) => m.id === parseInt(materialId));
    if (material) {
      const newItems = [...items];
      newItems[index] = {
        ...newItems[index],
        material_id: material.id,
        material_code: material.material_code,
        material_name: material.material_name,
        unit: material.unit || "个"
      };
      setItems(newItems);
    }
  };

  const handleQtyChange = (index, qty) => {
    const newItems = [...items];
    newItems[index].qty = parseInt(qty) || 0;
    setItems(newItems);
  };

  const handleAddItem = () => {
    setItems([
    ...items,
    {
      material_id: "",
      material_code: "",
      material_name: "",
      qty: 1,
      unit: ""
    }]
    );
  };

  const handleRemoveItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async () => {
    // 验证
    const invalidItems = items.filter(
      (item) => !item.material_id || !item.qty || item.qty <= 0
    );
    if (invalidItems.length > 0) {
      setError("请完善物料信息并填写数量");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await productionApi.materialRequisitions.create({
        work_order_id: workOrderId ? parseInt(workOrderId) : null,
        items: items.map((item) => ({
          material_id: item.material_id,
          required_qty: item.qty
        })),
        remark: ""
      });

      setSuccess(true);
      setTimeout(() => {
        navigate("/mobile/tasks");
      }, 1500);
    } catch (error) {
      console.error("Failed to create requisition:", error);
      setError(
        "领料申请失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="p-2">

              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold">领料申请</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 工单信息 */}
        {workOrder &&
        <Card>
            <CardContent className="pt-6">
              <div className="space-y-2">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono text-sm">
                    {workOrder.work_order_no}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">任务名称</div>
                  <div className="font-medium text-sm">
                    {workOrder.task_name}
                  </div>
                </div>
              </div>
            </CardContent>
        </Card>
        }

        {/* 错误提示 */}
        {error &&
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-800">{error}</div>
            </div>
        </div>
        }

        {/* 成功提示 */}
        {success &&
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <div className="flex-1">
              <div className="text-sm font-medium text-emerald-800">
                领料申请成功！
              </div>
            </div>
        </div>
        }

        {/* 物料列表 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold">物料清单</h2>
                <Button variant="outline" size="sm" onClick={handleAddItem}>
                  <Plus className="w-4 h-4 mr-1" />
                  添加物料
                </Button>
              </div>

              {items.map((item, index) =>
              <div key={index} className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      物料 {index + 1}
                    </span>
                    {items.length > 1 &&
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveItem(index)}
                    className="p-1 h-auto text-red-500">

                        <X className="w-4 h-4" />
                  </Button>
                  }
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      物料 *
                    </label>
                    <Select
                    value={item.material_id ? String(item.material_id) : ""}
                    onValueChange={(value) =>
                    handleMaterialChange(index, value)
                    }>

                      <SelectTrigger>
                        <SelectValue placeholder="请选择物料" />
                      </SelectTrigger>
                      <SelectContent>
                        {materials.map((material) =>
                      <SelectItem
                        key={material.id}
                        value={String(material.id)}>

                            {material.material_code} - {material.material_name}
                      </SelectItem>
                      )}
                      </SelectContent>
                    </Select>
                  </div>

                  {item.material_id &&
                <div className="bg-slate-50 rounded-lg p-3 space-y-1">
                      <div className="text-xs text-slate-500">物料编码</div>
                      <div className="font-mono text-sm">
                        {item.material_code}
                      </div>
                      <div className="text-xs text-slate-500">物料名称</div>
                      <div className="text-sm">{item.material_name}</div>
                </div>
                }

                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      数量 *
                    </label>
                    <div className="flex gap-2">
                      <Input
                      type="number"
                      min="1"
                      value={item.qty}
                      onChange={(e) => handleQtyChange(index, e.target.value)}
                      placeholder="0"
                      className="flex-1" />

                      <div className="flex items-center px-3 bg-slate-50 rounded-lg text-sm text-slate-600">
                        {item.unit || "个"}
                      </div>
                    </div>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 提交按钮 */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-600 h-12 text-base">

          <Package className="w-5 h-5 mr-2" />
          {loading ? "提交中..." : "提交申请"}
        </Button>
      </div>
    </div>);

}