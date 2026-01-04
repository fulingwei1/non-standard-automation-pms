import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ClipboardList,
  CheckSquare,
  Square,
  Camera,
  FileText,
  Calendar,
  User,
  Building2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Clock,
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  Edit3,
  MessageSquare,
  Image,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock acceptance data
const mockAcceptances = [
  {
    id: 'FAT-20260104-001',
    type: 'FAT',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: 'PN001',
    customer: '宁德时代',
    customerContact: '张工',
    status: 'in_progress',
    scheduledDate: '2026-01-06',
    completedDate: null,
    inspector: '李品质',
    totalItems: 25,
    passedItems: 18,
    failedItems: 2,
    pendingItems: 5,
    issues: [
      {
        id: 'ISS001',
        item: '老化温度控制精度',
        category: '功能测试',
        severity: 'major',
        description: '温度波动超过±2℃规格要求',
        status: 'open',
        photos: ['issue1.jpg'],
      },
      {
        id: 'ISS002',
        item: '触摸屏响应速度',
        category: 'HMI',
        severity: 'minor',
        description: '部分按钮响应延迟约0.5秒',
        status: 'resolved',
        photos: [],
      },
    ],
    checklistCategories: [
      { name: '外观检查', total: 5, passed: 5, failed: 0 },
      { name: '功能测试', total: 8, passed: 5, failed: 2 },
      { name: '安全测试', total: 4, passed: 4, failed: 0 },
      { name: '精度测试', total: 5, passed: 3, failed: 0 },
      { name: '文档资料', total: 3, passed: 1, failed: 0 },
    ],
  },
  {
    id: 'SAT-20260102-001',
    type: 'SAT',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    machineNo: 'PN001',
    customer: '比亚迪',
    customerContact: '王工',
    status: 'completed',
    scheduledDate: '2026-01-02',
    completedDate: '2026-01-02',
    inspector: '李品质',
    totalItems: 20,
    passedItems: 20,
    failedItems: 0,
    pendingItems: 0,
    issues: [],
    checklistCategories: [
      { name: '现场安装', total: 5, passed: 5, failed: 0 },
      { name: '功能验证', total: 8, passed: 8, failed: 0 },
      { name: '培训确认', total: 4, passed: 4, failed: 0 },
      { name: '文档移交', total: 3, passed: 3, failed: 0 },
    ],
  },
  {
    id: 'FAT-20260103-002',
    type: 'FAT',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    machineNo: 'PN001',
    customer: '华为',
    customerContact: '李工',
    status: 'pending',
    scheduledDate: '2026-01-15',
    completedDate: null,
    inspector: null,
    totalItems: 22,
    passedItems: 0,
    failedItems: 0,
    pendingItems: 22,
    issues: [],
    checklistCategories: [],
  },
]

