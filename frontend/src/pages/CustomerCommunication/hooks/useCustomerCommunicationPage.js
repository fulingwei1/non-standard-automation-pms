/**
 * 客户沟通页面主 Hook
 * 管理数据加载、表单、CRUD操作、过滤等
 */

import { useState, useEffect } from "react";
import { customerCommunicationApi, customerApi, userApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";
import { confirmAction } from "@/lib/confirmAction";
import {
  COMMUNICATION_TYPE,
  COMMUNICATION_TOPIC,
  COMMUNICATION_PRIORITY,
  validateCommunicationData,
} from "../../../components/customer-communication";

const DEFAULT_FORM_DATA = {
  customer_id: "",
  communication_type: COMMUNICATION_TYPE.PHONE,
  topic: COMMUNICATION_TOPIC.SUPPORT,
  priority: COMMUNICATION_PRIORITY.MEDIUM,
  subject: "",
  content: "",
  communication_date: new Date().toISOString().split('T')[0],
  duration_minutes: "",
  customer_feedback: "",
  satisfaction_rating: null,
  next_action: "",
  next_action_date: "",
  assigned_to: "",
  notes: ""
};

// 标准化客户选项
const normalizeCustomerOption = (customer = {}) => ({
  ...customer,
  name: customer.name || customer.customer_name || customer.full_name || `客户${customer.id}`,
});

// 标准化用户选项
const normalizeUserOption = (user = {}) => ({
  ...user,
  name: user.name || user.real_name || user.username || `用户${user.id}`,
});

// 构建提交载荷
const buildCommunicationPayload = (formData, customers) => {
  const customer = (customers || []).find((item) => String(item.id) === String(formData.customer_id));
  return {
    customer_name: customer?.name,
    customer_contact: customer?.contact_name || customer?.contact_person || null,
    customer_phone: customer?.phone || customer?.contact_phone || null,
    customer_email: customer?.email || customer?.contact_email || null,
    communication_type: formData.communication_type,
    topic: formData.topic,
    priority: formData.priority,
    subject: formData.subject,
    content: formData.content,
    communication_date: formData.communication_date,
    duration_minutes: formData.duration_minutes ? Number(formData.duration_minutes) : null,
    next_action: formData.next_action,
    next_action_date: formData.next_action_date,
    tags: formData.notes
      ? formData.notes.split(/[，,]/).map((item) => item.trim()).filter(Boolean)
      : [],
  };
};

export function useCustomerCommunicationPage() {
  const [loading, setLoading] = useState(true);
  const [communications, setCommunications] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [users, setUsers] = useState([]);

  // 过滤状态
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterTopic, setFilterTopic] = useState("");
  const [filterCustomer, setFilterCustomer] = useState("");
  const [dateFilter, setDateFilter] = useState({ start: "", end: "" });

  // 对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedCommunication, setSelectedCommunication] = useState(null);
  const [formData, setFormData] = useState(DEFAULT_FORM_DATA);

  const [_stats, setStats] = useState({
    total: 0, pending: 0, in_progress: 0, completed: 0,
    follow_up: 0, high_priority: 0, today_count: 0, avg_satisfaction: 0
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
        userApi.list({ page_size: 1000 })
      ]);

      const commData = commRes.data?.items || commRes.data?.items || commRes.data || [];
      const customerData = (customerRes.data?.items || customerRes.data?.items || customerRes.data || []).map(normalizeCustomerOption);
      const userData = (userRes.data?.items || userRes.data?.items || userRes.data || []).map(normalizeUserOption);

      const transformedCommunications = (commData || [])
        .map((comm) => {
          const customer = (customerData || []).find((c) => String(c.id) === String(comm.customer_id)) || (customerData || []).find((c) => c.name === comm.customer_name);
          const assignedUser = (userData || []).find((u) => String(u.id) === String(comm.assigned_to));
          return {
            ...comm,
            customer_id: comm.customer_id ? String(comm.customer_id) : customer?.id ? String(customer.id) : "",
            assigned_to: comm.assigned_to ? String(comm.assigned_to) : "",
            customer,
            assigned_user: assignedUser,
          };
        })
        .filter((comm) => {
          const matchesSearch = !searchQuery || [comm.subject, comm.content, comm.customer?.name, comm.customer_name].filter(Boolean).some((v) => String(v).toLowerCase().includes(searchQuery.toLowerCase()));
          const matchesStatus = !filterStatus || comm.status === filterStatus;
          const matchesCustomer = !filterCustomer || String(comm.customer?.id || comm.customer_id) === String(filterCustomer);
          const matchesPriority = !filterPriority || comm.priority === filterPriority;
          const matchesType = !filterType || comm.communication_type === filterType;
          const matchesTopic = !filterTopic || comm.topic === filterTopic;
          const matchesDateStart = !dateFilter.start || new Date(comm.communication_date) >= new Date(`${dateFilter.start}T00:00:00`);
          const matchesDateEnd = !dateFilter.end || new Date(comm.communication_date) <= new Date(`${dateFilter.end}T23:59:59`);
          return matchesSearch && matchesStatus && matchesCustomer && matchesPriority && matchesType && matchesTopic && matchesDateStart && matchesDateEnd;
        });

      setCommunications(transformedCommunications);
      setCustomers(customerData);
      setUsers(userData);
    } catch (_error) {
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await customerCommunicationApi.statistics();
      setStats(res.data || {});
    } catch (_error) { /* 非关键操作失败时静默降级 */ }
  };

  const handleCreate = async () => {
    const validation = validateCommunicationData(formData);
    if (!validation.isValid) { toast.error(validation.errors.join(", ")); return; }
    try {
      const payload = buildCommunicationPayload(formData, customers);
      if (!payload.customer_name) { toast.error("请选择有效客户"); return; }
      await customerCommunicationApi.create(payload);
      toast.success("沟通记录创建成功");
      setShowCreateDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (_error) { toast.error("创建沟通记录失败"); }
  };

  const handleUpdate = async () => {
    try {
      await customerCommunicationApi.update(selectedCommunication.id, buildCommunicationPayload(formData, customers));
      toast.success("沟通记录更新成功");
      setShowEditDialog(false);
      resetForm();
      fetchData();
      fetchStats();
    } catch (_error) { toast.error("更新沟通记录失败"); }
  };

  const handleDelete = async (id) => {
    if (!await confirmAction("确定要删除这个沟通记录吗？")) return;
    try {
      await customerCommunicationApi.delete(id);
      toast.success("沟通记录删除成功");
      fetchData();
      fetchStats();
    } catch (_error) { toast.error("删除沟通记录失败"); }
  };

  const resetForm = () => {
    setFormData(DEFAULT_FORM_DATA);
    setSelectedCommunication(null);
  };

  const openEditDialog = (communication) => {
    setSelectedCommunication(communication);
    setFormData({
      customer_id: communication.customer_id ? String(communication.customer_id) : "",
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
      assigned_to: communication.assigned_to ? String(communication.assigned_to) : "",
      notes: communication.notes
    });
    setShowEditDialog(true);
  };

  // 快捷操作
  const handleQuickAction = (action) => {
    switch (action) {
      case 'createCommunication': setShowCreateDialog(true); break;
      case 'viewPending': setFilterStatus(COMMUNICATION_TYPE.PHONE ? 'pending' : ''); break;
      case 'viewOverdue': {
        const today = new Date();
        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        setDateFilter({ start: '', end: weekAgo.toISOString().split('T')[0] });
      } break;
      case 'viewAnalytics': toast.info('统计分析功能开发中...'); break;
      default: break;
    }
  };

  return {
    loading, communications, customers, users,
    searchQuery, setSearchQuery,
    filterStatus, setFilterStatus,
    filterPriority, setFilterPriority,
    filterType, setFilterType,
    filterTopic, setFilterTopic,
    filterCustomer, setFilterCustomer,
    dateFilter, setDateFilter,
    showCreateDialog, setShowCreateDialog,
    showDetailDialog, setShowDetailDialog,
    showEditDialog, setShowEditDialog,
    selectedCommunication, setSelectedCommunication,
    formData, setFormData,
    handleCreate, handleUpdate, handleDelete,
    openEditDialog, handleQuickAction,
  };
}
