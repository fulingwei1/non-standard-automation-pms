/**
 * Customer Communication Message List Component
 * 客户沟通消息列表组件
 */
import React, { useState } from "react";
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import {
  Search, Filter, Send, CheckCircle, Circle,
  MessageSquare, FileText, AlertCircle, Clock } from
"lucide-react";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import { cn } from "../../lib/utils";
import {
  statusConfigs,
  typeConfigs,
  priorityConfigs,
  channelConfigs as _channelConfigs,
  getStatusConfig as _getStatusConfig,
  getTypeConfig as _getTypeConfig,
  getPriorityConfig,
  getChannelConfig,
  formatStatus,
  formatType,
  formatPriority,
  formatChannel,
  sortByCreatedTime } from
"@/lib/constants/customer";

/**
 * 消息列表组件
 */
export const MessageList = ({
  messages = [],
  loading = false,
  selectedMessageId,
  onSelectMessage,
  onSendMessage,
  onFilterChange,
  searchTerm,
  filters
}) => {
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm || "");
  const [localFilters, setLocalFilters] = useState(filters || {});

  // 处理搜索
  const handleSearch = () => {
    onFilterChange(localSearchTerm, localFilters);
  };

  // 处理筛选
  const handleFilterChange = (key, value) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFilterChange(localSearchTerm, newFilters);
  };

  // 清除筛选
  const handleClearFilters = () => {
    setLocalSearchTerm("");
    setLocalFilters({});
    onFilterChange("", {});
  };

  // 获取优先级图标
  const getPriorityIcon = (priority) => {
    const _config = getPriorityConfig(priority);
    switch (priority) {
      case "CRITICAL":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "URGENT":
        return <Clock className="w-4 h-4 text-orange-500" />;
      default:
        return <Circle className="w-4 h-4 text-slate-400" />;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status) => {
    switch (status) {
      case "COMPLETED":
      case "CLOSED":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "FAILED":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-amber-500" />;
    }
  };

  // 获取渠道图标
  const getChannelIcon = (channel) => {
    const _config = getChannelConfig(channel);
    const iconMap = {
      EMAIL: <MessageSquare className="w-4 h-4" />,
      PHONE: <MessageSquare className="w-4 h-4" />,
      WECHAT: <MessageSquare className="w-4 h-4" />,
      MEETING: <MessageSquare className="w-4 h-4" />,
      SYSTEM: <MessageSquare className="w-4 h-4" />
    };
    return iconMap[channel] || <MessageSquare className="w-4 h-4" />;
  };

  // 排序消息
  const sortedMessages = [...messages].sort(sortByCreatedTime);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        <span className="ml-2 text-slate-600 dark:text-slate-400">加载中...</span>
      </div>);

  }

  return (
    <div className="space-y-6">
      {/* 搜索和筛选区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">消息列表</CardTitle>
        </CardHeader>
        <CardContent>
          {/* 搜索栏 */}
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索消息标题、内容或联系人..."
                value={localSearchTerm}
                onChange={(e) => setLocalSearchTerm(e.target.value)}
                className="pl-9" />

            </div>
            <Button variant="outline" onClick={handleSearch}>
              搜索
            </Button>
            <Button variant="outline" onClick={handleClearFilters}>
              清除
            </Button>
          </div>

          {/* 筛选条件 */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">状态:</span>
              {Object.entries(statusConfigs).map(([key, config]) =>
              <Button
                key={key}
                variant={localFilters.status === key ? "default" : "ghost"}
                size="sm"
                onClick={() => handleFilterChange("status", key)}
                className={cn(
                  "h-6 px-2",
                  config.color,
                  config.textColor,
                  localFilters.status === key && "ring-2 ring-offset-2"
                )}>

                  {config.label}
              </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">类型:</span>
              {Object.entries(typeConfigs).slice(0, 5).map(([key, config]) =>
              <Button
                key={key}
                variant={localFilters.type === key ? "default" : "ghost"}
                size="sm"
                onClick={() => handleFilterChange("type", key)}
                className={cn(
                  "h-6 px-2",
                  config.color,
                  config.textColor,
                  localFilters.type === key && "ring-2 ring-offset-2"
                )}>

                  {config.label}
              </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">优先级:</span>
              {Object.entries(priorityConfigs).slice(0, 4).map(([key, config]) =>
              <Button
                key={key}
                variant={localFilters.priority === key ? "default" : "ghost"}
                size="sm"
                onClick={() => handleFilterChange("priority", key)}
                className={cn(
                  "h-6 px-2",
                  config.color,
                  config.textColor,
                  localFilters.priority === key && "ring-2 ring-offset-2"
                )}>

                  {config.label}
              </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 消息表格 */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50 dark:bg-slate-900/50">
                <TableHead className="w-12" />
                <TableHead>消息</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>渠道</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>收件人</TableHead>
                <TableHead>发送时间</TableHead>
                <TableHead className="text-center">状态</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {(sortedMessages || []).map((message) =>
              <TableRow
                key={message.id}
                className={cn(
                  "cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50",
                  selectedMessageId === message.id && "bg-blue-50 dark:bg-blue-900/20"
                )}
                onClick={() => onSelectMessage && onSelectMessage(message)}>

                  {/* 选中状态 */}
                  <TableCell>
                    {selectedMessageId === message.id &&
                  <CheckCircle className="w-4 h-4 text-blue-500" />
                  }
                  </TableCell>

                  {/* 消息预览 */}
                  <TableCell className="max-w-xs">
                    <div className="flex items-start gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={message.avatar_url} alt={message.contact_name} />
                        <AvatarFallback>
                          {message.contact_name?.charAt(0) || "客"}
                        </AvatarFallback>
                      </Avatar>
                      <div className="min-w-0">
                        <div className="font-medium truncate" title={message.title}>
                          {message.title}
                        </div>
                        <div className="text-sm text-slate-500 dark:text-slate-400 truncate">
                          {message.preview_text}
                        </div>
                      </div>
                    </div>
                  </TableCell>

                  {/* 类型 */}
                  <TableCell>
                    <Badge
                    variant="secondary"
                    className={cn(
                      typeConfigs[message.communication_type]?.color,
                      typeConfigs[message.communication_type]?.textColor || "text-white"
                    )}>

                      {formatType(message.communication_type)}
                    </Badge>
                  </TableCell>

                  {/* 渠道 */}
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getChannelIcon(message.channel)}
                      <span className="text-sm">
                        {formatChannel(message.channel)}
                      </span>
                    </div>
                  </TableCell>

                  {/* 优先级 */}
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getPriorityIcon(message.priority)}
                      <span className="text-sm">
                        {formatPriority(message.priority)}
                      </span>
                    </div>
                  </TableCell>

                  {/* 收件人 */}
                  <TableCell>
                    <div className="text-sm">
                      {message.contact_name || "未知联系人"}
                    </div>
                    {message.contact_company &&
                  <div className="text-xs text-slate-500">
                        {message.contact_company}
                  </div>
                  }
                  </TableCell>

                  {/* 发送时间 */}
                  <TableCell className="text-sm text-slate-600 dark:text-slate-400">
                    {format(new Date(message.created_at || message.createdAt), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                  </TableCell>

                  {/* 状态 */}
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      {getStatusIcon(message.status)}
                      <Badge
                      variant="outline"
                      className={cn(
                        (statusConfigs[message.status]?.color || "bg-slate-500").replace("bg-", "border-"),
                        (statusConfigs[message.status]?.color || "bg-slate-500").replace("bg-", "text-"),
                        "border-2"
                      )}>

                        {formatStatus(message.status)}
                      </Badge>
                    </div>
                  </TableCell>

                  {/* 操作 */}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      {message.status !== "FAILED" && onSendMessage &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSendMessage(message);
                      }}
                      className="h-8 w-8 p-0"
                      title="重新发送">

                          <Send className="w-4 h-4" />
                    </Button>
                    }

                      {message.status === "FAILED" &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSendMessage(message);
                      }}
                      className="h-8 w-8 p-0"
                      title="重新发送">

                          <AlertCircle className="w-4 h-4 text-red-500" />
                    </Button>
                    }
                    </div>
                  </TableCell>
              </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 空状态 */}
      {sortedMessages.length === 0 &&
      <Card>
          <CardContent className="py-12 text-center">
            <MessageSquare className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 mb-2">暂无消息记录</p>
            <p className="text-sm text-slate-400">
              {searchTerm ? "请尝试调整搜索条件" : "开始创建新的客户沟通消息"}
            </p>
          </CardContent>
      </Card>
      }
    </div>);

};

export default MessageList;