const typeConfigs = {
  FAT: { label: '出厂验收', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  SAT: { label: '现场验收', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  FINAL: { label: '终验收', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
}

const statusConfigs = {
  pending: { label: '待验收', color: 'bg-slate-500', icon: Clock },
  in_progress: { label: '验收中', color: 'bg-blue-500', icon: ClipboardList },
  completed: { label: '已通过', color: 'bg-emerald-500', icon: CheckCircle2 },
  failed: { label: '未通过', color: 'bg-red-500', icon: XCircle },
}

const severityConfigs = {
  critical: { label: '严重', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
  major: { label: '主要', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  minor: { label: '次要', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
}

function AcceptanceCard({ acceptance, onView }) {
  const type = typeConfigs[acceptance.type]
  const status = statusConfigs[acceptance.status]
  const StatusIcon = status.icon

  const passRate = acceptance.totalItems > 0
    ? Math.round((acceptance.passedItems / acceptance.totalItems) * 100)
    : 0

  const openIssues = acceptance.issues.filter((i) => i.status === 'open').length

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden"
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn('text-[10px]', type.bgColor, type.color)}>
                {type.label}
              </Badge>
              <span className="font-mono text-xs text-slate-500">{acceptance.id}</span>
            </div>
            <h3 className="font-medium text-white">{acceptance.projectName}</h3>
            <p className="text-sm text-slate-400">{acceptance.machineNo}</p>
          </div>
          <Badge className={cn('gap-1', status.color)}>
            <StatusIcon className="w-3 h-3" />
            {status.label}
          </Badge>
        </div>

        {/* Customer */}
        <div className="flex items-center gap-4 mb-3 text-sm text-slate-400">
          <span className="flex items-center gap-1">
            <Building2 className="w-3.5 h-3.5" />
            {acceptance.customer}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {acceptance.scheduledDate}
          </span>
        </div>

        {/* Progress */}
        {acceptance.status !== 'pending' && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">验收进度</span>
              <span className="text-white">
                {acceptance.passedItems + acceptance.failedItems}/{acceptance.totalItems} 项
              </span>
            </div>
            <div className="h-2 bg-surface-2 rounded-full overflow-hidden flex">
              <div
                className="bg-emerald-500 transition-all"
                style={{ width: `${(acceptance.passedItems / acceptance.totalItems) * 100}%` }}
              />
              <div
                className="bg-red-500 transition-all"
                style={{ width: `${(acceptance.failedItems / acceptance.totalItems) * 100}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-1 text-xs">
              <span className="text-emerald-400">通过 {acceptance.passedItems}</span>
              <span className="text-red-400">不通过 {acceptance.failedItems}</span>
              <span className="text-slate-500">待检 {acceptance.pendingItems}</span>
            </div>
          </div>
        )}

        {/* Issues */}
        {openIssues > 0 && (
          <div className="p-2 rounded-lg bg-amber-500/10 text-xs text-amber-300 flex items-center gap-2 mb-3">
            <AlertCircle className="w-3 h-3" />
            {openIssues} 个待解决问题
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <div className="text-xs text-slate-500">
            {acceptance.inspector ? `检验员：${acceptance.inspector}` : '待分配检验员'}
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onView(acceptance)}>
              <Eye className="w-3.5 h-3.5" />
            </Button>
            {acceptance.status === 'in_progress' && (
              <Button variant="ghost" size="sm" className="h-7 px-2">
                <Edit3 className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function AcceptanceDetailDialog({ acceptance, open, onOpenChange }) {
  const [activeTab, setActiveTab] = useState('checklist')

  if (!acceptance) return null

  const type = typeConfigs[acceptance.type]
  const status = statusConfigs[acceptance.status]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Badge className={cn(type.bgColor, type.color)}>{type.label}</Badge>
            {acceptance.projectName} - {acceptance.machineNo}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Basic Info */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <label className="text-xs text-slate-500">验收单号</label>
              <p className="text-white font-mono">{acceptance.id}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">项目编号</label>
              <p className="text-accent">{acceptance.projectId}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">客户</label>
              <p className="text-white">{acceptance.customer}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">计划日期</label>
              <p className="text-white">{acceptance.scheduledDate}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">检验员</label>
              <p className="text-white">{acceptance.inspector || '-'}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">状态</label>
              <Badge className={cn('mt-1', status.color)}>{status.label}</Badge>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-border">
            {[
              { id: 'checklist', label: '检查清单' },
              { id: 'issues', label: `问题记录 (${acceptance.issues.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                  activeTab === tab.id
                    ? 'text-accent border-accent'
                    : 'text-slate-400 border-transparent hover:text-white'
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Checklist Tab */}
          {activeTab === 'checklist' && (
            <div className="space-y-3">
              {acceptance.checklistCategories.length > 0 ? (
                acceptance.checklistCategories.map((category, index) => (
                  <div key={index} className="p-3 rounded-lg bg-surface-2">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{category.name}</span>
                      <span className="text-sm text-slate-400">
                        {category.passed}/{category.total}
                      </span>
                    </div>
                    <div className="h-1.5 bg-surface-0 rounded-full overflow-hidden flex">
                      <div
                        className="bg-emerald-500"
                        style={{ width: `${(category.passed / category.total) * 100}%` }}
                      />
                      <div
                        className="bg-red-500"
                        style={{ width: `${(category.failed / category.total) * 100}%` }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  暂无检查记录
                </div>
              )}
            </div>
          )}

          {/* Issues Tab */}
          {activeTab === 'issues' && (
            <div className="space-y-3">
              {acceptance.issues.length > 0 ? (
                acceptance.issues.map((issue) => (
                  <div
                    key={issue.id}
                    className={cn(
                      'p-4 rounded-lg border',
                      issue.status === 'open'
                        ? 'bg-amber-500/5 border-amber-500/30'
                        : 'bg-surface-2 border-border/50'
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">{issue.item}</span>
                          <Badge
                            className={cn('text-[10px] border', severityConfigs[issue.severity].color)}
                          >
                            {severityConfigs[issue.severity].label}
                          </Badge>
                        </div>
                        <span className="text-xs text-slate-500">{issue.category}</span>
                      </div>
                      <Badge
                        className={cn(
                          issue.status === 'open'
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        )}
                      >
                        {issue.status === 'open' ? '待解决' : '已解决'}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-300">{issue.description}</p>
                    {issue.photos.length > 0 && (
                      <div className="flex gap-2 mt-2">
                        {issue.photos.map((photo, i) => (
                          <div
                            key={i}
                            className="w-16 h-16 rounded bg-surface-0 flex items-center justify-center"
                          >
                            <Image className="w-6 h-6 text-slate-600" />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  暂无问题记录
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {acceptance.status === 'in_progress' && (
            <>
              <Button variant="outline">
                <Camera className="w-4 h-4 mr-1" />
                记录问题
              </Button>
              <Button>
                <FileText className="w-4 h-4 mr-1" />
                生成报告
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function Acceptance() {
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAcceptance, setSelectedAcceptance] = useState(null)
  const [showDetail, setShowDetail] = useState(false)

  const filteredAcceptances = mockAcceptances.filter((acceptance) => {
    if (typeFilter !== 'all' && acceptance.type !== typeFilter) return false
    if (statusFilter !== 'all' && acceptance.status !== statusFilter) return false
    if (
      searchQuery &&
      !acceptance.projectName.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !acceptance.id.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false
    }
    return true
  })

  const stats = {
    total: mockAcceptances.length,
    pending: mockAcceptances.filter((a) => a.status === 'pending').length,
    inProgress: mockAcceptances.filter((a) => a.status === 'in_progress').length,
    completed: mockAcceptances.filter((a) => a.status === 'completed').length,
  }

  const handleView = (acceptance) => {
    setSelectedAcceptance(acceptance)
    setShowDetail(true)
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="验收管理"
        description="管理FAT/SAT验收流程，记录验收问题"
        actions={
          <Button>
            <Plus className="w-4 h-4 mr-1" />
            新建验收单
          </Button>
        }
      />

      {/* Stats */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '全部验收单', value: stats.total, icon: ClipboardList, color: 'text-blue-400' },
          { label: '待验收', value: stats.pending, icon: Clock, color: 'text-slate-400' },
          { label: '验收中', value: stats.inProgress, icon: ClipboardList, color: 'text-amber-400' },
          { label: '已完成', value: stats.completed, icon: CheckCircle2, color: 'text-emerald-400' },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
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
                    { value: 'all', label: '全部' },
                    { value: 'FAT', label: 'FAT' },
                    { value: 'SAT', label: 'SAT' },
                  ].map((filter) => (
                    <Button
                      key={filter.value}
                      variant={typeFilter === filter.value ? 'default' : 'ghost'}
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
                    { value: 'all', label: '全部状态' },
                    { value: 'pending', label: '待验收' },
                    { value: 'in_progress', label: '验收中' },
                    { value: 'completed', label: '已完成' },
                  ].map((filter) => (
                    <Button
                      key={filter.value}
                      variant={statusFilter === filter.value ? 'default' : 'ghost'}
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
                    value={searchQuery}
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

      {/* Acceptance List */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAcceptances.map((acceptance) => (
          <AcceptanceCard
            key={acceptance.id}
            acceptance={acceptance}
            onView={handleView}
          />
        ))}
      </motion.div>

      {/* Empty State */}
      {filteredAcceptances.length === 0 && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <ClipboardList className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无验收单</h3>
          <p className="text-sm text-slate-500 mt-1">
            {searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
              ? '没有符合条件的验收单'
              : '点击"新建验收单"开始验收'}
          </p>
        </motion.div>
      )}

      {/* Detail Dialog */}
      <AcceptanceDetailDialog
        acceptance={selectedAcceptance}
        open={showDetail}
        onOpenChange={setShowDetail}
      />
    </motion.div>
  )
}

