/**
 * Delay Analysis Page - 延期深度分析
 * Features: 延期根因分析、影响分析、趋势分析
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Calendar,
  Filter,
  DollarSign,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { fadeIn, staggerContainer } from "../lib/animations";
import { delayAnalysisApi } from "../services/api";
import { formatAmount, formatDate } from "../lib/utils";

export default function DelayAnalysis() {
  const [loading, setLoading] = useState(false);
  const [rootCauseData, setRootCauseData] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [trendsData, setTrendsData] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [projectId, setProjectId] = useState("");
  const [months, setMonths] = useState(12);
  const [activeTab, setActiveTab] = useState("root-cause");

  const loadRootCause = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (projectId) params.project_id = parseInt(projectId);

      const response = await delayAnalysisApi.getRootCause(params);
      if (response.data?.data) {
        setRootCauseData(response.data.data);
      }
    } catch (error) {
      console.error("加载延期根因分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadImpact = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await delayAnalysisApi.getImpact(params);
      if (response.data?.data) {
        setImpactData(response.data.data);
      }
    } catch (error) {
      console.error("加载延期影响分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTrends = async () => {
    setLoading(true);
    try {
      const response = await delayAnalysisApi.getTrends({ months });
      if (response.data?.data) {
        setTrendsData(response.data.data);
      }
    } catch (error) {
      console.error("加载延期趋势分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "root-cause") loadRootCause();
    if (activeTab === "impact") loadImpact();
    if (activeTab === "trends") loadTrends();
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <PageHeader title="延期深度分析" />

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
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                结束日期
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                项目ID（可选）
              </label>
              <Input
                type="number"
                placeholder="项目ID"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={loadRootCause} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="root-cause">根因分析</TabsTrigger>
          <TabsTrigger value="impact">影响分析</TabsTrigger>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
        </TabsList>

        {/* 根因分析 */}
        <TabsContent value="root-cause">
          {rootCauseData && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">延期任务总数</div>
                    <div className="text-2xl font-bold mt-2">
                      {rootCauseData.total_delayed_tasks || 0}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">总延期天数</div>
                    <div className="text-2xl font-bold mt-2">
                      {rootCauseData.summary?.total_delay_days || 0} 天
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">主要原因</div>
                    <div className="text-lg font-semibold mt-2">
                      {rootCauseData.summary?.top_reason || "无"}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>延期原因统计</CardTitle>
                </CardHeader>
                <CardContent>
                  {rootCauseData.root_causes &&
                    rootCauseData.root_causes.length > 0 && (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>延期原因</TableHead>
                            <TableHead>延期次数</TableHead>
                            <TableHead>总延期天数</TableHead>
                            <TableHead>平均延期天数</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {rootCauseData.root_causes.map((cause, idx) => (
                            <TableRow key={idx}>
                              <TableCell>{cause.reason}</TableCell>
                              <TableCell>{cause.count}</TableCell>
                              <TableCell>{cause.total_delay_days} 天</TableCell>
                              <TableCell>
                                {cause.average_delay_days} 天
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* 影响分析 */}
        <TabsContent value="impact">
          {impactData && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">成本影响</div>
                    <div className="text-2xl font-bold mt-2 text-red-600">
                      {formatAmount(impactData.cost_impact?.total || 0)}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {impactData.cost_impact?.description}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">回款影响</div>
                    <div className="text-2xl font-bold mt-2 text-amber-600">
                      {formatAmount(impactData.revenue_impact?.total || 0)}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {impactData.revenue_impact?.description}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>受影响项目</CardTitle>
                </CardHeader>
                <CardContent>
                  {impactData.affected_projects &&
                    impactData.affected_projects.length > 0 && (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>项目编码</TableHead>
                            <TableHead>项目名称</TableHead>
                            <TableHead>延期天数</TableHead>
                            <TableHead>成本影响</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {impactData.affected_projects.map((project, idx) => (
                            <TableRow key={idx}>
                              <TableCell>{project.project_code}</TableCell>
                              <TableCell>{project.project_name}</TableCell>
                              <TableCell>{project.delay_days} 天</TableCell>
                              <TableCell>
                                {formatAmount(project.cost_impact)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* 趋势分析 */}
        <TabsContent value="trends">
          {trendsData && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>延期趋势分析</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <div className="text-sm text-slate-500 mb-2">
                      分析周期: {trendsData.period?.start_date} 至{" "}
                      {trendsData.period?.end_date}
                    </div>
                    <div className="text-sm text-slate-500">
                      平均延期率: {trendsData.summary?.average_delay_rate?.toFixed(2)}%
                    </div>
                    <div className="text-sm text-slate-500">
                      趋势方向:{" "}
                      {trendsData.summary?.trend_direction === "INCREASING"
                        ? "上升"
                        : trendsData.summary?.trend_direction === "DECREASING"
                        ? "下降"
                        : "稳定"}
                    </div>
                  </div>
                  {trendsData.trends && trendsData.trends.length > 0 && (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>月份</TableHead>
                          <TableHead>总任务数</TableHead>
                          <TableHead>延期任务数</TableHead>
                          <TableHead>延期率</TableHead>
                          <TableHead>总延期天数</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {trendsData.trends.map((trend, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{trend.month}</TableCell>
                            <TableCell>{trend.total_tasks}</TableCell>
                            <TableCell>{trend.delayed_tasks}</TableCell>
                            <TableCell>
                              {trend.delay_rate.toFixed(2)}%
                            </TableCell>
                            <TableCell>{trend.total_delay_days} 天</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
