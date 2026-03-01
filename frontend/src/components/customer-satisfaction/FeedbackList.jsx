/**
 * Feedback List Component
 * 反馈列表组件 - 显示和筛选客户反馈信息
 */

import { useState, useMemo, useEffect as _useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Filter,
  MessageSquare,
  Star,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  User,
  Building,
  Calendar,
  Tag } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger } from
"../../components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger } from
"../../components/ui/tooltip";
import { cn, formatDateTime } from "../../lib/utils";
import {
  getFeedbackStatusConfig,
  getFeedbackTypeConfig,
  getPriorityConfig,
  getSatisfactionScoreConfig as _getSatisfactionScoreConfig,
  formatSatisfactionScore,
  satisfactionConstants } from
"@/lib/constants/customer";

import { confirmAction } from "@/lib/confirmAction";
export const FeedbackList = ({
  feedbacks = [],
  loading = false,
  className = "",
  onFeedbackClick = null,
  onStatusChange = null,
  onPriorityChange = null,
  onDelete = null,
  onRefresh = null,
  showActions = true,
  pageSize = 10,
  currentPage: initialPage = 1
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedPriority, _setSelectedPriority] = useState("all");
  const [sortBy, _setSortBy] = useState("createdAt");
  const [sortOrder, _setSortOrder] = useState("desc");
  const [currentPage, setCurrentPage] = useState(initialPage);

  _useEffect(() => {
    setCurrentPage(initialPage);
  }, [initialPage]);

  // 过滤和排序反馈数据
  const filteredAndSortedFeedbacks = useMemo(() => {
    let filtered = feedbacks;

    // 搜索过滤
    if (searchQuery) {
      filtered = (filtered || []).filter((feedback) =>
      feedback.customerName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feedback.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      feedback.id?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // 类型过滤
    if (selectedType !== "all") {
      filtered = (filtered || []).filter((feedback) => feedback.feedbackType === selectedType);
    }

    // 状态过滤
    if (selectedStatus !== "all") {
      filtered = (filtered || []).filter((feedback) => feedback.status === selectedStatus);
    }

    // 优先级过滤
    if (selectedPriority !== "all") {
      filtered = (filtered || []).filter((feedback) => feedback.priority === selectedPriority);
    }

    // 排序
    filtered.sort((a, b) => {
      let aValue, bValue;

      switch (sortBy) {
        case "rating":
          aValue = a.rating;
          bValue = b.rating;
          break;
        case "priority":
          {
            const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
            aValue = priorityOrder[a.priority] || 0;
            bValue = priorityOrder[b.priority] || 0;
          }
          break;
        case "createdAt":
        default:
          aValue = new Date(a.createdAt);
          bValue = new Date(b.createdAt);
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [feedbacks, searchQuery, selectedType, selectedStatus, selectedPriority, sortBy, sortOrder]);

  // 分页数据
  const paginatedFeedbacks = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredAndSortedFeedbacks.slice(startIndex, endIndex);
  }, [filteredAndSortedFeedbacks, currentPage, pageSize]);

  // 处理反馈点击
  const handleFeedbackClick = (feedback) => {
    if (onFeedbackClick) {
      onFeedbackClick(feedback);
    }
  };

  // 处理状态变更
  const handleStatusChange = (feedbackId, newStatus) => {
    if (onStatusChange) {
      onStatusChange(feedbackId, newStatus);
    }
  };

  // 处理优先级变更
  const _handlePriorityChange = (feedbackId, newPriority) => {
    if (onPriorityChange) {
      onPriorityChange(feedbackId, newPriority);
    }
  };

  // 处理删除
  const handleDelete = async (feedbackId, e) => {
    e.stopPropagation();
    if (onDelete && await confirmAction("确定要删除这条反馈吗？")) {
      onDelete(feedbackId);
    }
  };

  // 渲染星级评分
  const renderRating = (rating) => {
    if (!rating || rating === 0) {
      return (
        <div className="flex items-center text-slate-400">
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm ml-1">未评分</span>
        </div>);

    }

    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <Star
          key={i}
          className={cn(
            "w-4 h-4",
            i <= rating ?
            "text-yellow-400 fill-current" :
            "text-slate-300"
          )} />

      );
    }

    return (
      <div className="flex items-center gap-1">
        {stars}
        <span className="text-sm text-slate-600 ml-1">
          {formatSatisfactionScore(rating)}
        </span>
      </div>);

  };

  // 渲染操作按钮
  const renderActions = (feedback) => {
    if (!showActions) {return null;}

    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-slate-500 hover:text-slate-700">

            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-48">
          <div className="space-y-1">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleFeedbackClick(feedback)}>

              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleStatusChange(feedback.id, "in_progress")}>

              <RefreshCw className="w-4 h-4 mr-2" />
              开始处理
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-red-500 hover:text-red-700"
              onClick={(e) => handleDelete(feedback.id, e)}>

              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </Button>
          </div>
        </PopoverContent>
      </Popover>);

  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("w-full", className)}>

      <Card className="border-slate-200 bg-white/80 backdrop-blur-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-slate-800">
              客户反馈列表
            </CardTitle>
            {onRefresh &&
            <Button
              variant="outline"
              size="sm"
              onClick={onRefresh}
              disabled={loading}>

                <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
                刷新
            </Button>
            }
          </div>

          {/* 筛选和搜索 */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索客户名称、内容或ID..."
                value={searchQuery || "unknown"}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={selectedType || "unknown"} onValueChange={setSelectedType}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="反馈类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(satisfactionConstants.feedbackTypeConfig).map(([key, config]) =>
                <SelectItem key={key} value={key || "unknown"}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={selectedStatus || "unknown"} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="处理状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(satisfactionConstants.feedbackStatusConfig).map(([key, config]) =>
                <SelectItem key={key} value={key || "unknown"}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* 反馈列表 */}
          <div className="space-y-3">
            <AnimatePresence mode="wait">
              {loading ?
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-3">

                  {[1, 2, 3].map((i) =>
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-slate-50 rounded-lg border border-slate-200">

                      <div className="animate-pulse">
                        <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
                        <div className="h-3 bg-slate-200 rounded w-1/2 mb-3" />
                        <div className="flex gap-2">
                          <div className="h-6 bg-slate-200 rounded w-20" />
                          <div className="h-6 bg-slate-200 rounded w-20" />
                        </div>
                      </div>
                </motion.div>
                )}
              </motion.div> :
              paginatedFeedbacks.length > 0 ?
              (paginatedFeedbacks || []).map((feedback, index) =>
              <motion.div
                key={feedback.id || index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ delay: index * 0.05 }}
                className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer"
                onClick={() => handleFeedbackClick(feedback)}>

                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-3 mb-2">
                          <div className="flex-shrink-0">
                            {feedback.customerLevel === "vip" ?
                        <Building className="w-5 h-5 text-purple-400" /> :

                        <User className="w-5 h-5 text-slate-400" />
                        }
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-slate-800 truncate">
                                {feedback.customerName || "匿名客户"}
                              </h4>
                              <Badge
                            variant="outline"
                            className={cn(
                              "text-xs",
                              getPriorityConfig(feedback.priority).color
                            )}>

                                {getPriorityConfig(feedback.priority).label}
                              </Badge>
                            </div>
                            <p className="text-sm text-slate-600 line-clamp-2 mb-2">
                              {feedback.content || "暂无反馈内容"}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {formatDateTime(feedback.createdAt)}
                              </span>
                              <span className="flex items-center gap-1">
                                <Tag className="w-3 h-3" />
                                {getFeedbackTypeConfig(feedback.feedbackType).label}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                          <div className="flex items-center gap-4">
                            {renderRating(feedback.rating)}
                            <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            getFeedbackStatusConfig(feedback.status).color
                          )}>

                              {getFeedbackStatusConfig(feedback.status).label}
                            </Badge>
                          </div>
                          {renderActions(feedback)}
                        </div>
                      </div>
                    </div>
              </motion.div>
              ) :

              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-12">

                  <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">暂无反馈数据</p>
              </motion.div>
              }
            </AnimatePresence>
          </div>

          {/* 分页信息 */}
          {paginatedFeedbacks.length > 0 &&
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
              <div className="text-sm text-slate-600">
                显示 {(currentPage - 1) * pageSize + 1} -{" "}
                {Math.min(currentPage * pageSize, filteredAndSortedFeedbacks.length)}{" "}
                条，共 {filteredAndSortedFeedbacks.length} 条
              </div>
              <div className="flex items-center gap-2">
                <Button
                variant="outline"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}>

                  上一页
                </Button>
                <Button
                variant="outline"
                size="sm"
                disabled={currentPage * pageSize >= filteredAndSortedFeedbacks.length}
                onClick={() => setCurrentPage(currentPage + 1)}>

                  下一页
                </Button>
              </div>
          </div>
          }
        </CardContent>
      </Card>
    </motion.div>);

};
