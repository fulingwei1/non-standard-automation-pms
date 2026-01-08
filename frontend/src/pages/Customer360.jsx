/**
 * Customer 360 View - Comprehensive customer information dashboard
 * Issue 6.1: 客户360视图完善
 * Features: Basic info, Orders, Quotes, Contracts, Invoices, Payments, Projects, Satisfaction, Service Records
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  Building2,
  FileText,
  DollarSign,
  Receipt,
  Package,
  TrendingUp,
  Calendar,
  Users,
  Star,
  MessageSquare,
  Settings,
  BarChart3,
  Target,
  Clock,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui'
import { cn, formatDate, formatCurrency } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { customerApi, projectApi, quoteApi, contractApi, invoiceApi } from '../services/api'

export default function Customer360() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [customer360, setCustomer360] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('basic')
  const [customerProfile, setCustomerProfile] = useState(null)

  useEffect(() => {
    if (id) {
      loadCustomer360()
    }
  }, [id])

  const loadCustomer360 = async () => {
    try {
      setLoading(true)
      const response = await customerApi.get360(parseInt(id))
      const data = response.data || response
      setCustomer360(data)
      
      // Calculate customer profile (Issue 6.1: 客户画像)
      if (data) {
        const profile = calculateCustomerProfile(data)
        setCustomerProfile(profile)
      }
    } catch (error) {
      console.error('加载客户360失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // Issue 6.1: 计算客户画像
  const calculateCustomerProfile = (data) => {
    const summary = data.summary || {}
    const projects = data.projects || []
    const contracts = data.contracts || []
    const quotes = data.quotes || []
    
    // 价值等级
    const totalContractAmount = contracts.reduce((sum, c) => sum + (parseFloat(c.contract_amount || 0)), 0)
    let valueGrade = 'C'
    if (totalContractAmount >= 10000000) valueGrade = 'A+'
    else if (totalContractAmount >= 5000000) valueGrade = 'A'
    else if (totalContractAmount >= 2000000) valueGrade = 'B'
    else if (totalContractAmount >= 500000) valueGrade = 'C'
    else valueGrade = 'D'
    
    // 合作年限
    const firstProject = projects.length > 0 ? projects[0] : null
    const firstContract = contracts.length > 0 ? contracts[0] : null
    const firstDate = firstProject?.created_at || firstContract?.signed_date || data.basic_info?.created_at
    const cooperationYears = firstDate ? Math.floor((new Date() - new Date(firstDate)) / (1000 * 60 * 60 * 24 * 365)) : 0
    
    // 订单频率（每年订单数）
    const orderFrequency = contracts.length > 0 && cooperationYears > 0 
      ? (contracts.length / Math.max(cooperationYears, 1)).toFixed(1)
      : 0
    
    // 平均订单金额
    const avgOrderAmount = contracts.length > 0
      ? totalContractAmount / contracts.length
      : 0
    
    return {
      valueGrade,
      cooperationYears,
      orderFrequency,
      avgOrderAmount,
      totalContractAmount,
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-20 text-slate-400">加载中...</div>
        </div>
      </div>
    )
  }

  if (!customer360) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-20 text-slate-400">客户不存在</div>
        </div>
      </div>
    )
  }

  const basicInfo = customer360.basic_info || {}
  const summary = customer360.summary || {}

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
            <div>
              <h1 className="text-2xl font-bold text-white">{basicInfo.customer_name || '客户360视图'}</h1>
              <p className="text-sm text-slate-400 mt-1">
                {basicInfo.customer_code || ''} | {basicInfo.industry || ''}
              </p>
            </div>
          </div>
        </div>

        {/* Summary Cards - Issue 6.1: 客户画像 */}
        <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">项目总数</p>
                  <p className="text-2xl font-bold text-white mt-1">{summary.total_projects || 0}</p>
                </div>
                <Package className="w-8 h-8 text-blue-400/50" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">活跃项目</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">{summary.active_projects || 0}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-emerald-400/50" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">在途金额</p>
                  <p className="text-xl font-bold text-amber-400 mt-1">
                    {formatCurrency(summary.pipeline_amount)}
                  </p>
                </div>
                <Target className="w-8 h-8 text-amber-400/50" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-red-500/10 to-rose-500/5 border-red-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">未回款</p>
                  <p className="text-xl font-bold text-red-400 mt-1">
                    {formatCurrency(summary.open_receivables)}
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-red-400/50" />
              </div>
            </CardContent>
          </Card>
          
          {/* Issue 6.1: 客户画像 - 价值等级 */}
          {customerProfile && (
            <>
              <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-400">价值等级</p>
                      <p className="text-2xl font-bold text-purple-400 mt-1">{customerProfile.valueGrade}</p>
                    </div>
                    <Star className="w-8 h-8 text-purple-400/50" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-cyan-500/10 to-blue-500/5 border-cyan-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-400">合作年限</p>
                      <p className="text-2xl font-bold text-cyan-400 mt-1">{customerProfile.cooperationYears}年</p>
                    </div>
                    <Calendar className="w-8 h-8 text-cyan-400/50" />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </motion.div>

        {/* Customer Profile - Issue 6.1: 客户画像详情 */}
        {customerProfile && (
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
                  <div className="p-3 rounded-lg bg-surface-50">
                    <p className="text-xs text-slate-400 mb-1">价值等级</p>
                    <p className="text-lg font-bold text-white">{customerProfile.valueGrade}</p>
                    <p className="text-xs text-slate-500 mt-1">
                      累计合同金额: {formatCurrency(customerProfile.totalContractAmount)}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-50">
                    <p className="text-xs text-slate-400 mb-1">合作年限</p>
                    <p className="text-lg font-bold text-white">{customerProfile.cooperationYears} 年</p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-50">
                    <p className="text-xs text-slate-400 mb-1">订单频率</p>
                    <p className="text-lg font-bold text-white">{customerProfile.orderFrequency} 单/年</p>
                  </div>
                  <div className="p-3 rounded-lg bg-surface-50">
                    <p className="text-xs text-slate-400 mb-1">平均订单金额</p>
                    <p className="text-lg font-bold text-white">{formatCurrency(customerProfile.avgOrderAmount)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Tabs - Issue 6.1: 标签页 */}
        <motion.div variants={fadeIn}>
          <Card>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-5 lg:grid-cols-9">
                <TabsTrigger value="basic">基本信息</TabsTrigger>
                <TabsTrigger value="projects">项目交付</TabsTrigger>
                <TabsTrigger value="quotes">历史报价</TabsTrigger>
                <TabsTrigger value="contracts">历史合同</TabsTrigger>
                <TabsTrigger value="invoices">历史发票</TabsTrigger>
                <TabsTrigger value="payments">回款记录</TabsTrigger>
                <TabsTrigger value="opportunities">关联商机</TabsTrigger>
                <TabsTrigger value="satisfaction">满意度调查</TabsTrigger>
                <TabsTrigger value="service">服务记录</TabsTrigger>
              </TabsList>

              {/* 基本信息 */}
              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>客户基本信息</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <label className="text-xs text-slate-400">客户编码</label>
                        <p className="text-white">{basicInfo.customer_code || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">客户名称</label>
                        <p className="text-white">{basicInfo.customer_name || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">行业</label>
                        <p className="text-white">{basicInfo.industry || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">联系人</label>
                        <p className="text-white">{basicInfo.contact_person || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">联系电话</label>
                        <p className="text-white">{basicInfo.contact_phone || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">联系邮箱</label>
                        <p className="text-white">{basicInfo.contact_email || '-'}</p>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400">地址</label>
                        <p className="text-white">{basicInfo.address || '-'}</p>
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Issue 6.1: 关联分析 - 关联项目、关联商机 */}
                  <Card>
                    <CardHeader>
                      <CardTitle>关联分析</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <label className="text-xs text-slate-400 mb-2 block">关联项目</label>
                        <div className="space-y-2">
                          {(customer360.projects || []).slice(0, 5).map(project => (
                            <div key={project.project_id} className="flex items-center justify-between p-2 rounded bg-surface-50">
                              <span className="text-sm text-white">{project.project_name || project.project_code}</span>
                              <Badge variant="outline">{project.status || '-'}</Badge>
                            </div>
                          ))}
                          {(customer360.projects || []).length === 0 && (
                            <p className="text-sm text-slate-400">暂无关联项目</p>
                          )}
                        </div>
                      </div>
                      <div>
                        <label className="text-xs text-slate-400 mb-2 block">关联商机</label>
                        <div className="space-y-2">
                          {(customer360.opportunities || []).slice(0, 5).map(opp => (
                            <div key={opp.opportunity_id} className="flex items-center justify-between p-2 rounded bg-surface-50">
                              <span className="text-sm text-white">{opp.opp_name || opp.opp_code}</span>
                              <Badge variant="outline">{opp.stage || '-'}</Badge>
                            </div>
                          ))}
                          {(customer360.opportunities || []).length === 0 && (
                            <p className="text-sm text-slate-400">暂无关联商机</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* 项目交付 */}
              <TabsContent value="projects" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>项目交付记录</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.projects || []).map(project => (
                        <div key={project.project_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{project.project_name || project.project_code}</h4>
                              <p className="text-xs text-slate-400 mt-1">项目编码: {project.project_code}</p>
                            </div>
                            <Badge variant="outline">{project.status || '-'}</Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">阶段: </span>
                              <span className="text-white">{project.stage || '-'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">进度: </span>
                              <span className="text-white">{project.progress_pct || 0}%</span>
                            </div>
                            <div>
                              <span className="text-slate-400">合同金额: </span>
                              <span className="text-white">{formatCurrency(project.contract_amount)}</span>
                            </div>
                          </div>
                          {project.planned_end_date && (
                            <div className="mt-2 text-xs text-slate-400">
                              计划完成: {formatDate(project.planned_end_date)}
                            </div>
                          )}
                        </div>
                      ))}
                      {(customer360.projects || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无项目记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 历史报价 */}
              <TabsContent value="quotes" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>历史报价</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.quotes || []).map(quote => (
                        <div key={quote.quote_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{quote.quote_code}</h4>
                              <p className="text-xs text-slate-400 mt-1">负责人: {quote.owner_name || '-'}</p>
                            </div>
                            <Badge variant="outline">{quote.status || '-'}</Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">报价金额: </span>
                              <span className="text-white">{formatCurrency(quote.total_price)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">毛利率: </span>
                              <span className="text-white">{quote.gross_margin ? `${(quote.gross_margin * 100).toFixed(1)}%` : '-'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">有效期至: </span>
                              <span className="text-white">{quote.valid_until ? formatDate(quote.valid_until) : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(customer360.quotes || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无报价记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 历史合同 */}
              <TabsContent value="contracts" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>历史合同</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.contracts || []).map(contract => (
                        <div key={contract.contract_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{contract.contract_code}</h4>
                              <p className="text-xs text-slate-400 mt-1">关联项目: {contract.project_code || '-'}</p>
                            </div>
                            <Badge variant="outline">{contract.status || '-'}</Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">合同金额: </span>
                              <span className="text-white">{formatCurrency(contract.contract_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">签订日期: </span>
                              <span className="text-white">{contract.signed_date ? formatDate(contract.signed_date) : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(customer360.contracts || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无合同记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 历史发票 */}
              <TabsContent value="invoices" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>历史发票</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.invoices || []).map(invoice => (
                        <div key={invoice.invoice_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{invoice.invoice_code}</h4>
                              <p className="text-xs text-slate-400 mt-1">发票类型: {invoice.invoice_type || '-'}</p>
                            </div>
                            <Badge variant="outline">{invoice.status || '-'}</Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">发票金额: </span>
                              <span className="text-white">{formatCurrency(invoice.total_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">已收金额: </span>
                              <span className="text-white">{formatCurrency(invoice.paid_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">开票日期: </span>
                              <span className="text-white">{invoice.issue_date ? formatDate(invoice.issue_date) : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(customer360.invoices || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无发票记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 回款记录 */}
              <TabsContent value="payments" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>回款记录</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.payment_plans || []).map(plan => (
                        <div key={plan.plan_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{plan.payment_name}</h4>
                              <p className="text-xs text-slate-400 mt-1">计划日期: {plan.planned_date ? formatDate(plan.planned_date) : '-'}</p>
                            </div>
                            <Badge 
                              variant={plan.status === 'COMPLETED' ? 'default' : plan.status === 'PENDING' ? 'secondary' : 'outline'}
                            >
                              {plan.status === 'COMPLETED' ? '已完成' : plan.status === 'PENDING' ? '待回款' : plan.status || '-'}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">计划金额: </span>
                              <span className="text-white">{formatCurrency(plan.planned_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">已收金额: </span>
                              <span className="text-white">{formatCurrency(plan.actual_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">实际日期: </span>
                              <span className="text-white">{plan.actual_date ? formatDate(plan.actual_date) : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(customer360.payment_plans || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无回款记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 关联商机 */}
              <TabsContent value="opportunities" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>关联商机</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.opportunities || []).map(opp => (
                        <div key={opp.opportunity_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{opp.opp_name || opp.opp_code}</h4>
                              <p className="text-xs text-slate-400 mt-1">负责人: {opp.owner_name || '-'}</p>
                            </div>
                            <Badge variant="outline">{opp.stage || '-'}</Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                              <span className="text-slate-400">预估金额: </span>
                              <span className="text-white">{formatCurrency(opp.est_amount)}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">赢单概率: </span>
                              <span className="text-white">{opp.win_probability ? `${opp.win_probability}%` : '-'}</span>
                            </div>
                            <div>
                              <span className="text-slate-400">更新时间: </span>
                              <span className="text-white">{opp.updated_at ? formatDate(opp.updated_at) : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {(customer360.opportunities || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无商机数据</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 满意度调查 */}
              <TabsContent value="satisfaction" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>满意度调查</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-center py-8 text-slate-400">满意度调查功能待实现</p>
                    {/* TODO: 集成满意度调查 API */}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* 服务记录 */}
              <TabsContent value="service" className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>服务记录</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {(customer360.communications || []).map(comm => (
                        <div key={comm.communication_id} className="p-4 rounded-lg bg-surface-50 border border-border">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h4 className="font-medium text-white">{comm.topic || '沟通记录'}</h4>
                              <p className="text-xs text-slate-400 mt-1">负责人: {comm.owner_name || '-'}</p>
                            </div>
                            <Badge variant="outline">{comm.communication_type || '-'}</Badge>
                          </div>
                          <div className="mt-2 text-sm text-slate-300">
                            {comm.content || comm.description || '-'}
                          </div>
                          <div className="mt-2 text-xs text-slate-400">
                            日期: {comm.communication_date ? formatDate(comm.communication_date) : '-'}
                          </div>
                        </div>
                      ))}
                      {(customer360.communications || []).length === 0 && (
                        <p className="text-center py-8 text-slate-400">暂无服务记录</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
