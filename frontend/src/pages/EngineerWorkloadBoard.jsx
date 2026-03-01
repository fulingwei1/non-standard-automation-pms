/**
 * 工程师工作量预警看板
 * 功能：
 * - 工程师负载分析
 * - 任务冲突检测
 * - 风险预警
 * - 排产决策支持
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Users,
  Clock,
  TrendingUp,
  AlertOctagon,
  RefreshCw,
  BarChart3,
  Calendar,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui";
import { engineerSchedulingApi } from "../services/api";

// 预警级别配置
const WARNING_LEVELS = {
  CRITICAL: { label: "严重", color: "bg-red-700", textColor: "text-red-700" },
  HIGH: { label: "高", color: "bg-red-600", textColor: "text-red-600" },
  MEDIUM: { label: "中", color: "bg-orange-500", textColor: "text-orange-600" },
  LOW: { label: "低", color: "bg-yellow-500", textColor: "text-yellow-600" },
};

// 负载状态配置
const WORKLOAD_STATUS = {
  OVERLOAD: { label: "过载", color: "bg-red-500", icon: AlertOctagon },
  BUSY: { label: "繁忙", color: "bg-orange-500", icon: AlertTriangle },
  NORMAL: { label: "正常", color: "bg-green-500", icon: CheckCircle },
  IDLE: { label: "空闲", color: "bg-blue-500", icon: Clock },
};

export default function EngineerWorkloadBoard() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [showConflictDetail, setShowConflictDetail] = useState(false);
  const [selectedEngineer, setSelectedEngineer] = useState(null);

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      // 获取排产报告
      const reportRes = await engineerSchedulingApi.getSchedulingReport(projectId);
      setReport(reportRes.data || reportRes);

      // 获取预警
      const warningsRes = await engineerSchedulingApi.generateWarnings({ project_id: projectId });
      setWarnings(warningsRes.data?.warnings || []);
    } catch (error) {
      console.error("加载失败:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
        <span className="text-slate-400">加载中...</span>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="text-center py-12 text-slate-400">
        暂无数据
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="工程师工作量预警看板"
            description="智能排产与风险预警系统"
            actions={
              <Button onClick={loadData} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            }
          />

          {/* 预警汇总 */}
          {warnings.length > 0 && (
            <Card className="border-red-500/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-500">
                  <AlertTriangle className="w-5 h-5" />
                  风险预警（{warnings.length}条）
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {warnings.map((warning, idx) => {
                    const levelConfig = WARNING_LEVELS[warning.warning_level];
                    return (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${levelConfig.color} bg-opacity-10`}
                      >
                        <div className={`font-medium ${levelConfig.textColor} mb-1`}>
                          {levelConfig.label} - {warning.title}
                        </div>
                        <div className="text-sm text-slate-400 mb-2">
                          {warning.description}
                        </div>
                        <div className="text-xs text-slate-500">
                          💡 {warning.suggestion}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 项目概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-8 h-8 text-blue-500" />
                  <div>
                    <div className="text-sm text-slate-400">总任务数</div>
                    <div className="text-2xl font-bold">{report.total_tasks}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Users className="w-8 h-8 text-green-500" />
                  <div>
                    <div className="text-sm text-slate-400">工程师数</div>
                    <div className="text-2xl font-bold">{report.total_engineers}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-8 h-8 text-orange-500" />
                  <div>
                    <div className="text-sm text-slate-400">冲突数</div>
                    <div className="text-2xl font-bold text-orange-500">
                      {report.total_conflicts}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <Calendar className="w-8 h-8 text-purple-500" />
                  <div>
                    <div className="text-sm text-slate-400">生成时间</div>
                    <div className="text-sm font-medium">
                      {new Date(report.generated_at).toLocaleString('zh-CN')}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 工程师负载分析 */}
          <Card>
            <CardHeader>
              <CardTitle>工程师负载分析</CardTitle>
              <CardDescription>
                实时监控每位工程师的工作量和任务冲突
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>工程师</TableHead>
                    <TableHead>任务数</TableHead>
                    <TableHead>总工时</TableHead>
                    <TableHead>负载状态</TableHead>
                    <TableHead>预警级别</TableHead>
                    <TableHead>冲突数</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(report.engineer_analysis || {}).map(([engId, data]) => {
                    const statusConfig = WORKLOAD_STATUS[data.workload_status];
                    const StatusIcon = statusConfig?.icon || Clock;

                    return (
                      <TableRow key={engId}>
                        <TableCell className="font-medium">
                          {data.engineer_name}
                        </TableCell>
                        <TableCell>{data.task_count}</TableCell>
                        <TableCell>{data.total_hours}h</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`${statusConfig?.color} text-white`}
                          >
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {statusConfig?.label || data.workload_status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {data.warning_level ? (
                            <Badge
                              variant="outline"
                              className={WARNING_LEVELS[data.warning_level]?.color + " text-white"}
                            >
                              {WARNING_LEVELS[data.warning_level]?.label}
                            </Badge>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {data.conflicts?.length > 0 ? (
                            <Badge variant="destructive">
                              {data.conflicts.length}
                            </Badge>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedEngineer({ id: engId, ...data });
                              setShowConflictDetail(true);
                            }}
                          >
                            详情
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 排产建议 */}
          {report.suggestions?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-blue-500" />
                  排产建议
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {report.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      {suggestion.includes('⚠️') ? (
                        <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5" />
                      ) : suggestion.includes('💡') ? (
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5" />
                      )}
                      <span className="text-slate-300">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* 冲突详情对话框 */}
          <Dialog open={showConflictDetail} onOpenChange={setShowConflictDetail}>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>
                  {selectedEngineer?.engineer_name} - 任务冲突详情
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-400">任务数</div>
                    <div className="text-xl font-bold">
                      {selectedEngineer?.task_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">总工时</div>
                    <div className="text-xl font-bold">
                      {selectedEngineer?.total_hours}h
                    </div>
                  </div>
                </div>

                {selectedEngineer?.conflicts?.length > 0 ? (
                  <div>
                    <div className="text-sm font-medium mb-2">冲突列表</div>
                    <div className="space-y-2">
                      {selectedEngineer.conflicts.map((conflict, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg border bg-red-500/10 border-red-500/50"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-red-500">
                              冲突 {idx + 1}
                            </span>
                            <Badge variant="destructive">
                              {conflict.severity}
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400">
                            重叠{conflict.overlap_days}天（
                            {conflict.overlap_start} 至 {conflict.overlap_end}）
                          </div>
                          <div className="text-xs text-slate-500 mt-1">
                            💡 {conflict.suggestion}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                    无任务冲突
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button onClick={() => setShowConflictDetail(false)}>
                  关闭
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
