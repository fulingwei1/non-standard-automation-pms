import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  FileText,
  Calendar,
  AlertCircle,
  Plus } from
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import { Label } from "../components/ui/label";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import { hrManagementApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";

export default function HRManagement() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [expiringContracts, setExpiringContracts] = useState(null);

  // 对话框状态
  const [transactionDialogOpen, setTransactionDialogOpen] = useState(false);
  const [contractDialogOpen, setContractDialogOpen] = useState(false);
  const [_selectedTransaction, setSelectedTransaction] = useState(null);
  const [_selectedContract, setSelectedContract] = useState(null);

  // 表单数据
  const [transactionForm, setTransactionForm] = useState({
    employee_id: "",
    transaction_type: "onboarding",
    transaction_date: new Date().toISOString().split("T")[0]
  });
  const [contractForm, setContractForm] = useState({
    employee_id: "",
    contract_type: "fixed_term",
    start_date: new Date().toISOString().split("T")[0],
    duration_months: 36
  });

  useEffect(() => {
    loadDashboard();
    loadTransactions();
    loadContracts();
    loadExpiringContracts();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await hrManagementApi.dashboard.getOverview();
      const data = response.data?.data || response.data || response;
      setDashboardData(data);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    }
  };

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const response = await hrManagementApi.transactions.list({
        page: 1,
        page_size: 10
      });
      const data = response.data?.data || response.data || response;
      setTransactions(data.items || []);
    } catch (err) {
      console.error("Failed to load transactions:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadContracts = async () => {
    try {
      const response = await hrManagementApi.contracts.list({
        page: 1,
        page_size: 10
      });
      const data = response.data?.data || response.data || response;
      setContracts(data.items || []);
    } catch (err) {
      console.error("Failed to load contracts:", err);
    }
  };

  const loadExpiringContracts = async () => {
    try {
      const response = await hrManagementApi.contracts.getExpiring(60);
      const data = response.data?.data || response.data || response;
      setExpiringContracts(data);
    } catch (err) {
      console.error("Failed to load expiring contracts:", err);
    }
  };

  const handleCreateTransaction = () => {
    setSelectedTransaction(null);
    setTransactionForm({
      employee_id: "",
      transaction_type: "onboarding",
      transaction_date: new Date().toISOString().split("T")[0]
    });
    setTransactionDialogOpen(true);
  };

  const handleSaveTransaction = async () => {
    try {
      setLoading(true);
      setError(null);
      await hrManagementApi.transactions.create(transactionForm);
      setTransactionDialogOpen(false);
      loadTransactions();
      loadDashboard();
    } catch (err) {
      console.error("Failed to create transaction:", err);
      setError(err.response?.data?.detail || err.message || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveTransaction = async (id) => {
    try {
      setLoading(true);
      await hrManagementApi.transactions.approve(id, "");
      loadTransactions();
      loadDashboard();
    } catch (err) {
      console.error("Failed to approve transaction:", err);
      setError(err.response?.data?.detail || err.message || "审批失败");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateContract = () => {
    setSelectedContract(null);
    setContractForm({
      employee_id: "",
      contract_type: "fixed_term",
      start_date: new Date().toISOString().split("T")[0],
      duration_months: 36
    });
    setContractDialogOpen(true);
  };

  const handleSaveContract = async () => {
    try {
      setLoading(true);
      setError(null);
      await hrManagementApi.contracts.create(contractForm);
      setContractDialogOpen(false);
      loadContracts();
      loadExpiringContracts();
    } catch (err) {
      console.error("Failed to create contract:", err);
      setError(err.response?.data?.detail || err.message || "创建失败");
    } finally {
      setLoading(false);
    }
  };

  const getTransactionTypeLabel = (type) => {
    const labels = {
      onboarding: "入职",
      resignation: "离职",
      confirmation: "转正",
      transfer: "调岗",
      promotion: "晋升",
      salary_adjustment: "调薪"
    };
    return labels[type] || type;
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6">

      <PageHeader title="人事管理" />

      {/* 仪表板概览 */}
      {dashboardData &&
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">在职员工</p>
                  <p className="text-2xl font-bold">
                    {dashboardData.total_active || 0}
                  </p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">试用期员工</p>
                  <p className="text-2xl font-bold">
                    {dashboardData.probation_count || 0}
                  </p>
                </div>
                <Calendar className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">待处理事务</p>
                  <p className="text-2xl font-bold">
                    {dashboardData.pending_transactions || 0}
                  </p>
                </div>
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">即将到期合同</p>
                  <p className="text-2xl font-bold">
                    {dashboardData.expiring_contracts_60days || 0}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>
      </div>
      }

      <Tabs defaultValue="transactions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="transactions">人事事务</TabsTrigger>
          <TabsTrigger value="contracts">合同管理</TabsTrigger>
          <TabsTrigger value="expiring">到期提醒</TabsTrigger>
        </TabsList>

        {/* 人事事务 */}
        <TabsContent value="transactions">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>人事事务列表</CardTitle>
              <Button onClick={handleCreateTransaction}>
                <Plus className="h-4 w-4 mr-2" />
                新建事务
              </Button>
            </CardHeader>
            <CardContent>
              {error &&
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
                  {error}
              </div>
              }
              {loading ?
              <div className="text-center py-8">加载中...</div> :
              transactions.length === 0 ?
              <div className="text-center py-8 text-gray-500">暂无事务</div> :

              <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">员工</th>
                        <th className="text-left p-2">事务类型</th>
                        <th className="text-left p-2">事务日期</th>
                        <th className="text-left p-2">状态</th>
                        <th className="text-left p-2">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((t) =>
                    <tr key={t.id} className="border-b hover:bg-gray-50">
                          <td className="p-2">
                            {t.employee_name || t.employee_code}
                          </td>
                          <td className="p-2">
                            <Badge variant="outline">
                              {getTransactionTypeLabel(t.transaction_type)}
                            </Badge>
                          </td>
                          <td className="p-2">
                            {t.transaction_date ?
                        formatDate(t.transaction_date) :
                        "-"}
                          </td>
                          <td className="p-2">
                            <Badge
                          variant={
                          t.status === "pending" ?
                          "secondary" :
                          t.status === "approved" ?
                          "default" :
                          "outline"
                          }>

                              {t.status === "pending" ?
                          "待审批" :
                          t.status === "approved" ?
                          "已审批" :
                          t.status}
                            </Badge>
                          </td>
                          <td className="p-2">
                            {t.status === "pending" &&
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleApproveTransaction(t.id)}>

                                审批
                        </Button>
                        }
                          </td>
                    </tr>
                    )}
                    </tbody>
                  </table>
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 合同管理 */}
        <TabsContent value="contracts">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>合同列表</CardTitle>
              <Button onClick={handleCreateContract}>
                <Plus className="h-4 w-4 mr-2" />
                新建合同
              </Button>
            </CardHeader>
            <CardContent>
              {contracts.length === 0 ?
              <div className="text-center py-8 text-gray-500">暂无合同</div> :

              <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">员工</th>
                        <th className="text-left p-2">合同编号</th>
                        <th className="text-left p-2">开始日期</th>
                        <th className="text-left p-2">结束日期</th>
                        <th className="text-left p-2">状态</th>
                        <th className="text-left p-2">到期天数</th>
                      </tr>
                    </thead>
                    <tbody>
                      {contracts.map((c) =>
                    <tr key={c.id} className="border-b hover:bg-gray-50">
                          <td className="p-2">
                            {c.employee_name || c.employee_code}
                          </td>
                          <td className="p-2">{c.contract_no}</td>
                          <td className="p-2">
                            {c.start_date ? formatDate(c.start_date) : "-"}
                          </td>
                          <td className="p-2">
                            {c.end_date ? formatDate(c.end_date) : "-"}
                          </td>
                          <td className="p-2">
                            <Badge
                          variant={
                          c.status === "active" ? "default" : "secondary"
                          }>

                              {c.status === "active" ? "有效" : c.status}
                            </Badge>
                          </td>
                          <td className="p-2">
                            {c.days_until_expiry !== null &&
                        c.days_until_expiry !== undefined &&
                        <span
                          className={
                          c.days_until_expiry <= 30 ?
                          "text-red-600 font-semibold" :
                          ""
                          }>

                                  {c.days_until_expiry} 天
                        </span>
                        }
                          </td>
                    </tr>
                    )}
                    </tbody>
                  </table>
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 到期提醒 */}
        <TabsContent value="expiring">
          {expiringContracts &&
          <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>两周内到期</CardTitle>
                </CardHeader>
                <CardContent>
                  {expiringContracts.two_weeks?.length === 0 ?
                <div className="text-center py-4 text-gray-500">无</div> :

                <div className="space-y-2">
                      {expiringContracts.two_weeks?.map((c) =>
                  <div
                    key={c.id}
                    className="p-3 bg-red-50 border border-red-200 rounded">

                          <div className="font-semibold">{c.employee_name}</div>
                          <div className="text-sm text-gray-600">
                            {c.contract_no} - 还有 {c.days_until_expiry} 天到期
                          </div>
                  </div>
                  )}
                </div>
                }
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>一个月内到期</CardTitle>
                </CardHeader>
                <CardContent>
                  {expiringContracts.one_month?.length === 0 ?
                <div className="text-center py-4 text-gray-500">无</div> :

                <div className="space-y-2">
                      {expiringContracts.one_month?.map((c) =>
                  <div
                    key={c.id}
                    className="p-3 bg-yellow-50 border border-yellow-200 rounded">

                          <div className="font-semibold">{c.employee_name}</div>
                          <div className="text-sm text-gray-600">
                            {c.contract_no} - 还有 {c.days_until_expiry} 天到期
                          </div>
                  </div>
                  )}
                </div>
                }
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>
      </Tabs>

      {/* 创建人事事务对话框 */}
      <Dialog
        open={transactionDialogOpen}
        onOpenChange={setTransactionDialogOpen}>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建人事事务</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>员工ID *</Label>
              <Input
                type="number"
                value={transactionForm.employee_id}
                onChange={(e) =>
                setTransactionForm({
                  ...transactionForm,
                  employee_id: e.target.value
                })
                } />

            </div>
            <div>
              <Label>事务类型 *</Label>
              <Select
                value={transactionForm.transaction_type}
                onValueChange={(value) =>
                setTransactionForm({
                  ...transactionForm,
                  transaction_type: value
                })
                }>

                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="onboarding">入职</SelectItem>
                  <SelectItem value="resignation">离职</SelectItem>
                  <SelectItem value="confirmation">转正</SelectItem>
                  <SelectItem value="transfer">调岗</SelectItem>
                  <SelectItem value="promotion">晋升</SelectItem>
                  <SelectItem value="salary_adjustment">调薪</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>事务日期 *</Label>
              <Input
                type="date"
                value={transactionForm.transaction_date}
                onChange={(e) =>
                setTransactionForm({
                  ...transactionForm,
                  transaction_date: e.target.value
                })
                } />

            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTransactionDialogOpen(false)}>

              取消
            </Button>
            <Button onClick={handleSaveTransaction} disabled={loading}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建合同对话框 */}
      <Dialog open={contractDialogOpen} onOpenChange={setContractDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建员工合同</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>员工ID *</Label>
              <Input
                type="number"
                value={contractForm.employee_id}
                onChange={(e) =>
                setContractForm({
                  ...contractForm,
                  employee_id: e.target.value
                })
                } />

            </div>
            <div>
              <Label>合同类型 *</Label>
              <Select
                value={contractForm.contract_type}
                onValueChange={(value) =>
                setContractForm({ ...contractForm, contract_type: value })
                }>

                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fixed_term">固定期限</SelectItem>
                  <SelectItem value="open_term">无固定期限</SelectItem>
                  <SelectItem value="project_based">项目制</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>开始日期 *</Label>
                <Input
                  type="date"
                  value={contractForm.start_date}
                  onChange={(e) =>
                  setContractForm({
                    ...contractForm,
                    start_date: e.target.value
                  })
                  } />

              </div>
              <div>
                <Label>合同期限（月）</Label>
                <Input
                  type="number"
                  value={contractForm.duration_months}
                  onChange={(e) =>
                  setContractForm({
                    ...contractForm,
                    duration_months: parseInt(e.target.value)
                  })
                  } />

              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setContractDialogOpen(false)}>

              取消
            </Button>
            <Button onClick={handleSaveContract} disabled={loading}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}