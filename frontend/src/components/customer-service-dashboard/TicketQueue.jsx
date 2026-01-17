/**
 * Ticket Queue Component
 * 服务工单队列组件
 */
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../ui/table";
import {
  Search,
  Filter,
  Clock,
  User,
  Phone,
  Mail,
  MessageSquare,
  Building2,
  CheckCircle2,
  AlertTriangle,
  ChevronUp,
  ChevronDown,
  ArrowUpDown,
  RefreshCw,
  Eye,
  Edit,
  Trash2 } from
"lucide-react";
import {
  servicePriorityConfigs,
  serviceStatusConfigs,
  serviceTypeConfigs,
  serviceChannelConfigs as _serviceChannelConfigs,
  filterTicketsByStatus,
  filterTicketsByPriority,
  filterTicketsByType,
  filterTicketsByCustomer as _filterTicketsByCustomer,
  sortByPriority,
  sortByCreateTime } from
"./customerServiceConstants";

export function TicketQueue({
  tickets = [],
  onTicketClick,
  onTicketAssign,
  onTicketUpdate: _onTicketUpdate,
  onTicketDelete,
  className = ""
}) {
  const [filteredTickets, setFilteredTickets] = useState(tickets);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortConfig, setSortConfig] = useState({
    key: "createTime",
    direction: "desc"
  });
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 应用筛选和排序
  useEffect(() => {
    let filtered = [...tickets];

    // 搜索筛选
    if (searchTerm) {
      filtered = filteredTickets.filter((ticket) =>
      ticket.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.ticketId?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // 状态筛选
    if (statusFilter !== "all") {
      filtered = filterTicketsByStatus(filtered, statusFilter);
    }

    // 优先级筛选
    if (priorityFilter !== "all") {
      filtered = filterTicketsByPriority(filtered, priorityFilter);
    }

    // 类型筛选
    if (typeFilter !== "all") {
      filtered = filterTicketsByType(filtered, typeFilter);
    }

    // 排序
    if (sortConfig.key === "priority") {
      filtered = sortByPriority(filtered);
      if (sortConfig.direction === "desc") {
        filtered.reverse();
      }
    } else if (sortConfig.key === "createTime") {
      filtered = sortByCreateTime(filtered);
    }

    setFilteredTickets(filtered);
  }, [tickets, searchTerm, statusFilter, priorityFilter, typeFilter, sortConfig]);

  // 分页计算
  const totalPages = Math.ceil(filteredTickets.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedTickets = filteredTickets.slice(
    startIndex,
    startIndex + itemsPerPage
  );

  // 处理排序
  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  // 获取排序图标
  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return <ArrowUpDown className="w-4 h-4" />;
    return sortConfig.direction === "asc" ?
    <ChevronUp className="w-4 h-4" /> :
    <ChevronDown className="w-4 h-4" />;
  };

  // 获取状态配置
  const getStatusConfig = (status) => {
    return serviceStatusConfigs[status] || serviceStatusConfigs.NEW;
  };

  // 获取优先级配置
  const getPriorityConfig = (priority) => {
    return servicePriorityConfigs[priority] || servicePriorityConfigs.MEDIUM;
  };

  // 获取类型配置
  const getTypeConfig = (type) => {
    return serviceTypeConfigs[type] || serviceTypeConfigs.OTHER;
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-slate-600" />
            服务工单队列
            <Badge variant="outline">
              {filteredTickets.length} 个工单
            </Badge>
          </CardTitle>
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>

        {/* 筛选区域 */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索工单标题、描述、客户..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10" />

            </div>
          </div>
          <div className="flex gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有状态</SelectItem>
                {Object.entries(serviceStatusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有优先级</SelectItem>
                {Object.entries(servicePriorityConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有类型</SelectItem>
                {Object.entries(serviceTypeConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="w-[120px] cursor-pointer"
                  onClick={() => handleSort("priority")}>

                  <div className="flex items-center gap-1">
                    优先级 {getSortIcon("priority")}
                  </div>
                </TableHead>
                <TableHead>工单标题</TableHead>
                <TableHead className="w-[120px]">客户</TableHead>
                <TableHead className="w-[100px]">状态</TableHead>
                <TableHead className="w-[100px]">类型</TableHead>
                <TableHead
                  className="w-[120px] cursor-pointer"
                  onClick={() => handleSort("createTime")}>

                  <div className="flex items-center gap-1">
                    创建时间 {getSortIcon("createTime")}
                  </div>
                </TableHead>
                <TableHead className="w-[100px]">负责人</TableHead>
                <TableHead className="w-[80px] text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedTickets.map((ticket) => {
                const statusConfig = getStatusConfig(ticket.status);
                const priorityConfig = getPriorityConfig(ticket.priority);
                const typeConfig = getTypeConfig(ticket.type);

                return (
                  <TableRow
                    key={ticket.id}
                    className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                    onClick={() => onTicketClick?.(ticket)}>

                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge
                          className={`${priorityConfig.bg} ${priorityConfig.textColor} border-0 px-2 py-1`}>

                          {priorityConfig.icon}
                        </Badge>
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {priorityConfig.label}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="min-w-0">
                        <div className="font-medium text-sm text-slate-900 dark:text-slate-100 truncate">
                          {ticket.title}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 truncate mt-1">
                          {ticket.description}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-600 dark:text-slate-400 truncate max-w-[100px]">
                          {ticket.customerName}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={`${statusConfig.color} ${statusConfig.textColor} border-0 px-2 py-1`}>

                        {statusConfig.icon} {statusConfig.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <span className="text-lg">{typeConfig.icon}</span>
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {typeConfig.label}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {new Date(ticket.createTime).toLocaleDateString()}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {ticket.assignee ?
                      <div className="flex items-center gap-2">
                          <div className="w-6 h-6 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center">
                            <User className="w-3 h-3 text-slate-600 dark:text-slate-400" />
                          </div>
                          <span className="text-sm text-slate-600 dark:text-slate-400 truncate">
                            {ticket.assignee}
                          </span>
                      </div> :

                      <Badge variant="outline" className="text-xs">
                          未分配
                      </Badge>
                      }
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onTicketClick?.(ticket);
                          }}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        {onTicketAssign &&
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onTicketAssign(ticket);
                          }}>

                            <Edit className="w-4 h-4" />
                        </Button>
                        }
                        {onTicketDelete &&
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onTicketDelete(ticket);
                          }}>

                            <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                        }
                      </div>
                    </TableCell>
                  </TableRow>);

              })}
            </TableBody>
          </Table>
        </div>

        {/* 分页 */}
        {totalPages > 1 &&
        <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-slate-500 dark:text-slate-400">
              显示 {startIndex + 1}-{Math.min(startIndex + itemsPerPage, filteredTickets.length)} 条，
              共 {filteredTickets.length} 条
            </div>
            <div className="flex gap-2">
              <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}>

                上一页
              </Button>
              <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}>

                下一页
              </Button>
            </div>
        </div>
        }

        {filteredTickets.length === 0 &&
        <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400">
              没有找到符合条件的工单
            </p>
        </div>
        }
      </CardContent>
    </Card>);

}