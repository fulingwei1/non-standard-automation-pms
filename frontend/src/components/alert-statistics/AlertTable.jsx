/**
 * Alert Table Component - 告警列表表格组件
 * 用于展示告警的详细信息列表
 */

import React, { useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  Download,
  Eye,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  RefreshCw
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import {
  ALERT_LEVEL_STATS,
  ALERT_STATUS_STATS,
  ALERT_TYPE_STATS,
  formatStatValue
} from "./alertStatsConstants";

export function AlertTable({
  data,
  height = 500,
  showActions = true,
  showFilters = true,
  showPagination = true,
  className = ""
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState("created_at");
  const [sortDirection, setSortDirection] = useState("desc");
  const [statusFilter, setStatusFilter] = useState("all");
  const [levelFilter, setLevelFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // 过滤和排序数据
  const filteredAndSortedData = useMemo(() => {
    let filtered = data || [];

    // 应用搜索过滤
    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.alert_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.project_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // 应用状态过滤
    if (statusFilter !== "all") {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    // 应用级别过滤
    if (levelFilter !== "all") {
      filtered = filtered.filter(alert => alert.alert_level === levelFilter);
    }

    // 应用类型过滤
    if (typeFilter !== "all") {
      filtered = filtered.filter(alert => alert.alert_type === typeFilter);
    }

    // 排序
    filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // 处理日期字段
      if (sortField.includes('_at') || sortField.includes('_time')) {
        aValue = new Date(aValue || 0).getTime();
        bValue = new Date(bValue || 0).getTime();
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [data, searchTerm, sortField, sortDirection, statusFilter, levelFilter, typeFilter]);

  // 分页数据
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredAndSortedData.slice(startIndex, endIndex);
  }, [filteredAndSortedData, currentPage, itemsPerPage]);

  // 总页数
  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);

  // 处理排序
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  // 获取排序图标
  const getSortIcon = (field) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="h-4 w-4 ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 ml-1" />
    );
  };

  // 获取状态徽章
  const getStatusBadge = (status) => {
    const config = ALERT_STATUS_STATS[status] || ALERT_STATUS_STATS.PENDING;
    return (
      <Badge variant="secondary" className={config.color}>
        {config.label}
      </Badge>
    );
  };

  // 获取级别徽章
  const getLevelBadge = (level) => {
    const config = ALERT_LEVEL_STATS[level] || ALERT_LEVEL_STATS.INFO;
    return (
      <Badge variant="secondary" className={config.color}>
        {config.label}
      </Badge>
    );
  };

  // 获取类型信息
  const getTypeInfo = (type, subtype) => {
    const typeConfig = ALERT_TYPE_STATS[type] || ALERT_TYPE_STATS.SYSTEM;
    const subtypeConfig = typeConfig.subtypes[subtype] || { label: subtype || '其他' };

    return (
      <div className="flex items-center gap-2">
        <span className="text-lg">{typeConfig.icon}</span>
        <span className="text-sm text-gray-600">{subtypeConfig.label}</span>
      </div>
    );
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) return '刚刚';
    if (diffMinutes < 60) return `${diffMinutes}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString();
  };

  // 渲染操作列
  const renderActions = (alert) => {
    if (!showActions) return null;

    return (
      <div className="flex items-center gap-2">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
              >
                <Eye className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>查看详情</TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>处理告警</DropdownMenuItem>
            <DropdownMenuItem>分配责任人</DropdownMenuItem>
            <DropdownMenuItem>升级告警</DropdownMenuItem>
            <DropdownMenuItem>标记为已解决</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  };

  // 无数据时的显示
  if (!data || data.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg mb-2">暂无告警数据</p>
            <p className="text-sm">请检查数据源或调整筛选条件</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <CardTitle className="text-lg font-semibold">告警列表</CardTitle>

          <div className="flex flex-col space-y-2 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-2">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索告警..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-64"
              />
            </div>

            {/* 过滤器 */}
            {showFilters && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    筛选
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <div className="p-2 space-y-2">
                    <div>
                      <label className="text-sm font-medium">状态</label>
                      <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="w-full mt-1 text-sm border rounded p-1"
                      >
                        <option value="all">全部</option>
                        {Object.entries(ALERT_STATUS_STATS).map(([key, config]) => (
                          <option key={key} value={key}>{config.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">级别</label>
                      <select
                        value={levelFilter}
                        onChange={(e) => setLevelFilter(e.target.value)}
                        className="w-full mt-1 text-sm border rounded p-1"
                      >
                        <option value="all">全部</option>
                        {Object.entries(ALERT_LEVEL_STATS).map(([key, config]) => (
                          <option key={key} value={key}>{config.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">类型</label>
                      <select
                        value={typeFilter}
                        onChange={(e) => setTypeFilter(e.target.value)}
                        className="w-full mt-1 text-sm border rounded p-1"
                      >
                        <option value="all">全部</option>
                        {Object.entries(ALERT_TYPE_STATS).map(([key, config]) => (
                          <option key={key} value={key}>{config.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {/* 导出按钮 */}
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* 表格 */}
        <div className="rounded-md border overflow-hidden">
          <div className="overflow-x-auto">
            <Table style={{ height }}>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("alert_no")}
                  >
                    <div className="flex items-center">
                      编号
                      {getSortIcon("alert_no")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("title")}
                  >
                    <div className="flex items-center">
                      标题
                      {getSortIcon("title")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("alert_level")}
                  >
                    <div className="flex items-center">
                      级别
                      {getSortIcon("alert_level")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("alert_type")}
                  >
                    <div className="flex items-center">
                      类型
                      {getSortIcon("alert_type")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("status")}
                  >
                    <div className="flex items-center">
                      状态
                      {getSortIcon("status")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("project_name")}
                  >
                    <div className="flex items-center">
                      项目
                      {getSortIcon("project_name")}
                    </div>
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSort("created_at")}
                  >
                    <div className="flex items-center">
                      创建时间
                      {getSortIcon("created_at")}
                    </div>
                  </TableHead>
                  {showActions && (
                    <TableHead className="w-24 text-center">操作</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedData.map((alert) => (
                  <TableRow key={alert.id || alert.alert_no}>
                    <TableCell className="font-medium text-sm">
                      {alert.alert_no}
                    </TableCell>
                    <TableCell className="max-w-[200px]">
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-400" />
                        <span className="text-sm truncate">
                          {alert.title || '无标题'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            {getLevelBadge(alert.alert_level)}
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-xs">
                              <p>级别: {alert.alert_level}</p>
                              <p>目标响应时间: {
                                ALERT_LEVEL_STATS[alert.alert_level]?.targetResponseTime || '未设置'
                              }分钟</p>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                    <TableCell>
                      {getTypeInfo(alert.alert_type, alert.alert_subtype)}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(alert.status)}
                    </TableCell>
                    <TableCell className="text-sm text-gray-600">
                      {alert.project_name || '-'}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatTime(alert.created_at)}
                    </TableCell>
                    {showActions && (
                      <TableCell className="text-center">
                        {renderActions(alert)}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* 分页 */}
          {showPagination && totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t">
              <div className="text-sm text-gray-600">
                显示 {(currentPage - 1) * itemsPerPage + 1} -{' '}
                {Math.min(currentPage * itemsPerPage, filteredAndSortedData.length)}{' '}
                条，共 {filteredAndSortedData.length} 条
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  上一页
                </Button>
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let page;
                    if (totalPages <= 5) {
                      page = i + 1;
                    } else if (currentPage <= 3) {
                      page = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      page = totalPages - 4 + i;
                    } else {
                      page = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={page}
                        variant={currentPage === page ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCurrentPage(page)}
                        className="h-8 w-8"
                      >
                        {page}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}