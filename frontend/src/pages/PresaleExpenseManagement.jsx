/**
 * Presale Expense Management Page - 售前费用管理
 * Features: 工时费用化处理、费用列表、费用统计
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  DollarSign,
  Clock,
  Users,
  Building2,
  Download,
  Filter,
  Calendar,
  CheckCircle2,
  AlertCircle,
  TrendingDown } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label } from
"../components/ui";
import { fadeIn as _fadeIn, staggerContainer as _staggerContainer } from "../lib/animations";
import { presaleExpenseApi } from "../services/api";
import { formatAmount } from "../lib/utils";

export default function PresaleExpenseManagement() {
  const [loading, setLoading] = useState(false);
  const [expenses, setExpenses] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [salespersonId, setSalespersonId] = useState("");
  const [groupBy, setGroupBy] = useState("person");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showExpenseDialog, setShowExpenseDialog] = useState(false);
  const [expenseRequest, setExpenseRequest] = useState({
    project_ids: null,
    start_date: null,
    end_date: null
  });

  const pageSize = 20;

  const loadExpenses = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}
      if (salespersonId) {params.salesperson_id = parseInt(salespersonId);}

      const response = await presaleExpenseApi.getLostProjectExpenses(params);
      if (response.data && response.data.data) {
        setExpenses(response.data.data.items || []);
        setTotal(response.data.data.total || 0);
      }
    } catch (error) {
      console.error("加载费用列表失败:", error);
      alert("加载费用列表失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const params = { group_by: groupBy };
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}

      const response = await presaleExpenseApi.getExpenseStatistics(params);
      if (response.data && response.data.data) {
        setStatistics(response.data.data);
      }
    } catch (error) {
      console.error("加载统计数据失败:", error);
    }
  };

  useEffect(() => {
    loadExpenses();
    loadStatistics();
  }, [page, startDate, endDate, salespersonId, groupBy]);

  const handleExpenseLostProjects = async () => {
    try {
      setLoading(true);
      const response = await presaleExpenseApi.expenseLostProjects(expenseRequest);
      if (response.data) {
        alert(response.data.message || "费用化成功");
        setShowExpenseDialog(false);
        loadExpenses();
        loadStatistics();
      }
    } catch (error) {
      console.error("费用化失败:", error);
      alert("费用化失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const formatHours = (hours) => {
    if (!hours) {return "0h";}
    return `${parseFloat(hours).toFixed(1)}h`;
  };

  return (
    <div className="space-y-6">
      <PageHeader title="售前费用管理" />

      {/* 操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button onClick={() => setShowExpenseDialog(true)}>
                费用化未中标项目
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                placeholder="开始日期"
                className="w-40" />

              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                placeholder="结束日期"
                className="w-40" />

              <Input
                type="number"
                value={salespersonId}
                onChange={(e) => setSalespersonId(e.target.value)}
                placeholder="销售人员ID"
                className="w-32" />

            </div>
          </div>
        </CardContent>
      </Card>

      {/* 费用化对话框 */}
      <Dialog open={showExpenseDialog} onOpenChange={setShowExpenseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>费用化未中标项目</DialogTitle>
            <DialogDescription>
              将未中标项目的工时转为费用记录
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>项目ID列表（可选，留空则处理所有未中标项目）</Label>
              <Input
                placeholder="例如: 1,2,3"
                onChange={(e) => {
                  const ids = e.target.value.
                  split(",").
                  map((id) => parseInt(id.trim())).
                  filter((id) => !isNaN(id));
                  setExpenseRequest({
                    ...expenseRequest,
                    project_ids: ids.length > 0 ? ids : null
                  });
                }} />

            </div>
            <div>
              <Label>开始日期（可选）</Label>
              <Input
                type="date"
                onChange={(e) =>
                setExpenseRequest({
                  ...expenseRequest,
                  start_date: e.target.value || null
                })
                } />

            </div>
            <div>
              <Label>结束日期（可选）</Label>
              <Input
                type="date"
                onChange={(e) =>
                setExpenseRequest({
                  ...expenseRequest,
                  end_date: e.target.value || null
                })
                } />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExpenseDialog(false)}>
              取消
            </Button>
            <Button onClick={handleExpenseLostProjects} disabled={loading}>
              {loading ? "处理中..." : "确认费用化"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 统计卡片 */}
      {statistics &&
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">总费用记录</p>
                  <p className="text-2xl font-bold mt-1">
                    {statistics.summary?.total_projects || 0}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">总费用金额</p>
                  <p className="text-2xl font-bold mt-1">
                    {formatAmount(statistics.summary?.total_amount || 0)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">总工时</p>
                  <p className="text-2xl font-bold mt-1">
                    {formatHours(statistics.summary?.total_hours || 0)}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
      </div>
      }

      {/* 费用统计 */}
      {statistics && statistics.statistics &&
      <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                费用统计（按{groupBy === "person" ? "人员" : groupBy === "department" ? "部门" : "时间"}）
              </CardTitle>
              <div className="flex items-center gap-2">
                <select
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
                className="px-3 py-1 border rounded">

                  <option value="person">按人员</option>
                  <option value="department">按部门</option>
                  <option value="time">按时间</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  {groupBy === "person" &&
                <>
                      <TableHead>人员</TableHead>
                      <TableHead>部门</TableHead>
                </>
                }
                  {groupBy === "department" &&
                <>
                      <TableHead>部门</TableHead>
                </>
                }
                  {groupBy === "time" &&
                <>
                      <TableHead>月份</TableHead>
                </>
                }
                  <TableHead>项目数</TableHead>
                  <TableHead>总工时</TableHead>
                  <TableHead>总费用</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(statistics.statistics || []).map((stat, index) =>
              <TableRow key={index}>
                    {groupBy === "person" &&
                <>
                        <TableCell>{stat.person_name}</TableCell>
                        <TableCell>{stat.department || "-"}</TableCell>
                </>
                }
                    {groupBy === "department" &&
                <>
                        <TableCell>{stat.department_name}</TableCell>
                </>
                }
                    {groupBy === "time" &&
                <>
                        <TableCell>{stat.month}</TableCell>
                </>
                }
                    <TableCell>{stat.project_count || 0}</TableCell>
                    <TableCell>{formatHours(stat.total_hours)}</TableCell>
                    <TableCell>{formatAmount(stat.total_amount)}</TableCell>
              </TableRow>
              )}
              </TableBody>
            </Table>
          </CardContent>
      </Card>
      }

      {/* 费用列表 */}
      <Card>
        <CardHeader>
          <CardTitle>未中标项目费用列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-500">加载中...</div> :
          expenses.length === 0 ?
          <div className="text-center py-8 text-slate-500">暂无数据</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>项目编号</TableHead>
                  <TableHead>项目名称</TableHead>
                  <TableHead>费用分类</TableHead>
                  <TableHead>工时</TableHead>
                  <TableHead>费用金额</TableHead>
                  <TableHead>销售人员</TableHead>
                  <TableHead>未中标原因</TableHead>
                  <TableHead>费用日期</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(expenses || []).map((expense) =>
              <TableRow key={expense.project_id}>
                    <TableCell>{expense.project_code}</TableCell>
                    <TableCell>{expense.project_name}</TableCell>
                    <TableCell>
                      <Badge
                    variant={
                    expense.expense_category === "LOST_BID" ?
                    "destructive" :
                    "outline"
                    }>

                        {expense.expense_category === "LOST_BID" ? "丢标" : "放弃"}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatHours(expense.labor_hours)}</TableCell>
                    <TableCell>{formatAmount(expense.amount)}</TableCell>
                    <TableCell>{expense.salesperson_name || "-"}</TableCell>
                    <TableCell>{expense.loss_reason || "-"}</TableCell>
                    <TableCell>{expense.expense_date}</TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }

          {/* 分页 */}
          {total > pageSize &&
          <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-slate-500">
                共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
              </div>
              <div className="flex items-center gap-2">
                <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}>

                  上一页
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / pageSize)}>

                  下一页
                </Button>
              </div>
          </div>
          }
        </CardContent>
      </Card>
    </div>);

}