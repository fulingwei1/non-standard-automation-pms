/**
 * Mobile Complete Report - 移动端完工报告
 * 功能：上报完工数量、合格数量、不良数量等
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, AlertCircle, Camera, X } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { productionApi } from "../../services/api";

export default function MobileCompleteReport() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workOrderId = searchParams.get("workOrderId");

  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [formData, setFormData] = useState({
    completed_qty: 0,
    qualified_qty: 0,
    defect_qty: 0,
    work_hours: 0,
    report_note: ""
  });

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder();
    }
  }, [workOrderId]);

  const fetchWorkOrder = async () => {
    try {
      const res = await productionApi.workOrders.get(workOrderId);
      const order = res.data;
      setWorkOrder(order);

      // 自动填充已完成数量和工时
      const autoHours = order.actual_start_time ?
      calculateWorkHours(order.actual_start_time) :
      0;

      setFormData({
        completed_qty: order.completed_qty || 0,
        qualified_qty: order.qualified_qty || order.completed_qty || 0,
        defect_qty: 0,
        work_hours: autoHours,
        report_note: ""
      });
    } catch (error) {
      console.error("Failed to fetch work order:", error);
      setError("获取工单信息失败");
    }
  };

  const calculateWorkHours = (startTime) => {
    if (!startTime) {return 0;}
    const start = new Date(startTime);
    const now = new Date();
    const diffMs = now - start;
    const diffHours = diffMs / (1000 * 60 * 60);
    return Math.round(diffHours * 10) / 10;
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) {return;}

    const reader = new FileReader();
    reader.onload = (event) => {
      const photoUrl = event.target.result;
      setPhotos((prev) => [...prev, { url: photoUrl, file }]);
    };
    reader.readAsDataURL(file);
  };

  const handleQuickQuantity = (type, value) => {
    if (!workOrder) {return;}
    const planQty = workOrder.plan_qty || 0;

    if (type === "completed") {
      const qty = value === "all" ? planQty : value;
      setFormData((prev) => ({
        ...prev,
        completed_qty: qty,
        qualified_qty: qty, // 默认全部合格
        defect_qty: 0
      }));
    } else if (type === "qualified") {
      setFormData((prev) => ({
        ...prev,
        qualified_qty: value === "all" ? prev.completed_qty : value,
        defect_qty:
        prev.completed_qty - (value === "all" ? prev.completed_qty : value)
      }));
    }
  };

  const handleSubmit = async () => {
    if (!formData.completed_qty) {
      setError("请填写完成数量");
      return;
    }
    if (formData.qualified_qty > formData.completed_qty) {
      setError("合格数量不能超过完成数量");
      return;
    }

    const defectQty =
    formData.defect_qty || formData.completed_qty - formData.qualified_qty;

    try {
      setLoading(true);
      setError("");
      await productionApi.workReports.complete({
        work_order_id: workOrderId,
        completed_qty: formData.completed_qty,
        qualified_qty: formData.qualified_qty,
        defect_qty: defectQty,
        work_hours: formData.work_hours,
        report_note: formData.report_note
      });
      setSuccess(true);
      setTimeout(() => {
        navigate("/mobile/tasks");
      }, 1500);
    } catch (error) {
      console.error("Failed to complete work:", error);
      setError(
        "完工报工失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  if (!workOrder) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-400">加载中...</div>
      </div>);

  }

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
            <h1 className="text-lg font-semibold">完工报工</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 工单信息 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div>
                <div className="text-sm text-slate-500 mb-1">工单号</div>
                <div className="font-mono text-base">
                  {workOrder.work_order_no}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">任务名称</div>
                <div className="font-medium text-base">
                  {workOrder.task_name}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">计划数量</div>
                <div className="font-medium text-base">
                  {workOrder.plan_qty || 0}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

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
                完工报工成功！
              </div>
            </div>
        </div>
        }

        {/* 表单 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* 完成数量 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  完成数量 *
                </label>
                <Input
                  type="number"
                  min="0"
                  max={workOrder.plan_qty || 0}
                  value={formData.completed_qty}
                  onChange={(e) => {
                    const qty = parseInt(e.target.value) || 0;
                    setFormData({
                      ...formData,
                      completed_qty: qty,
                      qualified_qty: Math.min(formData.qualified_qty, qty)
                    });
                  }}
                  placeholder="0"
                  className="text-lg mb-2" />

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                    handleQuickQuantity("completed", workOrder.plan_qty)
                    }
                    className="flex-1">

                    全部完成
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() =>
                    handleQuickQuantity(
                      "completed",
                      Math.floor((workOrder.plan_qty || 0) / 2)
                    )
                    }
                    className="flex-1">

                    一半
                  </Button>
                </div>
              </div>

              {/* 合格数量 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  合格数量
                </label>
                <Input
                  type="number"
                  min="0"
                  max={formData.completed_qty}
                  value={formData.qualified_qty}
                  onChange={(e) => {
                    const qty = parseInt(e.target.value) || 0;
                    setFormData({
                      ...formData,
                      qualified_qty: qty,
                      defect_qty: formData.completed_qty - qty
                    });
                  }}
                  placeholder="0"
                  className="text-lg mb-2" />

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickQuantity("qualified", "all")}
                  className="w-full">

                  全部合格
                </Button>
              </div>

              {/* 不良数量（自动计算） */}
              {formData.completed_qty > 0 &&
              <div className="bg-slate-50 rounded-lg p-3">
                  <div className="text-sm text-slate-500 mb-1">不良数量</div>
                  <div className="text-lg font-medium text-red-600">
                    {formData.completed_qty - formData.qualified_qty}
                    （自动计算）
                  </div>
              </div>
              }

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
                    onChange={handlePhotoUpload}
                    className="hidden"
                    id="photo-upload-complete" />

                  <label
                    htmlFor="photo-upload-complete"
                    className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">

                    <Camera className="w-5 h-5 text-slate-400" />
                    <span className="text-sm text-slate-600">拍照上传</span>
                  </label>
                  {photos.length > 0 &&
                  <div className="grid grid-cols-3 gap-2">
                      {photos.map((photo, idx) =>
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
                        prev.filter((_, i) => i !== idx)
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

              {/* 工时 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  工时 (小时)
                  {workOrder.actual_start_time &&
                  <span className="text-xs text-slate-500 ml-2">
                      已用: {calculateWorkHours(workOrder.actual_start_time)}h
                  </span>
                  }
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.work_hours}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    work_hours: parseFloat(e.target.value) || 0
                  })
                  }
                  placeholder="0"
                  className="text-lg" />

              </div>

              {/* 说明 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  完工说明（可选）
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.report_note}
                  onChange={(e) =>
                  setFormData({ ...formData, report_note: e.target.value })
                  }
                  placeholder="填写完工说明..." />

              </div>
            </div>
          </CardContent>
        </Card>

        {/* 提交按钮 */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-emerald-500 hover:bg-emerald-600 h-12 text-base">

          <CheckCircle2 className="w-5 h-5 mr-2" />
          {loading ? "提交中..." : "确认完工"}
        </Button>
      </div>
    </div>);

}