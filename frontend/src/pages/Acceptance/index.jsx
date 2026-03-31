import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ClipboardList,
  Clock,
  Plus,
  Search,
  Download,
  CheckCircle2,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { acceptanceApi, projectApi } from "../../services/api";
import { typeConfigs } from "./constants";
import AcceptanceCard from "./AcceptanceCard";
import AcceptanceDetailDialog from "./AcceptanceDetailDialog";

export default function Acceptance() {
  const [acceptances, setAcceptances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAcceptance, setSelectedAcceptance] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [projects, setProjects] = useState([]);
  const [newOrder, setNewOrder] = useState({
    project_id: null,
    machine_id: null,
    acceptance_type: "FAT",
    template_id: null,
    planned_date: "",
    location: "",
  });

  // Map backend status to frontend status
  const mapBackendStatusToFrontend = (backendStatus) => {
    const statusMap = {
      DRAFT: "draft",
      READY: "ready",
      PENDING: "pending",
      PENDING_SIGN: "pending_sign",
      IN_PROGRESS: "in_progress",
      COMPLETED: "completed",
      CANCELLED: "cancelled",
      FAILED: "failed",
    };
    return (
      statusMap[backendStatus] || backendStatus?.toLowerCase() || "pending"
    );
  };

  // Load acceptances from API
  const loadAcceptances = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query parameters
      const params = {
        page: 1,
        page_size: 100,
      };

      // Apply filters
      if (typeFilter !== "all") {
        params.acceptance_type = typeFilter;
      }
      if (statusFilter !== "all") {
        // Map frontend status to backend status
        const statusMap = {
          draft: "DRAFT",
          ready: "READY",
          pending: "PENDING",
          pending_sign: "PENDING_SIGN",
          in_progress: "IN_PROGRESS",
          completed: "COMPLETED",
          cancelled: "CANCELLED",
          failed: "FAILED",
        };
        params.status = statusMap[statusFilter] || statusFilter.toUpperCase();
      }
      if (searchQuery) {
        params.keyword = searchQuery;
      }

      const response = await acceptanceApi.orders.list(params);
      // Handle different response formats
      const data = response.data?.data || response.data || response;
      const ordersData = data?.items || (Array.isArray(data) ? data : []);

      // Transform backend data to frontend format
      const transformedAcceptances = await Promise.all(
        (ordersData || []).map(async (order) => {
          // Load issues for this order
          let issues = [];
          try {
            const issuesResponse = await acceptanceApi.issues.list(order.id);
            issues = issuesResponse.data?.items || issuesResponse.data || [];
          } catch (err) {
            console.error(`Failed to load issues for order ${order.id}:`, err);
          }

          // Load items for this order
          let items;
          let checklistCategories;
          try {
            const itemsResponse = await acceptanceApi.orders.getItems(order.id);
            items = itemsResponse.data?.items || itemsResponse.data || [];

            // Group items by category
            const categoryMap = {};
            (items || []).forEach((item) => {
              const category = item.category_name || "其他";
              if (!categoryMap[category]) {
                categoryMap[category] = {
                  name: category,
                  total: 0,
                  passed: 0,
                  failed: 0,
                };
              }
              categoryMap[category].total++;
              if (item.result === "PASS") {
                categoryMap[category].passed++;
              } else if (item.result === "FAIL") {
                categoryMap[category].failed++;
              }
            });
            checklistCategories = Object.values(categoryMap);
          } catch (err) {
            console.error(`Failed to load items for order ${order.id}:`, err);
          }

          return {
            id: order.order_no || order.id?.toString(),
            type: order.acceptance_type,
            projectId: order.project_id?.toString(),
            projectName: order.project_name || "",
            machineNo: order.machine_name || order.machine_code || "",
            customer: order.project_name || "", // Will be populated from project
            customerContact: "",
            status: mapBackendStatusToFrontend(order.status),
            scheduledDate: order.planned_date || "",
            completedDate: order.actual_end_date || null,
            inspector: "",
            totalItems: order.total_items || 0,
            passedItems: order.passed_items || 0,
            failedItems: order.failed_items || 0,
            pendingItems:
              order.total_items -
              (order.passed_items || 0) -
              (order.failed_items || 0),
            issues: (issues || []).map((issue) => ({
              id: issue.id?.toString(),
              item: issue.title || "",
              category: issue.category || "",
              severity: issue.severity?.toLowerCase() || "minor",
              description: issue.description || "",
              status: issue.status?.toLowerCase() || "open",
              photos: issue.attachments || [],
            })),
            checklistCategories,
            // Store original order for detail view
            _original: order,
          };
        }),
      );

      setAcceptances(transformedAcceptances);
    } catch (err) {
      console.error("Failed to load acceptances:", err);
      let errorMessage = "加载验收单失败";
      if (err.response) {
        errorMessage =
          err.response.data?.detail ||
          err.response.data?.message ||
          errorMessage;
      } else if (err.request) {
        errorMessage = "无法连接到服务器，请检查后端服务是否启动";
      } else {
        errorMessage = err.message || errorMessage;
      }
      setError(errorMessage);
      setAcceptances([]);
    } finally {
      setLoading(false);
    }
  }, [typeFilter, statusFilter, searchQuery]);

  // Load projects for create dialog
  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  }, []);

  // Load acceptances when component mounts or filters change
  useEffect(() => {
    loadAcceptances();
    fetchProjects();
  }, [loadAcceptances, fetchProjects]);

  // Handle create order
  const handleCreateOrder = async () => {
    if (!newOrder.project_id || !newOrder.planned_date) {
      alert("请填写项目和计划日期");
      return;
    }
    try {
      await acceptanceApi.orders.create(newOrder);
      setShowCreateDialog(false);
      setNewOrder({
        project_id: null,
        machine_id: null,
        acceptance_type: "FAT",
        template_id: null,
        planned_date: "",
        location: "",
      });
      loadAcceptances();
    } catch (error) {
      console.error("Failed to create order:", error);
      alert(
        "创建验收单失败: " + (error.response?.data?.detail || error.message),
      );
    }
  };

  // Client-side filtering (for additional filtering beyond API)
  const normalizedQuery = searchQuery.trim().toLowerCase();
  const filteredAcceptances = (acceptances || []).filter((acceptance) => {
    if (!normalizedQuery) {
      return true;
    }

    const projectMatches = acceptance.projectName
      ?.toLowerCase()
      .includes(normalizedQuery);
    const idMatches = acceptance.id?.toLowerCase().includes(normalizedQuery);

    return projectMatches || idMatches;
  });

  const stats = {
    total: acceptances.length,
    pending: (acceptances || []).filter((a) => a.status === "pending").length,
    inProgress: (acceptances || []).filter((a) => a.status === "in_progress").length,
    completed: (acceptances || []).filter((a) => a.status === "completed").length,
  };

  const handleView = async (acceptance) => {
    // Load full details if needed
    if (acceptance._original) {
      try {
        await acceptanceApi.orders.get(acceptance._original.id);

        // Load items and issues
        const [itemsResponse, issuesResponse] = await Promise.all([
          acceptanceApi.orders.getItems(acceptance._original.id),
          acceptanceApi.issues.list(acceptance._original.id),
        ]);

        const items = itemsResponse.data?.items || itemsResponse.data || [];
        const issues = issuesResponse.data?.items || issuesResponse.data || [];

        // Update acceptance with full details
        const updatedAcceptance = {
          ...acceptance,
          items,
          issues: (issues || []).map((issue) => ({
            id: issue.id?.toString(),
            item: issue.title || "",
            category: issue.category || "",
            severity: issue.severity?.toLowerCase() || "minor",
            description: issue.description || "",
            status: issue.status?.toLowerCase() || "open",
            photos: issue.attachments || [],
          })),
        };

        setSelectedAcceptance(updatedAcceptance);
      } catch (err) {
        console.error("Failed to load acceptance details:", err);
        setSelectedAcceptance(acceptance);
      }
    } else {
      setSelectedAcceptance(acceptance);
    }
    setShowDetail(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 py-6 space-y-6"
      >
        <PageHeader
          title="验收管理"
          description="管理FAT/SAT验收流程，记录验收问题"
          actions={
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-1" />
              新建验收单
            </Button>
          }
        />

        {/* Stats */}
        <motion.div
          variants={fadeIn}
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          {[
            {
              label: "全部验收单",
              value: stats.total,
              icon: ClipboardList,
              color: "text-blue-400",
            },
            {
              label: "待验收",
              value: stats.pending,
              icon: Clock,
              color: "text-slate-400",
            },
            {
              label: "验收中",
              value: stats.inProgress,
              icon: ClipboardList,
              color: "text-amber-400",
            },
            {
              label: "已完成",
              value: stats.completed,
              icon: CheckCircle2,
              color: "text-emerald-400",
            },
          ].map((stat, index) => (
            <Card key={index} className="bg-surface-1/50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">{stat.label}</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {stat.value}
                    </p>
                  </div>
                  <stat.icon className={cn("w-8 h-8", stat.color)}  />
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn}>
          <Card className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                <div className="flex items-center gap-4">
                  {/* Type Filter */}
                  <div className="flex items-center gap-2">
                    {[
                      { value: "all", label: "全部" },
                      { value: "FAT", label: "FAT" },
                      { value: "SAT", label: "SAT" },
                    ].map((filter) => (
                      <Button
                        key={filter.value}
                        variant={
                          typeFilter === filter.value ? "default" : "ghost"
                        }
                        size="sm"
                        onClick={() => setTypeFilter(filter.value)}
                      >
                        {filter.label}
                      </Button>
                    ))}
                  </div>

                  <div className="h-6 w-px bg-border" />

                  {/* Status Filter */}
                  <div className="flex items-center gap-2">
                    {[
                      { value: "all", label: "全部状态" },
                      { value: "pending", label: "待验收" },
                      { value: "in_progress", label: "验收中" },
                      { value: "completed", label: "已完成" },
                    ].map((filter) => (
                      <Button
                        key={filter.value}
                        variant={
                          statusFilter === filter.value ? "default" : "ghost"
                        }
                        size="sm"
                        onClick={() => setStatusFilter(filter.value)}
                      >
                        {filter.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 w-full md:w-auto">
                  <div className="relative flex-1 md:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索验收单..."
                      value={searchQuery || "unknown"}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4 mr-1" />
                    导出
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Loading State */}
        {loading && (
          <motion.div variants={fadeIn} className="text-center py-16">
            <div className="text-slate-400">加载中...</div>
          </motion.div>
        )}

        {/* Error State */}
        {error && !loading && (
          <motion.div variants={fadeIn} className="text-center py-16">
            <div className="text-red-400">{error}</div>
          </motion.div>
        )}

        {/* Acceptance List */}
        {!loading && !error && (
          <motion.div
            variants={fadeIn}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filteredAcceptances.length > 0 ? (
              (filteredAcceptances || []).map((acceptance) => (
                <AcceptanceCard
                  key={acceptance.id}
                  acceptance={acceptance}
                  onView={handleView}
                />
              ))
            ) : (
              <div className="col-span-full">
                <motion.div variants={fadeIn} className="text-center py-16">
                  <ClipboardList className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                  <h3 className="text-lg font-medium text-slate-400">
                    暂无验收单
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {searchQuery ||
                    typeFilter !== "all" ||
                    statusFilter !== "all"
                      ? "没有符合条件的验收单"
                      : '点击"新建验收单"开始验收'}
                  </p>
                </motion.div>
              </div>
            )}
          </motion.div>
        )}

        {/* Detail Dialog */}
        <AcceptanceDetailDialog
          acceptance={selectedAcceptance}
          open={showDetail}
          onOpenChange={setShowDetail}
        />

        {/* Create Order Dialog */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>新建验收单</DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block text-white">
                    项目 *
                  </label>
                  <Select
                    value={newOrder.project_id?.toString() || ""}
                    onValueChange={(val) =>
                      setNewOrder({
                        ...newOrder,
                        project_id: val ? parseInt(val) : null,
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      {(projects || []).map((proj) => (
                        <SelectItem key={proj.id} value={proj.id.toString()}>
                          {proj.project_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block text-white">
                      验收类型
                    </label>
                    <Select
                      value={newOrder.acceptance_type}
                      onValueChange={(val) =>
                        setNewOrder({ ...newOrder, acceptance_type: val })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(typeConfigs).map(([key, config]) => (
                          <SelectItem key={key} value={key || "unknown"}>
                            {config.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block text-white">
                      计划日期 *
                    </label>
                    <Input
                      type="date"
                      value={newOrder.planned_date}
                      onChange={(e) =>
                        setNewOrder({
                          ...newOrder,
                          planned_date: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block text-white">
                    验收地点
                  </label>
                  <Input
                    value={newOrder.location}
                    onChange={(e) =>
                      setNewOrder({ ...newOrder, location: e.target.value })
                    }
                    placeholder="验收地点"
                  />
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
              >
                取消
              </Button>
              <Button onClick={handleCreateOrder}>创建</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </motion.div>
    </div>
  );
}
