/**
 * Mobile Shortage Report - 移动端缺料上报表单
 * 功能：填写缺料上报信息，支持拍照
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  Package,
  Camera,
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
import { productionApi, shortageApi, materialApi } from "../../services/api";

const urgentLevels = [
{ value: "LOW", label: "低" },
{ value: "MEDIUM", label: "中" },
{ value: "HIGH", label: "高" },
{ value: "URGENT", label: "紧急" }];


export default function MobileShortageReport() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workOrderId = searchParams.get("workOrderId");

  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [formData, setFormData] = useState({
    project_id: "",
    machine_id: "",
    material_id: "",
    required_qty: 0,
    shortage_qty: 0,
    urgent_level: "MEDIUM",
    report_location: "",
    remark: ""
  });

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder();
    }
    fetchMaterials();
  }, [workOrderId]);

  const fetchWorkOrder = async () => {
    try {
      const res = await productionApi.workOrders.get(workOrderId);
      const order = res.data;
      setWorkOrder(order);
      setFormData((prev) => ({
        ...prev,
        project_id: order.project_id,
        machine_id: order.machine_id
      }));
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

  const handleMaterialChange = (materialId) => {
    const material = (materials || []).find((m) => m.id === parseInt(materialId));
    if (material) {
      setFormData((prev) => ({
        ...prev,
        material_id: material.id
      }));
    }
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files || []);
    (files || []).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const photoUrl = event.target.result;
        setPhotos((prev) => [...prev, { url: photoUrl, file }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const handleSubmit = async () => {
    if (!formData.project_id) {
      setError("请选择项目");
      return;
    }
    if (!formData.material_id) {
      setError("请选择物料");
      return;
    }
    if (!formData.shortage_qty || formData.shortage_qty <= 0) {
      setError("请填写缺料数量");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await shortageApi.reports.create({
        project_id: parseInt(formData.project_id),
        machine_id: formData.machine_id ? parseInt(formData.machine_id) : null,
        work_order_id: workOrderId ? parseInt(workOrderId) : null,
        material_id: parseInt(formData.material_id),
        required_qty: formData.required_qty || formData.shortage_qty,
        shortage_qty: formData.shortage_qty,
        urgent_level: formData.urgent_level,
        report_location: formData.report_location,
        remark:
          formData.remark +
          (photos.length ? `\n[移动端] 已选择${photos.length}张照片（当前接口不支持上传）` : "")
      });

      setSuccess(true);
      setTimeout(() => {
        navigate("/mobile/my-shortage-reports");
      }, 1500);
    } catch (error) {
      console.error("Failed to create shortage report:", error);
      setError(
        "缺料上报失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const selectedMaterial = (materials || []).find(
    (m) => m.id === parseInt(formData.material_id)
  );

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
            <h1 className="text-lg font-semibold">缺料上报</h1>
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
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div className="text-sm">{workOrder.project_name || "-"}</div>
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
                缺料上报成功！
              </div>
            </div>
        </div>
        }

        {/* 表单 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* 物料选择 */}
              <div>
                <label className="text-sm font-medium mb-2 block">物料 *</label>
                <Select
                  value={
                  formData.material_id ? String(formData.material_id) : ""
                  }
                  onValueChange={handleMaterialChange}>

                  <SelectTrigger>
                    <SelectValue placeholder="请选择物料" />
                  </SelectTrigger>
                  <SelectContent>
                    {(materials || []).map((material) =>
                    <SelectItem key={material.id} value={String(material.id)}>
                        {material.material_code} - {material.material_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {selectedMaterial &&
                <div className="mt-2 bg-slate-50 rounded-lg p-3 space-y-1">
                    <div className="text-xs text-slate-500">物料编码</div>
                    <div className="font-mono text-sm">
                      {selectedMaterial.material_code}
                    </div>
                    <div className="text-xs text-slate-500">物料名称</div>
                    <div className="text-sm">
                      {selectedMaterial.material_name}
                    </div>
                    <div className="text-xs text-slate-500">单位</div>
                    <div className="text-sm">
                      {selectedMaterial.unit || "个"}
                    </div>
                </div>
                }
              </div>

              {/* 需求数量 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  需求数量
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.required_qty}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    required_qty: parseInt(e.target.value) || 0
                  })
                  }
                  placeholder="0"
                  className="text-lg" />

              </div>

              {/* 缺料数量 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  缺料数量 *
                </label>
                <Input
                  type="number"
                  min="1"
                  value={formData.shortage_qty}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    shortage_qty: parseInt(e.target.value) || 0
                  })
                  }
                  placeholder="0"
                  className="text-lg" />

              </div>

              {/* 紧急程度 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  紧急程度
                </label>
                <Select
                  value={formData.urgent_level}
                  onValueChange={(value) =>
                  setFormData({ ...formData, urgent_level: value })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(urgentLevels || []).map((level) =>
                    <SelectItem key={level.value} value={level.value}>
                        {level.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* 上报位置 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  上报位置（可选）
                </label>
                <Input
                  value={formData.report_location}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    report_location: e.target.value
                  })
                  }
                  placeholder="车间/工位" />

              </div>

              {/* 说明 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  说明（可选）
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.remark}
                  onChange={(e) =>
                  setFormData({ ...formData, remark: e.target.value })
                  }
                  placeholder="填写缺料说明..." />

              </div>

              {/* 拍照 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  拍照（可选）
                </label>
                <div className="space-y-2">
                  <input
                    type="file"
                    accept="image/*"
                    capture="environment"
                    multiple
                    onChange={handlePhotoUpload}
                    className="hidden"
                    id="photo-upload-shortage" />

                  <label
                    htmlFor="photo-upload-shortage"
                    className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">

                    <Camera className="w-5 h-5 text-slate-400" />
                    <span className="text-sm text-slate-600">
                      拍照上传（可多张）
                    </span>
                  </label>
                  {photos.length > 0 &&
                  <div className="grid grid-cols-3 gap-2">
                      {(photos || []).map((photo, idx) =>
                    <div
                      key={idx}
                      className="relative aspect-square rounded-lg overflow-hidden">

                          <img
                        src={photo.url}
                        alt={`Photo ${idx + 1}`}
                        className="w-full h-full object-cover" />

                          <button
                        type="button"
                        onClick={() =>
                        setPhotos((prev) =>
                        (prev || []).filter((_, i) => i !== idx)
                        )
                        }
                        className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full">

                            <X className="w-3 h-3" />
                          </button>
                    </div>
                    )}
                  </div>
                  }
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 提交按钮 */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-red-500 hover:bg-red-600 h-12 text-base">

          <Package className="w-5 h-5 mr-2" />
          {loading ? "提交中..." : "提交上报"}
        </Button>
      </div>
    </div>);

}
