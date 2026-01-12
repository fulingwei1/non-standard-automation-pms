/**
 * Customer List Page - CRM customer management for sales
 */

import { useState, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Building2,
  Search,
  Plus,
  LayoutGrid,
  List,
  ChevronRight,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Star,
  TrendingUp,
  AlertTriangle,
  Download,
  Upload,
  Tag,
  MoreHorizontal,
  Edit,
  Trash2,
  UserPlus,
  Target,
  DollarSign,
  History,
  MessageSquare,
} from "lucide-react"
import { PageHeader } from "../components/layout"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../components/ui"
import { cn } from "../lib/utils"
import { fadeIn, staggerContainer } from "../lib/animations"
import { CustomerCard } from "../components/sales"

// Mock customer data for UI preview before backend integration
const mockCustomers = [
  {
    id: 1,
    name: "宁德时代新能源科技股份有限公司",
    shortName: "宁德时代",
    grade: "A",
    status: "active",
    industry: "新能源电池",
    location: "福建宁德",
    contactPerson: "李晓明",
    phone: "138-0000-1111",
    email: "lixm@catl.com",
    totalAmount: 12800000,
    pendingAmount: 2500000,
    projectCount: 8,
    lastContact: "2026-01-10",
    isWarning: false,
    tags: ["重点客户", "战略合作"],
  },
  {
    id: 2,
    name: "比亚迪电子有限公司",
    shortName: "比亚迪电子",
    grade: "A",
    status: "potential",
    industry: "消费电子",
    location: "广东深圳",
    contactPerson: "王丽",
    phone: "139-0000-2222",
    email: "wangli@byd.com",
    totalAmount: 9600000,
    pendingAmount: 0,
    projectCount: 5,
    lastContact: "2026-01-08",
    isWarning: false,
    tags: ["新能源", "重点拓展"],
  },
  {
    id: 3,
    name: "立讯精密工业股份有限公司",
    shortName: "立讯精密",
    grade: "B",
    status: "active",
    industry: "电子制造",
    location: "广东东莞",
    contactPerson: "陈飞",
    phone: "137-0000-3333",
    email: "chenfei@luxshare.com",
    totalAmount: 6800000,
    pendingAmount: 1200000,
    projectCount: 4,
    lastContact: "2026-01-06",
    isWarning: true,
    tags: ["产能提升", "定制化"],
  },
  {
    id: 4,
    name: "欣旺达电子股份有限公司",
    shortName: "欣旺达",
    grade: "B",
    status: "dormant",
    industry: "储能系统",
    location: "广东深圳",
    contactPerson: "赵倩",
    phone: "136-0000-4444",
    email: "zhaoqian@sunwoda.com",
    totalAmount: 4200000,
    pendingAmount: 800000,
    projectCount: 3,
    lastContact: "2025-12-28",
    isWarning: true,
    tags: ["储能", "需跟进"],
  },
  {
    id: 5,
    name: "蓝思科技股份有限公司",
    shortName: "蓝思科技",
    grade: "C",
    status: "lost",
    industry: "智能制造",
    location: "湖南长沙",
    contactPerson: "周强",
    phone: "135-0000-5555",
    email: "zhouqiang@lens.com",
    totalAmount: 2100000,
    pendingAmount: 0,
    projectCount: 2,
    lastContact: "2025-11-30",
    isWarning: false,
    tags: ["流失客户"],
  },
  {
    id: 6,
    name: "歌尔股份有限公司",
    shortName: "歌尔股份",
    grade: "B",
    status: "potential",
    industry: "消费电子",
    location: "山东潍坊",
    contactPerson: "孙蕾",
    phone: "134-0000-6666",
    email: "sunlei@goertek.com",
    totalAmount: 5800000,
    pendingAmount: 400000,
    projectCount: 4,
    lastContact: "2026-01-03",
    isWarning: false,
    tags: ["声学", "重点跟进"],
  },
];

const gradeOptions = [
  { value: "all", label: "全部等级" },
  { value: "A", label: "A级客户" },
  { value: "B", label: "B级客户" },
  { value: "C", label: "C级客户" },
  { value: "D", label: "D级客户" },
];

const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "active", label: "活跃客户" },
  { value: "potential", label: "潜在客户" },
  { value: "dormant", label: "沉睡客户" },
  { value: "lost", label: "流失客户" },
];

