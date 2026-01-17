/**
 * Customer Communication Quick Actions Component
 * 客户沟通快速操作组件
 */
import React, { useState } from "react";
import { motion } from 'framer-motion';
import {
  Plus, Send, MessageSquare, Phone, Mail, Video,
  FileText, Users, Calendar, Clock, AlertCircle,
  CheckCircle, Search, Filter, MoreHorizontal } from
"lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger } from
"../ui/dropdown-menu";
import { cn } from "../../lib/utils";
import {
  typeConfigs,
  priorityConfigs as _priorityConfigs,
  channelConfigs as _channelConfigs,
  formatType as _formatType,
  formatPriority as _formatPriority,
  formatChannel as _formatChannel } from
"./communicationConstants";

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
};

const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

/**
 * 快速创建按钮组
 */
const QuickCreateButtons = ({ onCreate }) => {
  const quickActions = [
  {
    key: 'email',
    icon: <Mail className="w-4 h-4" />,
    label: '邮件沟通',
    type: 'EMAIL',
    defaultType: 'TECHNICAL_DISCUSSION'
  },
  {
    key: 'phone',
    icon: <Phone className="w-4 h-4" />,
    label: '电话沟通',
    type: 'PHONE',
    defaultType: 'TECHNICAL_DISCUSSION'
  },
  {
    key: 'meeting',
    icon: <Users className="w-4 h-4" />,
    label: '安排会议',
    type: 'MEETING',
    defaultType: 'MEETING_INVITATION'
  },
  {
    key: 'message',
    icon: <MessageSquare className="w-4 h-4" />,
    label: '即时消息',
    type: 'WECHAT',
    defaultType: 'TECHNICAL_DISCUSSION'
  },
  {
    key: 'video',
    icon: <Video className="w-4 h-4" />,
    label: '视频会议',
    type: 'VIDEO_CALL',
    defaultType: 'TECHNICAL_PRESENTATION'
  }];


  return (
    <div className="flex flex-wrap gap-2">
      {quickActions.map((action) =>
      <Button
        key={action.key}
        variant="outline"
        size="sm"
        onClick={() => onCreate && onCreate(action.type, action.defaultType)}
        className="h-9">

          {action.icon}
          <span className="ml-2">{action.label}</span>
      </Button>
      )}
    </div>);

};

/**
 * 快速筛选按钮
 */
const QuickFilterButtons = ({ onFilter, activeFilters }) => {
  const filterOptions = [
  {
    key: 'pending',
    label: '待处理',
    count: 5,
    status: ['PENDING_REVIEW', 'PENDING_APPROVAL', 'IN_PROGRESS']
  },
  {
    key: 'high_priority',
    label: '高优先级',
    count: 3,
    priority: ['HIGH', 'URGENT', 'CRITICAL']
  },
  {
    key: 'today',
    label: '今日',
    count: 8,
    dateFilter: 'today'
  },
  {
    key: 'overdue',
    label: '已逾期',
    count: 2,
    status: ['OVERDUE']
  }];


  return (
    <div className="flex flex-wrap gap-2">
      {filterOptions.map((filter) =>
      <Button
        key={filter.key}
        variant={activeFilters?.[filter.key] ? "default" : "ghost"}
        size="sm"
        onClick={() => onFilter && onFilter(filter.key)}
        className={cn(
          "h-9",
          activeFilters?.[filter.key] && filter.key === 'high_priority' && "bg-red-100 text-red-700 border-red-200"
        )}>

          {filter.label}
          {filter.count > 0 &&
        <Badge variant="secondary" className="ml-2 h-5 px-1.5">
              {filter.count}
        </Badge>
        }
      </Button>
      )}
    </div>);

};

/**
 * 批量操作下拉菜单
 */
const BulkActionsMenu = ({ onSelect }) => {
  const actions = [
  { key: 'resend', label: '批量重新发送', icon: <Send className="w-4 h-4" /> },
  { key: 'mark_read', label: '标记为已读', icon: <CheckCircle className="w-4 h-4" /> },
  { key: 'archive', label: '归档选中', icon: <FileText className="w-4 h-4" /> },
  { key: 'export', label: '导出数据', icon: <FileText className="w-4 h-4" /> }];


  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="h-9">
          <MoreHorizontal className="w-4 h-4" />
          批量操作
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {actions.map((action) =>
        <DropdownMenuItem
          key={action.key}
          onClick={() => onSelect && onSelect(action.key)}>

            {action.icon}
            <span className="ml-2">{action.label}</span>
        </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>);

};

/**
 * 客户沟通快速操作组件
 */
export const QuickActions = ({
  onCreate,
  onFilter,
  onSelect,
  onSearch,
  activeFilters,
  searchQuery,
  showCreateForm = false,
  showFilters = true
}) => {
  const [localSearch, setLocalSearch] = useState(searchQuery || "");

  const handleSearch = () => {
    onSearch(localSearch);
  };

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-4">

      {/* 主操作卡片 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              快速操作
            </span>
            <BulkActionsMenu onSelect={onSelect} />
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 创建操作 */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium mb-1">创建沟通</div>
                <div className="text-xs text-slate-500">快速创建新的客户沟通记录</div>
              </div>
              <div className="flex items-center gap-2">
                {showCreateForm &&
                <div className="flex items-center gap-1">
                    <Button variant="default" size="sm" onClick={() => onCreate && onCreate()}>
                      <Plus className="w-4 h-4 mr-1" />
                      新建沟通
                    </Button>
                    <QuickCreateButtons onCreate={onCreate} />
                </div>
                }
              </div>
            </div>

            {/* 筛选操作 */}
            {showFilters &&
            <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium mb-1">快速筛选</div>
                  <div className="text-xs text-slate-500">按状态、优先级或时间快速筛选</div>
                </div>
                <QuickFilterButtons
                onFilter={onFilter}
                activeFilters={activeFilters} />

            </div>
            }

            {/* 搜索操作 */}
            <div className="flex items-center gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="搜索客户、沟通内容或主题..."
                  value={localSearch}
                  onChange={(e) => setLocalSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSearch();
                  }} />

              </div>
              <Button variant="outline" size="sm" onClick={handleSearch}>
                搜索
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 统计信息卡片 */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">12</div>
              <div className="text-xs text-slate-500">待处理</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">3</div>
              <div className="text-xs text-slate-500">高优先级</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">2</div>
              <div className="text-xs text-slate-500">已逾期</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">85%</div>
              <div className="text-xs text-slate-500">响应率</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 常用沟通类型 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">常用沟通类型</CardTitle>
        </CardHeader>
        <CardContent>
          <motion.div
            variants={stagger}
            animate="animate"
            className="grid grid-cols-2 md:grid-cols-4 gap-2">

            {Object.entries(typeConfigs).slice(0, 8).map(([key, config]) =>
            <Button
              key={key}
              variant="outline"
              size="sm"
              className="h-10 justify-start"
              onClick={() => onCreate && onCreate('SYSTEM', key)}>

                <span className="mr-2">{config.icon}</span>
                <span className="text-sm">{config.label}</span>
            </Button>
            )}
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>);

};

export default QuickActions;