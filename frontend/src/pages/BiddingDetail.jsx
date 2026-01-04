/**
 * Bidding Detail Page - Comprehensive bidding project management
 * Tracks bidding progress, documents, evaluation status
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Target,
  FileText,
  Calendar,
  Users,
  DollarSign,
  Download,
  Upload,
  Send,
  Edit,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Paperclip,
  User,
  Building2,
  ChevronRight,
  TrendingUp,
  MessageSquare,
  Share2,
  Trash2,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
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
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

const mockBiddingDetail = {
  id: 'BID-2025-0001',
  projectName: '某大型汽车电池测试线体',
  customerName: '某汽车供应商',
  bidAmount: 2500000,
  estimatedCost: 1850000,
  estimatedMargin: 26,
  bidDeadline: '2025-01-10',
  daysLeft: 5,

  // 状态信息
  status: 'bidding_phase', // inquiry | bidding_phase | technical_evaluation | commercial_evaluation | won | lost
  documentStatus: 'draft', // draft | review | submitted | approved
  progress: 60,

  // 投标项目信息
  projectType: '线体',
  equipmentType: 'ICT/FCT',
  industry: '汽车电池',
  projectScope: '建设完整的电池测试线体，包括10台测试设备，软件系统集成',

  // 技术方案
  technicalApproach: {
    mainPoints: [
      '采用模块化设计，支持灵活扩展',
      '集成国际领先的测试技术',
      '提供完整的软件解决方案',
      '包含3年技术支持和维护'
    ],
    deliveryPeriod: '6个月',
    warranty: '3年',
    support: '7×24技术支持'
  },

  // 商务条款
  commercialTerms: {
    paymentTerms: '签约30%、进度40%、验收20%、质保10%',
    deliveryAddress: '客户指定地点',
    transportCost: '由我方承担',
    installationService: '包含现场安装和调试'
  },

  // 团队成员
  team: [
    {
      id: 1,
      name: '李经理',
      role: '项目经理',
      department: '销售部',
      responsibility: '整体协调'
    },
    {
      id: 2,
      name: '王工程师',
      role: '技术负责人',
      department: '技术部',
      responsibility: '技术方案'
    },
    {
      id: 3,
      name: '张工程师',
      role: '商务经理',
      department: '商务部',
      responsibility: '商务谈判'
    }
  ],

  // 文件
  documents: [
    {
      id: 1,
      name: '技术方案书v1.pdf',
      type: 'proposal',
      status: 'submitted',
      size: '8.5 MB',
      uploadDate: '2025-12-15',
      uploadedBy: '王工程师'
    },
    {
      id: 2,
      name: '商务报价v1.xlsx',
      type: 'pricing',
      status: 'submitted',
      size: '450 KB',
      uploadDate: '2025-12-16',
      uploadedBy: '张工程师'
    },
    {
      id: 3,
      name: '实施计划.pptx',
      type: 'plan',
      status: 'submitted',
      size: '3.2 MB',
      uploadDate: '2025-12-17',
      uploadedBy: '李经理'
    },
    {
      id: 4,
      name: 'FAQ回复.docx',
      type: 'faq',
      status: 'draft',
      size: '220 KB',
      uploadDate: '2025-12-18',
      uploadedBy: '王工程师'
    }
  ],

  // 评标信息
  evaluation: [
    {
      id: 1,
      stage: '资格审查',
      status: 'completed',
      completedDate: '2025-12-20',
      notes: '资格审查通过'
    },
    {
      id: 2,
      stage: '技术评标',
      status: 'in_progress',
      dueDate: '2026-01-05',
      notes: '技术评标进行中'
    },
    {
      id: 3,
      stage: '商务评标',
      status: 'pending',
      dueDate: '2026-01-08',
      notes: '待技术评标完成'
    },
    {
      id: 4,
      stage: '综合评定',
      status: 'pending',
      dueDate: '2026-01-10',
      notes: '待商务评标完成'
    }
  ],

  // 竞争对手
  competitors: [
    { id: 1, name: '竞争对手A', estimatedPrice: '2800000', status: '已提交' },
    { id: 2, name: '竞争对手B', estimatedPrice: '2450000', status: '已提交' },
    { id: 3, name: '竞争对手C', estimatedPrice: '2650000', status: '已提交' }
  ],

  // 风险和机会
  risks: [
    { id: 1, description: '客户可能延长评标时间', probability: '中', impact: '中', mitigation: '提前沟通评标进度' },
    { id: 2, description: '竞争对手可能大幅降价', probability: '高', impact: '高', mitigation: '强化技术优势宣传' }
  ],

  opportunities: [
    { id: 1, description: '可争取后续维保服务合同', value: '高' },
    { id: 2, description: '可引入配套软件和咨询服务', value: '中' }
  ],

  // 沟通记录
  communications: [
    {
      id: 1,
      date: '2025-12-20',
      type: '邮件',
      content: '提交技术方案书初稿',
      contact: '采购经理',
      status: '已发送'
    },
    {
      id: 2,
      date: '2025-12-22',
      type: '电话',
      content: '技术方案讨论，客户建议增加模块化功能',
      contact: '采购经理',
      status: '已完成'
    }
  ]
}

export default function BiddingDetail() {
  const [bidding] = useState(mockBiddingDetail)
  const [activeTab, setActiveTab] = useState('overview')

  const statusConfig = {
    inquiry: { label: '询价阶段', color: 'bg-slate-500/20 text-slate-300' },
    bidding_phase: { label: '投标阶段', color: 'bg-blue-500/20 text-blue-400' },
    technical_evaluation: { label: '技术评标', color: 'bg-purple-500/20 text-purple-400' },
    commercial_evaluation: { label: '商务评标', color: 'bg-orange-500/20 text-orange-400' },
    won: { label: '中标', color: 'bg-emerald-500/20 text-emerald-400' },
    lost: { label: '未中标', color: 'bg-red-500/20 text-red-400' }
  }

  const documentStatusConfig = {
    draft: { label: '编制中', color: 'bg-slate-700/40 text-slate-300' },
    review: { label: '审核中', color: 'bg-amber-500/20 text-amber-400' },
    submitted: { label: '已提交', color: 'bg-emerald-500/20 text-emerald-400' },
    approved: { label: '已批准', color: 'bg-blue-500/20 text-blue-400' }
  }

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title={bidding.projectName}
        description={`${bidding.customerName} | ${bidding.id}`}
        breadcrumb={[
          { label: '商务工作台', path: '/business-support' },
          { label: '投标管理', path: '/bidding' },
          { label: bidding.projectName }
        ]}
        action={{
          label: '编辑投标',
          icon: Edit,
          onClick: () => console.log('Edit bidding')
        }}
      />

      {/* Top Stats */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
      >
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">投标金额</p>
              <p className="text-2xl font-bold text-purple-400">
                {formatCurrency(bidding.bidAmount)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">投标阶段</p>
              <Badge className={statusConfig[bidding.status].color}>
                {statusConfig[bidding.status].label}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">截止日期</p>
              <p className="text-xl font-bold text-cyan-400">
                {bidding.daysLeft}天
              </p>
              <p className="text-xs text-slate-500">{bidding.bidDeadline}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">预期毛利</p>
              <p className="text-2xl font-bold text-emerald-400">
                {bidding.estimatedMargin}%
              </p>
              <p className="text-xs text-slate-500">
                {formatCurrency(bidding.bidAmount - bidding.estimatedCost)}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>标书编制进度</span>
                <span className="text-sm font-normal text-slate-400">
                  {bidding.progress}% 完成
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Progress value={bidding.progress} className="h-3 bg-slate-700/50" />
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-800/40 px-3 py-2">
                  <p className="text-slate-400">标书状态</p>
                  <Badge className={documentStatusConfig[bidding.documentStatus].color}>
                    {documentStatusConfig[bidding.documentStatus].label}
                  </Badge>
                </div>
                <div className="rounded-lg bg-slate-800/40 px-3 py-2">
                  <p className="text-slate-400">项目类型</p>
                  <p className="mt-1 font-medium text-slate-200">{bidding.projectType}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Technical Approach */}
          <Card>
            <CardHeader>
              <CardTitle>技术方案</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="mb-2 font-semibold text-slate-100">主要方案点</h4>
                <ul className="space-y-2">
                  {bidding.technicalApproach.mainPoints.map((point, idx) => (
                    <motion.li
                      key={idx}
                      variants={fadeIn}
                      className="flex items-start gap-3 text-sm text-slate-300"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-400" />
                      <span>{point}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-slate-700/30 pt-4 text-sm">
                <div>
                  <p className="text-slate-400">交付周期</p>
                  <p className="mt-1 font-semibold text-slate-200">
                    {bidding.technicalApproach.deliveryPeriod}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400">质保期</p>
                  <p className="mt-1 font-semibold text-slate-200">
                    {bidding.technicalApproach.warranty}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400">技术支持</p>
                  <p className="mt-1 font-semibold text-slate-200">
                    {bidding.technicalApproach.support}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Evaluation Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>评标进度</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bidding.evaluation.map((evalItem, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeIn}
                    className="flex items-center justify-between rounded-lg bg-slate-800/40 px-4 py-3"
                  >
                    <div className="flex items-center gap-3">
                      {evalItem.status === 'completed' && (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                      )}
                      {evalItem.status === 'in_progress' && (
                        <Clock className="h-5 w-5 text-blue-400" />
                      )}
                      {evalItem.status === 'pending' && (
                        <AlertTriangle className="h-5 w-5 text-slate-500" />
                      )}
                      <div>
                        <p className="font-semibold text-slate-200">{evalItem.stage}</p>
                        <p className="text-xs text-slate-500">{evalItem.notes}</p>
                      </div>
                    </div>
                    <span className="text-sm text-slate-400">
                      {evalItem.completedDate || evalItem.dueDate}
                    </span>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Documents */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>投标文件</span>
                <span className="text-sm font-normal text-slate-400">
                  {bidding.documents.length} 份
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {bidding.documents.map((doc, idx) => (
                <motion.div
                  key={idx}
                  variants={fadeIn}
                  className="flex items-center justify-between rounded-lg bg-slate-800/40 px-4 py-3"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <Paperclip className="h-4 w-4 flex-shrink-0 text-slate-500" />
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-200">{doc.name}</p>
                      <p className="text-xs text-slate-500">{doc.size} · {doc.uploadDate}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={documentStatusConfig[doc.status].color} variant="outline">
                      {documentStatusConfig[doc.status].label}
                    </Badge>
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 text-slate-400 hover:text-slate-100"
              >
                <Upload className="h-4 w-4" />
                上传新文件
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full justify-start gap-2">
                <Send className="h-4 w-4" />
                提交标书
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <MessageSquare className="h-4 w-4" />
                发送回函
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Share2 className="h-4 w-4" />
                分享投标信息
              </Button>
              <Button variant="ghost" className="w-full justify-start gap-2">
                <Download className="h-4 w-4" />
                下载方案包
              </Button>
            </CardContent>
          </Card>

          {/* Team Members */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">项目团队</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {bidding.team.map((member, idx) => (
                <motion.div
                  key={idx}
                  variants={fadeIn}
                  className="rounded-lg bg-slate-800/40 px-3 py-2.5"
                >
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-slate-500" />
                    <div>
                      <p className="font-medium text-slate-200">{member.name}</p>
                      <p className="text-xs text-slate-500">
                        {member.role} · {member.department}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Competitor Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">竞争分析</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="space-y-1">
                {bidding.competitors.map((comp, idx) => (
                  <motion.div
                    key={idx}
                    variants={fadeIn}
                    className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2 text-sm"
                  >
                    <span className="text-slate-300">{comp.name}</span>
                    <span className="font-semibold text-amber-400">
                      {formatCurrency(parseInt(comp.estimatedPrice))}
                    </span>
                  </motion.div>
                ))}
              </div>
              <div className="mt-3 rounded-lg bg-blue-500/10 border border-blue-500/30 px-3 py-2 text-xs">
                <p className="text-blue-300">
                  💡 我们的报价比最低价高 {formatCurrency(bidding.bidAmount - 2450000)}，但技术优势明显
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Key Dates */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">关键日期</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2">
                <span className="text-slate-400">标书截止</span>
                <span className="font-semibold text-red-400">{bidding.bidDeadline}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2">
                <span className="text-slate-400">技术评标</span>
                <span className="font-semibold text-slate-300">2026-01-05</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2">
                <span className="text-slate-400">商务评标</span>
                <span className="font-semibold text-slate-300">2026-01-08</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-800/40 px-3 py-2">
                <span className="text-slate-400">综合评定</span>
                <span className="font-semibold text-slate-300">2026-01-10</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
