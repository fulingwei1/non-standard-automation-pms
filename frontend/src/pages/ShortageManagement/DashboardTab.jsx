import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Package, AlertTriangle, Truck, Clock, Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { staggerContainer } from "../../lib/animations";
import { statusConfigs, urgentLevelConfigs } from "./constants";

/**
 * DashboardTab
 *
 * Renders the 看板 (dashboard) summary cards and the recent reports list.
 * Props:
 *   dashboardData — the data object returned by shortageApi.statistics.dashboard()
 */
export function DashboardTab({ dashboardData }) {
  const navigate = useNavigate();

  if (!dashboardData) return null;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4"
      >
        {/* 缺料上报总数 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">缺料上报总数</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.reports?.total || 0}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="bg-blue-500/20 text-blue-400">
                已上报: {dashboardData.reports?.reported || 0}
              </Badge>
              <Badge
                variant="outline"
                className="bg-amber-500/20 text-amber-400"
              >
                处理中: {dashboardData.reports?.handling || 0}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* 紧急缺料 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">紧急缺料</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-400">
              {dashboardData.reports?.urgent || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-2">需要立即处理</p>
          </CardContent>
        </Card>

        {/* 到货跟踪 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">到货跟踪</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData.arrivals?.total || 0}
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge
                variant="outline"
                className="bg-amber-500/20 text-amber-400"
              >
                待处理: {dashboardData.arrivals?.pending || 0}
              </Badge>
              <Badge variant="outline" className="bg-red-500/20 text-red-400">
                延迟: {dashboardData.arrivals?.delayed || 0}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* 待审批 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">待审批</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(dashboardData.substitutions?.pending || 0) +
                (dashboardData.transfers?.pending || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              替代: {dashboardData.substitutions?.pending || 0} | 调拨:{" "}
              {dashboardData.transfers?.pending || 0}
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent reports */}
      {dashboardData.recent_reports?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>最近缺料上报</CardTitle>
            <CardDescription>最近10条缺料上报记录</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(dashboardData.recent_reports || []).map((report) => {
                const urgent =
                  urgentLevelConfigs[report.urgent_level] ||
                  urgentLevelConfigs.NORMAL;
                const status =
                  statusConfigs[report.status] || statusConfigs.REPORTED;
                return (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-2 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{report.report_no}</span>
                        <Badge
                          variant="outline"
                          className={cn(urgent.color)}
                        >
                          {urgent.label}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={cn(status.color, "text-white")}
                        >
                          {status.label}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {report.project_name} - {report.material_name}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">
                        缺料: {report.shortage_qty}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          navigate(`/shortage/reports/${report.id}`)
                        }
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
