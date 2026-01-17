/**
 * Mobile Scan Start - 移动端扫码开工
 * 功能：扫码或输入工单号，快速开工
 */
import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  QrCode,
  Scan,
  CheckCircle2,
  AlertCircle,
  Camera } from
"lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn as _cn } from "../../lib/utils";
import { productionApi } from "../../services/api";

const statusConfigs = {
  PENDING: { label: "待派工", color: "bg-slate-500" },
  ASSIGNED: { label: "待开工", color: "bg-blue-500" },
  STARTED: { label: "已开始", color: "bg-amber-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" }
};

export default function MobileScanStart() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workOrderId = searchParams.get("workOrderId");

  const [scanInput, setScanInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [workOrder, setWorkOrder] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder(workOrderId);
    }
  }, [workOrderId]);

  const fetchWorkOrder = async (id) => {
    try {
      setLoading(true);
      setError("");
      const res = await productionApi.workOrders.get(id);
      const order = res.data;

      if (order.status !== "ASSIGNED") {
        setError(
          `工单状态为"${statusConfigs[order.status]?.label || order.status}"，无法开工`
        );
        return;
      }

      setWorkOrder(order);
    } catch (error) {
      console.error("Failed to fetch work order:", error);
      setError(
        "查找工单失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

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

      if (order.status !== "ASSIGNED") {
        setError(
          `工单状态为"${statusConfigs[order.status]?.label || order.status}"，无法开工`
        );
        return;
      }

      setWorkOrder(order);
    } catch (error) {
      console.error("Failed to scan work order:", error);
      setError(
        "查找工单失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    if (!workOrder) return;

    try {
      setLoading(true);
      setError("");
      await productionApi.workReports.start({
        work_order_id: workOrder.id,
        report_note: ""
      });
      setSuccess(true);
      setTimeout(() => {
        navigate("/mobile/tasks");
      }, 1500);
    } catch (error) {
      console.error("Failed to start work:", error);
      setError("开工失败: " + (error.response?.data?.detail || error.message));
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
            <h1 className="text-lg font-semibold">扫码开工</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 扫码输入框 */}
        {!workOrder &&
        <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-blue-50 mb-4">
                    <QrCode className="w-10 h-10 text-blue-500" />
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
                开工成功！
              </div>
            </div>
          </div>
        }

        {/* 工单信息 */}
        {workOrder && !success &&
        <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">工单信息</h2>
                  <Badge
                  className={
                  statusConfigs[workOrder.status]?.color || "bg-slate-500"
                  }>

                    {statusConfigs[workOrder.status]?.label || workOrder.status}
                  </Badge>
                </div>

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
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div className="text-base">
                      {workOrder.project_name || "-"}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间/工位</div>
                    <div className="text-base">
                      {workOrder.workshop_name || "-"} /{" "}
                      {workOrder.workstation_name || "-"}
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划数量</div>
                    <div className="font-medium text-base">
                      {workOrder.plan_qty || 0}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-200">
                  <Button
                  onClick={handleStart}
                  disabled={loading}
                  className="w-full bg-blue-500 hover:bg-blue-600 h-12 text-base">

                    {loading ? "开工中..." : "确认开工"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        }
      </div>
    </div>);

}