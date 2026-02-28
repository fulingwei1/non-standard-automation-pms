import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bell,
  Check,
  CheckCheck,
  AlertTriangle,
  Info,
  Calendar,
  Package,
  FileText,
  Users,
  Clock,
  Trash2,
  Filter,
  Search } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { notificationApi } from "../services/api";
import { ApiIntegrationError } from "../components/ui";

// Mock notification data - 已移除，使用真实API

import { confirmAction } from "@/lib/confirmAction";
const notificationTypes = [
{ value: "all", label: "全部", icon: Bell },
{ value: "alert", label: "预警", icon: AlertTriangle },
{ value: "task", label: "任务", icon: FileText },
{ value: "material", label: "物料", icon: Package },
{ value: "system", label: "系统", icon: Info },
{ value: "milestone", label: "里程碑", icon: Calendar }];


const getNotificationIcon = (type) => {
  const icons = {
    alert: AlertTriangle,
    task: FileText,
    material: Package,
    system: Info,
    milestone: Calendar
  };
  return icons[type] || Bell;
};

const getNotificationColor = (type, priority) => {
  if (priority === "high") {
    return "text-red-400 bg-red-400/10";
  }
  const colors = {
    alert: "text-amber-400 bg-amber-400/10",
    task: "text-blue-400 bg-blue-400/10",
    material: "text-emerald-400 bg-emerald-400/10",
    system: "text-slate-400 bg-slate-400/10",
    milestone: "text-cyan-400 bg-cyan-400/10"
  };
  return colors[type] || "text-slate-400 bg-slate-400/10";
};