const industryOptions = [
  { value: "all", label: "全部行业" },
  { value: "新能源电池", label: "新能源电池" },
  { value: "消费电子", label: "消费电子" },
  { value: "汽车零部件", label: "汽车零部件" },
  { value: "储能系统", label: "储能系统" },
  { value: "智能制造", label: "智能制造" },
  { value: "电子制造", label: "电子制造" },
];

const gradeColors = {
  A: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  B: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  C: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  D: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

const statusConfig = {
  active: {
    label: "活跃",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  potential: {
    label: "潜在",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  dormant: {
    label: "沉睡",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  lost: { label: "流失", color: "bg-red-500", textColor: "text-red-400" },
};

export default function CustomerList() {
  const [viewMode, setViewMode] = useState("grid"); // 'grid' or 'list'
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGrade, setSelectedGrade] = useState("all");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedIndustry, setSelectedIndustry] = useState("all");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Filter customers
  const filteredCustomers = useMemo(() => {
    return mockCustomers.filter((customer) => {
      const matchesSearch =
        !searchTerm ||
        customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.shortName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.contactPerson
          ?.toLowerCase()
          .includes(searchTerm.toLowerCase());

      const matchesGrade =
        selectedGrade === "all" || customer.grade === selectedGrade;
      const matchesStatus =
        selectedStatus === "all" || customer.status === selectedStatus;
      const matchesIndustry =
        selectedIndustry === "all" || customer.industry === selectedIndustry;

      return matchesSearch && matchesGrade && matchesStatus && matchesIndustry;
    });
  }, [searchTerm, selectedGrade, selectedStatus, selectedIndustry]);

  // Stats
  const stats = useMemo(() => {
    return {
      total: mockCustomers.length,
      active: mockCustomers.filter((c) => c.status === "active").length,
      gradeA: mockCustomers.filter((c) => c.grade === "A").length,
      warning: mockCustomers.filter((c) => c.isWarning).length,
    };
  }, []);

  const handleCustomerClick = (customer) => {
    setSelectedCustomer(customer);
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
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Building2 className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-400">客户总数</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.active}</p>
              <p className="text-xs text-slate-400">活跃客户</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <Star className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.gradeA}</p>
              <p className="text-xs text-slate-400">A级客户</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.warning}</p>
              <p className="text-xs text-slate-400">需关注</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div
        variants={fadeIn}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
      >
        <div className="flex flex-wrap gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索客户名称、联系人..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          <select
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {gradeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {statusOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {industryOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">
            共 {filteredCustomers.length} 个客户
          </span>
          <div className="flex border border-white/10 rounded-lg overflow-hidden">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode("list")}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Customer Grid/List */}
      <motion.div variants={fadeIn}>
        {viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCustomers.map((customer) => (
              <CustomerCard
                key={customer.id}
                customer={customer}
                onClick={handleCustomerClick}
              />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      客户名称
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      等级
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      状态
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      行业
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      联系人
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">
                      累计金额
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">
                      待回款
                    </th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCustomers.map((customer) => {
                    const statusConf = statusConfig[customer.status];
                    return (
                      <tr
                        key={customer.id}
                        onClick={() => handleCustomerClick(customer)}
                        className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                              <Building2 className="w-4 h-4 text-primary" />
                            </div>
                            <div>
                              <div className="font-medium text-white">
                                {customer.shortName}
                              </div>
                              <div className="text-xs text-slate-500">
                                {customer.location}
                              </div>
                            </div>
                            {customer.isWarning && (
                              <AlertTriangle className="w-4 h-4 text-amber-500" />
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge
                            variant="outline"
                            className={gradeColors[customer.grade]}
                          >
                            {customer.grade}级
                          </Badge>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div
                              className={cn(
                                "w-2 h-2 rounded-full",
                                statusConf.color,
                              )}
                            />
                            <span
                              className={cn("text-sm", statusConf.textColor)}
                            >
                              {statusConf.label}
                            </span>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-400">
                          {customer.industry}
                        </td>
                        <td className="p-4">
                          <div className="text-sm text-white">
                            {customer.contactPerson}
                          </div>
                          <div className="text-xs text-slate-500">
                            {customer.phone}
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <span className="text-sm font-medium text-white">
                            ¥{(customer.totalAmount / 10000).toFixed(0)}万
                          </span>
                        </td>
                        <td className="p-4 text-right">
                          <span
                            className={cn(
                              "text-sm font-medium",
                              customer.pendingAmount > 0
                                ? "text-amber-400"
                                : "text-slate-500",
                            )}
                          >
                            ¥{(customer.pendingAmount / 10000).toFixed(0)}万
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex justify-center">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                >
                                  <MoreHorizontal className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Target className="w-4 h-4 mr-2" />
                                  新建商机
                                </DropdownMenuItem>
                                <DropdownMenuItem>
                                  <MessageSquare className="w-4 h-4 mr-2" />
                                  添加跟进
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem>
                                  <Edit className="w-4 h-4 mr-2" />
                                  编辑
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-red-400">
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  删除
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
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
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建客户</DialogTitle>
            <DialogDescription>
              创建新的客户档案，填写基本信息
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">公司全称 *</label>
              <Input placeholder="请输入公司全称" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">公司简称</label>
              <Input placeholder="请输入公司简称" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">客户等级</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="B">B级客户</option>
                <option value="A">A级客户</option>
                <option value="C">C级客户</option>
                <option value="D">D级客户</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">所属行业</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择行业</option>
                <option value="新能源电池">新能源电池</option>
                <option value="消费电子">消费电子</option>
                <option value="汽车零部件">汽车零部件</option>
                <option value="储能系统">储能系统</option>
                <option value="智能制造">智能制造</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">联系人</label>
              <Input placeholder="请输入联系人姓名" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">联系电话</label>
              <Input placeholder="请输入联系电话" />
            </div>
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">公司地址</label>
              <Input placeholder="请输入公司地址" />
            </div>
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">备注</label>
              <textarea
                placeholder="请输入备注信息"
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={() => setShowCreateDialog(false)}>创建客户</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}

// Customer Detail Side Panel
function CustomerDetailPanel({ customer, onClose }) {
  const statusConf = statusConfig[customer.status];

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-white">
                  {customer.shortName}
                </h2>
                <Badge
                  variant="outline"
                  className={gradeColors[customer.grade]}
                >
                  {customer.grade}级
                </Badge>
              </div>
              <p className="text-sm text-slate-400">{customer.name}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-white">
              ¥{(customer.totalAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400">累计金额</div>
          </div>
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-amber-400">
              ¥{(customer.pendingAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400">待回款</div>
          </div>
          <div className="text-center p-3 bg-surface-50 rounded-lg">
            <div className="text-lg font-semibold text-white">
              {customer.projectCount}
            </div>
            <div className="text-xs text-slate-400">项目数</div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">基本信息</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <MapPin className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">地址:</span>
              <span className="text-white">{customer.location}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Tag className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">行业:</span>
              <span className="text-white">{customer.industry}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className={cn("w-2 h-2 rounded-full", statusConf.color)} />
              <span className="text-slate-400">状态:</span>
              <span className={statusConf.textColor}>{statusConf.label}</span>
            </div>
          </div>
        </div>

        {/* Contact Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">联系方式</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <UserPlus className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">联系人:</span>
              <span className="text-white">{customer.contactPerson}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Phone className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">电话:</span>
              <span className="text-white">{customer.phone}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <Mail className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">邮箱:</span>
              <span className="text-white">{customer.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <History className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">最近联系:</span>
              <span className="text-white">{customer.lastContact}</span>
            </div>
          </div>
        </div>

        {/* Tags */}
        {customer.tags?.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">标签</h3>
            <div className="flex flex-wrap gap-2">
              {customer.tags.map((tag, index) => (
                <Badge key={index} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">快捷操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Target className="w-4 h-4 mr-2 text-blue-400" />
              新建商机
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <MessageSquare className="w-4 h-4 mr-2 text-green-400" />
              添加跟进
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <Calendar className="w-4 h-4 mr-2 text-purple-400" />
              安排拜访
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <DollarSign className="w-4 h-4 mr-2 text-amber-400" />
              查看回款
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button className="flex-1">
          <Edit className="w-4 h-4 mr-2" />
          编辑客户
        </Button>
      </div>
    </motion.div>
  );
}
