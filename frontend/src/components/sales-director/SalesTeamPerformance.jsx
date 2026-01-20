/**
 * Sales Team Performance Component
 * 销售团队绩效组件
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Trophy,
  Target,
  TrendingUp,
  TrendingDown,
  Award,
  Star,
  Search,
  Filter,
  Settings,
  ChevronDown,
  ChevronUp,
  BarChart3,
  PieChart } from
'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui';
import { Button } from '../../components/ui';
import { Badge } from '../../components/ui';
import { Input } from '../../components/ui';
import { Progress } from '../../components/ui';
import { cn } from '../../lib/utils';
import {
  RANKING_METRIC_LIBRARY,
  PERFORMANCE_GRADES,
  SALES_REGIONS,
  formatCurrency,
  formatPercentage,
  getPerformanceGrade,
  calculateRankingValidation,
  validateMetricConfig as _validateMetricConfig } from
'./salesDirectorConstants';

export default function SalesTeamPerformance({
  teamPerformance = [],
  rankingConfig = null,
  configLoading: _configLoading = false,
  configSaving = false,
  onConfigUpdate,
  onViewMemberDetail
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [sortOrder, _setSortOrder] = useState('desc');
  const [isEditingConfig, setIsEditingConfig] = useState(false);
  const [configDraft, setConfigDraft] = useState([]);
  const [metricToAdd, setMetricToAdd] = useState('');
  const [configFormError, setConfigFormError] = useState('');
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const saving = configSaving || isSavingConfig;

  // 过滤团队成员
  const filteredTeam = useMemo(() => {
    return teamPerformance.filter((member) => {
      const matchesSearch = !searchQuery ||
      member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.department?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesRegion = selectedRegion === 'all' || member.region === selectedRegion;

      return matchesSearch && matchesRegion;
    });
  }, [teamPerformance, searchQuery, selectedRegion]);

  // 排序团队成员
  const sortedTeam = useMemo(() => {
    const sorted = [...filteredTeam].sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case 'score':
          aValue = a.performanceScore || 0;
          bValue = b.performanceScore || 0;
          break;
        case 'revenue':
          aValue = a.totalRevenue || 0;
          bValue = b.totalRevenue || 0;
          break;
        case 'deals':
          aValue = a.dealCount || 0;
          bValue = b.dealCount || 0;
          break;
        case 'conversion':
          aValue = a.conversionRate || 0;
          bValue = b.conversionRate || 0;
          break;
        default:
          aValue = a.performanceScore || 0;
          bValue = b.performanceScore || 0;
      }

      if (sortOrder === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });

    return sorted;
  }, [filteredTeam, sortBy, sortOrder]);

  // 显示的排名指标
  const displayRankingMetrics = useMemo(() => {
    const targets = isEditingConfig ? configDraft : rankingConfig?.metrics || [];
    return [...targets].sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0));
  }, [configDraft, rankingConfig, isEditingConfig]);

  // 可选择的指标
  const availableMetricOptions = useMemo(() => {
    const usedKeys = new Set(
      (configDraft || []).map((metric) => metric.data_source || metric.key)
    );
    return RANKING_METRIC_LIBRARY.filter((metric) => !usedKeys.has(metric.value));
  }, [configDraft]);

  // 指标验证
  const metricValidation = useMemo(() => {
    return calculateRankingValidation(configDraft);
  }, [configDraft]);

  // 获取绩效等级
  const getPerformanceBadge = (score) => {
    const grade = getPerformanceGrade(score);
    return (
      <Badge className={cn(grade.color.replace('#', 'bg-'), 'text-white')}>
        {grade.label}
      </Badge>);

  };

  // 渲染成员排名卡片
  const renderMemberCard = (member, index) => {
    const _grade = getPerformanceGrade(member.performanceScore || 0);
    const isTopPerformer = index < 3;

    return (
      <motion.div
        key={member.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}>

        <Card className={cn(
          'h-full hover:shadow-lg transition-all duration-200',
          isTopPerformer && 'border-yellow-500/50 bg-gradient-to-br from-yellow-500/10 to-transparent'
        )}>
          <CardContent className="p-6">
            {/* 排名徽章 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {isTopPerformer &&
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 text-white font-bold text-sm">
                    {index + 1}
                </div>
                }
                <div>
                  <h3 className="font-semibold text-slate-100">{member.name}</h3>
                  <p className="text-sm text-slate-400">{member.department}</p>
                  {member.region &&
                  <Badge variant="outline" className="mt-1">
                      {SALES_REGIONS[member.region.toUpperCase()]?.label || member.region}
                  </Badge>
                  }
                </div>
              </div>
              {getPerformanceBadge(member.performanceScore)}
            </div>

            {/* 综合得分 */}
            <div className="mb-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-slate-400">综合得分</span>
                <span className="text-2xl font-bold text-slate-100">
                  {Math.round(member.performanceScore || 0)}
                </span>
              </div>
              <Progress value={member.performanceScore || 0} className="h-2" />
            </div>

            {/* 关键指标 */}
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">总收入</span>
                <span className="font-medium text-slate-200">{formatCurrency(member.totalRevenue || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">签单数</span>
                <span className="font-medium text-slate-200">{member.dealCount || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">转化率</span>
                <span className="font-medium text-slate-200">{formatPercentage(member.conversionRate || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-400">平均订单额</span>
                <span className="font-medium text-slate-200">{formatCurrency(member.avgDealSize || 0)}</span>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="mt-4 pt-4 border-t border-slate-700">
              <Button
                size="sm"
                variant="outline"
                className="w-full"
                onClick={() => onViewMemberDetail?.(member)}>

                查看详情
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>);

  };

  // 渲染配置编辑器
  const renderConfigEditor = () => {
    if (!isEditingConfig) {return null;}

    return (
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>排名指标配置</span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsEditingConfig(false);
                  setConfigDraft([]);
                  setConfigFormError('');
                }}>

                取消
              </Button>
              <Button
                size="sm"
                onClick={async () => {
                  if (metricValidation.isValid) {
                    setIsSavingConfig(true);
                    try {
                      await onConfigUpdate?.(configDraft);
                      setIsEditingConfig(false);
                      setConfigFormError('');
                    } catch (error) {
                      setConfigFormError('保存失败: ' + error.message);
                    } finally {
                      setIsSavingConfig(false);
                    }
                  } else {
                    setConfigFormError(metricValidation.errors.join(', '));
                  }
                }}
                disabled={saving || !metricValidation.isValid}>

                {saving ? '保存中...' : '保存'}
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {configFormError &&
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-3 py-2 rounded-md text-sm">
              {configFormError}
          </div>
          }

          {/* 当前指标列表 */}
          <div>
            <h4 className="font-medium mb-3 text-slate-200">当前指标 (权重总和: {metricValidation.totalWeight.toFixed(2)})</h4>
            <div className="space-y-2">
              {configDraft.map((metric, index) =>
              <div key={index} className="flex items-center gap-3 p-3 border border-slate-700 rounded-lg bg-slate-800/50">
                  <span className="font-medium flex-1 text-slate-200">{metric.label}</span>
                  <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={metric.weight || 0}
                  onChange={(e) => {
                    const newDraft = [...configDraft];
                    newDraft[index].weight = parseFloat(e.target.value);
                    setConfigDraft(newDraft);
                  }}
                  className="w-20 px-2 py-1 border border-slate-600 rounded text-sm bg-slate-700 text-slate-200" />

                  <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const newDraft = configDraft.filter((_, i) => i !== index);
                    setConfigDraft(newDraft);
                  }}>

                    删除
                  </Button>
              </div>
              )}
            </div>
          </div>

          {/* 添加新指标 */}
          <div>
            <h4 className="font-medium mb-3 text-slate-200">添加指标</h4>
            <div className="flex gap-2">
              <select
                value={metricToAdd}
                onChange={(e) => setMetricToAdd(e.target.value)}
                className="flex-1 px-3 py-2 border border-slate-600 rounded-md bg-slate-700 text-slate-200">

                <option value="">选择指标...</option>
                {availableMetricOptions.map((metric) =>
                <option key={metric.value} value={metric.value}>
                    {metric.label} - {metric.description}
                </option>
                )}
              </select>
              <Button
                onClick={() => {
                  if (metricToAdd) {
                    const metric = RANKING_METRIC_LIBRARY.find((m) => m.value === metricToAdd);
                    if (metric) {
                      setConfigDraft([...configDraft, {
                        key: metric.value,
                        label: metric.label,
                        data_source: metric.value,
                        weight: 0.1,
                        isPrimary: metric.isPrimary,
                        description: metric.description
                      }]);
                      setMetricToAdd('');
                    }
                  }
                }}
                disabled={!metricToAdd}>

                添加
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>);

  };

  return (
    <div className="space-y-6">
      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-blue-400" />
              <div>
                <div className="text-2xl font-bold text-slate-100">{teamPerformance.length}</div>
                <div className="text-sm text-slate-400">团队成员</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Trophy className="w-8 h-8 text-yellow-400" />
              <div>
                <div className="text-2xl font-bold text-slate-100">
                  {teamPerformance.filter((m) => (m.performanceScore || 0) >= 90).length}
                </div>
                <div className="text-sm text-slate-400">优秀成员</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-green-400" />
              <div>
                <div className="text-2xl font-bold text-slate-100">
                  {Math.round(teamPerformance.reduce((sum, m) => sum + (m.performanceScore || 0), 0) / Math.max(teamPerformance.length, 1))}
                </div>
                <div className="text-sm text-slate-400">平均得分</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Award className="w-8 h-8 text-purple-400" />
              <div>
                <div className="text-2xl font-bold text-slate-100">
                  {formatCurrency(teamPerformance.reduce((sum, m) => sum + (m.totalRevenue || 0), 0))}
                </div>
                <div className="text-sm text-slate-400">总收入</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 控制栏 */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex-1 flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500 w-4 h-4" />
            <Input
              placeholder="搜索成员姓名、邮箱或部门..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10" />

          </div>

          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="px-3 py-2 border border-slate-600 rounded-md text-sm bg-slate-700 text-slate-200">

            <option value="all">所有区域</option>
            {Object.values(SALES_REGIONS).map((region) =>
            <option key={region.value} value={region.value}>
                {region.label}
            </option>
            )}
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-slate-600 rounded-md text-sm bg-slate-700 text-slate-200">

            <option value="score">综合得分</option>
            <option value="revenue">总收入</option>
            <option value="deals">签单数</option>
            <option value="conversion">转化率</option>
          </select>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setIsEditingConfig(!isEditingConfig);
              if (!isEditingConfig) {
                setConfigDraft(rankingConfig?.metrics || []);
              }
            }}>

            <Settings className="w-4 h-4 mr-2" />
            {isEditingConfig ? '完成配置' : '指标配置'}
          </Button>
        </div>
      </div>

      {/* 配置编辑器 */}
      <AnimatePresence>
        {isEditingConfig && renderConfigEditor()}
      </AnimatePresence>

      {/* 当前排名指标说明 */}
      {!isEditingConfig && displayRankingMetrics.length > 0 &&
      <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-slate-400" />
              <span className="font-medium text-slate-300">当前排名指标</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {displayRankingMetrics.map((metric, index) =>
            <Badge key={index} variant="outline" className="bg-blue-500/10 border-blue-500/30 text-blue-300">
                  {metric.label} ({formatPercentage((metric.weight || 0) * 100)})
            </Badge>
            )}
            </div>
          </CardContent>
      </Card>
      }

      {/* 团队成员排名 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {sortedTeam.map(renderMemberCard)}
      </div>

      {sortedTeam.length === 0 &&
      <Card>
          <CardContent className="p-8 text-center">
            <Users className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-100 mb-2">没有找到团队成员</h3>
            <p className="text-slate-400">请调整搜索条件或筛选器</p>
          </CardContent>
      </Card>
      }
    </div>);

}
