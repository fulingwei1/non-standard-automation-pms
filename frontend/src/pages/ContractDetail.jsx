/**
 * Contract Detail Page - Comprehensive contract management view
 * Shows contract information, payment tracking, documents, and actions
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Phone,
  Mail,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Download,
  ExternalLink,
  Upload,
  Edit,
  FilePlus2,
  Send,
  Paperclip,
  Printer,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { contractApi, paymentPlanApi, pmoApi } from "../services/api";
import {
  buildContractInitiationPath,
  pickExistingInitiationByContractNo,
} from "../utils/pmoInitiations";

// Mock contract detail data
// Mock data - 已移除，使用真实API
const PaymentStageBar = ({ payment, contractAmount }) => {
  const statusConfig = {
    paid: {
      color: "bg-emerald-500",
      textColor: "text-emerald-400",
      badgeColor: "bg-emerald-500/20 text-emerald-300",
      label: "已到账"
    },
    pending: {
      color: "bg-slate-500",
      textColor: "text-slate-400",
      badgeColor: "bg-slate-500/20 text-slate-300",
      label: "待收款"
    },
    overdue: {
      color: "bg-red-500",
      textColor: "text-red-400",
      badgeColor: "bg-red-500/20 text-red-300",
      label: "已逾期"
    }
  };

  const config = statusConfig[payment.status] || statusConfig.pending;
  const safeContractAmount = contractAmount || 1;

  return (
    <motion.div
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
          <Badge className={cn("text-xs", config.badgeColor)}>
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
  projectName: "",
  customerName: "",
  customer: {
    name: "",
    legalPerson: "",
    contact: {
      phone: "",
      email: "",
    },
    address: "",
  },
  status: "draft",
  contractAmount: 0,
  paidAmount: 0,
  paymentProgress: 0,
  daysRemaining: null,
  signedDate: null,
  startDate: null,
  endDate: null,
  project_id: null,
  project_code: null,
  paymentTerms: [],
  paymentPlan: [],
  deliverables: [],
  milestones: [],
  documents: [],
  notes: ""
};

const statusConfig = {
  draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
  review: { label: "审批中", color: "bg-blue-500/20 text-blue-400" },
  in_review: { label: "审批中", color: "bg-blue-500/20 text-blue-400" },
  signed: { label: "已签订", color: "bg-purple-500/20 text-purple-400" },
  active: { label: "执行中", color: "bg-emerald-500/20 text-emerald-400" },
  executing: { label: "执行中", color: "bg-emerald-500/20 text-emerald-400" },
  completed: { label: "已完成", color: "bg-emerald-500/20 text-emerald-400" },
  closed: { label: "已结案", color: "bg-slate-500/20 text-slate-400" },
  cancelled: { label: "已取消", color: "bg-red-500/20 text-red-400" },
};

const initiationStatusConfig = {
  DRAFT: { label: "立项草稿", color: "bg-slate-500/20 text-slate-300" },
  SUBMITTED: { label: "待PMO审批", color: "bg-amber-500/20 text-amber-300" },
  REVIEWING: { label: "审批中", color: "bg-blue-500/20 text-blue-300" },
  IN_REVIEW: { label: "审批中", color: "bg-blue-500/20 text-blue-300" },
  APPROVED: { label: "立项通过", color: "bg-emerald-500/20 text-emerald-300" },
  REJECTED: { label: "已驳回", color: "bg-red-500/20 text-red-300" },
  CANCELLED: { label: "已取消", color: "bg-slate-500/20 text-slate-300" },
};

const getResponsePayload = (response) => response?.data?.data ?? response?.data ?? response ?? {};

const getPaginatedItems = (response) => {
  const payload = getResponsePayload(response);
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
};

const toNumber = (value) => {
  const number = Number(value ?? 0);
  return Number.isFinite(number) ? number : 0;
};

const normalizeStatus = (value) => String(value || "draft").toLowerCase();

const getDaysRemaining = (dateValue) => {
  if (!dateValue) {
    return null;
  }
  const endDate = new Date(dateValue);
  if (Number.isNaN(endDate.getTime())) {
    return null;
  }
  const today = new Date();
  endDate.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return Math.ceil((endDate.getTime() - today.getTime()) / 86400000);
};

const normalizePaymentStatus = (status, plannedDate) => {
  const normalized = String(status || "").toUpperCase();
  if (["PAID", "COMPLETED", "RECEIVED"].includes(normalized)) {
    return "paid";
  }
  if (["OVERDUE", "DELAYED"].includes(normalized)) {
    return "overdue";
  }
  if (plannedDate) {
    const date = new Date(plannedDate);
    if (!Number.isNaN(date.getTime()) && date < new Date()) {
      return "overdue";
    }
  }
  return "pending";
};

const normalizePaymentPlan = (plan) => ({
  id: plan.id,
  type: plan.payment_name || plan.payment_stage || plan.payment_type || `第${plan.payment_no || ""}期`,
  amount: toNumber(plan.planned_amount ?? plan.amount),
  actualAmount: toNumber(plan.actual_amount ?? plan.paid_amount),
  dueDate: plan.planned_date || plan.due_date || "",
  paidDate: plan.actual_date || plan.paid_date || "",
  status: normalizePaymentStatus(plan.status, plan.planned_date || plan.due_date),
});

const normalizeContract = (raw = {}) => {
  const customer = raw.customer || {};
  const contractAmount = toNumber(raw.contract_amount ?? raw.total_amount ?? raw.amount ?? raw.contractAmount);
  const paidAmount = toNumber(raw.paid_amount ?? raw.paidAmount ?? raw.received_amount);
  const endDate = raw.end_date || raw.delivery_deadline || raw.endDate || null;
  const paymentProgress =
    contractAmount > 0 ? Math.min(100, Math.round((paidAmount / contractAmount) * 100)) : toNumber(raw.payment_progress ?? raw.paymentProgress);

  return {
    ...emptyContract,
    ...raw,
    contractNo: raw.contract_code || raw.contract_no || raw.contractNo || raw.customer_contract_no || String(raw.id || ""),
    contractName: raw.contract_name || raw.contractName || raw.project_name || raw.projectName || raw.contract_code || `合同-${raw.id}`,
    projectName: raw.project_name || raw.projectName || raw.contract_name || raw.contract_code || `合同-${raw.id}`,
    customerName: raw.customer_name || raw.customerName || customer.customer_name || customer.name || "未关联客户",
    customer: {
      name: raw.customer_name || raw.customerName || customer.customer_name || customer.name || "未关联客户",
      legalPerson: customer.legal_person || customer.legalPerson || raw.legal_person || "-",
      contact: {
        phone: customer.phone || customer.contact_phone || raw.customer_phone || "-",
        email: customer.email || customer.contact_email || raw.customer_email || "-",
      },
      address: customer.address || raw.customer_address || "-",
    },
    status: normalizeStatus(raw.status),
    contractAmount,
    paidAmount,
    paymentProgress,
    signedDate: raw.signed_date || raw.signing_date || raw.signedDate || null,
    startDate: raw.start_date || raw.startDate || null,
    endDate,
    daysRemaining: getDaysRemaining(endDate),
    project_id: raw.project_id || raw.projectId || null,
    project_code: raw.project_code || raw.projectCode || null,
    paymentPlan: Array.isArray(raw.paymentPlan) ? raw.paymentPlan.map(normalizePaymentPlan) : [],
  };
};

const findExistingInitiationByContractNo = async (contractNo) => {
  if (!contractNo) {
    return null;
  }

  const response = await pmoApi.initiations.list({
    contract_no: String(contractNo),
    page: 1,
    page_size: 20,
  });
  return pickExistingInitiationByContractNo(getPaginatedItems(response), contractNo);
};

const FlowStep = ({ title, value, done, warning }) => (
  <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4">
    <div className="mb-3 flex items-center justify-between gap-3">
      <p className="text-sm text-slate-400">{title}</p>
      {done ? (
        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
      ) : warning ? (
        <AlertTriangle className="h-4 w-4 text-amber-400" />
      ) : (
        <Clock className="h-4 w-4 text-slate-500" />
      )}
    </div>
    <p className="text-base font-semibold text-slate-100">{value}</p>
  </div>
);

export default function ContractDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [contract, setContract] = useState(emptyContract);
  const [linkedInitiation, setLinkedInitiation] = useState(null);
  const [paymentPlans, setPaymentPlans] = useState([]);
  const [workflowWarning, setWorkflowWarning] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [_activeTab, _setActiveTab] = useState("overview"); // overview | payments | deliverables | milestones | documents | notes
  const [_showEditDialog, setShowEditDialog] = useState(false);

  // Load contract data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setWorkflowWarning(null);
      try {
        const res = await contractApi.get(id);
        const rawContract = getResponsePayload(res);
        const normalizedContract = normalizeContract(rawContract);

        const [initiationResult, paymentPlanResult] = await Promise.allSettled([
          findExistingInitiationByContractNo(normalizedContract.contractNo),
          contractApi.getPaymentPlans
            ? contractApi.getPaymentPlans(id)
            : paymentPlanApi.list({ contract_id: id, page: 1, page_size: 100 }),
        ]);

        if (initiationResult.status === "fulfilled") {
          setLinkedInitiation(initiationResult.value);
        } else {
          setLinkedInitiation(null);
          setWorkflowWarning("立项状态加载失败");
        }

        let normalizedPlans = [];
        if (paymentPlanResult.status === "fulfilled") {
          normalizedPlans = getPaginatedItems(paymentPlanResult.value).map(normalizePaymentPlan);
          setPaymentPlans(normalizedPlans);
        } else {
          setPaymentPlans([]);
          setWorkflowWarning((prev) => [prev, "收款计划加载失败"].filter(Boolean).join("；"));
        }

        setContract({
          ...normalizedContract,
          paymentPlan: normalizedPlans.length > 0 ? normalizedPlans : normalizedContract.paymentPlan,
        });
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

  const hasProject = Boolean(contract.project_id || contract.projectId || contract.project_code);
  const canCreateInitiation = ["signed", "active", "executing", "completed"].includes(contract.status) && !hasProject;
  const contractStatus = statusConfig[contract.status] || statusConfig.draft;
  const initiationStatus = initiationStatusConfig[String(linkedInitiation?.status || "").toUpperCase()];
  const paymentPlanItems = paymentPlans.length > 0 ? paymentPlans : contract.paymentPlan || [];

  const handleCreateInitiation = async () => {
    if (!contract.contractNo) {
      setWorkflowWarning("合同编号为空，不能发起立项");
      return;
    }

    setActionLoading(true);
    setWorkflowWarning(null);
    try {
      const existing = await findExistingInitiationByContractNo(contract.contractNo);
      if (existing) {
        setLinkedInitiation(existing);
        navigate(`/pmo/initiations/${existing.id}`);
        return;
      }

      navigate(buildContractInitiationPath(contract));
    } catch (err) {
      console.error("Create PMO initiation from contract failed:", err);
      setWorkflowWarning(err?.response?.data?.detail || err.message || "发起立项失败");
    } finally {
      setActionLoading(false);
    }
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
        title={contract.contractName || contract.contractNo || `合同-${id}`}
        description={`${contract.customerName || "未关联客户"} | ${contract.contractNo || id}`}
        breadcrumb={[
        { label: "技术方案", path: "/presales/technical-solutions" },
        { label: "合同管理", path: "/sales/contracts" },
        { label: contract.contractName || contract.contractNo }]
        }
        action={{
          label: "编辑合同",
          icon: Edit,
          onClick: () => setShowEditDialog(true)
        }} />

      {loading && (
        <div className="rounded-md border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-300">
          正在加载合同详情...
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {workflowWarning && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          {workflowWarning}
        </div>
      )}


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
              <Badge className={contractStatus.color}>
                {contractStatus.label}
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
                {contract.daysRemaining === null ? "-" : `${contract.daysRemaining}天`}
              </p>
              <p className="text-xs text-slate-500">{contract.endDate}</p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-3">
            <span>项目/回款闭环</span>
            {linkedInitiation && initiationStatus && (
              <Badge className={initiationStatus.color}>{initiationStatus.label}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            <FlowStep
              title="合同"
              value={contractStatus.label}
              done={["signed", "active", "executing", "completed"].includes(contract.status)}
            />
            <FlowStep
              title="PMO立项"
              value={
                linkedInitiation
                  ? initiationStatus?.label || linkedInitiation.status || "已发起"
                  : canCreateInitiation
                    ? "待发起"
                    : "未到立项"
              }
              done={Boolean(linkedInitiation)}
              warning={canCreateInitiation && !linkedInitiation}
            />
            <FlowStep
              title="项目"
              value={hasProject ? contract.project_code || `项目 #${contract.project_id}` : "待创建"}
              done={hasProject}
              warning={Boolean(linkedInitiation) && !hasProject}
            />
            <FlowStep
              title="收款计划"
              value={`${paymentPlanItems.length} 条`}
              done={paymentPlanItems.length > 0}
              warning={hasProject && paymentPlanItems.length === 0}
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {linkedInitiation ? (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(`/pmo/initiations/${linkedInitiation.id}`)}
              >
                <ExternalLink className="h-4 w-4" />
                查看立项
              </Button>
            ) : (
              canCreateInitiation && (
                <Button
                  className="gap-2"
                  onClick={handleCreateInitiation}
                  disabled={actionLoading}
                >
                  <FilePlus2 className="h-4 w-4" />
                  发起立项
                </Button>
              )
            )}
            {hasProject && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(`/projects/${contract.project_id || contract.projectId}`)}
              >
                <ExternalLink className="h-4 w-4" />
                查看项目
              </Button>
            )}
            {paymentPlanItems.length > 0 && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => navigate(`/sales/receivables?contract_id=${contract.id}`)}
              >
                <ExternalLink className="h-4 w-4" />
                查看回款
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

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

                {paymentPlanItems.length === 0 && (
                  <div className="rounded-md border border-slate-800 bg-slate-900/60 px-4 py-6 text-center text-sm text-slate-400">
                    暂无收款计划
                  </div>
                )}

                {paymentPlanItems.map((payment, idx) =>
                <PaymentStageBar
                  key={idx}
                  payment={payment}
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
