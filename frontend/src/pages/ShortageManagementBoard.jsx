/**
 * Shortage Management Board Page - 缺料管理看板页面
 * Features: 缺料预警、齐套率、到货跟踪汇总
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Package,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Eye,
  ArrowRight } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import { cn, formatDate } from "../lib/utils";
import { shortageApi, shortageAlertApi } from "../services/api";
export default function ShortageManagementBoard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [boardData, setBoardData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [arrivals, setArrivals] = useState([]);
  useEffect(() => {
    fetchBoardData();
    fetchAlerts();
    fetchArrivals();
  }, []);
  const fetchBoardData = async () => {
    try {
      // Try to get dashboard data from API, if not available, calculate from alerts and arrivals
      try {
        const res = await shortageApi.statistics.dashboard();
        setBoardData(res.data || res);
      } catch (_apiError) {
        // If dashboard API is not available, calculate from existing data
        // This will be populated after fetchAlerts and fetchArrivals complete
        setBoardData({
          total_alerts: 0,
          critical_alerts: 0,
          major_alerts: 0,
          minor_alerts: 0,
          total_arrivals: 0,
          delayed_arrivals: 0,
          pending_arrivals: 0
        });
      }
    } catch (error) {
      console.error("Failed to fetch board data:", error);
      setBoardData({
        total_alerts: 0,
        critical_alerts: 0,
        major_alerts: 0,
        minor_alerts: 0,
        total_arrivals: 0,
        delayed_arrivals: 0,
        pending_arrivals: 0
      });
    }
  };

  // Update board data after alerts and arrivals are loaded
  useEffect(() => {
    if (alerts.length > 0 || arrivals.length > 0) {
      setBoardData((_prev) => ({
        total_alerts: alerts.length,
        critical_alerts: alerts.filter(
          (a) => a.alert_level === "LEVEL1" || a.alert_level === "CRITICAL"
        ).length,
        major_alerts: alerts.filter(
          (a) => a.alert_level === "LEVEL2" || a.alert_level === "MAJOR"
        ).length,
        minor_alerts: alerts.filter(
          (a) =>
          a.alert_level === "LEVEL3" ||
          a.alert_level === "LEVEL4" ||
          a.alert_level === "MINOR"
        ).length,
        total_arrivals: arrivals.length,
        delayed_arrivals: arrivals.filter(
          (a) =>
          a.is_delayed ||
          a.expected_date &&
          a.actual_date &&
          new Date(a.actual_date) > new Date(a.expected_date)
        ).length,
        pending_arrivals: arrivals.filter(
          (a) => !a.actual_date || a.status === "PENDING"
        ).length
      }));
    }
  }, [alerts, arrivals]);
  const fetchAlerts = async () => {
    try {
      const res = await shortageAlertApi.list({ page_size: 10 });
      const alertList = res.data?.items || res.data || [];
      setAlerts(alertList);
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    }
  };
  const fetchArrivals = async () => {
    try {
      const res = await shortageApi.arrivals.list({ page_size: 10 });
      const arrivalList = res.data?.items || res.data || [];
      setArrivals(arrivalList);
    } catch (error) {
      console.error("Failed to fetch arrivals:", error);
    } finally {
      setLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="缺料管理看板"
          description="缺料预警、齐套率、到货跟踪汇总" />

        <Button
          variant="outline"
          onClick={() => {
            fetchBoardData();
            fetchAlerts();
            fetchArrivals();
          }}>

          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">缺料预警总数</div>
                <div className="text-2xl font-bold">
                  {boardData?.total_alerts || alerts.length}
                </div>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">严重预警</div>
                <div className="text-2xl font-bold text-red-600">
                  {boardData?.critical_alerts ||
                  alerts.filter((a) => a.alert_level === "CRITICAL").length}
                </div>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">到货跟踪</div>
                <div className="text-2xl font-bold">
                  {boardData?.total_arrivals || arrivals.length}
                </div>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">延迟到货</div>
                <div className="text-2xl font-bold text-amber-600">
                  {boardData?.delayed_arrivals ||
                  arrivals.filter((a) => a.is_delayed).length}
                </div>
              </div>
              <Clock className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>最新缺料预警</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/shortage-alerts")}>

                查看全部
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ?
            <div className="text-center py-8 text-slate-400">
                暂无缺料预警
              </div> :

            <div className="space-y-3">
                {alerts.slice(0, 5).map((alert) =>
              <div
                key={alert.id}
                className="border rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
                onClick={() => navigate(`/shortage-alerts/${alert.id}`)}>

                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {alert.material_name}
                        </div>
                        <div className="text-xs text-slate-500 mt-1 font-mono">
                          {alert.material_code}
                        </div>
                      </div>
                      <Badge
                    className={cn(
                      alert.alert_level === "CRITICAL" && "bg-red-500",
                      alert.alert_level === "MAJOR" && "bg-orange-500",
                      alert.alert_level === "MINOR" && "bg-amber-500",
                      "bg-slate-500"
                    )}>

                        {alert.alert_level === "CRITICAL" ?
                    "严重" :
                    alert.alert_level === "MAJOR" ?
                    "重要" :
                    alert.alert_level === "MINOR" ?
                    "一般" :
                    alert.alert_level}
                      </Badge>
                    </div>
                    {alert.project_name &&
                <div className="text-xs text-slate-500">
                        项目: {alert.project_name}
                      </div>
                }
                    <div className="text-xs text-slate-500 mt-1">
                      缺料数量:{" "}
                      <span className="font-medium text-red-600">
                        {alert.shortage_qty}
                      </span>
                    </div>
                  </div>
              )}
              </div>
            }
          </CardContent>
        </Card>
        {/* Recent Arrivals */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>到货跟踪</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/arrival-tracking")}>

                查看全部
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {arrivals.length === 0 ?
            <div className="text-center py-8 text-slate-400">
                暂无到货跟踪
              </div> :

            <div className="space-y-3">
                {arrivals.slice(0, 5).map((arrival) =>
              <div
                key={arrival.id}
                className="border rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
                onClick={() => navigate(`/arrival-tracking/${arrival.id}`)}>

                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {arrival.material_name}
                        </div>
                        <div className="text-xs text-slate-500 mt-1 font-mono">
                          {arrival.arrival_no}
                        </div>
                      </div>
                      {arrival.is_delayed &&
                  <Badge variant="destructive">延迟</Badge>
                  }
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-500 mt-2">
                      <div>
                        <span>预期: </span>
                        <span>
                          {arrival.expected_date ?
                      formatDate(arrival.expected_date) :
                      "-"}
                        </span>
                      </div>
                      <div>
                        <span>实际: </span>
                        <span
                      className={
                      arrival.actual_date ?
                      "text-emerald-600" :
                      "text-slate-400"
                      }>

                          {arrival.actual_date ?
                      formatDate(arrival.actual_date) :
                      "未到货"}
                        </span>
                      </div>
                    </div>
                    {arrival.supplier_name &&
                <div className="text-xs text-slate-500 mt-1">
                        供应商: {arrival.supplier_name}
                      </div>
                }
                  </div>
              )}
              </div>
            }
          </CardContent>
        </Card>
      </div>
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate("/shortage-alerts")}>

              <AlertTriangle className="w-6 h-6 mb-2" />
              <span>缺料预警</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate("/shortage-reports")}>

              <Package className="w-6 h-6 mb-2" />
              <span>缺料上报</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate("/arrival-tracking")}>

              <Clock className="w-6 h-6 mb-2" />
              <span>到货跟踪</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate("/kit-rate")}>

              <TrendingUp className="w-6 h-6 mb-2" />
              <span>齐套看板</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>);

}