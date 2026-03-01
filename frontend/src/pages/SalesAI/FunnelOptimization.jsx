/**
 * 销售漏斗优化页面
 * 
 * 功能：
 * 1. 转化率分析
 * 2. 瓶颈识别
 * 3. 预测准确性
 * 4. 健康度仪表盘
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  Target,
  Zap,
  ArrowRight,
  BarChart3,
  Activity,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
} from "../../components/ui";

// 转化率分析组件
function ConversionRates() {
  const [funnelData, setFunnelData] = useState(null);

  useEffect(() => {
    // 模拟数据
    setFunnelData({
      stages: [
        { stage: "STAGE1", stage_name: "初步接触", count: 45, conversion_to_next: 62.2, avg_days_in_stage: 5.2, trend: "up" },
        { stage: "STAGE2", stage_name: "需求挖掘", count: 28, conversion_to_next: 53.6, avg_days_in_stage: 7.8, trend: "stable" },
        { stage: "STAGE3", stage_name: "方案介绍", count: 15, conversion_to_next: 66.7, avg_days_in_stage: 10.5, trend: "up" },
        { stage: "STAGE4", stage_name: "价格谈判", count: 10, conversion_to_next: 50.0, avg_days_in_stage: 8.3, trend: "down" },
        { stage: "STAGE5", stage_name: "成交促成", count: 5, conversion_to_next: 80.0, avg_days_in_stage: 4.1, trend: "stable" },
        { stage: "WON", stage_name: "赢单", count: 4, conversion_to_next: null, avg_days_in_stage: null, trend: "up" },
      ],
      overall_metrics: {
        total_leads: 45,
        total_won: 4,
        overall_conversion_rate: 8.9,
        avg_sales_cycle_days: 35.9,
        total_pipeline_value: 15800000,
        weighted_pipeline_value: 6320000,
      },
    });
  }, []);

  if (!funnelData) return <div>加载中...</div>;

  return (
    <div className="space-y-6">
      {/* 整体指标 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">总线索数</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics.total_leads}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">赢单数</div>
            <div className="text-2xl font-bold text-green-500">{funnelData.overall_metrics.total_won}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">整体转化率</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics.overall_conversion_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">平均销售周期</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics.avg_sales_cycle_days}天</div>
          </CardContent>
        </Card>
      </div>

      {/* 漏斗可视化 */}
      <Card>
        <CardHeader>
          <CardTitle>销售漏斗转化率</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {funnelData.stages.map((stage, idx) => (
              <div key={stage.stage} className="flex items-center gap-4">
                <div className="w-32 text-sm font-medium">{stage.stage_name}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">{stage.count}个商机</span>
                    {stage.conversion_to_next && (
                      <span className={`text-sm ${stage.conversion_to_next < 55 ? 'text-red-500' : 'text-green-500'}`}>
                        转化率 {stage.conversion_to_next}%
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress 
                      value={(stage.count / funnelData.overall_metrics.total_leads) * 100} 
                      className="h-3 flex-1"
                    />
                    {stage.trend === "up" && <TrendingUp className="w-4 h-4 text-green-500" />}
                    {stage.trend === "down" && <TrendingDown className="w-4 h-4 text-red-500" />}
                    {stage.trend === "stable" && <Activity className="w-4 h-4 text-slate-400" />}
                  </div>
                </div>
                {stage.avg_days_in_stage && (
                  <div className="w-24 text-sm text-slate-400 text-right">
                    平均{stage.avg_days_in_stage}天
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 瓶颈识别组件
function Bottlenecks() {
  const [bottlenecks, setBottlenecks] = useState([
    {
      stage: "STAGE4",
      stage_name: "价格谈判",
      issue_type: "low_conversion",
      current_rate: 50.0,
      benchmark_rate: 65.0,
      gap: -15.0,
      severity: "HIGH",
      impact: "每月约损失 3-5 个商机，预计金额 800-1200 万",
      root_causes: ["价格异议处理能力不足", "价值传递不够清晰", "决策链渗透不够深入"],
      recommendations: ["加强价格谈判培训", "准备 TCO（总拥有成本）分析工具", "提前识别并接触技术/采购决策人"],
    },
    {
      stage: "STAGE2",
      stage_name: "需求挖掘",
      issue_type: "long_stay",
      current_days: 7.8,
      benchmark_days: 5.0,
      gap: 2.8,
      severity: "MEDIUM",
      impact: "销售周期延长，影响整体效率",
      root_causes: ["需求调研不够系统化", "客户配合度低"],
      recommendations: ["使用标准化需求调研模板", "设定明确的客户反馈截止时间"],
    },
  ]);

  return (
    <div className="space-y-4">
      {bottlenecks.map((bottleneck, idx) => (
        <Card key={idx} className={bottleneck.severity === "HIGH" ? "border-red-500" : "border-orange-500"}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className={`w-5 h-5 ${bottleneck.severity === "HIGH" ? "text-red-500" : "text-orange-500"}`} />
                {bottleneck.stage_name}
              </CardTitle>
              <Badge variant={bottleneck.severity === "HIGH" ? "destructive" : "secondary"}>
                {bottleneck.severity === "HIGH" ? "严重" : "中等"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-400">问题</div>
                <div className="text-lg font-medium">
                  {bottleneck.issue_type === "low_conversion" 
                    ? `转化率 ${bottleneck.current_rate}%（基准${bottleneck.benchmark_rate}%）`
                    : `停留${bottleneck.current_days}天（基准${bottleneck.benchmark_days}天）`
                  }
                </div>
              </div>
              
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <div className="text-sm">{bottleneck.impact}</div>
              </Alert>

              <div>
                <div className="text-sm text-slate-400 mb-2">根本原因</div>
                <div className="flex flex-wrap gap-2">
                  {bottleneck.root_causes.map((cause, i) => (
                    <Badge key={i} variant="outline">{cause}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-sm text-slate-400 mb-2">改进建议</div>
                <div className="space-y-2">
                  {bottleneck.recommendations.map((rec, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm">
                      <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
                      {rec}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// 预测准确性组件
function PredictionAccuracy() {
  const [accuracyData, setAccuracyData] = useState({
    overall_accuracy: {
      predicted_win_rate: 68.5,
      actual_win_rate: 62.9,
      accuracy_score: 91.8,
      bias: "略微乐观",
    },
    by_stage: [
      { stage: "STAGE1", predicted: 25.0, actual: 18.5, accuracy: 74.0, bias: "乐观" },
      { stage: "STAGE2", predicted: 45.0, actual: 42.3, accuracy: 94.0, bias: "准确" },
      { stage: "STAGE3", predicted: 65.0, actual: 68.2, accuracy: 95.1, bias: "准确" },
      { stage: "STAGE4", predicted: 80.0, actual: 71.4, accuracy: 89.3, bias: "乐观" },
      { stage: "STAGE5", predicted: 90.0, actual: 88.9, accuracy: 98.8, bias: "准确" },
    ],
  });

  return (
    <div className="space-y-6">
      {/* 整体准确性 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">预测赢单率</div>
            <div className="text-2xl font-bold">{accuracyData.overall_accuracy.predicted_win_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">实际赢单率</div>
            <div className="text-2xl font-bold">{accuracyData.overall_accuracy.actual_win_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">准确性评分</div>
            <div className="text-2xl font-bold text-green-500">{accuracyData.overall_accuracy.accuracy_score}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">偏差</div>
            <div className="text-2xl font-bold text-orange-500">{accuracyData.overall_accuracy.bias}</div>
          </CardContent>
        </Card>
      </div>

      {/* 各阶段对比 */}
      <Card>
        <CardHeader>
          <CardTitle>各阶段预测准确性</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>阶段</TableHead>
                <TableHead>预测赢单率</TableHead>
                <TableHead>实际赢单率</TableHead>
                <TableHead>差距</TableHead>
                <TableHead>准确性</TableHead>
                <TableHead>评估</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accuracyData.by_stage.map((stage) => (
                <TableRow key={stage.stage}>
                  <TableCell className="font-medium">{stage.stage}</TableCell>
                  <TableCell>{stage.predicted}%</TableCell>
                  <TableCell>{stage.actual}%</TableCell>
                  <TableCell className={stage.predicted > stage.actual ? "text-red-500" : "text-green-500"}>
                    {stage.predicted > stage.actual ? "+" : ""}{(stage.predicted - stage.actual).toFixed(1)}%
                  </TableCell>
                  <TableCell>
                    <Progress value={stage.accuracy} className="w-20 h-2" />
                  </TableCell>
                  <TableCell>
                    <Badge variant={stage.bias === "准确" ? "default" : "secondary"}>
                      {stage.bias}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function FunnelOptimization() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售漏斗优化"
          description="分析转化率、识别瓶颈、提升预测准确性"
          icon={<BarChart3 className="w-6 h-6 text-blue-500" />}
        />

        <Tabs defaultValue="conversion" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="conversion">
              <TrendingUp className="w-4 h-4 mr-2" />
              转化率分析
            </TabsTrigger>
            <TabsTrigger value="bottlenecks">
              <AlertTriangle className="w-4 h-4 mr-2" />
              瓶颈识别
            </TabsTrigger>
            <TabsTrigger value="accuracy">
              <Target className="w-4 h-4 mr-2" />
              预测准确性
            </TabsTrigger>
          </TabsList>

          <TabsContent value="conversion" className="mt-6">
            <ConversionRates />
          </TabsContent>

          <TabsContent value="bottlenecks" className="mt-6">
            <Bottlenecks />
          </TabsContent>

          <TabsContent value="accuracy" className="mt-6">
            <PredictionAccuracy />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
