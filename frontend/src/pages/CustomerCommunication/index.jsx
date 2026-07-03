/**
 * Customer Communication Management
 * 客户沟通历史管理 - 客服工程师高级功能
 *
 * 功能：
 * 1. 客户沟通记录创建、查看、编辑
 * 2. 沟通方式管理（电话、邮件、现场、微信、会议等）
 * 3. 沟通主题分类
 * 4. 沟通内容详细记录
 * 5. 后续跟进任务
 * 6. 沟通记录搜索和筛选
 * 7. 沟通统计分析
 */

import { useState, useEffect } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { customerCommunicationApi, customerApi, userApi } from "../../services/api";
import { toast } from "../../components/ui/toast";
import {
  CustomerCommunicationOverview,
  COMMUNICATION_STATUS,
  validateCommunicationData } from
"../../components/customer-communication";
import { confirmAction } from "@/lib/confirmAction";

import { initialFormData } from "./constants";
import CommunicationTable from "./CommunicationTable";
import CreateDialog from "./CreateDialog";
import DetailDialog from "./DetailDialog";
import EditDialog from "./EditDialog";

export default function CustomerCommunication() {
  const [loading, setLoading] = useState(true);
  const [communications, setCommunications] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterTopic, setFilterTopic] = useState("");
  const [filterCustomer, setFilterCustomer] = useState("");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedCommunication, setSelectedCommunication] = useState(null);
  const [formData, setFormData] = useState({ ...initialFormData });

  const [_stats, setStats] = useState({
    total: 0,
    pending: 0,
    in_progress: 0,
    completed: 0,
    follow_up: 0,
    high_priority: 0,
    today_count: 0,
    avg_satisfaction: 0
  });

  useEffect(() => {
    fetchData();
    fetchStats();
  }, [searchQuery, filterStatus, filterPriority, filterType, filterTopic, filterCustomer, dateFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        search: searchQuery,
        status: filterStatus || undefined,
        priority: filterPriority || undefined,
        communication_type: filterType || undefined,
        topic: filterTopic || undefined,
        customer_id: filterCustomer || undefined,
        start_date: dateFilter.start || undefined,
        end_date: dateFilter.end || undefined
      };

      const [commRes, customerRes, userRes] = await Promise.all([
      customerCommunicationApi.list(params),
      customerApi.list({ page_size: 1000 }),
      userApi.options({ page_size: 1000, is_active: true })]
      );

      const commData = commRes.data?.items || commRes.data?.items || commRes.data || [];
      const customerData = customerRes.data?.items || customerRes.data?.items || customerRes.data || [];
      const userData = userRes.data?.items || userRes.data?.items || userRes.data || [];

      const transformedCommunications = (commData || []).map((comm) => ({
        ...comm,
        customer: (customerData || []).find((c) => c.id === comm.customer_id),
        assigned_user: (userData || []).find((u) => u.id === comm.assigned_to)
      }));

      setCommunications(transformedCommunications);
      setCustomers(customerData);
      setUsers(userData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await customerCommunicationApi.statistics();
      setStats(res.data || {});
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const handleCreate = async () => {
    const validation = validateCommunicationData(formData);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }

    try {
      await customerCommunicationApi.create(formData);
      toast.success("沟通记录创建成功");
      setShowCreateDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to create communication:", error);
      toast.error("创建沟通记录失败");
    }
  };

  const handleUpdate = async () => {
    try {
      await customerCommunicationApi.update(selectedCommunication.id, formData);
      toast.success("沟通记录更新成功");
      setShowEditDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to update communication:", error);
      toast.error("更新沟通记录失败");
    }
  };

  const handleDelete = async (id) => {
    if (!await confirmAction("确定要删除这个沟通记录吗？")) {return;}

    try {
      await customerCommunicationApi.delete(id);
      toast.success("沟通记录删除成功");
      fetchData();
      fetchStats();
    } catch (error) {
      console.error("Failed to delete communication:", error);
      toast.error("删除沟通记录失败");
    }
  };

  const resetForm = () => {
    setFormData({ ...initialFormData, communication_date: new Date().toISOString().split('T')[0] });
    setSelectedCommunication(null);
  };

  const openEditDialog = (communication) => {
    setSelectedCommunication(communication);
    setFormData({
      customer_id: communication.customer_id,
      communication_type: communication.communication_type,
      topic: communication.topic,
      priority: communication.priority,
      subject: communication.subject,
      content: communication.content,
      communication_date: communication.communication_date,
      duration_minutes: communication.duration_minutes,
      customer_feedback: communication.customer_feedback,
      satisfaction_rating: communication.satisfaction_rating,
      next_action: communication.next_action,
      next_action_date: communication.next_action_date,
      assigned_to: communication.assigned_to,
      notes: communication.notes
    });
    setShowEditDialog(true);
  };

  // Quick action handlers for overview component
  const handleQuickAction = (action) => {
    switch (action) {
      case 'createCommunication':
        setShowCreateDialog(true);
        break;
      case 'viewPending':
        setFilterStatus(COMMUNICATION_STATUS.PENDING);
        break;
      case 'viewOverdue':
        // Filter for overdue communications
        {
          const today = new Date();
          const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
          setDateFilter({ start: '', end: weekAgo.toISOString().split('T')[0] });
        }
        break;
      case 'viewAnalytics':
        // Navigate to analytics view or show analytics dialog
        toast.info('统计分析功能开发中...');
        break;
      default:
        break;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="客户沟通管理"
        description="管理客户沟通记录、跟进和分析"
        actions={
        <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建沟通记录
        </Button>
        } />


      {/* Overview Section */}
      <CustomerCommunicationOverview
        communications={communications}
        customers={customers}
        onQuickAction={handleQuickAction} />


      {/* Filters & Table Section */}
      <CommunicationTable
        loading={loading}
        communications={communications}
        customers={customers}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
        filterPriority={filterPriority}
        setFilterPriority={setFilterPriority}
        filterType={filterType}
        setFilterType={setFilterType}
        filterTopic={filterTopic}
        setFilterTopic={setFilterTopic}
        filterCustomer={filterCustomer}
        setFilterCustomer={setFilterCustomer}
        dateFilter={dateFilter}
        setDateFilter={setDateFilter}
        onView={(comm) => {
          setSelectedCommunication(comm);
          setShowDetailDialog(true);
        }}
        onEdit={openEditDialog}
        onDelete={handleDelete}
      />

      {/* Create Dialog */}
      <CreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        setFormData={setFormData}
        customers={customers}
        users={users}
        onSubmit={handleCreate}
      />

      {/* Detail Dialog */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        communication={selectedCommunication}
      />

      {/* Edit Dialog */}
      <EditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        setFormData={setFormData}
        customers={customers}
        users={users}
        onSubmit={handleUpdate}
      />
    </div>);

}
