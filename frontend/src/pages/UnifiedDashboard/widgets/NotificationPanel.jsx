/**
 * 通知面板组件 (Notification Panel)
 *
 * 显示系统通知、预警信息
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bell,
  AlertTriangle,
  Info,
  CheckCircle2,
  ChevronRight,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import api from '../../../services/api';
import { cn } from '../../../lib/utils';

// 通知类型图标映射
const typeIcons = {
  alert: AlertTriangle,
  warning: AlertTriangle,
  info: Info,
  success: CheckCircle2,
  default: Bell,
};

// 通知类型颜色映射
const typeColors = {
  alert: 'text-red-500 bg-red-50',
  warning: 'text-yellow-500 bg-yellow-50',
  info: 'text-blue-500 bg-blue-50',
  success: 'text-green-500 bg-green-50',
  default: 'text-gray-500 bg-gray-50',
};

// 默认通知数据
const defaultNotifications = [
  {
    id: 1,
    type: 'alert',
    title: '项目 PJ250101-001 进度延期预警',
    message: '当前进度落后计划 3 天',
    time: '10分钟前',
    read: false,
  },
  {
    id: 2,
    type: 'warning',
    title: '物料库存预警',
    message: '电阻 R0603-10K 库存不足',
    time: '30分钟前',
    read: false,
  },
  {
    id: 3,
    type: 'info',
    title: '审批通过通知',
    message: '您的请假申请已通过',
    time: '1小时前',
    read: true,
  },
  {
    id: 4,
    type: 'success',
    title: '任务完成',
    message: '项目方案评审已完成',
    time: '2小时前',
    read: true,
  },
];

/**
 * 单个通知项
 */
function NotificationItem({ notification, index, onClick }) {
  const Icon = typeIcons[notification.type] || typeIcons.default;
  const colorClass = typeColors[notification.type] || typeColors.default;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onClick?.(notification)}
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
        'hover:bg-muted/50',
        !notification.read && 'bg-primary/5'
      )}
    >
      {/* 类型图标 */}
      <div className={cn('p-2 rounded-md', colorClass)}>
        <Icon className="h-4 w-4" />
      </div>

      {/* 通知内容 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={cn(
            'text-sm font-medium truncate',
            !notification.read && 'font-semibold'
          )}>
            {notification.title}
          </p>
          {!notification.read && (
            <Badge variant="default" className="text-xs px-1.5 py-0 h-4">
              新
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1 truncate">
          {notification.message}
        </p>
      </div>

      {/* 时间 */}
      <div className="flex items-center text-xs text-muted-foreground whitespace-nowrap">
        <Clock className="h-3 w-3 mr-1" />
        {notification.time}
      </div>
    </motion.div>
  );
}

/**
 * 通知面板主组件
 *
 * @param {Object} props
 * @param {string} props.filter - 过滤类型（critical/warning/all）
 * @param {number} props.limit - 显示数量限制
 * @param {Object} props.data - 预加载的数据
 */
export default function NotificationPanel({ filter, limit = 5, data }) {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const loadNotifications = async () => {
      setLoading(true);
      try {
        // 如果有预加载数据，直接使用
        if (data?.notifications) {
          const items = data.notifications.slice(0, limit);
          setNotifications(items);
          setUnreadCount(items.filter(n => !n.read).length);
          return;
        }

        // 否则尝试从 API 获取
        try {
          const params = filter ? { type: filter } : {};
          const response = await api.get('/notifications', { params });
          if (response.data?.items) {
            const items = response.data.items.slice(0, limit);
            setNotifications(items);
            setUnreadCount(items.filter(n => !n.read).length);
            return;
          }
        } catch {
          // API 不可用，使用默认数据
        }

        // 使用默认数据
        const items = defaultNotifications.slice(0, limit);
        setNotifications(items);
        setUnreadCount(items.filter(n => !n.read).length);
      } finally {
        setLoading(false);
      }
    };

    loadNotifications();
  }, [filter, limit, data]);

  const handleNotificationClick = (notification) => {
    // 根据通知类型跳转
    if (notification.type === 'alert' || notification.type === 'warning') {
      navigate('/alerts');
    } else {
      navigate('/notifications');
    }
  };

  const handleViewAll = () => {
    navigate('/notifications');
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Bell className="h-4 w-4" />
            通知中心
            {unreadCount > 0 && (
              <Badge variant="destructive" className="text-xs px-1.5 py-0 h-5">
                {unreadCount}
              </Badge>
            )}
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={handleViewAll}>
            查看���部
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="h-16 bg-muted/50 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <Bell className="h-8 w-8 mb-2" />
            <p className="text-sm">暂无通知</p>
          </div>
        ) : (
          <div className="space-y-1">
            {notifications.map((notification, index) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                index={index}
                onClick={handleNotificationClick}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
