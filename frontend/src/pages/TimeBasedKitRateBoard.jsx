/**
 * 基于时间的齐套率预警看板
 * 功能：
 * - 显示各阶段齐套率
 * - 预计到货时间
 * - 预警级别（L1-L4）
 * - 是否能赶上计划开工
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  AlertCircle,
  AlertOctagon,
  CheckCircle,
  Clock,
  Calendar,
  Truck,
  Package,
  RefreshCw,
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
  Input,
  Label,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Progress,
} from "../components/ui";
import { assemblyKitApi } from "../services/api";

// 预警级别配置
const WARNING_LEVELS = {
  L1: {
    label: "停工预警",
    color: "bg-red-600",
    textColor: "text-red-600",
    bgLight: "bg-red-500/10 border-red-500",
    icon: AlertOctagon,
    description: "已延期或 3 天内开工但物料未到",
  },
  L2: {
    label: "紧急预警",
    color: "bg-orange-500",
    textColor: "text-orange-600",
    bgLight: "bg-orange-500/10 border-orange-500",
    icon: AlertTriangle,
    description: "7 天内开工，风险高",
  },
  L3: {
    label: "提前预警",
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
    bgLight: "bg-yellow-500/10 border-yellow-500",
    icon: AlertCircle,
    description: "需注意，提前期紧张",
  },
  L4: {
    label: "常规",
    color: "bg-blue-500",
    textColor: "text-blue-600",
    bgLight: "bg-blue-500/10 border-blue-500",
    icon: CheckCircle,
    description: "时间充裕",
  },
};

// 装配阶段名称
const STAGE_NAMES = {
  FRAME: "机架装配",
  MECH: "机械装配",
  ELECTRIC: "电气装配",
  WIRING: "接线",
  DEBUG: "调试",
  COSMETIC: "外观",
};

export default function TimeBasedKitRateBoard() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [plannedStartDate, setPlannedStartDate] = useState("");

  const loadData = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const params = { machine_id: null };
      if (plannedStartDate) params.planned_start_date = plannedStartDate;
      
      const res = await assemblyKitApi.getTimeBasedKitRate(projectId, params);
      setData(res.data || res);
    } catch (error) {
      console.error("加载失败:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId, plannedStartDate]);

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

  if (!data) {
    return (
      <div className="text-center py-12 text-slate-400">
        暂无数据
      </div>
    );
  }

  const summary = data.summary || {};

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
            title="齐套率时间预警看板"
            description="基于采购提前期和生产周期的智能预警"
            actions={
              <div className="flex gap-2 items-center">
                <div>
                  <Label className="text-xs text-slate-400">计划开工日期</Label>
                  <Input
                    type="date"
                    value={plannedStartDate}
                    onChange={(e) => setPlannedStartDate(e.target.value)}
                    className="w-40"
                  />
                </div>
                <Button onClick={loadData} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  刷新
                </Button>
              </div>
            }
          />

          {/* 预警级别说明 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                预警级别说明
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(WARNING_LEVELS).map(([level, config]) => {
                  const Icon = config.icon;
                  return (
                    <div
                      key={level}
                      className={`p-3 rounded-lg border ${config.bgLight}`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className={`w-4 h-4 ${config.textColor}`} />
                        <span className={`font-medium ${config.textColor}`}>
                          {level} - {config.label}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        {config.description}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 预警汇总 */}
          {summary.total_shortage_items > 0 && (
            <Card className="border-red-500/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-500">
                  <AlertOctagon className="w-5 h-5" />
                  缺料预警汇总
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-sm text-slate-400">缺料物料数</div>
                    <div className="text-2xl font-bold text-white">
                      {summary.total_shortage_items}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">紧急缺料</div>
                    <div className="text-2xl font-bold text-orange-500">
                      {summary.total_urgent_items}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">停工风险 (L1)</div>
                    <div className="text-2xl font-bold text-red-500">
                      {summary.l1_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400">紧急风险 (L2)</div>
                    <div className="text-2xl font-bold text-orange-500">
                      {summary.l2_count}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 各阶段分析 */}
          {data.stages && Object.entries(data.stages).map(([stageCode, stageData]) => {
            const stageName = STAGE_NAMES[stageCode] || stageCode;
            const warningLevel = stageData.overall_warning || "L4";
            const warningConfig = WARNING_LEVELS[warningLevel];
            const WarningIcon = warningConfig.icon;

            return (
              <Card key={stageCode} className={`border ${warningConfig.bgLight}`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <WarningIcon className={`w-5 h-5 ${warningConfig.textColor}`} />
                      <div>
                        <CardTitle>{stageName}</CardTitle>
                        <CardDescription className={warningConfig.textColor}>
                          {warningConfig.label} - {warningConfig.description}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm text-slate-400">齐套率</div>
                        <div className="text-2xl font-bold">
                          {stageData.comprehensive_kit_rate?.toFixed(1) || 0}%
                        </div>
                      </div>
                      <Badge variant={warningLevel === "L1" ? "destructive" : "outline"}>
                        {warningLevel}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* 齐套率进度条 */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-400">整体齐套率</span>
                      <span className="text-slate-300">
                        {stageData.fulfilled_items || 0} / {stageData.total_items || 0} 项
                      </span>
                    </div>
                    <Progress
                      value={stageData.comprehensive_kit_rate || 0}
                      className="h-2"
                    />
                  </div>

                  {/* 缺料明细 */}
                  {stageData.shortage_items && stageData.shortage_items.length > 0 && (
                    <div>
                      <div className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Package className="w-4 h-4 text-slate-400" />
                        缺料明细（考虑采购提前期）
                      </div>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>物料编码</TableHead>
                            <TableHead>物料名称</TableHead>
                            <TableHead>缺料数</TableHead>
                            <TableHead>预计到货</TableHead>
                            <TableHead>提前期</TableHead>
                            <TableHead>距开工</TableHead>
                            <TableHead>预警</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {stageData.shortage_items.map((item, idx) => {
                            const itemWarning = WARNING_LEVELS[item.warning_level];
                            const daysToStart = item.days_to_start;
                            
                            return (
                              <TableRow key={idx} className={itemWarning.bgLight}>
                                <TableCell className="font-mono text-sm">
                                  {item.material_code}
                                </TableCell>
                                <TableCell>{item.material_name}</TableCell>
                                <TableCell className="text-red-500 font-medium">
                                  -{item.shortage_qty.toFixed(1)}
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-1">
                                    <Truck className="w-3 h-3 text-slate-400" />
                                    {item.estimated_arrival || "未下单"}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-1">
                                    <Clock className="w-3 h-3 text-slate-400" />
                                    {item.lead_time_days}天
                                  </div>
                                </TableCell>
                                <TableCell>
                                  {daysToStart !== null ? (
                                    <span className={daysToStart < 0 ? "text-red-500" : daysToStart < 7 ? "text-orange-500" : "text-green-500"}>
                                      {daysToStart < 0 ? `延期${Math.abs(daysToStart)}天` : `${daysToStart}天`}
                                    </span>
                                  ) : (
                                    "-"
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Badge variant={itemWarning.color} className="text-white">
                                    {item.warning_level}
                                  </Badge>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}
