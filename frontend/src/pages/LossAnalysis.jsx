/**
 * Loss Analysis Page - 未中标深度分析
 * Features: 投入阶段分析、未中标原因分析、投入产出分析、模式识别
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingDown,
  DollarSign,
  Clock,
  Users,
  Building2,
  AlertTriangle,
  BarChart3,
  PieChart,
  Download,
  Filter,
  Calendar,
} from "lucide-react";
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
} from "../components/ui";
import { fadeIn, staggerContainer } from "../lib/animations";
import { lossAnalysisApi } from "../services/api";
import { formatAmount } from "../lib/utils";

export default function LossAnalysis() {
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [salespersonId, setSalespersonId] = useState("");
  const [selectedStage, setSelectedStage] = useState("all");

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (salespersonId) params.salesperson_id = parseInt(salespersonId);

      const response = await lossAnalysisApi.deepAnalysis(params);
      if (response.data && response.data.data) {
        setAnalysisData(response.data.data);
      }
    } catch (error) {
      console.error("加载分析数据失败:", error);
      alert("加载分析数据失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  const formatHours = (hours) => {
    if (!hours) return "0h";
    return `${hours.toFixed(1)}h`;
  };

  return (
    <div className="space-y-6">
      <PageHeader title="未中标深度分析" />

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">开始日期</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">结束日期</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">销售人员ID</label>
              <Input
                type="number"
                value={salespersonId}
                onChange={(e) => setSalespersonId(e.target.value)}
                placeholder="可选"
              />
            </div>
            <div className="flex items-end">
              <Button onClick={loadAnalysis} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading && (
        <div className="text-center py-8 text-slate-500">加载中...</div>
      )}

      {analysisData && !loading && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          {/* 汇总统计 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">未中标项目数</p>
                    <p className="text-2xl font-bold mt-1">
                      {analysisData.total_lost_projects}
                    </p>
                  </div>
                  <TrendingDown className="h-8 w-8 text-red-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">总投入工时</p>
                    <p className="text-2xl font-bold mt-1">
                      {formatHours(analysisData.investment_analysis?.summary?.total_hours)}
                    </p>
                  </div>
                  <Clock className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">总投入成本</p>
                    <p className="text-2xl font-bold mt-1">
                      {formatAmount(analysisData.investment_analysis?.summary?.total_cost)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-orange-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">总损失金额</p>
                    <p className="text-2xl font-bold mt-1 text-red-600">
                      {formatAmount(analysisData.investment_analysis?.summary?.total_loss)}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-red-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 投入阶段分析 */}
          <Card>
            <CardHeader>
              <CardTitle>投入阶段分析</CardTitle>
            </CardHeader>
            <CardContent>
              {analysisData.stage_analysis && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">仅需求调研</p>
                      <p className="text-2xl font-bold mt-1">
                        {analysisData.stage_analysis.statistics.requirement_only}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">方案设计</p>
                      <p className="text-2xl font-bold mt-1">
                        {analysisData.stage_analysis.statistics.design}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg border-2 border-red-200">
                      <p className="text-sm text-slate-500 font-medium">详细设计</p>
                      <p className="text-2xl font-bold mt-1 text-red-600">
                        {analysisData.stage_analysis.statistics.detailed_design}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {analysisData.stage_analysis.summary.detailed_design_percentage}%
                      </p>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">报价阶段</p>
                      <p className="text-2xl font-bold mt-1">
                        {analysisData.stage_analysis.statistics.quotation}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-slate-50 rounded-lg">
                      <p className="text-sm text-slate-500">未知</p>
                      <p className="text-2xl font-bold mt-1">
                        {analysisData.stage_analysis.statistics.unknown}
                      </p>
                    </div>
                  </div>

                  {/* 详细设计项目列表 */}
                  {analysisData.stage_analysis.details
                    .filter((d) => d.stage === "detailed_design")
                    .length > 0 && (
                    <div className="mt-6">
                      <h3 className="text-lg font-semibold mb-3 text-red-600">
                        已完成详细设计但未中标的项目
                      </h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>项目编号</TableHead>
                            <TableHead>项目名称</TableHead>
                            <TableHead>投入工时</TableHead>
                            <TableHead>投入成本</TableHead>
                            <TableHead>未中标原因</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {analysisData.stage_analysis.details
                            .filter((d) => d.stage === "detailed_design")
                            .map((detail) => (
                              <TableRow key={detail.project_id}>
                                <TableCell>{detail.project_code}</TableCell>
                                <TableCell>{detail.project_name}</TableCell>
                                <TableCell>{formatHours(detail.total_hours)}</TableCell>
                                <TableCell>{formatAmount(detail.total_cost)}</TableCell>
                                <TableCell>
                                  <Badge variant="outline">{detail.loss_reason}</Badge>
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 未中标原因分析 */}
          <Card>
            <CardHeader>
              <CardTitle>未中标原因分析</CardTitle>
            </CardHeader>
            <CardContent>
              {analysisData.reason_analysis && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysisData.reason_analysis.top_reasons.map((reason, index) => (
                      <div
                        key={index}
                        className="p-4 bg-slate-50 rounded-lg border-l-4 border-blue-500"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold">{reason.reason}</span>
                          <Badge>{reason.count}个</Badge>
                        </div>
                        <div className="text-sm text-slate-600">
                          <p>占比: {reason.percentage}%</p>
                          <p>总工时: {formatHours(reason.total_hours)}</p>
                          <p>总成本: {formatAmount(reason.total_cost)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 投入产出分析 */}
          <Card>
            <CardHeader>
              <CardTitle>投入产出分析</CardTitle>
            </CardHeader>
            <CardContent>
              {analysisData.investment_analysis && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-500">平均工时/项目</p>
                      <p className="text-xl font-bold">
                        {formatHours(
                          analysisData.investment_analysis.summary
                            .average_hours_per_project
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">平均成本/项目</p>
                      <p className="text-xl font-bold">
                        {formatAmount(
                          analysisData.investment_analysis.summary
                            .average_cost_per_project
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">预期收益</p>
                      <p className="text-xl font-bold">
                        {formatAmount(
                          analysisData.investment_analysis.summary
                            .total_expected_revenue
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">总损失</p>
                      <p className="text-xl font-bold text-red-600">
                        {formatAmount(
                          analysisData.investment_analysis.summary.total_loss
                        )}
                      </p>
                    </div>
                  </div>

                  {/* 按人员统计 */}
                  {analysisData.investment_analysis.by_person.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">按人员统计</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>人员</TableHead>
                            <TableHead>部门</TableHead>
                            <TableHead>项目数</TableHead>
                            <TableHead>总工时</TableHead>
                            <TableHead>总成本</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {analysisData.investment_analysis.by_person.map((person) => (
                            <TableRow key={person.person_id}>
                              <TableCell>{person.person_name}</TableCell>
                              <TableCell>{person.department || "-"}</TableCell>
                              <TableCell>{person.project_count}</TableCell>
                              <TableCell>{formatHours(person.hours)}</TableCell>
                              <TableCell>{formatAmount(person.cost)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 模式识别 */}
          {analysisData.pattern_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>模式识别</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysisData.pattern_analysis.detailed_design_loss_patterns.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">
                        详细设计后未中标的主要原因
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {analysisData.pattern_analysis.detailed_design_loss_patterns.map(
                          (pattern, index) => (
                            <div
                              key={index}
                              className="p-4 bg-amber-50 rounded-lg border border-amber-200"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <span className="font-semibold">{pattern.reason}</span>
                                <Badge variant="outline">{pattern.count}个</Badge>
                              </div>
                              <p className="text-sm text-slate-600">
                                占比: {pattern.percentage}%
                              </p>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  {analysisData.pattern_analysis.salesperson_patterns.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">
                        高投入但未中标率高的销售人员
                      </h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>销售人员</TableHead>
                            <TableHead>未中标数</TableHead>
                            <TableHead>总工时</TableHead>
                            <TableHead>总成本</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {analysisData.pattern_analysis.salesperson_patterns.map((sp) => (
                            <TableRow key={sp.person_id}>
                              <TableCell>{sp.person_name}</TableCell>
                              <TableCell>{sp.lost_count}</TableCell>
                              <TableCell>{formatHours(sp.total_hours)}</TableCell>
                              <TableCell>{formatAmount(sp.total_cost)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}
    </div>
  );
}
