/**
 * Contract Detail Page - Comprehensive contract management view
 * Shows contract information, payment tracking, documents, and actions
 */

import { useState, useEffect, useMemo as _useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText,
  DollarSign,
  Calendar,
  User,
  Building2,
  Phone,
  Mail,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Download,
  Upload,
  Edit,
  Send,
  Archive,
  MoreVertical,
  ChevronRight,
  TrendingUp,
  Paperclip,
  Eye,
  Printer,
  Loader2,
  ArrowLeft } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { contractApi } from "../services/api";

// Mock contract detail data
// Mock data - 已移除，使用真实API
const PaymentStageBar = ({ payment, index, contractAmount }) => {
  const statusConfig = {
    paid: {
      color: "bg-emerald-500",
      textColor: "text-emerald-400",
      label: "已到账"
    },
    pending: {
      color: "bg-slate-500",
      textColor: "text-slate-400",
      label: "待收款"
    },
    overdue: {
      color: "bg-red-500",
      textColor: "text-red-400",
      label: "已逾期"
    }
  };

  const config = statusConfig[payment.status];
  const safeContractAmount = contractAmount || 1;

  return (
    <motion.div
      key={index}
      variants={fadeIn}
      className="flex items-center gap-4">

      {/* Percentage bar */}
      <div className="flex-1">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-200">
            {payment.type}
          </span>
          <span className={cn("text-sm font-bold", config.textColor)}>
            {formatCurrency(payment.amount)}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-700/50">
          <motion.div
            initial={{ width: 0 }}
            animate={{
              width: `${Math.min(payment.amount / safeContractAmount * 100, 100)}%`
            }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={cn("h-full transition-all", config.color)} />

        </div>
        <div className="mt-1 flex items-center justify-between">
          <Badge
            className={cn("text-xs", `bg-${config.color.split("-")[1]}-500/20`)}>

            {config.label}
          </Badge>
          <span className="text-xs text-slate-500">
            {payment.dueDate}
            {payment.status === "paid" && payment.paidDate &&
            <> / 实付: {payment.paidDate}</>
            }
          </span>
        </div>
      </div>
    </motion.div>);

};

const MilestoneTimeline = ({ milestones }) => {
  return (
    <div className="relative space-y-4">
      {(milestones || []).map((milestone, idx) =>
      <motion.div key={idx} variants={fadeIn} className="relative flex gap-4">
          {/* Timeline dot */}
          <div className="flex flex-col items-center">
            <div
            className={cn(
              "relative z-10 h-4 w-4 rounded-full border-2",
              milestone.status === "completed" ?
              "border-emerald-400 bg-emerald-500/20" :
              milestone.status === "in_progress" ?
              "border-blue-400 bg-blue-500/20" :
              "border-slate-600 bg-slate-700/20"
            )} />

            {idx < milestones.length - 1 &&
          <div
            className={cn(
              "mt-1 h-12 w-0.5",
              milestone.status === "completed" ?
              "bg-emerald-500/30" :
              "bg-slate-700/30"
            )} />

          }
          </div>

          {/* Content */}
          <div className="flex-1 pb-4">
            <div className="rounded-lg bg-slate-800/40 px-4 py-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-slate-100">
                  {milestone.name}
                </h4>
                {milestone.status === "completed" &&
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              }
              </div>
              <div className="mt-2 flex items-center gap-4 text-sm">
                <span className="text-slate-400">
                  计划: {formatDate(milestone.dueDate)}
                </span>
                {milestone.completedDate &&
              <span className="text-emerald-400">
                    完成: {formatDate(milestone.completedDate)}
              </span>
              }
              </div>
            </div>
          </div>
      </motion.div>
      )}
    </div>);

};

// 空合同数据模板
const emptyContract = {
  id: "",
  contractNo: "",
  contractName: "",
  customerName: "",
  status: "draft",
  contractAmount: 0,
  signedDate: null,
  startDate: null,
  endDate: null,
  paymentTerms: [],
  deliverables: [],
  milestones: [],
  documents: [],
  notes: ""
};

export default function ContractDetail() {
  const { id } = useParams();
  const _navigate = useNavigate();
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);
  const [contract, setContract] = useState(emptyContract);
  const [_activeTab, _setActiveTab] = useState("overview"); // overview | payments | deliverables | milestones | documents | notes
  const [_showEditDialog, setShowEditDialog] = useState(false);

  // Load contract data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await contractApi.get(id);
        if (res.data) {
          setContract({ ...emptyContract, ...res.data });
        }
      } catch (err) {
        console.error("Contract detail API error:", err);
        setError("加载合同详情失败");
      } finally {
        setLoading(false);
      }
    };
    if (id) {
      fetchData();
    } else {
      setLoading(false);
    }
  }, [id]);

  const statusConfig = {
    draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
    review: { label: "审批中", color: "bg-blue-500/20 text-blue-400" },
    signed: { label: "已签订", color: "bg-purple-500/20 text-purple-400" },
    active: { label: "执行中", color: "bg-emerald-500/20 text-emerald-400" },
    closed: { label: "已结案", color: "bg-slate-500/20 text-slate-400" },
    cancelled: { label: "已取消", color: "bg-red-500/20 text-red-400" }
  };

  const completedDeliverables = (contract.deliverables || []).filter(
    (d) => d.status === "completed"
  ).length;
  const completedMilestones = (contract.milestones || []).filter(
    (m) => m.status === "completed"
  ).length;

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title={contract.projectName}
        description={`${contract.customer.name} | ${contract.id}`}
        breadcrumb={[
        { label: "商务工作台", path: "/business-support" },
        { label: "合同管理", path: "/contracts" },
        { label: contract.projectName }]
        }
        action={{
          label: "编辑合同",
          icon: Edit,
          onClick: () => setShowEditDialog(true)
        }} />


      {/* Top Stats */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">合同状态</p>
              <Badge className={statusConfig[contract.status].color}>
                {statusConfig[contract.status].label}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">合同金额</p>
              <p className="text-2xl font-bold text-amber-400">
                {formatCurrency(contract.contractAmount)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">已回款</p>
              <p className="text-2xl font-bold text-emerald-400">
                {formatCurrency(contract.paidAmount)}
              </p>
              <p className="text-xs text-slate-500">
                {contract.paymentProgress}% 已到账
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">距截止日期</p>
              <p className="text-2xl font-bold text-cyan-400">
                {contract.daysRemaining}天
              </p>
              <p className="text-xs text-slate-500">{contract.endDate}</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Schedule */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>回款计划</span>
                <span className="text-sm font-normal text-slate-400">
                  {contract.paymentProgress}% 完成
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Progress
                value={contract.paymentProgress}
                className="h-3 bg-slate-700/50" />

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-4">

                {(contract.paymentPlan || []).map((payment, idx) =>
                <PaymentStageBar
                  key={idx}
                  payment={payment}
                  index={idx}
                  contractAmount={contract.contractAmount}
                />
                )}
              </motion.div>
            </CardContent>
          </Card>

          {/* Milestones Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>里程碑</span>
                <span className="text-sm font-normal text-slate-400">
                  {completedMilestones}/{contract.milestones?.length} 完成
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MilestoneTimeline milestones={contract.milestones} />
            </CardContent>
          </Card>

          {/* Deliverables */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>交付物清单</span>
                <span className="text-sm font-normal text-slate-400">
                  {completedDeliverables}/{contract.deliverables?.length}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-2">

                {(contract.deliverables || []).map((deliverable, idx) =>
                <motion.div
                  key={idx}
                  variants={fadeIn}
                  className="flex items-center justify-between rounded-lg bg-slate-800/40 px-4 py-3">

                    <span className="text-sm text-slate-200">
                      {deliverable.name}
                    </span>
                    <div className="flex items-center gap-2">
                      {deliverable.status === "completed" &&
                    <>
                          <span className="text-xs text-slate-500">
                            {deliverable.completedDate}
                          </span>
                          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    </>
                    }
                      {deliverable.status === "in_progress" &&
                    <>
                          <span className="text-xs text-slate-500">
                            截止: {deliverable.dueDate}
                          </span>
                          <Clock className="h-4 w-4 text-blue-400" />
                    </>
                    }
                      {deliverable.status === "pending" &&
                    <>
                          <span className="text-xs text-slate-500">
                            截止: {deliverable.dueDate}
                          </span>
                          <AlertTriangle className="h-4 w-4 text-slate-500" />
                    </>
                    }
                    </div>
                </motion.div>
                )}
              </motion.div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full justify-start gap-2">
                <Send className="h-4 w-4" />
                发送提醒
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Upload className="h-4 w-4" />
                上传文件
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Download className="h-4 w-4" />
                下载合同
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Printer className="h-4 w-4" />
                打印
              </Button>
            </CardContent>
          </Card>

          {/* Customer Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">客户信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-slate-400">公司名称</p>
                <p className="font-medium text-slate-200">
                  {contract.customer.name}
                </p>
              </div>
              <div>
                <p className="text-slate-400">法人代表</p>
                <p className="font-medium text-slate-200">
                  {contract.customer.legalPerson}
                </p>
              </div>
              <div>
                <p className="text-slate-400">联系方式</p>
                <div className="mt-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-slate-500" />
                    <p className="text-slate-200">
                      {contract.customer.contact.phone}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-slate-500" />
                    <p className="text-slate-200">
                      {contract.customer.contact.email}
                    </p>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-slate-400">地址</p>
                <p className="font-medium text-slate-200">
                  {contract.customer.address}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">附件</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(contract.documents || []).map((doc, idx) =>
              <motion.div
                key={idx}
                variants={fadeIn}
                className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2 text-xs transition-all hover:bg-slate-800/60">

                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <Paperclip className="h-3.5 w-3.5 flex-shrink-0 text-slate-500" />
                    <div className="min-w-0">
                      <p className="truncate text-slate-200">{doc.name}</p>
                      <p className="text-slate-500">{doc.size}</p>
                    </div>
                  </div>
                  <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 flex-shrink-0">

                    <Download className="h-3.5 w-3.5" />
                  </Button>
              </motion.div>
              )}
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 text-xs text-slate-400 hover:text-slate-100">

                <Upload className="h-3.5 w-3.5" />
                上传新文件
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>);

}
