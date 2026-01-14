import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  UserPlus, UserCheck, Target, FileText, 
  BarChart3, ChevronRight, TrendingUp, TrendingDown 
} from 'lucide-react';
import { cn } from '@/lib/utils';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * 招聘统计卡片
 */
const RecruitmentStatCard = ({ title, value, icon: Icon, color, bgColor }) => (
  <Card className="bg-surface-50 border-white/10">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={cn("w-12 h-12 rounded-full flex items-center justify-center", bgColor)}>
          <Icon className={cn("w-6 h-6", color)} />
        </div>
      </div>
    </CardContent>
  </Card>
);

/**
 * 招聘趋势项
 */
const RecruitmentTrendItem = ({ month, positions, hired }) => {
  const successRate = positions > 0 ? (hired / positions) * 100 : 0;
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-300">{month}</span>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">发布</span>
            <span className="text-sm font-semibold text-white">{positions}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">录用</span>
            <span className="text-sm font-semibold text-emerald-400">{hired}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">成功率</span>
            <span className={cn(
              "text-sm font-semibold",
              successRate >= 80 ? "text-emerald-400" : 
              successRate >= 60 ? "text-amber-400" : "text-red-400"
            )}>
              {successRate.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
            <div 
              className="h-full bg-blue-500/50 rounded-full transition-all" 
              style={{ width: `${Math.min(100, (positions / 50) * 100)}%` }}
            />
          </div>
          <span className="text-xs text-slate-400 w-12 text-right">发布数</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
            <div 
              className="h-full bg-emerald-500/50 rounded-full transition-all" 
              style={{ width: `${successRate}%` }}
            />
          </div>
          <span className="text-xs text-slate-400 w-12 text-right">成功率</span>
        </div>
      </div>
    </div>
  );
};

/**
 * 招聘管理标签页组件
 * 
 * @param {Object} props
 * @param {Object} props.stats - 招聘统计数据
 * @param {Array} props.trends - 招聘趋势数据
 * @param {Function} props.onCreateRecruitment - 创建招聘回调
 */
export const HRRecruitmentTab = ({ 
  stats = {
    inProgressRecruitments: 0,
    completedRecruitments: 0,
    recruitmentSuccessRate: 0,
    pendingRecruitments: 0
  },
  trends = [],
  onCreateRecruitment
}) => {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <RecruitmentStatCard
          title="进行中招聘"
          value={stats.inProgressRecruitments}
          icon={UserPlus}
          color="text-blue-400"
          bgColor="bg-blue-500/20"
        />
        <RecruitmentStatCard
          title="已完成招聘"
          value={stats.completedRecruitments}
          icon={UserCheck}
          color="text-emerald-400"
          bgColor="bg-emerald-500/20"
        />
        <RecruitmentStatCard
          title="招聘成功率"
          value={`${stats.recruitmentSuccessRate}%`}
          icon={Target}
          color="text-purple-400"
          bgColor="bg-purple-500/20"
        />
        <RecruitmentStatCard
          title="待审批"
          value={stats.pendingRecruitments}
          icon={FileText}
          color="text-amber-400"
          bgColor="bg-amber-500/20"
        />
      </div>

      {/* 招聘趋势分析 */}
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              招聘趋势分析
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              查看详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trends.length > 0 ? (
              trends.map((trend, index) => (
                <RecruitmentTrendItem key={index} {...trend} />
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                暂无招聘趋势数据
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="text-base">快速操作</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button 
            className="flex items-center gap-2"
            onClick={onCreateRecruitment}
          >
            <UserPlus className="w-4 h-4" />
            发布招聘
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            招聘报表
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default HRRecruitmentTab;
