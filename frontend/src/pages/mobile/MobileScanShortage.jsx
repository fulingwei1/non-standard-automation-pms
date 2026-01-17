/**
 * Mobile Scan Shortage - 移动端扫码上报缺料
 * 功能：扫码工单，选择物料，上报缺料
 */
import { useState, useEffect as _useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  QrCode,
  Scan,
  Package,
  AlertCircle,
  Camera } from
"lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn as _cn } from "../../lib/utils";
import { productionApi } from "../../services/api";

export default function MobileScanShortage() {
  const navigate = useNavigate();
  const [scanInput, setScanInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [error, setError] = useState("");

  const handleScan = async () => {
    if (!scanInput.trim()) {
      setError("请输入工单号");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const res = await productionApi.workOrders.list({
        search: scanInput,
        page_size: 10
      });
      const orders = res.data?.items || res.data || [];
      const order = orders.find((o) => o.work_order_no === scanInput);

      if (!order) {
        setError("未找到工单: " + scanInput);
        return;
      }

      setWorkOrder(order);
      // 跳转到上报表单页，带上工单ID
      navigate(`/mobile/shortage-report?workOrderId=${order.id}`);
    } catch (error) {
      console.error("Failed to scan work order:", error);
      setError(
        "查找工单失败: " + (error.response?.data?.detail || error.message)
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
            <h1 className="text-lg font-semibold">扫码上报缺料</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 扫码输入框 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-red-50 mb-4">
                  <QrCode className="w-10 h-10 text-red-500" />
                </div>
                <h2 className="text-lg font-semibold mb-2">扫描工单二维码</h2>
                <p className="text-sm text-slate-500">或手动输入工单号</p>
              </div>

              <div className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    value={scanInput}
                    onChange={(e) => setScanInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        handleScan();
                      }
                    }}
                    placeholder="扫描或输入工单号"
                    className="flex-1 text-lg"
                    autoFocus />

                  <Button
                    onClick={handleScan}
                    disabled={loading}
                    className="px-6">

                    <Scan className="w-5 h-5" />
                  </Button>
                </div>

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    // TODO: 打开相机扫码
                    alert("扫码功能需要调用相机API");
                  }}>

                  <Camera className="w-4 h-4 mr-2" />
                  打开相机扫码
                </Button>
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

        {/* 工单信息预览 */}
        {workOrder &&
        <Card>
            <CardContent className="pt-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">工单信息</h3>
                  <Badge className="bg-blue-500">{workOrder.status}</Badge>
                </div>
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
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div className="text-base">
                    {workOrder.project_name || "-"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        }

        {/* 快捷入口 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <h3 className="font-medium mb-3">快捷操作</h3>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate("/mobile/shortage-report")}>

                <Package className="w-4 h-4 mr-2" />
                直接上报缺料（不扫码）
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate("/mobile/my-shortage-reports")}>

                <Package className="w-4 h-4 mr-2" />
                我的上报记录
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>);

}