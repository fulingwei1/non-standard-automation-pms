/**
 * Mobile Exception Report - 移动端异常上报
 * 功能：拍照上报生产异常
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  AlertTriangle,
  Camera,
  X,
  CheckCircle2,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { cn } from "../../lib/utils";
import { productionApi } from "../../services/api";

const exceptionTypes = [
  { value: "QUALITY", label: "质量问题" },
  { value: "EQUIPMENT", label: "设备故障" },
  { value: "MATERIAL", label: "物料问题" },
  { value: "PROCESS", label: "工艺问题" },
  { value: "SAFETY", label: "安全问题" },
  { value: "OTHER", label: "其他" },
];

const urgentLevels = [
  { value: "LOW", label: "低" },
  { value: "MEDIUM", label: "中" },
  { value: "HIGH", label: "高" },
  { value: "URGENT", label: "紧急" },
];

export default function MobileExceptionReport() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workOrderId = searchParams.get("workOrderId");

  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [photos, setPhotos] = useState([]);
  const [formData, setFormData] = useState({
    exception_type: "",
    urgent_level: "MEDIUM",
    description: "",
    location: "",
  });

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder();
    }
  }, [workOrderId]);

  const fetchWorkOrder = async () => {
    try {
      const res = await productionApi.workOrders.get(workOrderId);
      setWorkOrder(res.data);
    } catch (error) {
      console.error("Failed to fetch work order:", error);
    }
  };

  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const photoUrl = event.target.result;
        setPhotos((prev) => [...prev, { url: photoUrl, file }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const handleSubmit = async () => {
    if (!formData.exception_type) {
      setError("请选择异常类型");
      return;
    }
    if (!formData.description.trim()) {
      setError("请填写异常描述");
      return;
    }

    try {
      setLoading(true);
      setError("");

      // Upload photos to server (convert to base64 for now)
      // TODO: Replace with actual file upload API when available
      const photoUrls = await Promise.all(
        photos.map(async (photo) => {
          if (photo.url.startsWith("data:")) {
            // Already base64, return as is
            return photo.url;
          }
          // Convert file to base64 if needed
          return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => resolve(photo.url); // Fallback to original URL
            reader.readAsDataURL(photo.file);
          });
        }),
      );

      await productionApi.exceptions.create({
        work_order_id: workOrderId ? parseInt(workOrderId) : null,
        exception_type: formData.exception_type,
        urgent_level: formData.urgent_level,
        description: formData.description,
        location: formData.location,
        photos: photoUrls,
      });

      setSuccess(true);
      setTimeout(() => {
        navigate("/mobile/tasks");
      }, 1500);
    } catch (error) {
      console.error("Failed to report exception:", error);
      setError(
        "异常上报失败: " + (error.response?.data?.detail || error.message),
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
              className="p-2"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold">异常上报</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 工单信息 */}
        {workOrder && (
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
        )}

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-800">{error}</div>
            </div>
          </div>
        )}

        {/* 成功提示 */}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <div className="flex-1">
              <div className="text-sm font-medium text-emerald-800">
                异常上报成功！
              </div>
            </div>
          </div>
        )}

        {/* 表单 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* 异常类型 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  异常类型 *
                </label>
                <Select
                  value={formData.exception_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, exception_type: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="请选择异常类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {exceptionTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {urgentLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* 异常描述 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  异常描述 *
                </label>
                <textarea
                  className="w-full min-h-[120px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="详细描述异常情况..."
                />
              </div>

              {/* 位置 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  发生位置（可选）
                </label>
                <Input
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                  placeholder="车间/工位"
                />
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
                    id="photo-upload-exception"
                  />
                  <label
                    htmlFor="photo-upload-exception"
                    className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
                  >
                    <Camera className="w-5 h-5 text-slate-400" />
                    <span className="text-sm text-slate-600">
                      拍照上传（可多张）
                    </span>
                  </label>
                  {photos.length > 0 && (
                    <div className="grid grid-cols-3 gap-2">
                      {photos.map((photo, idx) => (
                        <div
                          key={idx}
                          className="relative aspect-square rounded-lg overflow-hidden"
                        >
                          <img
                            src={photo.url}
                            alt={`Photo ${idx + 1}`}
                            className="w-full h-full object-cover"
                          />
                          <button
                            type="button"
                            onClick={() =>
                              setPhotos((prev) =>
                                prev.filter((_, i) => i !== idx),
                              )
                            }
                            className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 提交按钮 */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-red-500 hover:bg-red-600 h-12 text-base"
        >
          <AlertTriangle className="w-5 h-5 mr-2" />
          {loading ? "提交中..." : "提交异常"}
        </Button>
      </div>
    </div>
  );
}
