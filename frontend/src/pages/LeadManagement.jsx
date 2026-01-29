/**
 * Lead Management Page - Sales lead management
 * Features: Lead list, creation, update, convert to opportunity
 */

import { useState, useEffect, useMemo } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui";
import { leadApi, customerApi } from "../services/api";
import {
  LeadStatsCards,
  LeadFilters,
  LeadList,
  LeadInsights,
  CreateLeadDialog,
  EditLeadDialog,
  ConvertLeadDialog,
  LeadDetailDialog,
  FollowUpDialog,
  statusConfig,
} from "../components/lead-management";

export default function LeadManagement() {
  const [leads, setLeads] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [viewMode, setViewMode] = useState("grid");
  const [selectedLead, setSelectedLead] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showFollowUpDialog, setShowFollowUpDialog] = useState(false);
  const [followUps, setFollowUps] = useState([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sortBy, setSortBy] = useState("priority"); // priority, created_at, status
  const [showKeyLeadsOnly, setShowKeyLeadsOnly] = useState(false);
  const pageSize = 20;

  // 表单数据
  const [formData, setFormData] = useState({
    customer_name: "",
    source: "",
    industry: "",
    contact_name: "",
    contact_phone: "",
    demand_summary: "",
    status: "NEW",
  });

  // 跟进记录表单
  const [followUpData, setFollowUpData] = useState({
    follow_up_type: "CALL",
    content: "",
    next_action: "",
    next_action_at: "",
  });

  // 加载线索列表
  const loadLeads = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      };
      const response = await leadApi.list(params);
      if (response.data && response.data.items) {
        setLeads(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
      console.error("加载线索列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 加载客户列表
  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 });
      if (response.data && response.data.items) {
        setCustomers(response.data.items);
      }
    } catch (error) {
      console.error("加载客户列表失败:", error);
    }
  };

  useEffect(() => {
    loadLeads();
  }, [page, searchTerm, statusFilter]);

  useEffect(() => {
    loadCustomers();
  }, []);

  // 筛选线索
  // 计算优先级并排序
  const processedLeads = useMemo(() => {
    let processed = [...leads];
    
    // 筛选关键线索
    if (showKeyLeadsOnly) {
      processed = processed.filter(lead => lead.is_key_lead === true);
    }
    
    // 排序
    if (sortBy === "priority") {
      processed.sort((a, b) => {
        const scoreA = a.priority_score || 0;
        const scoreB = b.priority_score || 0;
        return scoreB - scoreA; // 降序
      });
    } else if (sortBy === "created_at") {
      processed.sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB - dateA;
      });
    }
    
    return processed;
  }, [leads, showKeyLeadsOnly, sortBy]);

  const filteredLeads = useMemo(() => {
    return processedLeads.filter((lead) => {
      const matchesSearch =
        lead.lead_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.contact_name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || lead.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [processedLeads, searchTerm, statusFilter]);

  // 统计数据
  const stats = useMemo(() => {
    return {
      total: total,
      new: leads.filter((l) => l.status === "NEW").length,
      qualifying: leads.filter((l) => l.status === "QUALIFIED" || l.status === "QUALIFYING").length,
      converted: leads.filter((l) => l.status === "CONVERTED").length,
    };
  }, [leads, total]);

  const normalizeCustomerName = (value) =>
    String(value || "")
      .toLowerCase()
      .replace(/[\s\-_/,，。.]/g, "");

  const exactCustomerMatch = useMemo(() => {
    const normalized = normalizeCustomerName(formData.customer_name);
    if (!normalized) {
      return null;
    }
    return customers.find(
      (customer) =>
        normalizeCustomerName(customer.customer_name) === normalized
    );
  }, [customers, formData.customer_name]);

  const similarCustomers = useMemo(() => {
    const normalized = normalizeCustomerName(formData.customer_name);
    if (!normalized || exactCustomerMatch) {
      return [];
    }
    return customers
      .filter((customer) => {
        const candidate = normalizeCustomerName(customer.customer_name);
        return candidate && (candidate.includes(normalized) || normalized.includes(candidate));
      })
      .slice(0, 5);
  }, [customers, formData.customer_name, exactCustomerMatch]);

  const handleSelectCustomer = (customer) => {
    if (!customer) {
      setSelectedCustomerId("");
      return;
    }
    setSelectedCustomerId(String(customer.id));
    setFormData((prev) => ({
      ...prev,
      customer_name: customer.customer_name || "",
      industry: prev.industry || customer.industry || "",
    }));
  };

  const handleCustomerNameChange = (value) => {
    setSelectedCustomerId("");
    setFormData({ ...formData, customer_name: value });
  };

  // 创建线索
  const handleCreate = async () => {
    try {
      const customerName = formData.customer_name.trim();
      if (!customerName) {
        alert("请输入客户名称");
        return;
      }
      if (!exactCustomerMatch && similarCustomers.length === 0) {
        const shouldCreate = window.confirm(
          "未找到相似客户，是否新建该客户？"
        );
        if (!shouldCreate) {
          return;
        }
        await customerApi.create({
          customer_name: customerName,
          industry: formData.industry || undefined,
          contact_person: formData.contact_name || undefined,
          contact_phone: formData.contact_phone || undefined,
        });
        await loadCustomers();
      }
      await leadApi.create({ ...formData, customer_name: customerName });
      setShowCreateDialog(false);
      setFormData({
        customer_name: "",
        source: "",
        industry: "",
        contact_name: "",
        contact_phone: "",
        demand_summary: "",
        status: "NEW",
      });
      setSelectedCustomerId("");
      loadLeads();
    } catch (error) {
      console.error("创建线索失败:", error);
      alert("创建线索失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 更新线索
  const handleUpdate = async () => {
    if (!selectedLead) return;
    try {
      await leadApi.update(selectedLead.id, formData);
      setShowEditDialog(false);
      setSelectedLead(null);
      loadLeads();
    } catch (error) {
      console.error("更新线索失败:", error);
      alert("更新线索失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 打开编辑对话框
  const handleEdit = (lead) => {
    setSelectedLead(lead);
    setFormData({
      customer_name: lead.customer_name || "",
      source: lead.source || "",
      industry: lead.industry || "",
      contact_name: lead.contact_name || "",
      contact_phone: lead.contact_phone || "",
      demand_summary: lead.demand_summary || "",
      status: lead.status || "NEW",
    });
    setShowEditDialog(true);
  };

  // 线索转商机
  const handleConvert = async (customerId) => {
    if (!selectedLead) return;
    try {
      await leadApi.convert(selectedLead.id, customerId);
      setShowConvertDialog(false);
      setSelectedLead(null);
      loadLeads();
      alert("线索已成功转为商机");
    } catch (error) {
      console.error("转商机失败:", error);
      alert("转商机失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 查看详情
  const handleViewDetail = async (lead) => {
    setSelectedLead(lead);
    setShowDetailDialog(true);
    // 加载跟进记录
    try {
      const response = await leadApi.getFollowUps(lead.id);
      if (response.data) {
        setFollowUps(response.data);
      }
    } catch (error) {
      console.error("加载跟进记录失败:", error);
      setFollowUps([]);
    }
  };

  // 添加跟进记录
  const handleAddFollowUp = async () => {
    if (!selectedLead) return;
    try {
      await leadApi.createFollowUp(selectedLead.id, followUpData);
      setShowFollowUpDialog(false);
      setFollowUpData({
        follow_up_type: "CALL",
        content: "",
        next_action: "",
        next_action_at: "",
      });
      // 重新加载跟进记录
      const response = await leadApi.getFollowUps(selectedLead.id);
      if (response.data) {
        setFollowUps(response.data);
      }
      loadLeads(); // 刷新列表
    } catch (error) {
      console.error("添加跟进记录失败:", error);
      alert(
        "添加跟进记录失败: " + (error.response?.data?.detail || error.message),
      );
    }
  };

  const handleOpenConvertDialog = (lead) => {
    setSelectedLead(lead);
    setShowConvertDialog(true);
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="线索管理"
        description="管理销售线索，跟进潜在客户需求"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建线索
          </Button>
        }
      />

      {/* 统计卡片 */}
      <LeadStatsCards stats={stats} leads={leads} />

      {/* 数据洞察：来源分布、热门线索、即将跟进 */}
      <LeadInsights
        leads={leads}
        onViewLead={handleViewDetail}
        onViewAll={() => {
          setShowKeyLeadsOnly(true);
          setSortBy("priority");
        }}
      />

      {/* 筛选栏 */}
      <LeadFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        sortBy={sortBy}
        setSortBy={setSortBy}
        showKeyLeadsOnly={showKeyLeadsOnly}
        setShowKeyLeadsOnly={setShowKeyLeadsOnly}
        viewMode={viewMode}
        setViewMode={setViewMode}
        statusConfig={statusConfig}
      />

      {/* 线索列表 */}
      <LeadList
        loading={loading}
        leads={filteredLeads}
        viewMode={viewMode}
        statusConfig={statusConfig}
        handleViewDetail={handleViewDetail}
        handleEdit={handleEdit}
        handleConvert={handleOpenConvertDialog}
      />

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 创建线索对话框 */}
      <CreateLeadDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        setFormData={setFormData}
        statusConfig={statusConfig}
        onCreate={handleCreate}
        customers={customers}
        selectedCustomerId={selectedCustomerId}
        onSelectCustomer={handleSelectCustomer}
        onCustomerNameChange={handleCustomerNameChange}
        similarCustomers={similarCustomers}
        hasExactCustomerMatch={!!exactCustomerMatch}
      />

      {/* 编辑线索对话框 */}
      <EditLeadDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        setFormData={setFormData}
        statusConfig={statusConfig}
        onUpdate={handleUpdate}
      />

      {/* 转商机对话框 */}
      <ConvertLeadDialog
        open={showConvertDialog}
        onOpenChange={setShowConvertDialog}
        customers={customers}
        onConvert={handleConvert}
      />

      {/* 详情对话框 */}
      <LeadDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        lead={selectedLead}
        followUps={followUps}
        statusConfig={statusConfig}
        onOpenFollowUp={() => setShowFollowUpDialog(true)}
      />

      {/* 添加跟进记录对话框 */}
      <FollowUpDialog
        open={showFollowUpDialog}
        onOpenChange={setShowFollowUpDialog}
        data={followUpData}
        setData={setFollowUpData}
        onSave={handleAddFollowUp}
      />
    </div>
  );
}
