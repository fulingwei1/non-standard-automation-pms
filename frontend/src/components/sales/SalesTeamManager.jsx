/**
 * Sales Team Manager Component
 * 销售团队管理组件 - 团队成员管理和排名
 */

import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Users,
  UserPlus,
  Search,
  Filter,
  Edit,
  MoreHorizontal,
  TrendingUp,
  TrendingDown,
  Award,
  Target,
  Phone,
  Mail,
  Calendar,
  Star,
  ArrowUp,
  ArrowDown
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { cn } from "../../lib/utils";
import {
  getSalesMemberStatusConfig,
  getSalesPerformanceLevelConfig,
  SALES_RANKING_OPTIONS,
  salesRankingMetricsConfig,
  formatPerformanceMetric,
  calculateSalesCompletionRate,
  formatCurrency
} from "./salesConstants";

export const SalesTeamManager = ({
  teamMembers = [],
  rankingData = [],
  rankingType = "revenue",
  rankingLoading = false,
  metricConfigList = [],
  searchTerm = "",
  onSearchChange = null,
  selectedMember = null,
  onMemberSelect = null,
  onMemberEdit = null,
  onRankingTypeChange = null,
  filters = {},
  onFilterChange = null,
  departmentOptions = [],
  regionOptions = [],
  className = ""
}) => {
  const [showMemberDialog, setShowMemberDialog] = useState(false);
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm);

  // 获取当前排名选项
  const selectedRankingOption = useMemo(() => {
    return SALES_RANKING_OPTIONS.find(option => option.value === rankingType);
  }, [rankingType]);

  // 过滤后的团队成员
  const filteredMembers = useMemo(() => {
    return teamMembers.filter(member => {
      if (localSearchTerm && !member.name.toLowerCase().includes(localSearchTerm.toLowerCase())) {
        return false;
      }
      if (filters.departmentId && member.departmentId !== filters.departmentId) {
        return false;
      }
      if (filters.region && member.region !== filters.region) {
        return false;
      }
      return true;
    });
  }, [teamMembers, localSearchTerm, filters]);

  // 处理搜索
  const handleSearchChange = useCallback((value) => {
    setLocalSearchTerm(value);
    if (onSearchChange) {
      onSearchChange(value);
    }
  }, [onSearchChange]);

  // 处理成员选择
  const handleMemberSelect = useCallback((member) => {
    if (onMemberSelect) {
      onMemberSelect(member);
    }
    setShowMemberDialog(true);
  }, [onMemberSelect]);

  // 成员状态徽章
  const renderMemberStatus = (status) => {
    const config = getSalesMemberStatusConfig(status);
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>
    );
  };

  // 绩效等级徽章
  const renderPerformanceLevel = (member) => {
    const completionRate = calculateSalesCompletionRate(member.monthlyAchieved, member.monthlyTarget);
    const level = completionRate >= 120 ? 'excellent' : completionRate >= 100 ? 'good' : completionRate >= 80 ? 'average' : 'poor';
    const config = getSalesPerformanceLevelConfig(level);
    
    return (
      <Badge variant="outline" className={config.color}>
        {config.label}
      </Badge>
    );
  };

  // 排名变化指示器
  const renderRankingChange = (change) => {
    if (change === 0) {
      return <span className="text-slate-400">-</span>;
    }
    if (change > 0) {
      return (
        <span className="flex items-center text-emerald-400">
          <ArrowUp className="w-3 h-3" />
          {change}
        </span>
      );
    }
    return (
      <span className="flex items-center text-red-400">
        <ArrowDown className="w-3 h-3" />
        {Math.abs(change)}
      </span>
    );
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* 搜索和筛选栏 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
      >
        <div className="flex-1 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <Input
              placeholder="搜索销售成员..."
              value={localSearchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10 bg-slate-800/60 border-slate-700 text-white placeholder-slate-400"
            />
          </div>
          
          {onFilterChange && (
            <>
              <Select
                value={filters.departmentId || ""}
                onValueChange={(value) => onFilterChange({ ...filters, departmentId: value })}
              >
                <SelectTrigger className="w-40 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue placeholder="选择部门" />
                </SelectTrigger>
                <SelectContent>
                  {departmentOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={filters.region || ""}
                onValueChange={(value) => onFilterChange({ ...filters, region: value })}
              >
                <SelectTrigger className="w-40 bg-slate-800/60 border-slate-700 text-white">
                  <SelectValue placeholder="选择区域" />
                </SelectTrigger>
                <SelectContent>
                  {regionOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          )}
        </div>

        <Button
          onClick={() => setShowMemberDialog(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <UserPlus className="w-4 h-4 mr-2" />
          添加成员
        </Button>
      </motion.div>

      {/* 销售业绩排名 */}
      {rankingData && rankingData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border border-slate-700/70 bg-slate-900/40">
            <CardHeader>
              <div className="flex flex-col gap-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/40">
                      <Award className="h-5 w-5 text-amber-400" />
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2 text-base text-white">
                        销售业绩排名
                        <Badge
                          variant="outline"
                          className="bg-slate-800/80 text-xs border-slate-600 text-slate-200"
                        >
                          {rankingData.length} 名成员
                        </Badge>
                      </CardTitle>
                      <p className="text-xs text-slate-500 mt-1">
                        模型支持综合评分与多指标排名，由销售总监维护权重
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {onRankingTypeChange && (
                      <Select
                        value={rankingType}
                        onValueChange={onRankingTypeChange}
                      >
                        <SelectTrigger className="w-40 bg-slate-800 border-slate-700 text-white text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {SALES_RANKING_OPTIONS.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs"
                      onClick={() => window.location.href = "/sales-director-dashboard"}
                    >
                      权重配置
                    </Button>
                  </div>
                </div>
                
                {selectedRankingOption && (
                  <div className="flex items-center gap-2 text-xs text-emerald-400">
                    <TrendingUp className="w-3 h-3" />
                    <span>当前排序：{selectedRankingOption.label}</span>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {rankingLoading ? (
                <div className="text-center py-8 text-slate-400">加载中...</div>
              ) : rankingData.length === 0 ? (
                <div className="text-center py-8 text-slate-400">暂无排名数据</div>
              ) : (
                <div className="overflow-x-auto -mx-4 md:mx-0">
                  <table className="min-w-full divide-y divide-slate-700/60 text-sm">
                    <thead>
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">排名</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">成员</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">综合得分</th>
                        {metricConfigList.map((metric) => (
                          <th
                            key={`header-${metric.key}`}
                            className="px-3 py-2 text-left text-xs font-semibold text-slate-400 whitespace-nowrap"
                          >
                            <div className="text-slate-300">{metric.label}</div>
                            <div className="text-[11px] text-slate-500">
                              权重 {(Number(metric.weight || 0) * 100).toFixed(0)}%
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/40">
                      {rankingData.map((member, index) => (
                        <motion.tr
                          key={member.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
                                  index === 0 ? "bg-amber-500/20 text-amber-400 border-amber-400/30" :
                                  index === 1 ? "bg-slate-400/20 text-slate-400 border-slate-400/30" :
                                  index === 2 ? "bg-orange-600/20 text-orange-400 border-orange-400/30" :
                                  "bg-slate-700/40 text-slate-300 border-slate-600/30"
                                )}
                              >
                                {index + 1}
                              </Badge>
                              {renderRankingChange(member.rankingChange)}
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                                {member.name?.charAt(0) || '?'}
                              </div>
                              <div>
                                <div className="font-medium text-white">{member.name}</div>
                                <div className="text-xs text-slate-500">{member.department}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <div className="font-medium text-emerald-400">
                              {member.comprehensiveScore || '-'}
                            </div>
                          </td>
                          {metricConfigList.map((metric) => {
                            const value = member.metrics?.[metric.key];
                            const formattedValue = formatPerformanceMetric(
                              value,
                              salesRankingMetricsConfig[metric.key]?.format
                            );
                            return (
                              <td key={metric.key} className="px-3 py-3 text-slate-300">
                                {formattedValue}
                              </td>
                            );
                          })}
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 团队成员列表 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-base text-white">
              <Users className="w-5 h-5 text-blue-400" />
              团队成员
              <Badge variant="outline" className="bg-slate-800/80 text-xs border-slate-600 text-slate-200">
                {filteredMembers.length} 名成员
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredMembers.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无团队成员</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredMembers.map((member, index) => {
                  const completionRate = calculateSalesCompletionRate(member.monthlyAchieved, member.monthlyTarget);
                  const performanceLevel = completionRate >= 120 ? 'excellent' : completionRate >= 100 ? 'good' : completionRate >= 80 ? 'average' : 'poor';
                  const performanceConfig = getSalesPerformanceLevelConfig(performanceLevel);
                  
                  return (
                    <motion.div
                      key={member.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ scale: 1.02 }}
                      className="bg-slate-800/60 rounded-lg border border-slate-700/60 p-4 hover:border-slate-600/60 transition-all cursor-pointer"
                      onClick={() => handleMemberSelect(member)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                            {member.name?.charAt(0) || '?'}
                          </div>
                          <div>
                            <h4 className="font-medium text-white">{member.name}</h4>
                            <p className="text-xs text-slate-500">{member.position}</p>
                          </div>
                        </div>
                        <div className="flex flex-col gap-1">
                          {renderMemberStatus(member.status)}
                          {renderPerformanceLevel(member)}
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">月度目标</span>
                          <span className="text-white font-medium">{formatCurrency(member.monthlyTarget || 0)}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">已完成</span>
                          <span className="text-emerald-400 font-medium">{formatCurrency(member.monthlyAchieved || 0)}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">完成率</span>
                          <span className={cn(
                            "font-medium",
                            completionRate >= 100 ? "text-emerald-400" :
                            completionRate >= 80 ? "text-amber-400" : "text-red-400"
                          )}>
                            {completionRate}%
                          </span>
                        </div>
                        <Progress
                          value={Math.min(completionRate, 100)}
                          className={cn(
                            "h-1.5 mt-2",
                            completionRate >= 100 ? "opacity-100" : "opacity-60"
                          )}
                          style={{
                            background: performanceConfig.progress
                          }}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700/40">
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <Mail className="w-3 h-3" />
                          <span className="truncate">{member.email}</span>
                        </div>
                        {onMemberEdit && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 text-slate-400 hover:text-white"
                            onClick={(e) => {
                              e.stopPropagation();
                              onMemberEdit(member);
                            }}
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 成员详情对话框 */}
      <Dialog open={showMemberDialog} onOpenChange={setShowMemberDialog}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">销售成员详情</DialogTitle>
          </DialogHeader>
          {selectedMember && (
            <div className="space-y-4">
              {/* 基本信息 */}
              <div className="flex items-center gap-4 p-4 bg-slate-800/60 rounded-lg">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xl font-bold">
                  {selectedMember.name?.charAt(0) || '?'}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white">{selectedMember.name}</h3>
                  <p className="text-slate-400">{selectedMember.position}</p>
                  <div className="flex items-center gap-2 mt-2">
                    {renderMemberStatus(selectedMember.status)}
                    {renderPerformanceLevel(selectedMember)}
                  </div>
                </div>
              </div>

              {/* 详细信息网格 */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-800/40 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">邮箱</div>
                  <div className="text-sm text-white">{selectedMember.email}</div>
                </div>
                <div className="p-3 bg-slate-800/40 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">电话</div>
                  <div className="text-sm text-white">{selectedMember.phone || '未设置'}</div>
                </div>
                <div className="p-3 bg-slate-800/40 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">部门</div>
                  <div className="text-sm text-white">{selectedMember.department || '未分配'}</div>
                </div>
                <div className="p-3 bg-slate-800/40 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">区域</div>
                  <div className="text-sm text-white">{selectedMember.region || '未分配'}</div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SalesTeamManager;