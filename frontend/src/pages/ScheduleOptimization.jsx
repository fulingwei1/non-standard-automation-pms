/**
 * AI 智能优化分析页面
 * 功能：
 * - 分析可节省时间的环节
 * - 识别可复用内容
 * - 自动化建议
 */

import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Sparkles,
  TrendingDown,
  Clock,
  CheckCircle,
  AlertCircle,
  Zap,
  Copy,
  RefreshCw,
  ArrowRight,
  Package,
  FileText,
  ShoppingCart,
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
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertTitle,
  AlertDescription,
} from "../components/ui";
import { scheduleOptimizationApi } from "../services/api";

export default function ScheduleOptimization() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const runAnalysis = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await scheduleOptimizationApi.analyzeOptimization(projectId);
      setAnalysis(res.data || res);
    } catch (error) {
      console.error("分析失败:", error);
      alert("分析失败：" + error.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    runAnalysis();
  }, [runAnalysis]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Sparkles className="w-6 h-6 animate-pulse text-purple-500 mr-2" />
        <span className="text-slate-400">AI 分析优化潜力中...</span>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-12 text-slate-400">
        分析失败
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
            title="AI 智能优化分析"
            description="分析可节省时间的环节，自动复用历史项目内容"
            actions={
              <Button onClick={runAnalysis} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                重新分析
              </Button>
            }
          />

          {/* 总体优化潜力 */}
          <Card className="border-purple-500/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-purple-500">
                <Sparkles className="w-5 h-5" />
                优化潜力总览
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">当前工期</div>
                  <div className="text-2xl font-bold">
                    {analysis.time_savings?.total_current_days}天
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">可优化工期</div>
                  <div className="text-2xl font-bold text-green-500">
                    {analysis.time_savings?.total_optimizable_days}天
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">可节省</div>
                  <div className="text-2xl font-bold text-orange-500">
                    {analysis.time_savings?.total_savings_days}天
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">优化潜力</div>
                  <div className="text-2xl font-bold text-purple-500">
                    {analysis.overall_optimization_score?.toFixed(0)}分
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">优化进度</span>
                  <span className="text-sm font-medium">
                    {analysis.time_savings?.savings_percentage}%
                  </span>
                </div>
                <Progress
                  value={analysis.time_savings?.savings_percentage}
                  className="h-3"
                />
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="phases" className="space-y-4">
            <TabsList>
              <TabsTrigger value="phases">环节优化</TabsTrigger>
              <TabsTrigger value="reusable">可复用内容</TabsTrigger>
              <TabsTrigger value="automation">自动化建议</TabsTrigger>
            </TabsList>

            {/* 环节优化 */}
            <TabsContent value="phases" className="space-y-4">
              {Object.entries(analysis.optimization_analysis || {}).map(
                ([phaseKey, phaseData]) => (
                  <Card key={phaseKey}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle>{phaseData.phase_name}</CardTitle>
                          <CardDescription>
                            当前{phaseData.current_duration}天 → 可优化至{phaseData.optimizable_duration}天
                          </CardDescription>
                        </div>
                        <Badge variant="destructive">
                          节省{phaseData.potential_savings}天
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {phaseData.optimizations?.map((opt, idx) => (
                          <Alert
                            key={idx}
                            className={
                              opt.confidence === 'HIGH'
                                ? 'border-green-500 bg-green-500/10'
                                : opt.confidence === 'MEDIUM'
                                ? 'border-blue-500 bg-blue-500/10'
                                : 'border-yellow-500 bg-yellow-500/10'
                            }
                          >
                            <CheckCircle className="h-4 w-4" />
                            <AlertTitle className="flex items-center gap-2">
                              {opt.title}
                              <Badge
                                variant={
                                  opt.confidence === 'HIGH'
                                    ? 'default'
                                    : 'secondary'
                                }
                                className="text-xs"
                              >
                                {opt.confidence}
                              </Badge>
                            </AlertTitle>
                            <AlertDescription className="mt-2">
                              <div className="text-sm">{opt.description}</div>
                              <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  节省{opt.potential_savings_days}天
                                </span>
                                <span className="flex items-center gap-1">
                                  <Zap className="w-3 h-3" />
                                  {opt.action}
                                </span>
                              </div>
                            </AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )
              )}
            </TabsContent>

            {/* 可复用内容 */}
            <TabsContent value="reusable" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    设计文档复用
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>来源项目</TableHead>
                        <TableHead>相似度</TableHead>
                        <TableHead>可复用内容</TableHead>
                        <TableHead>复用率</TableHead>
                        <TableHead>操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(analysis.reusable_content?.design_documents || []).map(
                        (doc, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">
                              {doc.project_name}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  doc.similarity === 'HIGH'
                                    ? 'default'
                                    : 'secondary'
                                }
                              >
                                {doc.similarity}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-1">
                                {doc.items?.map((item, i) => (
                                  <Badge key={i} variant="outline">
                                    {item}
                                  </Badge>
                                ))}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress
                                  value={doc.reuse_rate}
                                  className="w-20 h-2"
                                />
                                <span className="text-xs">{doc.reuse_rate}%</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Button variant="outline" size="sm">
                                <Copy className="w-3 h-3 mr-1" />
                                复用
                              </Button>
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5" />
                    采购清单复用
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>来源项目</TableHead>
                        <TableHead>可复用物料</TableHead>
                        <TableHead>复用率</TableHead>
                        <TableHead>操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(analysis.reusable_content?.procurement_lists || []).map(
                        (list, idx) => (
                          <TableRow key={idx}>
                            <TableCell className="font-medium">
                              {list.project_name}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-wrap gap-1">
                                {list.items?.map((item, i) => (
                                  <Badge key={i} variant="outline">
                                    {item}
                                  </Badge>
                                ))}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Progress
                                  value={list.reuse_rate}
                                  className="w-20 h-2"
                                />
                                <span className="text-xs">{list.reuse_rate}%</span>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Button variant="outline" size="sm">
                                <Copy className="w-3 h-3 mr-1" />
                                导入
                              </Button>
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* 自动化建议 */}
            <TabsContent value="automation" className="space-y-4">
              {analysis.automation_suggestions?.map((suggestion, idx) => (
                <Card key={idx}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-yellow-500" />
                        {suggestion.title}
                      </CardTitle>
                      <Badge
                        variant={
                          suggestion.impact === 'HIGH' ? 'destructive' : 'default'
                        }
                      >
                        影响：{suggestion.impact}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="text-slate-300">
                        {suggestion.description}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <div className="text-sm text-slate-400">预计节省</div>
                          <div className="text-lg font-bold text-green-500">
                            {suggestion.savings_days}天
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-400">实施难度</div>
                          <div className="text-lg font-bold">
                            {suggestion.effort}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-slate-400">操作</div>
                          <Button size="sm">
                            <ArrowRight className="w-3 h-3 mr-1" />
                            {suggestion.action}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
