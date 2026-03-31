import {
  Search,
  Eye,
  Edit,
  XCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../../components/ui/card";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../../components/ui/table";
import { formatDate } from "../../lib/utils";
import {
  COMMUNICATION_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  TOPIC_FILTER_OPTIONS,
} from "../../components/customer-communication";
import { getStatusBadge, getPriorityBadge, getTypeDisplay, getSatisfactionDisplay } from "./displayHelpers";

export default function CommunicationTable({
  loading,
  communications,
  customers,
  searchQuery,
  setSearchQuery,
  filterStatus,
  setFilterStatus,
  filterPriority,
  setFilterPriority,
  filterType,
  setFilterType,
  filterTopic,
  setFilterTopic,
  filterCustomer,
  setFilterCustomer,
  dateFilter,
  setDateFilter,
  onView,
  onEdit,
  onDelete,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>沟通记录列表</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="搜索沟通记录..."
              value={searchQuery || "unknown"}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10" />

          </div>

          <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
            <SelectTrigger>
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              {COMMUNICATION_FILTER_OPTIONS.map((option) =>
              <SelectItem key={option.value} value={option.value}>
                  {option.label}
              </SelectItem>
              )}
            </SelectContent>
          </Select>

          <Select value={filterPriority || "unknown"} onValueChange={setFilterPriority}>
            <SelectTrigger>
              <SelectValue placeholder="优先级" />
            </SelectTrigger>
            <SelectContent>
              {PRIORITY_FILTER_OPTIONS.map((option) =>
              <SelectItem key={option.value} value={option.value}>
                  {option.label}
              </SelectItem>
              )}
            </SelectContent>
          </Select>

          <Select value={filterType || "unknown"} onValueChange={setFilterType}>
            <SelectTrigger>
              <SelectValue placeholder="沟通方式" />
            </SelectTrigger>
            <SelectContent>
              {TYPE_FILTER_OPTIONS.map((option) =>
              <SelectItem key={option.value} value={option.value}>
                  {option.label}
              </SelectItem>
              )}
            </SelectContent>
          </Select>

          <Select value={filterTopic || "unknown"} onValueChange={setFilterTopic}>
            <SelectTrigger>
              <SelectValue placeholder="主题" />
            </SelectTrigger>
            <SelectContent>
              {TOPIC_FILTER_OPTIONS.map((option) =>
              <SelectItem key={option.value} value={option.value}>
                  {option.label}
              </SelectItem>
              )}
            </SelectContent>
          </Select>

          <Select value={filterCustomer || "unknown"} onValueChange={setFilterCustomer}>
            <SelectTrigger>
              <SelectValue placeholder="客户" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">全部客户</SelectItem>
              {(customers || []).map((customer) =>
              <SelectItem key={customer.id} value={customer.id}>
                  {customer.name}
              </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Input
            type="date"
            placeholder="开始日期"
            value={dateFilter.start}
            onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })} />

          <Input
            type="date"
            placeholder="结束日期"
            value={dateFilter.end}
            onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })} />

        </div>

        {/* Communications Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>客户</TableHead>
                <TableHead>主题</TableHead>
                <TableHead>沟通方式</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>满意度</TableHead>
                <TableHead>沟通日期</TableHead>
                <TableHead>负责人</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ?
              <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    加载中...
                  </TableCell>
              </TableRow> :
              communications.length === 0 ?
              <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    暂无沟通记录
                  </TableCell>
              </TableRow> :

              (communications || []).map((comm) =>
              <TableRow key={comm.id}>
                    <TableCell className="font-medium">
                      {comm.customer?.name || "未知客户"}
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs truncate">{comm.subject}</div>
                    </TableCell>
                    <TableCell>{getTypeDisplay(comm.communication_type)}</TableCell>
                    <TableCell>{getPriorityBadge(comm.priority)}</TableCell>
                    <TableCell>{getStatusBadge(comm.status)}</TableCell>
                    <TableCell>{getSatisfactionDisplay(comm.satisfaction_rating)}</TableCell>
                    <TableCell>{formatDate(comm.communication_date)}</TableCell>
                    <TableCell>{comm.assigned_user?.name || "未分配"}</TableCell>
                    <TableCell>
                      <div className="flex space-x-1">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onView(comm)}>

                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(comm)}>

                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(comm.id)}>

                          <XCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
              </TableRow>
              )
              }
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
