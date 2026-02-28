import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Clock, CheckCircle2, Target, Award, 
  BarChart3, TrendingUp, Star 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import StatCard from '../common/StatCard';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * 绩效分布项
 */
const PerformanceDistributionItem = ({ level, count, percentage, color }) => (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Star className={cn("w-4 h-4", color)} />
        <span className="text-sm font-medium text-slate-300">{level}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">{count}人</span>
        <span className={cn("text-sm font-semibold", color)}>
          {percentage.toFixed(1)}%
        </span>
      </div>
    </div>
    <Progress value={percentage} className="h-2" />
  </div>
);

/**
 * 绩效管理标签页组件
 * 
 * @param {Object} props
 * @param {Object} props.stats - 绩效统计数据
 * @param {Array} props.distribution - 绩效分布数据
 * @param {Function} props.onCreateReview - 创建评审回调
 */
export const HRPerformanceTab = ({
  stats = {
    pendingPerformanceReviews: 0,
    completedPerformanceReviews: 0,
    performanceCompletionRate: 0,
    avgPerformanceScore: 0
  },
  distribution = [],
  onCreateReview
}) => {
  const performanceColors = {
    'A-优秀': 'text-emerald-400',
    'B-良好': 'text-blue-400',
    'C-合格': 'text-amber-400',
    'D-待改进': 'text-orange-400',
    'E-不合格': 'text-red-400'
  };

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="待评审"
          value={stats.pendingPerformanceReviews}
          icon={Clock}
          color="text-amber-400"
          bg="bg-amber-500/20"
          size="large"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:bg-surface-100 hover:border-white/20 bg-none hover:shadow-none"
          iconWrapperClassName="w-12 h-12 p-0 rounded-full flex items-center justify-center"
          iconClassName="w-6 h-6"
        />
        <StatCard
          title="已完成"
          value={stats.completedPerformanceReviews}
          icon={CheckCircle2}
          color="text-emerald-400"
          bg="bg-emerald-500/20"
          size="large"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:bg-surface-100 hover:border-white/20 bg-none hover:shadow-none"
          iconWrapperClassName="w-12 h-12 p-0 rounded-full flex items-center justify-center"
          iconClassName="w-6 h-6"
        />
        <StatCard
          title="完成率"
          value={`${stats.performanceCompletionRate}%`}
          icon={Target}
          color="text-blue-400"
          bg="bg-blue-500/20"
          size="large"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:bg-surface-100 hover:border-white/20 bg-none hover:shadow-none"
          iconWrapperClassName="w-12 h-12 p-0 rounded-full flex items-center justify-center"
          iconClassName="w-6 h-6"
        />
        <StatCard
          title="平均分"
          value={stats.avgPerformanceScore}
          icon={Award}
          color="text-purple-400"
          bg="bg-purple-500/20"
          size="large"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:bg-surface-100 hover:border-white/20 bg-none hover:shadow-none"
          iconWrapperClassName="w-12 h-12 p-0 rounded-full flex items-center justify-center"
          iconClassName="w-6 h-6"
        />
      </div>

      {/* 绩效分布 */}
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-5 w-5 text-blue-400" />
            绩效等级分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {distribution.length > 0 ? (
              distribution.map((item, index) => (
                <PerformanceDistributionItem
                  key={index}
                  level={item.level}
                  count={item.count}
                  percentage={item.percentage}
                  color={performanceColors[item.level] || 'text-slate-400'}
                />
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                暂无绩效分布数据
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
            onClick={onCreateReview}
          >
            <Award className="w-4 h-4" />
            创建评审
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            绩效报表
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            绩效分析
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default HRPerformanceTab;
