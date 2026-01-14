/**
 * HR Relations Tab Component - 员工关系标签页
 * 
 * 核心功能:
 * 1. 员工关系问题统计
 * 2. 问题类型分布
 * 3. 待处理问题列表
 * 4. 处理进度跟踪
 * 5. 快速操作
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  Heart,
  AlertTriangle,
  CheckCircle2,
  Clock,
  UserMinus,
  MessageSquare,
  FileText,
  TrendingUp,
  Plus,
  BarChart3,
  Shield,
  Users,
  Calendar,
  ChevronRight
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress
} from '../ui';
import { cn } from '../../lib/utils';
import { fadeIn } from '../../lib/animations';

const HRRelationsTab = ({
  stats = {},
  issues = [],
  onCreateIssue,
  onViewIssue,
  onResolveIssue,
  formatDate = (date) => date
}) => {
  // 计算统计数据
  const {
    totalIssues = 0,
    pendingIssues = 0,
    resolvedIssues = 0,
    avgResolutionTime = 0
  } = stats;

  // 问题类型配置
  const issueTypes = {
    conflict: { 
      label: '冲突', 
      icon: AlertTriangle, 
      color: 'text-red-400', 
      bg: 'bg-red-500/20',
      border: 'border-red-500/30'
    },
    leave: { 
      label: '请假', 
      icon: Calendar, 
      color: 'text-blue-400', 
      bg: 'bg-blue-500/20',
      border: 'border-blue-500/30'
    },
    complaint: { 
      label: '投诉', 
      icon: MessageSquare, 
      color: 'text-amber-400', 
      bg: 'bg-amber-500/20',
      border: 'border-amber-500/30'
    },
    resignation: { 
      label: '离职', 
      icon: UserMinus, 
      color: 'text-purple-400', 
      bg: 'bg-purple-500/20',
      border: 'border-purple-500/30'
    },
    performance: { 
      label: '绩效', 
      icon: TrendingUp, 
      color: 'text-cyan-400', 
      bg: 'bg-cyan-500/20',
      border: 'border-cyan-500/30'
    },
    other: { 
      label: '其他', 
      icon: FileText, 
      color: 'text-slate-400', 
      bg: 'bg-slate-500/20',
      border: 'border-slate-500/30'
    }
  };

  // 状态配置
  const statusConfig = {
    pending: { label: '待处理', color: 'text-amber-400', bg: 'bg-amber-500/20' },
    in_progress: { label: '处理中', color: 'text-blue-400', bg: 'bg-blue-500/20' },
    resolved: { label: '已解决', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
    closed: { label: '已关闭', color: 'text-slate-400', bg: 'bg-slate-500/20' }
  };

  // 优先级配置
  const priorityConfig = {
    low: { label: '低', color: 'text-slate-400', bg: 'bg-slate-500/20' },
    medium: { label: '中', color: 'text-blue-400', bg: 'bg-blue-500/20' },
    high: { label: '高', color: 'text-amber-400', bg: 'bg-amber-500/20' },
    urgent: { label: '紧急', color: 'text-red-400', bg: 'bg-red-500/20' }
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">待处理问题</p>
                  <p className="text-2xl font-bold text-white">{pendingIssues}</p>
                  <p className="text-xs text-amber-400 mt-1">需要关注</p>
                </div>
                <div className="p-3 bg-amber-500/20 rounded-lg">
                  <Clock className="w-6 h-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">已解决问题</p>
                  <p className="text-2xl font-bold text-white">{resolvedIssues}</p>
                  <p className="text-xs text-emerald-400 mt-1">本月累计</p>
                </div>
                <div className="p-3 bg-emerald-500/20 rounded-lg">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">问题总数</p>
                  <p className="text-2xl font-bold text-white">{totalIssues}</p>
                  <p className="text-xs text-slate-500 mt-1">本月统计</p>
                </div>
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <Heart className="w-6 h-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">平均处理时长</p>
                  <p className="text-2xl font-bold text-white">{avgResolutionTime}</p>
                  <p className="text-xs text-slate-500 mt-1">小时</p>
                </div>
                <div className="p-3 bg-purple-500/20 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 问题列表 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-5 w-5 text-blue-400" />
                员工关系问题
              </CardTitle>
              <Button
                size="sm"
                onClick={onCreateIssue}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                记录问题
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {issues.length === 0 ? (
                <div className="py-8 text-center text-slate-400">
                  <Heart className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>暂无员工关系问题</p>
                  <p className="text-xs text-slate-500 mt-1">良好的员工关系是企业发展的基石</p>
                </div>
              ) : (
                issues.map((issue, index) => {
                  const typeConfig = issueTypes[issue.type] || issueTypes.other;
                  const Icon = typeConfig.icon;
                  const statusCfg = statusConfig[issue.status] || statusConfig.pending;
                  const priorityCfg = priorityConfig[issue.priority] || priorityConfig.medium;

                  return (
                    <div
                      key={issue.id || index}
                      className={cn(
                        "p-4 rounded-lg border hover:border-slate-600/80 transition-all cursor-pointer",
                        "bg-slate-800/40",
                        issue.priority === 'urgent' || issue.priority === 'high'
                          ? "border-red-500/30"
                          : "border-slate-700/50"
                      )}
                      onClick={() => onViewIssue && onViewIssue(issue)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <div className={cn("p-1.5 rounded", typeConfig.bg)}>
                              <Icon className={cn("w-4 h-4", typeConfig.color)} />
                            </div>
                            <h3 className="font-medium text-white">{issue.title}</h3>
                            <Badge className={cn("text-xs", typeConfig.bg, typeConfig.color)}>
                              {typeConfig.label}
                            </Badge>
                            <Badge className={cn("text-xs", statusCfg.bg, statusCfg.color)}>
                              {statusCfg.label}
                            </Badge>
                            {(issue.priority === 'high' || issue.priority === 'urgent') && (
                              <Badge className={cn("text-xs", priorityCfg.bg, priorityCfg.color)}>
                                {priorityCfg.label}
                              </Badge>
                            )}
                          </div>
                          
                          {issue.description && (
                            <p className="text-sm text-slate-300 mb-2 line-clamp-2">
                              {issue.description}
                            </p>
                          )}
                          
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {issue.employee} · {issue.department}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(issue.created_at)}
                            </span>
                            {issue.handler && (
                              <span className="flex items-center gap-1">
                                处理人: {issue.handler}
                              </span>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0 ml-2" />
                      </div>

                      {/* 处理进度 */}
                      {issue.status === 'in_progress' && issue.progress !== undefined && (
                        <div className="mt-3 space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">处理进度</span>
                            <span className="text-blue-400 font-medium">{issue.progress}%</span>
                          </div>
                          <Progress value={issue.progress} className="h-1.5" />
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 快速操作 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-5 w-5 text-cyan-400" />
              快速操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-blue-500/10 hover:border-blue-500/30"
                onClick={onCreateIssue}
              >
                <Plus className="w-4 h-4 text-blue-400" />
                <span>记录新问题</span>
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-purple-500/10 hover:border-purple-500/30"
                onClick={() => {/* TODO: 查看报告 */}}
              >
                <FileText className="w-4 h-4 text-purple-400" />
                <span>关系报告</span>
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-amber-500/10 hover:border-amber-500/30"
                onClick={() => {/* TODO: 统计分析 */}}
              >
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <span>统计分析</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export { HRRelationsTab };