function NotificationItem({ notification, onMarkRead, onDelete }) {
  const Icon = getNotificationIcon(notification.type);
  const colorClass = getNotificationColor(
    notification.type,
    notification.priority
  );
  const isCc = notification.isCc || false; // 检查是否是抄送通知

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      whileHover={{ scale: 1.01 }}
      className={cn(
        "group relative p-4 rounded-xl border transition-all duration-200",
        notification.read ?
        "bg-surface-1/50 border-border/50" :
        "bg-surface-2 border-border shadow-lg shadow-black/10",
        isCc && "border-dashed border-slate-600/50" // 抄送通知使用虚线边框
      )}>

      {/* Unread indicator */}
      {!notification.read &&
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-accent rounded-r-full" />
      }

      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={cn("p-2.5 rounded-xl", colorClass)}>
          <Icon className="w-5 h-5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4
              className={cn(
                "font-medium",
                notification.read ? "text-slate-300" : "text-white"
              )}>

              {notification.title}
            </h4>
            {isCc &&
            <Badge
              variant="outline"
              className="text-[10px] px-1.5 py-0 text-slate-400 border-slate-600">

                抄送
            </Badge>
            }
            {notification.priority === "high" &&
            <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                紧急
            </Badge>
            }
          </div>
          <p className="text-sm text-slate-400 line-clamp-2">
            {notification.message}
          </p>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {notification.timestamp}
            </span>
            {notification.relatedId &&
            <span className="text-xs text-accent">
                #{notification.relatedId}
            </span>
            }
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {!notification.read &&
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onMarkRead(notification.id)}
            className="h-8 w-8 p-0">

              <Check className="w-4 h-4" />
          </Button>
          }
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(notification.id)}
            className="h-8 w-8 p-0 text-slate-400 hover:text-red-400">

            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </motion.div>);

}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [page, _setPage] = useState(1);
  const [_total, setTotal] = useState(0);

  // Map API notification type to display type
  const getNotificationType = (notification) => {
    const typeMap = {
      ALERT: "alert",
      TASK: "task",
      MATERIAL: "material",
      SYSTEM: "system",
      MILESTONE: "milestone"
    };
    return (
      typeMap[notification.notification_type] ||
      notification.notification_type?.toLowerCase() ||
      "system");

  };

  // Format notification for display
  const formatNotification = (notification) => {
    // 检查是否是抄送通知
    const isCc = notification.extra_data?.is_cc === true;

    return {
      id: notification.id,
      type: getNotificationType(notification),
      title: notification.title || "通知",
      message: notification.content || notification.message || "",
      timestamp: notification.created_at ?
      new Date(notification.created_at).toLocaleString("zh-CN") :
      "",
      read: notification.is_read || false,
      priority: notification.priority?.toLowerCase() || "normal",
      relatedId: notification.source_id,
      relatedType: notification.source_type?.toLowerCase(),
      isCc: isCc, // 标记是否为抄送通知
      extraData: notification.extra_data || {}
    };
  };

  // Load notifications
  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: 50,
        is_read: showUnreadOnly ? false : undefined,
        notification_type: filter !== "all" ? filter.toUpperCase() : undefined
      };
      const response = await notificationApi.list(params);
      const data = response.data || response;
      const notificationsData = data.items || data || [];

      // Format notifications for display
      const formattedNotifications = (notificationsData || []).map(formatNotification);
      setNotifications(formattedNotifications);
      setTotal(data.total || formattedNotifications.length);
    } catch (err) {
      console.error("Failed to load notifications:", err);
      setError(err);
      setNotifications([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, filter, showUnreadOnly]);

  // Load unread count
  const loadUnreadCount = useCallback(async () => {
    try {
      const response = await notificationApi.getUnreadCount();
      const data = response.data || response;
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error("Failed to load unread count:", err);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
    loadUnreadCount();
  }, [loadNotifications, loadUnreadCount]);

  const filteredNotifications = (notifications || []).filter((n) => {
    if (search && !n.title?.includes(search) && !n.content?.includes(search))
    {return false;}
    return true;
  });

  const handleMarkRead = async (id) => {
    try {
      await notificationApi.markRead(id);
      await loadNotifications();
      await loadUnreadCount();
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationApi.readAll();
      await loadNotifications();
      await loadUnreadCount();
    } catch (err) {
      console.error("Failed to mark all as read:", err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationApi.delete(id);
      await loadNotifications();
      await loadUnreadCount();
    } catch (err) {
      console.error("Failed to delete notification:", err);
    }
  };

  const handleClearAll = async () => {
    if (!await confirmAction("确定要清空所有通知吗？此操作不可撤销。")) {
      return;
    }
    try {
      // Delete all notifications one by one
      await Promise.all((notifications || []).map((n) => notificationApi.delete(n.id)));
      await loadNotifications();
      await loadUnreadCount();
    } catch (err) {
      console.error("Failed to clear all notifications:", err);
    }
  };

  // Show error state
  if (error && notifications?.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6 space-y-6">
          <PageHeader title="通知中心" description="查看系统通知和消息" />
          <ApiIntegrationError
            error={error}
            apiEndpoint="/api/v1/notifications"
            onRetry={loadNotifications} />

        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6">

          <PageHeader
            title="通知中心"
            description={`您有 ${unreadCount} 条未读通知`} />


          {/* Stats Cards */}
          <motion.div
            variants={fadeIn}
            className="grid grid-cols-2 md:grid-cols-4 gap-4">

            {[
            {
              label: "全部通知",
              value: notifications?.length,
              icon: Bell,
              color: "text-blue-400"
            },
            {
              label: "未读",
              value: unreadCount,
              icon: Info,
              color: "text-amber-400"
            },
            {
              label: "紧急",
              value: (notifications || []).filter((n) => n.priority === "high").
              length,
              icon: AlertTriangle,
              color: "text-red-400"
            },
            {
              label: "待审批",
              value: (notifications || []).filter(
                (n) => n.type === "approval" && !n.read
              ).length,
              icon: Users,
              color: "text-purple-400"
            }].
            map((stat, index) =>
            <Card key={index} className="bg-surface-1/50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">{stat.label}</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {stat.value}
                      </p>
                    </div>
                    {(() => { const DynIcon = stat.icon; return <DynIcon className={cn("w-8 h-8", stat.color)}  />; })()}
                  </div>
                </CardContent>
            </Card>
            )}
          </motion.div>

          {/* Filters & Actions */}
          <motion.div variants={fadeIn}>
            <Card className="bg-surface-1/50">
              <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
                  {/* Type Filter */}
                  <div className="flex flex-wrap gap-2">
                    {(notificationTypes || []).map((type) =>
                    <Button
                      key={type.value}
                      variant={filter === type.value ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setFilter(type.value)}
                      className={cn(
                        "gap-1.5",
                        filter === type.value &&
                        "bg-accent text-white hover:bg-accent/90"
                      )}>

                        {(() => { const DynIcon = type.icon; return <DynIcon className="w-4 h-4"  />; })()}
                        {type.label}
                    </Button>
                    )}
                  </div>

                  {/* Search & Actions */}
                  <div className="flex items-center gap-3 w-full lg:w-auto">
                    <div className="relative flex-1 lg:w-64">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        placeholder="搜索通知..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-9" />

                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowUnreadOnly(!showUnreadOnly)}
                      className={cn(
                        showUnreadOnly && "bg-accent/10 border-accent"
                      )}>

                      <Filter className="w-4 h-4 mr-1" />
                      未读
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Actions Bar */}
          {unreadCount > 0 &&
          <motion.div
            variants={fadeIn}
            className="flex items-center justify-between">

              <span className="text-sm text-slate-400">
                显示 {filteredNotifications.length} 条通知
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
                  <CheckCheck className="w-4 h-4 mr-1" />
                  全部已读
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={handleClearAll}
                className="text-red-400 hover:text-red-300">

                  <Trash2 className="w-4 h-4 mr-1" />
                  清空
                </Button>
              </div>
          </motion.div>
          }

          {/* Notification List */}
          <motion.div variants={fadeIn} className="space-y-3">
            {loading ?
            <div className="text-center py-16">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto" />
                <p className="text-sm text-slate-400 mt-4">加载中...</p>
            </div> :
            error ?
            <div className="text-center py-16">
                <AlertTriangle className="w-16 h-16 mx-auto text-red-400 mb-4" />
                <h3 className="text-lg font-medium text-red-400">加载失败</h3>
                <p className="text-sm text-slate-500 mt-1">请刷新页面重试</p>
            </div> :

            <AnimatePresence mode="popLayout">
                {filteredNotifications.length > 0 ?
              (filteredNotifications || []).map((notification) =>
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkRead={handleMarkRead}
                onDelete={handleDelete} />

              ) :

              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-16">

                    <Bell className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                    <h3 className="text-lg font-medium text-slate-400">
                      暂无通知
                    </h3>
                    <p className="text-sm text-slate-500 mt-1">
                      {search || showUnreadOnly ?
                  "没有符合条件的通知" :
                  "所有通知都已处理"}
                    </p>
              </motion.div>
              }
            </AnimatePresence>
            }
          </motion.div>
        </motion.div>
      </div>
    </div>);

}