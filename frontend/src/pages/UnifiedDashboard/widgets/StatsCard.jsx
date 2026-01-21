/**
 * 统计卡片组件 (Stats Card)
 *
 * 显示关键指标统计数据
 * 支持多种类型：销售、工程、生产等
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Briefcase,
  Users,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Package,
  FileText,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import api from '../../../services/api';
import { cn } from '../../../lib/utils';

// 指标图标映射
const metricIcons = {
  leads: Briefcase,
  opportunities: TrendingUp,
  contracts: FileText,
  revenue: DollarSign,
  tasks: CheckCircle2,
  'hours-logged': Clock,
  'ecn-pending': AlertTriangle,
  reviews: FileText,
  orders: Package,
  pending: Clock,
  overdue: AlertTriangle,
  savings: DollarSign,
  users: Users,
  roles: Users,
  logins: Users,
  errors: AlertTriangle,
  'my-projects': Briefcase,
  'on-track': CheckCircle2,
  issues: AlertTriangle,
  milestones: CheckCircle2,
  default: Briefcase,
};

// 默认统���数据
const defaultStats = {
  sales: [
    { key: 'leads', label: '活跃线索', value: 0, trend: 0 },
    { key: 'opportunities', label: '商机数', value: 0, trend: 0 },
    { key: 'contracts', label: '合同数', value: 0, trend: 0 },
    { key: 'revenue', label: '本月签约', value: '¥0', trend: 0 },
  ],
  engineer: [
    { key: 'tasks', label: '待办任务', value: 0, trend: 0 },
    { key: 'hours-logged', label: '本周工时', value: '0h', trend: 0 },
    { key: 'ecn-pending', label: '待处理ECN', value: 0, trend: 0 },
    { key: 'reviews', label: '待评审', value: 0, trend: 0 },
  ],
  procurement: [
    { key: 'orders', label: '采购订单', value: 0, trend: 0 },
    { key: 'pending', label: '待确认', value: 0, trend: 0 },
    { key: 'overdue', label: '逾期', value: 0, trend: 0 },
    { key: 'savings', label: '节省金额', value: '¥0', trend: 0 },
  ],
  production: [
    { key: 'work-orders', label: '工单数', value: 0, trend: 0 },
    { key: 'in-progress', label: '进行中', value: 0, trend: 0 },
    { key: 'completed', label: '已完成', value: 0, trend: 0 },
    { key: 'yield', label: '良品率', value: '0%', trend: 0 },
  ],
  pmo: [
    { key: 'active-projects', label: '活跃项目', value: 0, trend: 0 },
    { key: 'on-track', label: '正常进度', value: 0, trend: 0 },
    { key: 'delayed', label: '延期项目', value: 0, trend: 0 },
    { key: 'completed', label: '已完成', value: 0, trend: 0 },
  ],
  admin: [
    { key: 'users', label: '用户数', value: 0, trend: 0 },
    { key: 'roles', label: '角色数', value: 0, trend: 0 },
    { key: 'logins', label: '今日登录', value: 0, trend: 0 },
    { key: 'errors', label: '系统错误', value: 0, trend: 0 },
  ],
};

/**
 * 单个统计项
 */
function StatItem({ stat, index }) {
  const Icon = metricIcons[stat.key] || metricIcons.default;
  const isPositive = stat.trend > 0;
  const isNegative = stat.trend < 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
    >
      <div className="p-2 rounded-md bg-primary/10">
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted-foreground truncate">{stat.label}</p>
        <p className="text-lg font-semibold">{stat.value}</p>
      </div>
      {stat.trend !== 0 && (
        <div className={cn(
          'flex items-center text-xs',
          isPositive && 'text-green-600',
          isNegative && 'text-red-600'
        )}>
          {isPositive ? (
            <TrendingUp className="h-3 w-3 mr-1" />
          ) : (
            <TrendingDown className="h-3 w-3 mr-1" />
          )}
          {Math.abs(stat.trend)}%
        </div>
      )}
    </motion.div>
  );
}

/**
 * 统计卡片主组件
 *
 * @param {Object} props
 * @param {string} props.type - 统计类型（sales/engineer/procurement/production/pmo/admin）
 * @param {Array} props.metrics - 要显示的指标列表
 * @param {Object} props.data - 预加载的数据
 */
export default function StatsCard({ type = 'sales', metrics, data }) {
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      setLoading(true);
      try {
        // 如果有预加载数据，直接使用
        if (data?.stats) {
          setStats(data.stats);
          return;
        }

        // 否则尝试从 API 获取
        try {
          const response = await api.get(`/dashboard/stats/${type}`);
          if (response.data?.stats) {
            setStats(response.data.stats);
            return;
          }
        } catch {
          // API 不可用，使用默认数据
        }

        // 使用默认数据
        const defaultData = defaultStats[type] || defaultStats.sales;
        setStats(defaultData);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [type, data]);

  // 根据 metrics 参数过滤显示的统计项
  const displayStats = metrics
    ? stats.filter(s => metrics.includes(s.key))
    : stats;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">关键指标</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="grid grid-cols-2 gap-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {displayStats.map((stat, index) => (
              <StatItem key={stat.key} stat={stat} index={index} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
