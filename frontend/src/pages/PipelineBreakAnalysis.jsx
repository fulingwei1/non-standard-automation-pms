/**
 * Pipeline Break Analysis Page - 全链条断链分析
 * Features: 断链检测、断链率统计、断链模式识别、断链预警
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  TrendingDown,
  BarChart3,
  PieChart,
  Calendar,
  Filter,
  Download,
  Bell,
  Users,
  Building2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { fadeIn as _fadeIn, staggerContainer as _staggerContainer } from "../lib/animations";
import { pipelineAnalysisApi } from "../services/api";
import { formatAmount as _formatAmount, formatDate } from "../lib/utils";

export default function PipelineBreakAnalysis() {
  const [_loading, setLoading] = useState(false);
  const [breakData, setBreakData] = useState(null);
  const [breakReasons, setBreakReasons] = useState(null);
  const [breakPatterns, setBreakPatterns] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [pipelineType, setPipelineType] = useState("all");
  const [activeTab, setActiveTab] = useState("overview");

  const loadBreakAnalysis = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}
      if (pipelineType !== "all") {params.pipeline_type = pipelineType;}

      const [breaksRes, reasonsRes, patternsRes, warningsRes] =
      await Promise.all([
      pipelineAnalysisApi.getPipelineBreaks(params),
      pipelineAnalysisApi.getBreakReasons(params),
      pipelineAnalysisApi.getBreakPatterns(params),
      pipelineAnalysisApi.getBreakWarnings({ days_ahead: 7 })]
      );

      if (breaksRes.data?.data) {setBreakData(breaksRes.data.data);}
      if (reasonsRes.data?.data) {setBreakReasons(reasonsRes.data.data);}
      if (patternsRes.data?.data) {setBreakPatterns(patternsRes.data.data);}
      if (warningsRes.data?.data?.warnings)
      {setWarnings(warningsRes.data.data.warnings);}
    } catch (error) {
      console.error("加载断链分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBreakAnalysis();
  }, []);

  const getBreakStageLabel = (stage) => {
    const labels = {
      LEAD_TO_OPP: "线索→商机",
      OPP_TO_QUOTE: "商机→报价",
      QUOTE_TO_CONTRACT: "报价→合同",
      CONTRACT_TO_PROJECT: "合同→项目",
      PROJECT_TO_INVOICE: "项目→发票",
      INVOICE_TO_PAYMENT: "发票→回款"
    };
    return labels[stage] || stage;
  };

  const getHealthBadge = (rate) => {
    if (rate >= 30) {return <Badge variant="destructive">严重</Badge>;}
    if (rate >= 15) {return <Badge variant="warning">有风险</Badge>;}
    return <Badge variant="success">正常</Badge>;
  };

  return (
    <div className="space-y-6">
      <PageHeader title="全链条断链分析" />

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                开始日期
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)} />

            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                结束日期
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)} />

            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                流程类型
              </label>
              <select
                className="w-full px-3 py-2 border rounded-md"
                value={pipelineType}
                onChange={(e) => setPipelineType(e.target.value)}>

                <option value="all">全部</option>
                <option value="LEAD">线索</option>
                <option value="OPPORTUNITY">商机</option>
                <option value="QUOTE">报价</option>
                <option value="CONTRACT">合同</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={loadBreakAnalysis} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 断链预警 */}
      {warnings.length > 0 &&
      <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-amber-500" />
              即将断链预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {warnings.slice(0, 5).map((warning, idx) =>
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">

                  <div>
                    <div className="font-medium">
                      {warning.pipeline_code} - {warning.pipeline_type}
                    </div>
                    <div className="text-sm text-slate-500">
                      {getBreakStageLabel(warning.break_stage)} · 还有{" "}
                      {warning.days_until_break} 天
                    </div>
                  </div>
                  <Badge variant="warning">预警</Badge>
            </div>
            )}
            </div>
          </CardContent>
      </Card>
      }

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">断链概览</TabsTrigger>
          <TabsTrigger value="stages">按环节分析</TabsTrigger>
          <TabsTrigger value="reasons">断链原因</TabsTrigger>
          <TabsTrigger value="patterns">断链模式</TabsTrigger>
        </TabsList>

        {/* 断链概览 */}
        <TabsContent value="overview">
          {breakData &&
          <div className="space-y-6">
              {/* 总体统计 */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {breakData.top_break_stages?.map((stage, idx) =>
              <Card key={idx}>
                    <CardContent className="pt-6">
                      <div className="text-sm text-slate-500">
                        {getBreakStageLabel(stage.stage)}
                      </div>
                      <div className="text-2xl font-bold mt-2">
                        {stage.break_rate.toFixed(1)}%
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {stage.break_count} / {stage.total}
                      </div>
                      {getHealthBadge(stage.break_rate)}
                    </CardContent>
              </Card>
              )}
              </div>

              {/* 各环节断链详情 */}
              <Card>
                <CardHeader>
                  <CardTitle>各环节断链详情</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>环节</TableHead>
                        <TableHead>总数</TableHead>
                        <TableHead>断链数</TableHead>
                        <TableHead>断链率</TableHead>
                        <TableHead>状态</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(breakData.break_rates || {}).map(
                      ([stage, data]) =>
                      <TableRow key={stage}>
                            <TableCell>
                              {getBreakStageLabel(stage)}
                            </TableCell>
                            <TableCell>{data.total}</TableCell>
                            <TableCell>{data.break_count}</TableCell>
                            <TableCell>
                              {data.break_rate.toFixed(2)}%
                            </TableCell>
                            <TableCell>
                              {getHealthBadge(data.break_rate)}
                            </TableCell>
                      </TableRow>

                    )}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>

        {/* 按环节分析 */}
        <TabsContent value="stages">
          {breakData &&
          <div className="space-y-6">
              {Object.entries(breakData.breaks || {}).map(
              ([stage, data]) =>
              <Card key={stage}>
                    <CardHeader>
                      <CardTitle>{getBreakStageLabel(stage)}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <div className="text-sm text-slate-500">
                          总数: {data.total} · 断链数: {data.break_count}
                        </div>
                      </div>
                      {data.break_records && data.break_records?.length > 0 &&
                  <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>编码</TableHead>
                              <TableHead>名称</TableHead>
                              <TableHead>断链日期</TableHead>
                              <TableHead>断链天数</TableHead>
                              <TableHead>责任人</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {(data.break_records || []).map((record, idx) =>
                      <TableRow key={idx}>
                                <TableCell>{record.pipeline_code}</TableCell>
                                <TableCell>{record.pipeline_name}</TableCell>
                                <TableCell>
                                  {formatDate(record.break_date)}
                                </TableCell>
                                <TableCell>
                                  {record.days_since_break} 天
                                </TableCell>
                                <TableCell>
                                  {record.responsible_person_name || "未设置"}
                                </TableCell>
                      </TableRow>
                      )}
                          </TableBody>
                  </Table>
                  }
                    </CardContent>
              </Card>

            )}
          </div>
          }
        </TabsContent>

        {/* 断链原因 */}
        <TabsContent value="reasons">
          {breakReasons &&
          <Card>
              <CardHeader>
                <CardTitle>断链原因统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-slate-500">
                  断链原因分析功能开发中...
                </div>
              </CardContent>
          </Card>
          }
        </TabsContent>

        {/* 断链模式 */}
        <TabsContent value="patterns">
          {breakPatterns &&
          <Card>
              <CardHeader>
                <CardTitle>断链模式识别</CardTitle>
              </CardHeader>
              <CardContent>
                {breakPatterns.most_common_stage &&
              <div className="mb-4">
                    <div className="text-sm text-slate-500 mb-2">
                      最容易断链的环节
                    </div>
                    <div className="text-lg font-semibold">
                      {getBreakStageLabel(
                    breakPatterns.most_common_stage.stage
                  )}
                    </div>
                    <div className="text-sm text-slate-400">
                      断链率:{" "}
                      {breakPatterns.most_common_stage.break_rate.toFixed(2)}%
                    </div>
              </div>
              }
              </CardContent>
          </Card>
          }
        </TabsContent>
      </Tabs>
    </div>);

}