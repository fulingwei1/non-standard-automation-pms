/**
 * Scoring Matrix Component
 * 可视化评分矩阵 - 线索评分的视觉化展示和分析
 */

import { useState, useMemo, useEffect as _useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  BarChart3,
  PieChart,
  Radar,
  Eye,
  Filter,
  Download,
  RefreshCw,
  Target,
  Zap,
  AlertCircle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Minus } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import StatCard from "../common/StatCard";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { cn } from "../../lib/utils";
import {
  SCORING_CATEGORIES,
  SCORE_THRESHOLDS,
  FOLLOW_UP_STRATEGIES,
  LEAD_SOURCES,
  LEAD_TYPES,
  INDUSTRIES,
  BUDGET_RANGES,
  DECISION_TIMELINES,
  LEAD_STATUSES } from
"@/lib/constants/leadAssessment";
import { Checkbox } from "../ui/checkbox";
import { Input } from "../ui";
import { Mail, Phone } from "lucide-react";

export const ScoringMatrix = ({
  leads = [],
  filters = {},
  onFilterChange = null,
  onLeadSelect = null,
  onBulkAction = null,
  className = ""
}) => {
  const [viewMode, setViewMode] = useState("grid");
  const [selectedLeads, setSelectedLeads] = useState([]);
  const [hoveredLead, setHoveredLead] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: "assessmentScore", direction: "desc" });

  // 应用过滤器
  const filteredLeads = useMemo(() => {
    let result = leads;

    if (filters.status && filters.status !== "all") {
      result = result.filter((lead) => lead.status === filters.status);
    }

    if (filters.industry && filters.industry !== "all") {
      result = result.filter((lead) => lead.industry === filters.industry);
    }

    if (filters.source && filters.source !== "all") {
      result = result.filter((lead) => lead.source === filters.source);
    }

    if (filters.priority && filters.priority !== "all") {
      result = result.filter((lead) => lead.priority === filters.priority);
    }

    if (filters.scoreRange) {
      const [min, max] = filters.scoreRange;
      result = result.filter((lead) => {
        const score = lead.assessmentScore || 0;
        return score >= min && score <= max;
      });
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter((lead) =>
      lead.contactName?.toLowerCase().includes(searchLower) ||
      lead.companyName?.toLowerCase().includes(searchLower) ||
      lead.projectName?.toLowerCase().includes(searchLower)
      );
    }

    // 排序
    if (sortConfig.key) {
      result = [...result].sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        if (sortConfig.key === "assessmentScore") {
          aValue = aValue || 0;
          bValue = bValue || 0;
        }

        if (aValue < bValue) {
          return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [leads, filters, sortConfig]);

  // 统计数据
  const stats = useMemo(() => {
    const total = filteredLeads.length;
    const assessed = filteredLeads.filter((lead) => lead.assessmentScore).length;
    const highScore = filteredLeads.filter((lead) => (lead.assessmentScore || 0) >= 80).length;
    const mediumScore = filteredLeads.filter((lead) => (lead.assessmentScore || 0) >= 60 && (lead.assessmentScore || 0) < 80).length;
    const lowScore = filteredLeads.filter((lead) => (lead.assessmentScore || 0) < 60).length;

    // 计算平均分
    const totalScore = filteredLeads.reduce((sum, lead) => sum + (lead.assessmentScore || 0), 0);
    const averageScore = assessed > 0 ? totalScore / assessed : 0;

    // 计算各来源分布
    const sourceDistribution = {};
    filteredLeads.forEach((lead) => {
      sourceDistribution[lead.source] = (sourceDistribution[lead.source] || 0) + 1;
    });

    // 计算各行业分布
    const industryDistribution = {};
    filteredLeads.forEach((lead) => {
      industryDistribution[lead.industry] = (industryDistribution[lead.industry] || 0) + 1;
    });

    // 计算预算分布
    const budgetDistribution = {};
    filteredLeads.forEach((lead) => {
      budgetDistribution[lead.budgetRange] = (budgetDistribution[lead.budgetRange] || 0) + 1;
    });

    return {
      total,
      assessed,
      unassessed: total - assessed,
      highScore,
      mediumScore,
      lowScore,
      averageScore: Number(averageScore.toFixed(1)),
      sourceDistribution,
      industryDistribution,
      budgetDistribution,
      conversionRate: total > 0 ? (assessed / total * 100).toFixed(1) : 0
    };
  }, [filteredLeads]);

  // 获取评分等级
  const getScoreLevel = (score) => {
    if (score >= 80) {return { level: "excellent", color: "#52c41a", label: "优秀" };}
    if (score >= 60) {return { level: "good", color: "#1890ff", label: "良好" };}
    if (score >= 40) {return { level: "average", color: "#faad14", label: "一般" };}
    if (score >= 20) {return { level: "poor", color: "#ff7a45", label: "较差" };}
    return { level: "very_poor", color: "#ff4d4f", label: "很差" };
  };

  // 处理排序
  const _handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  // 切换选择状态
  const toggleLeadSelection = (lead) => {
    const index = selectedLeads.findIndex((l) => l.id === lead.id);
    if (index >= 0) {
      setSelectedLeads(selectedLeads.filter((_, i) => i !== index));
    } else {
      setSelectedLeads([...selectedLeads, lead]);
    }
  };

  // 全选/取消全选
  const _toggleSelectAll = () => {
    if (selectedLeads.length === filteredLeads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(filteredLeads);
    }
  };

  // 渲染雷达图数据
  const _radarData = useMemo(() => {
    const categories = SCORING_CATEGORIES.map((cat) => cat.name);
    const datasets = [];

    // 平均分数据
    const avgScores = SCORING_CATEGORIES.map((category) => {
      const categoryLeads = filteredLeads.filter((lead) => lead.scores?.[category.id]);
      if (categoryLeads.length === 0) {return 0;}

      const avgScore = categoryLeads.reduce((sum, lead) =>
      sum + (lead.scores[category.id] || 0), 0) / categoryLeads.length;
      return Number(avgScore.toFixed(1));
    });

    datasets.push({
      label: "平均评分",
      data: avgScores,
      borderColor: "#1890ff",
      backgroundColor: "rgba(24, 144, 255, 0.2)"
    });

    return { categories, datasets };
  }, [filteredLeads]);

  // 渲染柱状图数据
  const _barChartData = useMemo(() => {
    const data = {
      good: { count: 0, color: "#52c41a" },
      average: { count: 0, color: "#faad14" },
      poor: { count: 0, color: "#ff4d4f" }
    };

    filteredLeads.forEach((lead) => {
      const score = lead.assessmentScore || 0;
      if (score >= 60) {
        data.good.count++;
      } else if (score >= 40) {
        data.average.count++;
      } else {
        data.poor.count++;
      }
    });

    return [{
      label: "线索质量分布",
      data: [
      { name: "优质", value: data.good.count, color: data.good.color },
      { name: "一般", value: data.average.count, color: data.average.color },
      { name: "较差", value: data.poor.count, color: data.poor.color }]

    }];
  }, [filteredLeads]);

  // 渲染评分矩阵网格
  const renderScoringMatrix = () => {
    if (filteredLeads.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
          <BarChart3 className="h-12 w-12 mb-4" />
          <p>暂无线索数据</p>
        </div>);

    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredLeads.map((lead, index) => {
          const scoreLevel = getScoreLevel(lead.assessmentScore || 0);
          const healthColor = scoreLevel.color;

          return (
            <motion.div
              key={lead.id || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="relative bg-white rounded-lg border border-slate-200 p-4 hover:shadow-lg transition-all duration-200 cursor-pointer"
              onMouseEnter={() => setHoveredLead(lead)}
              onMouseLeave={() => setHoveredLead(null)}
              onClick={() => onLeadSelect && onLeadSelect(lead)}>

              {/* 健康度指示条 */}
              <div className="absolute top-0 left-0 right-0 h-1 rounded-t-lg" style={{ backgroundColor: healthColor }} />

              <div className="space-y-3">
                {/* 选择框 */}
                <Checkbox
                  checked={selectedLeads.some((l) => l.id === lead.id)}
                  onCheckedChange={() => toggleLeadSelection(lead)}
                  className="absolute top-2 right-2" />


                {/* 联系人信息 */}
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 truncate">
                      {lead.contactName}
                    </h3>
                    {lead.companyName &&
                    <p className="text-sm text-slate-600 truncate">
                        {lead.companyName}
                    </p>
                    }
                  </div>
                </div>

                {/* 项目信息 */}
                {lead.projectName &&
                <div>
                    <p className="text-sm font-medium text-slate-700 mb-1">项目</p>
                    <p className="text-sm text-slate-900 truncate">
                      {lead.projectName}
                    </p>
                </div>
                }

                {/* 评分 */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">线索评分</span>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: scoreLevel.color }} />
                      <span className="text-sm font-medium" style={{ color: scoreLevel.color }}>
                        {scoreLevel.label}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={lead.assessmentScore || 0} className="flex-1 h-2" />
                    <span className="text-sm font-semibold w-12 text-right">
                      {lead.assessmentScore || 0}
                    </span>
                  </div>
                </div>

                {/* 快速信息 */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center gap-1 text-slate-600">
                    <span>来源:</span>
                    <span className="text-slate-900 truncate">
                      {LEAD_SOURCES.find((s) => s.value === lead.source)?.label || lead.source}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-600">
                    <span>行业:</span>
                    <span className="text-sline-900 truncate">
                      {INDUSTRIES.find((i) => i.value === lead.industry)?.label || lead.industry}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-600">
                    <span>预算:</span>
                    <span className="text-slate-900">
                      {BUDGET_RANGES.find((b) => b.value === lead.budgetRange)?.label || lead.budgetRange}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-slate-600">
                    <span>状态:</span>
                    <span className="text-slate-900">
                      {LEAD_STATUSES.find((s) => s.value === lead.status)?.label || lead.status}
                    </span>
                  </div>
                </div>

                {/* 鼠标悬停时显示详细信息 */}
                {hoveredLead?.id === lead.id &&
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="absolute inset-0 bg-white/95 rounded-lg border border-slate-200 p-4 z-10">

                    <div className="space-y-2">
                      {lead.contactEmail &&
                    <div className="flex items-center gap-2 text-sm">
                          <Mail className="h-4 w-4 text-slate-500" />
                          <span>{lead.contactEmail}</span>
                    </div>
                    }
                      {lead.contactPhone &&
                    <div className="flex items-center gap-2 text-sm">
                          <Phone className="h-4 w-4 text-slate-500" />
                          <span>{lead.contactPhone}</span>
                    </div>
                    }
                      {lead.description &&
                    <div>
                          <p className="text-sm font-medium text-slate-700 mb-1">描述</p>
                          <p className="text-sm text-slate-600 line-clamp-2">
                            {lead.description}
                          </p>
                    </div>
                    }
                    </div>
                </motion.div>
                }
              </div>
            </motion.div>);

        })}
      </div>);

  };

  const renderStatValue = (value, change, unit = "") => (
    <span className="inline-flex items-baseline gap-2">
      <span>
        {value}
        {unit && <span className="text-lg font-normal text-slate-600">{unit}</span>}
      </span>
      {change !== null && (
        <span
          className={cn(
            "inline-flex items-center gap-1 text-xs font-normal",
            change > 0 ? "text-green-600" : change < 0 ? "text-red-600" : "text-slate-600"
          )}
        >
          {change > 0 ? (
            <ArrowUpRight className="h-3 w-3" />
          ) : change < 0 ? (
            <ArrowDownRight className="h-3 w-3" />
          ) : (
            <Minus className="h-3 w-3" />
          )}
          <span>{Math.abs(change)}%</span>
        </span>
      )}
    </span>
  );

  // 渲染统计卡片
  const renderStatCard = ({ title, value, change, icon: Icon, color, bg, unit = "" }) => (
    <StatCard
      title={title}
      value={renderStatValue(value, change, unit)}
      icon={Icon}
      color={color}
      iconColor={color}
      valueColor={color}
      bg={bg}
      showDecoration={false}
      titleClassName="text-sm text-slate-600"
      cardClassName="bg-white bg-none border-slate-200 hover:border-slate-300 shadow-sm hover:shadow-md p-4"
      iconWrapperClassName="p-2 rounded-lg bg-opacity-10"
      iconClassName="h-6 w-6"
    />
  );


  return (
    <div className={cn("space-y-6", className)}>
      {/* 标题和操作栏 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">线索评分矩阵</h2>
          <p className="text-slate-600 mt-1">
            线索质量可视化分析和评分管理
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={viewMode} onValueChange={setViewMode}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="grid">网格视图</SelectItem>
              <SelectItem value="list">列表视图</SelectItem>
            </SelectContent>
          </Select>
          {selectedLeads.length > 0 &&
          <Button variant="outline" onClick={() => onBulkAction && onBulkAction("score", selectedLeads)}>
              批量评分
          </Button>
          }
        </div>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderStatCard({
          title: "总线索数",
          value: stats.total,
          change: null,
          icon: Target,
          color: "text-blue-500",
          bg: "bg-blue-500"
        })}
        {renderStatCard({
          title: "已评估",
          value: stats.assessed,
          change: null,
          icon: CheckCircle,
          color: "text-green-500",
          bg: "bg-green-500"
        })}
        {renderStatCard({
          title: "平均分",
          value: stats.averageScore,
          change: 5.2,
          icon: TrendingUp,
          color: "text-orange-500",
          bg: "bg-orange-500"
        })}
        {renderStatCard({
          title: "转化率",
          value: `${stats.conversionRate}%`,
          change: 12.5,
          icon: Zap,
          color: "text-purple-500",
          bg: "bg-purple-500"
        })}
      </div>

      {/* 快速筛选 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <Input
              placeholder="搜索联系人、公司或项目..."
              value={filters.search || ""}
              onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
              className="w-64" />


            <Select value={filters.status || "all"} onValueChange={(value) => onFilterChange({ ...filters, status: value })}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有状态</SelectItem>
                {LEAD_STATUSES.map((status) =>
                <SelectItem key={status.value} value={status.value}>
                    {status.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filters.industry || "all"} onValueChange={(value) => onFilterChange({ ...filters, industry: value })}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有行业</SelectItem>
                {INDUSTRIES.map((industry) =>
                <SelectItem key={industry.value} value={industry.value}>
                    {industry.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={filters.source || "all"} onValueChange={(value) => onFilterChange({ ...filters, source: value })}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有来源</SelectItem>
                {LEAD_SOURCES.slice(0, 5).map((source) =>
                <SelectItem key={source.value} value={source.value}>
                    {source.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={() => onFilterChange({})}>
              <RefreshCw className="mr-2 h-4 w-4" />
              重置
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 评分矩阵 */}
      <Tabs defaultValue="matrix" className="space-y-4">
        <TabsList>
          <TabsTrigger value="matrix">评分矩阵</TabsTrigger>
          <TabsTrigger value="analysis">数据分析</TabsTrigger>
          <TabsTrigger value="distribution">分布图</TabsTrigger>
        </TabsList>

        <TabsContent value="matrix">
          {renderScoringMatrix()}
        </TabsContent>

        <TabsContent value="analysis">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>评分分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">优质线索 (≥80分)</span>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-2 rounded-full bg-green-500" style={{ width: `${stats.highScore / stats.total * 100 || 0}%` }} />
                      <span className="text-sm font-medium">{stats.highScore}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">良好线索 (60-79分)</span>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-2 rounded-full bg-blue-500" style={{ width: `${stats.mediumScore / stats.total * 100 || 0}%` }} />
                      <span className="text-sm font-medium">{stats.mediumScore}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">一般线索 (40-59分)</span>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-2 rounded-full bg-amber-500" style={{ width: `${stats.lowScore / stats.total * 100 || 0}%` }} />
                      <span className="text-sm font-medium">{stats.lowScore}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">较差线索 (&lt;40分)</span>
                    <span className="text-sm font-medium">
                      {stats.total - stats.highScore - stats.mediumScore - stats.lowScore}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>跟进策略建议</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {FOLLOW_UP_STRATEGIES.slice(0, 3).map((strategy) => {
                    const count = filteredLeads.filter((lead) => {
                      const score = lead.assessmentScore || 0;
                      return score >= strategy.scoreRange[0] && score <= strategy.scoreRange[1];
                    }).length;

                    return (
                      <div key={strategy.strategy} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium">{strategy.strategy}</h4>
                            <Badge variant="secondary" className="text-xs">
                              {count}个线索
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-600">
                            {strategy.description}
                          </p>
                        </div>
                      </div>);

                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="distribution">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>线索来源分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.sourceDistribution).map(([source, count]) => {
                    const sourceConfig = LEAD_SOURCES.find((s) => s.value === source);
                    const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

                    return (
                      <div key={source} className="flex items-center justify-between">
                        <span className="text-sm">{sourceConfig?.label || source}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage} className="w-20 h-2" />
                          <span className="text-xs text-slate-600 w-10 text-right">
                            {percentage}%
                          </span>
                        </div>
                      </div>);

                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>行业分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.industryDistribution).map(([industry, count]) => {
                    const industryConfig = INDUSTRIES.find((i) => i.value === industry);
                    const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

                    return (
                      <div key={industry} className="flex items-center justify-between">
                        <span className="text-sm">{industryConfig?.label || industry}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage} className="w-20 h-2" />
                          <span className="text-xs text-slate-600 w-10 text-right">
                            {percentage}%
                          </span>
                        </div>
                      </div>);

                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>预算分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats.budgetDistribution).map(([budget, count]) => {
                    const budgetConfig = BUDGET_RANGES.find((b) => b.value === budget);
                    const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

                    return (
                      <div key={budget} className="flex items-center justify-between">
                        <span className="text-sm">{budgetConfig?.label || budget}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={percentage} className="w-20 h-2" />
                          <span className="text-xs text-slate-600 w-10 text-right">
                            {percentage}%
                          </span>
                        </div>
                      </div>);

                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>);

};

export default ScoringMatrix;
