/**
 * Customer 360 View - Issue 6.1: 客户360视图完善
 * 展示客户的全面信息：基本信息、历史订单、历史报价、历史合同、历史发票、回款记录、项目交付、满意度调查、服务记录
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Building2,
  FileText,
  DollarSign,
  Receipt,
  Package,
  CheckCircle2,
  Star,
  MessageSquare,
  TrendingUp,
  Calendar,
  User,
  Phone,
  Mail,
  MapPin,
  BarChart3,
  Target,
  Award,
  Activity,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Progress,
} from "../components/ui";
import { cn, formatDate, formatCurrency } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  customerApi,
  projectApi,
  opportunityApi,
  quoteApi,
  contractApi,
  invoiceApi,
} from "../services/api";
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";

export default function Customer360() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customer360, setCustomer360] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [customerPortrait, setCustomerPortrait] = useState(null);
  const [satisfactionSurveys, setSatisfactionSurveys] = useState([]);
  const [serviceRecords, setServiceRecords] = useState([]);
  const [loadingSatisfaction, setLoadingSatisfaction] = useState(false);
  const [loadingService, setLoadingService] = useState(false);

  // Load customer 360 data
  useEffect(() => {
    if (id) {
      loadCustomer360();
    }
  }, [id]);

  const loadCustomer360 = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await customerApi.get360(id);
      const data = response.data || response;
      setCustomer360(data);

      // Calculate customer portrait (Issue 6.1: 客户画像)
      calculateCustomerPortrait(data);

      // Load satisfaction surveys and service records
      loadSatisfactionSurveys();
      loadServiceRecords();
    } catch (err) {
      console.error("Failed to load customer 360:", err);
      setError(
        err.response?.data?.detail || err.message || "加载客户360视图失败",
      );
    } finally {
      setLoading(false);
    }
  };

  // Issue 6.1: 计算客户画像
  const calculateCustomerPortrait = (data) => {
    if (!data) return;

    const basicInfo = data.basic_info || {};
    const summary = data.summary || {};
    const projects = data.projects || [];
    const contracts = data.contracts || [];
    const invoices = data.invoices || [];

    // 计算合作年限
    let firstProjectDate = new Date(basicInfo.created_at || Date.now());
    if (projects.length > 0) {
      const firstProject = projects.reduce((earliest, p) => {
        const pDate =
          p.created_at || p.planned_start_date || basicInfo.created_at || "";
        const eDate =
          earliest.created_at ||
          earliest.planned_start_date ||
          basicInfo.created_at ||
          "";
        if (!pDate || !eDate) return earliest;
        return new Date(pDate) < new Date(eDate) ? p : earliest;
      });
      if (
        firstProject &&
        (firstProject.created_at || firstProject.planned_start_date)
      ) {
        firstProjectDate = new Date(
          firstProject.created_at || firstProject.planned_start_date,
        );
      }
    }
    const cooperationYears = Math.max(
      0,
      Math.floor((new Date() - firstProjectDate) / (1000 * 60 * 60 * 24 * 365)),
    );

    // 计算订单频率（每年订单数）
    const totalOrders = contracts.length;
    const orderFrequency =
      cooperationYears > 0
        ? (totalOrders / cooperationYears).toFixed(1)
        : totalOrders;

    // 计算平均订单金额
    const totalAmount = contracts.reduce(
      (sum, c) => sum + parseFloat(c.contract_amount || 0),
      0,
    );
    const avgOrderAmount = totalOrders > 0 ? totalAmount / totalOrders : 0;

    // 计算价值等级（基于总金额和订单频率）
    let valueLevel = "C";
    let valueLabel = "普通客户";
    if (totalAmount > 5000000 && orderFrequency > 2) {
      valueLevel = "A";
      valueLabel = "核心客户";
    } else if (totalAmount > 2000000 || orderFrequency > 1) {
      valueLevel = "B";
      valueLabel = "重要客户";
    }

    // 计算回款率
    const totalInvoiceAmount = invoices.reduce(
      (sum, i) => sum + parseFloat(i.total_amount || 0),
      0,
    );
    const paidAmount = invoices.reduce(
      (sum, i) => sum + parseFloat(i.paid_amount || 0),
      0,
    );
    const paymentRate =
      totalInvoiceAmount > 0
        ? ((paidAmount / totalInvoiceAmount) * 100).toFixed(1)
        : 0;

    setCustomerPortrait({
      valueLevel,
      valueLabel,
      cooperationYears,
      orderFrequency,
      avgOrderAmount,
      totalOrders,
      totalAmount,
      paymentRate,
    });
  };

  // Issue 6.1: 加载满意度调查
  const loadSatisfactionSurveys = async () => {
    if (!id) return;
    try {
      setLoadingSatisfaction(true);
      const response = await serviceApi.getCustomerSatisfactions({
        customer_id: id,
        page_size: 100,
      });
      const data = response.data?.items || response.data || response || [];
      setSatisfactionSurveys(data);
    } catch (err) {
      console.error("Failed to load satisfaction surveys:", err);
      setSatisfactionSurveys([]);
    } finally {
      setLoadingSatisfaction(false);
    }
  };

  // Issue 6.1: 加载服务记录
  const loadServiceRecords = async () => {
    if (!id) return;
    try {
      setLoadingService(true);
      const response = await serviceApi.getServiceRecords({
        customer_id: id,
        page_size: 100,
      });
      const data = response.data?.items || response.data || response || [];
      setServiceRecords(data);
    } catch (err) {
      console.error("Failed to load service records:", err);
      setServiceRecords([]);
    } finally {
      setLoadingService(false);
    }
  };

  if (loading && !customer360) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <LoadingCard rows={8} />
      </div>
    );
  }

  if (error && !customer360) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <ErrorMessage error={error} onRetry={loadCustomer360} />
      </div>
    );
  }

  if (!customer360) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <EmptyState message="客户不存在" />
      </div>
    );
  }

  const basicInfo = customer360.basic_info || {};
  const summary = customer360.summary || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 py-6 space-y-6"
      >
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              返回
            </Button>
            <PageHeader
              title={basicInfo.customer_name || "客户360视图"}
              description={`客户编码: ${basicInfo.customer_code || "-"} | 行业: ${basicInfo.industry || "-"}`}
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadCustomer360}
            className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>
        </div>

        {/* Summary Cards */}
        <motion.div
          variants={fadeIn}
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400">项目总数</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {summary.total_projects || 0}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    活跃: {summary.active_projects || 0}
                  </p>
                </div>
                <Package className="w-8 h-8 text-blue-400/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400">在途金额</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1">
                    {formatCurrency(summary.pipeline_amount || 0)}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-amber-400/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400">累计签约</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {formatCurrency(summary.total_contract_amount || 0)}
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-emerald-400/50" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-500/10 to-rose-500/5 border-red-500/20">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400">未回款</p>
                  <p className="text-2xl font-bold text-red-400 mt-1">
                    {formatCurrency(summary.open_receivables || 0)}
                  </p>
                </div>
                <Receipt className="w-8 h-8 text-red-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Customer Portrait - Issue 6.1: 客户画像 */}
        {customerPortrait && (
          <motion.div variants={fadeIn}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  客户画像
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">价值等级</div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          customerPortrait.valueLevel === "A"
                            ? "default"
                            : customerPortrait.valueLevel === "B"
                              ? "secondary"
                              : "outline"
                        }
                        className={cn(
                          customerPortrait.valueLevel === "A" &&
                            "bg-emerald-500",
                          customerPortrait.valueLevel === "B" && "bg-amber-500",
                        )}
                      >
                        {customerPortrait.valueLevel}
                      </Badge>
                      <span className="text-sm font-medium text-white">
                        {customerPortrait.valueLabel}
                      </span>
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">合作年限</div>
                    <div className="text-2xl font-bold text-white">
                      {customerPortrait.cooperationYears}年
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">订单频率</div>
                    <div className="text-2xl font-bold text-white">
                      {customerPortrait.orderFrequency}次/年
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">
                      平均订单金额
                    </div>
                    <div className="text-xl font-bold text-white">
                      {formatCurrency(customerPortrait.avgOrderAmount)}
                    </div>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">
                      累计订单数
                    </div>
                    <div className="text-lg font-semibold text-white">
                      {customerPortrait.totalOrders}个
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">
                      累计签约金额
                    </div>
                    <div className="text-lg font-semibold text-white">
                      {formatCurrency(customerPortrait.totalAmount)}
                    </div>
                  </div>
                  <div className="p-4 rounded-lg bg-surface-50">
                    <div className="text-xs text-slate-400 mb-1">回款率</div>
                    <div className="flex items-center gap-2">
                      <Progress
                        value={parseFloat(customerPortrait.paymentRate)}
                        className="flex-1"
                      />
                      <span className="text-lg font-semibold text-white">
                        {customerPortrait.paymentRate}%
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Tabs - Issue 6.1: 标签页 */}
        <motion.div variants={fadeIn}>
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-5 lg:grid-cols-11">
              <TabsTrigger value="overview">概览</TabsTrigger>
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="projects">项目交付</TabsTrigger>
              <TabsTrigger value="opportunities">关联商机</TabsTrigger>
              <TabsTrigger value="quotes">历史报价</TabsTrigger>
              <TabsTrigger value="contracts">历史合同</TabsTrigger>
              <TabsTrigger value="invoices">历史发票</TabsTrigger>
              <TabsTrigger value="payments">回款记录</TabsTrigger>
              <TabsTrigger value="satisfaction">满意度调查</TabsTrigger>
              <TabsTrigger value="service">服务记录</TabsTrigger>
              <TabsTrigger value="communications">沟通记录</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Projects Overview */}
                <Card>
                  <CardHeader>
                    <CardTitle>项目概览</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {(customer360.projects || []).slice(0, 5).map((project) => (
                      <div
                        key={project.project_id}
                        className="p-3 rounded-lg bg-surface-50 hover:bg-surface-100 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-white">
                            {project.project_name || project.project_code}
                          </span>
                          <Badge variant="outline">
                            {project.status || "-"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-xs text-slate-400">
                          <span>进度 {project.progress_pct || 0}%</span>
                          <span>
                            {formatCurrency(project.contract_amount || 0)}
                          </span>
                        </div>
                        {project.planned_end_date && (
                          <div className="text-xs text-slate-500 mt-1">
                            计划完成: {formatDate(project.planned_end_date)}
                          </div>
                        )}
                      </div>
                    ))}
                    {(customer360.projects || []).length === 0 && (
                      <EmptyState message="暂无项目记录" />
                    )}
                  </CardContent>
                </Card>

                {/* Opportunities Overview */}
                <Card>
                  <CardHeader>
                    <CardTitle>关联商机</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {(customer360.opportunities || [])
                      .slice(0, 5)
                      .map((opportunity) => (
                        <div
                          key={opportunity.opportunity_id}
                          className="p-3 rounded-lg bg-surface-50 hover:bg-surface-100 transition-colors"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-white">
                              {opportunity.opp_name || opportunity.opp_code}
                            </span>
                            <Badge variant="outline">
                              {opportunity.stage || "-"}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>{opportunity.owner_name || "-"}</span>
                            <span>
                              {formatCurrency(opportunity.est_amount || 0)}
                            </span>
                          </div>
                          {opportunity.win_probability !== undefined && (
                            <div className="mt-1">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-slate-500">赢单概率</span>
                                <span className="text-white">
                                  {opportunity.win_probability}%
                                </span>
                              </div>
                              <Progress
                                value={opportunity.win_probability}
                                className="h-1.5"
                              />
                            </div>
                          )}
                        </div>
                      ))}
                    {(customer360.opportunities || []).length === 0 && (
                      <EmptyState message="暂无商机数据" />
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Basic Info Tab */}
            <TabsContent value="basic" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>基本信息</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <label className="text-xs text-slate-400">
                          客户编码
                        </label>
                        <p className="text-white font-medium">
                          {basicInfo.customer_code || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">
                          客户名称
                        </label>
                        <p className="text-white font-medium">
                          {basicInfo.customer_name || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">简称</label>
                        <p className="text-white">
                          {basicInfo.customer_short_name || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">行业</label>
                        <p className="text-white">
                          {basicInfo.industry || "-"}
                        </p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label className="text-xs text-slate-400 flex items-center gap-2">
                          <Phone className="w-3 h-3" />
                          联系电话
                        </label>
                        <p className="text-white">
                          {basicInfo.contact_phone || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 flex items-center gap-2">
                          <Mail className="w-3 h-3" />
                          联系邮箱
                        </label>
                        <p className="text-white">
                          {basicInfo.contact_email || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 flex items-center gap-2">
                          <User className="w-3 h-3" />
                          联系人
                        </label>
                        <p className="text-white">
                          {basicInfo.contact_person || "-"}
                        </p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 flex items-center gap-2">
                          <MapPin className="w-3 h-3" />
                          地址
                        </label>
                        <p className="text-white">{basicInfo.address || "-"}</p>
                      </div>
                    </div>
                  </div>
                  {basicInfo.remark && (
                    <div className="mt-6">
                      <label className="text-xs text-slate-400">备注</label>
                      <p className="text-white mt-1">{basicInfo.remark}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Projects Tab */}
            <TabsContent value="projects" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>项目交付</CardTitle>
                  <CardDescription>客户的所有项目记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.projects || []).map((project) => (
                      <div
                        key={project.project_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {project.project_name || project.project_code}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              项目编码: {project.project_code}
                            </p>
                          </div>
                          <Badge variant="outline">
                            {project.status || "-"}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              阶段
                            </label>
                            <p className="text-sm text-white">
                              {project.stage || "-"}
                            </p>
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">
                              进度
                            </label>
                            <div className="flex items-center gap-2">
                              <Progress
                                value={project.progress_pct || 0}
                                className="flex-1"
                              />
                              <span className="text-sm text-white">
                                {project.progress_pct || 0}%
                              </span>
                            </div>
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">
                              合同金额
                            </label>
                            <p className="text-sm text-white">
                              {formatCurrency(project.contract_amount || 0)}
                            </p>
                          </div>
                          {project.planned_end_date && (
                            <div>
                              <label className="text-xs text-slate-400">
                                计划完成
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(project.planned_end_date)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.projects || []).length === 0 && (
                      <EmptyState message="暂无项目记录" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Opportunities Tab */}
            <TabsContent value="opportunities" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>关联商机</CardTitle>
                  <CardDescription>客户的所有商机记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.opportunities || []).map((opportunity) => (
                      <div
                        key={opportunity.opportunity_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {opportunity.opp_name || opportunity.opp_code}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              商机编码: {opportunity.opp_code}
                            </p>
                          </div>
                          <Badge variant="outline">
                            {opportunity.stage || "-"}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              负责人
                            </label>
                            <p className="text-sm text-white">
                              {opportunity.owner_name || "-"}
                            </p>
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">
                              预估金额
                            </label>
                            <p className="text-sm text-white">
                              {formatCurrency(opportunity.est_amount || 0)}
                            </p>
                          </div>
                          {opportunity.win_probability !== undefined && (
                            <div>
                              <label className="text-xs text-slate-400">
                                赢单概率
                              </label>
                              <div className="flex items-center gap-2">
                                <Progress
                                  value={opportunity.win_probability}
                                  className="flex-1"
                                />
                                <span className="text-sm text-white">
                                  {opportunity.win_probability}%
                                </span>
                              </div>
                            </div>
                          )}
                          {opportunity.updated_at && (
                            <div>
                              <label className="text-xs text-slate-400">
                                更新时间
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(opportunity.updated_at)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.opportunities || []).length === 0 && (
                      <EmptyState message="暂无商机数据" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Quotes Tab */}
            <TabsContent value="quotes" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>历史报价</CardTitle>
                  <CardDescription>客户的所有报价记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.quotes || []).map((quote) => (
                      <div
                        key={quote.quote_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {quote.quote_code}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              负责人: {quote.owner_name || "-"}
                            </p>
                          </div>
                          <Badge variant="outline">{quote.status || "-"}</Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              报价金额
                            </label>
                            <p className="text-sm text-white">
                              {formatCurrency(quote.total_price || 0)}
                            </p>
                          </div>
                          {quote.gross_margin !== undefined && (
                            <div>
                              <label className="text-xs text-slate-400">
                                毛利率
                              </label>
                              <p className="text-sm text-white">
                                {quote.gross_margin}%
                              </p>
                            </div>
                          )}
                          {quote.valid_until && (
                            <div>
                              <label className="text-xs text-slate-400">
                                有效期至
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(quote.valid_until)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.quotes || []).length === 0 && (
                      <EmptyState message="暂无报价记录" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Contracts Tab */}
            <TabsContent value="contracts" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>历史合同</CardTitle>
                  <CardDescription>客户的所有合同记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.contracts || []).map((contract) => (
                      <div
                        key={contract.contract_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {contract.contract_code}
                            </h4>
                            {contract.project_code && (
                              <p className="text-xs text-slate-400 mt-1">
                                项目: {contract.project_code}
                              </p>
                            )}
                          </div>
                          <Badge variant="outline">
                            {contract.status || "-"}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              合同金额
                            </label>
                            <p className="text-sm text-white font-semibold">
                              {formatCurrency(contract.contract_amount || 0)}
                            </p>
                          </div>
                          {contract.signed_date && (
                            <div>
                              <label className="text-xs text-slate-400">
                                签订日期
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(contract.signed_date)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.contracts || []).length === 0 && (
                      <EmptyState message="暂无合同记录" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Invoices Tab */}
            <TabsContent value="invoices" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>历史发票</CardTitle>
                  <CardDescription>客户的所有发票记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.invoices || []).map((invoice) => (
                      <div
                        key={invoice.invoice_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {invoice.invoice_code}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              状态: {invoice.status || "-"}
                            </p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              发票金额
                            </label>
                            <p className="text-sm text-white font-semibold">
                              {formatCurrency(invoice.total_amount || 0)}
                            </p>
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">
                              已收金额
                            </label>
                            <p className="text-sm text-emerald-400">
                              {formatCurrency(invoice.paid_amount || 0)}
                            </p>
                          </div>
                          {invoice.issue_date && (
                            <div>
                              <label className="text-xs text-slate-400">
                                开票日期
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(invoice.issue_date)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.invoices || []).length === 0 && (
                      <EmptyState message="暂无发票记录" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Payments Tab */}
            <TabsContent value="payments" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>回款记录</CardTitle>
                  <CardDescription>客户的收款计划记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.payment_plans || []).map((plan) => (
                      <div
                        key={plan.plan_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {plan.payment_name || "收款计划"}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              项目ID: {plan.project_id || "-"}
                            </p>
                          </div>
                          <Badge
                            variant={
                              plan.status === "COMPLETED"
                                ? "default"
                                : plan.status === "PENDING"
                                  ? "secondary"
                                  : "outline"
                            }
                            className={cn(
                              plan.status === "COMPLETED" && "bg-emerald-500",
                              plan.status === "PENDING" && "bg-amber-500",
                            )}
                          >
                            {plan.status === "COMPLETED"
                              ? "已完成"
                              : plan.status === "PENDING"
                                ? "待收款"
                                : plan.status || "-"}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <label className="text-xs text-slate-400">
                              计划金额
                            </label>
                            <p className="text-sm text-white font-semibold">
                              {formatCurrency(plan.planned_amount || 0)}
                            </p>
                          </div>
                          <div>
                            <label className="text-xs text-slate-400">
                              已收金额
                            </label>
                            <p className="text-sm text-emerald-400">
                              {formatCurrency(plan.actual_amount || 0)}
                            </p>
                          </div>
                          {plan.planned_date && (
                            <div>
                              <label className="text-xs text-slate-400">
                                计划日期
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(plan.planned_date)}
                              </p>
                            </div>
                          )}
                          {plan.actual_date && (
                            <div>
                              <label className="text-xs text-slate-400">
                                实际日期
                              </label>
                              <p className="text-sm text-white">
                                {formatDate(plan.actual_date)}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {(customer360.payment_plans || []).length === 0 && (
                      <EmptyState message="暂无收款计划" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Satisfaction Survey Tab - Issue 6.1: 满意度调查 */}
            <TabsContent value="satisfaction" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>满意度调查</CardTitle>
                  <CardDescription>客户满意度调查记录</CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingSatisfaction ? (
                    <div className="text-center py-8 text-slate-400">
                      加载中...
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {satisfactionSurveys.map((survey) => (
                        <div
                          key={survey.id}
                          className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">
                                {survey.survey_no || "满意度调查"}
                              </h4>
                              <p className="text-xs text-slate-400 mt-1">
                                {survey.project_name || "-"} |{" "}
                                {survey.survey_type || "-"}
                              </p>
                            </div>
                            <Badge variant="outline">
                              {survey.status || "-"}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                            {survey.survey_date && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  调查日期
                                </label>
                                <p className="text-sm text-white">
                                  {formatDate(survey.survey_date)}
                                </p>
                              </div>
                            )}
                            {survey.overall_score !== undefined && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  总体评分
                                </label>
                                <div className="flex items-center gap-2">
                                  <Star className="w-4 h-4 text-amber-400" />
                                  <span className="text-sm text-white font-semibold">
                                    {survey.overall_score}/5
                                  </span>
                                </div>
                              </div>
                            )}
                            {survey.customer_contact && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  联系人
                                </label>
                                <p className="text-sm text-white">
                                  {survey.customer_contact}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {satisfactionSurveys.length === 0 && (
                        <EmptyState message="暂无满意度调查记录" />
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Service Records Tab - Issue 6.1: 服务记录 */}
            <TabsContent value="service" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>服务记录</CardTitle>
                  <CardDescription>客户服务记录和工单</CardDescription>
                </CardHeader>
                <CardContent>
                  {loadingService ? (
                    <div className="text-center py-8 text-slate-400">
                      加载中...
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {serviceRecords.map((record) => (
                        <div
                          key={record.id}
                          className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">
                                {record.record_no || "服务记录"}
                              </h4>
                              <p className="text-xs text-slate-400 mt-1">
                                {record.service_type || "-"} |{" "}
                                {record.service_engineer_name || "-"}
                              </p>
                            </div>
                            <Badge variant="outline">
                              {record.status || "-"}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                            {record.service_date && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  服务日期
                                </label>
                                <p className="text-sm text-white">
                                  {formatDate(record.service_date)}
                                </p>
                              </div>
                            )}
                            {record.duration_hours && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  服务时长
                                </label>
                                <p className="text-sm text-white">
                                  {record.duration_hours}小时
                                </p>
                              </div>
                            )}
                            {record.customer_satisfaction !== undefined && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  满意度
                                </label>
                                <div className="flex items-center gap-2">
                                  <Star className="w-4 h-4 text-amber-400" />
                                  <span className="text-sm text-white">
                                    {record.customer_satisfaction}/5
                                  </span>
                                </div>
                              </div>
                            )}
                            {record.location && (
                              <div>
                                <label className="text-xs text-slate-400">
                                  服务地点
                                </label>
                                <p className="text-sm text-white">
                                  {record.location}
                                </p>
                              </div>
                            )}
                          </div>
                          {record.service_content && (
                            <p className="text-sm text-slate-300 mt-2">
                              {record.service_content}
                            </p>
                          )}
                        </div>
                      ))}
                      {serviceRecords.length === 0 && (
                        <EmptyState message="暂无服务记录" />
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Communications Tab */}
            <TabsContent value="communications" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>沟通记录</CardTitle>
                  <CardDescription>与客户的所有沟通记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(customer360.communications || []).map((comm) => (
                      <div
                        key={comm.communication_id}
                        className="p-4 rounded-lg bg-surface-50 border border-surface-200"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-white">
                              {comm.topic || "沟通记录"}
                            </h4>
                            <p className="text-xs text-slate-400 mt-1">
                              {comm.owner_name || "-"} |{" "}
                              {comm.communication_type || "-"}
                            </p>
                          </div>
                          {comm.communication_date && (
                            <span className="text-xs text-slate-500">
                              {formatDate(comm.communication_date)}
                            </span>
                          )}
                        </div>
                        {comm.content && (
                          <p className="text-sm text-slate-300 mt-2">
                            {comm.content}
                          </p>
                        )}
                      </div>
                    ))}
                    {(customer360.communications || []).length === 0 && (
                      <EmptyState message="暂无沟通记录" />
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </motion.div>
    </div>
  );
}
