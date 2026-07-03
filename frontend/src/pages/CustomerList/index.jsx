/**
 * Customer List Page - CRM customer management for sales
 */

import { useState, useMemo, useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  Building2,
  Plus,
  Download,
  Upload,
} from "lucide-react"
import { PageHeader } from "../../components/layout"
import { Button } from "../../components/ui"
import { fadeIn, staggerContainer } from "../../lib/animations"
import { CustomerCard } from "../../components/sales"
import { useCustomerList } from "./hooks"
import { customerApi } from "../../services/api"
import { toast } from "sonner"
import { confirmAction } from "../../lib/confirmAction"

import { normalizeCustomer } from "./utils"
import { StatsRow } from "./StatsRow"
import { FilterBar } from "./FilterBar"
import { CustomerTable } from "./CustomerTable"
import { CreateDialog } from "./CreateDialog"
import { CustomerDetailPanel } from "./CustomerDetailPanel"

export default function CustomerList() {
  const navigate = useNavigate();
  const { customers: rawCustomers, setPagination, loadCustomers, deleteCustomer } = useCustomerList()
  const [viewMode, setViewMode] = useState("grid"); // 'grid' or 'list'
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGrade, setSelectedGrade] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedIndustry, setSelectedIndustry] = useState("all");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  // 命令栏"新建客户"动作：带 ai_hint 进来时自动打开新建对话框并 AI 预填
  const [searchParams, setSearchParams] = useSearchParams();
  const [autofillHint, setAutofillHint] = useState("");
  useEffect(() => {
    const hint = searchParams.get("ai_hint");
    if (hint) {
      setAutofillHint(hint);
      setShowCreateDialog(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);
  const [createForm, setCreateForm] = useState({
    customer_name: "",
    short_name: "",
    customer_level: "B",
    industry: "",
    contact_name: "",
    phone: "",
    address: "",
    remark: "",
  });

  useEffect(() => {
    setPagination((prev) =>
      prev.pageSize === 1000 ? prev : { ...prev, pageSize: 1000 }
    )
  }, [setPagination])

  const normalizedCustomers = useMemo(() => {
    if (!Array.isArray(rawCustomers)) {return []}
    return (rawCustomers || []).map(normalizeCustomer)
  }, [rawCustomers])

  // Filter customers
  const filteredCustomers = useMemo(() => {
    return (normalizedCustomers || []).filter((customer) => {
      const searchLower = (searchTerm || "").toLowerCase();
    const matchesSearch =
        !searchTerm ||
        (customer.name || "").toLowerCase().includes(searchLower) ||
        (customer.shortName || "").toLowerCase().includes(searchLower) ||
        (customer.contactPerson || "").toLowerCase().includes(searchLower);

      const matchesGrade =
        selectedGrade === "all" || customer.grade === selectedGrade;
      const matchesStatus =
        selectedStatus === "all" || customer.status === selectedStatus;
      const matchesIndustry =
        selectedIndustry === "all" || customer.industry === selectedIndustry;

      return matchesSearch && matchesGrade && matchesStatus && matchesIndustry;
    });
  }, [
    normalizedCustomers,
    searchTerm,
    selectedGrade,
    selectedStatus,
    selectedIndustry,
  ]);

  // Stats
  const stats = useMemo(() => {
    return {
      total: normalizedCustomers.length,
      active: (normalizedCustomers || []).filter((c) => c.status === "active").length,
      gradeA: (normalizedCustomers || []).filter((c) => c.grade === "A").length,
      warning: (normalizedCustomers || []).filter((c) => c.isWarning).length,
    };
  }, [normalizedCustomers]);

  const handleCustomerClick = (customer) => {
    // 跳转到客户详情页（整合版：包含360画像、关系成熟度等）
    navigate(`/sales/customers/${customer.id}`);
  };

  const resetCreateForm = () => {
    setCreateForm({
      customer_name: "",
      short_name: "",
      customer_level: "B",
      industry: "",
      contact_name: "",
      phone: "",
      address: "",
      remark: "",
    });
  };

  const handleCreateCustomer = async () => {
    if (!createForm.customer_name?.trim()) {
      toast.error("公司全称不能为空");
      return;
    }

    try {
      setCreating(true);
      await customerApi.create({
        customer_name: createForm.customer_name.trim(),
        short_name: createForm.short_name?.trim() || undefined,
        industry: createForm.industry || undefined,
        address: createForm.address?.trim() || undefined,
        customer_type: "enterprise",
        status: "potential",
        customer_source: "manual",
      });

      toast.success("客户创建成功");
      setShowCreateDialog(false);
      resetCreateForm();
      await loadCustomers();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(detail || "创建客户失败");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteCustomer = async (customer) => {
    if (!customer?.id) {
      return;
    }

    const confirmed = await confirmAction({
      title: "确认删除客户",
      description: `确定要删除客户「${customer.name || customer.shortName || customer.id}」吗？此操作不可撤销。`,
      confirmText: "删除",
      variant: "destructive",
    });

    if (!confirmed) {
      return;
    }

    const result = await deleteCustomer(customer.id);
    if (result.success) {
      toast.success("客户删除成功");
      return;
    }

    toast.error(result.error || "删除客户失败");
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="客户管理"
        description="管理客户档案、联系记录和业务往来"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              导入
            </Button>
            <Button
              className="flex items-center gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              新建客户
            </Button>
          </motion.div>
        }
      />

      {/* Stats Row */}
      <StatsRow stats={stats} />

      {/* Filters */}
      <FilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedGrade={selectedGrade}
        setSelectedGrade={setSelectedGrade}
        selectedStatus={selectedStatus}
        setSelectedStatus={setSelectedStatus}
        selectedIndustry={selectedIndustry}
        setSelectedIndustry={setSelectedIndustry}
        viewMode={viewMode}
        setViewMode={setViewMode}
        filteredCount={filteredCustomers.length}
      />

      {/* Customer Grid/List */}
      <motion.div variants={fadeIn}>
        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(filteredCustomers || []).map((customer) => (
              <CustomerCard
                key={customer.id}
                customer={customer}
                onClick={handleCustomerClick}
              />
            ))}
          </div>
        ) : (
          <CustomerTable
            customers={filteredCustomers}
            onCustomerClick={handleCustomerClick}
            onDeleteCustomer={handleDeleteCustomer}
          />
        )}

        {filteredCustomers.length === 0 && (
          <div className="text-center py-16">
            <Building2 className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">暂无客户</h3>
            <p className="text-slate-400 mb-4">没有找到符合条件的客户</p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新建客户
            </Button>
          </div>
        )}
      </motion.div>

      {/* Customer Detail Sidebar */}
      <AnimatePresence>
        {selectedCustomer && (
          <CustomerDetailPanel
            customer={selectedCustomer}
            onClose={() => setSelectedCustomer(null)}
          />
        )}
      </AnimatePresence>

      {/* Create Customer Dialog */}
      <CreateDialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          setShowCreateDialog(open);
          if (!open) setAutofillHint("");
        }}
        createForm={createForm}
        setCreateForm={setCreateForm}
        onSubmit={handleCreateCustomer}
        creating={creating}
        onReset={resetCreateForm}
        autofillHint={autofillHint}
      />
    </motion.div>
  );
}
