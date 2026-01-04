import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Plus,
  Search,
  Filter,
  Eye,
  Edit3,
  User,
  Calendar,
  Tag,
  FileText,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock issue data
const mockIssues = [
  {
    id: 1,
    issue_no: 'IS20260105001',
    category: 'PROJECT',
    project_id: 1,
    project_code: 'PJ250108001',
    project_name: 'BMS老化测试设备',
    machine_id: 1,
    machine_code: 'PN001',
    issue_type: 'DEFECT',
    severity: 'CRITICAL',
    priority: 'URGENT',
    title: '温度控制精度不达标',
    description: '老化测试过程中，温度波动超过±2℃规格要求，影响测试结果准确性。',
    reporter_id: 1,
    reporter_name: '张工',
    report_date: '2026-01-05 10:30:00',
    assignee_id: 2,
    assignee_name: '李工',
    due_date: '2026-01-08',
    status: 'PROCESSING',
    solution: null,
    resolved_at: null,
    is_blocking: true,
    impact_scope: '影响FAT验收进度',
    impact_level: 'HIGH',
    follow_up_count: 3,
    last_follow_up_at: '2026-01-05 14:20:00',
    tags: ['温度控制', 'FAT'],
  },
  {
    id: 2,
    issue_no: 'IS20260105002',
    category: 'TASK',
    project_id: 1,
    project_code: 'PJ250108001',
    task_id: 10,
    issue_type: 'RISK',
    severity: 'MAJOR',
    priority: 'HIGH',
    title: '关键物料到货延期',
    description: '核心控制器预计到货时间延期3天，可能影响装配进度。',
    reporter_id: 3,
    reporter_name: '王采购',
    report_date: '2026-01-05 09:15:00',
    assignee_id: 4,
    assignee_name: '赵经理',
    due_date: '2026-01-07',
    status: 'OPEN',
    solution: null,
    resolved_at: null,
    is_blocking: false,
    impact_scope: '影响S5阶段进度',
    impact_level: 'MEDIUM',
    follow_up_count: 1,
    last_follow_up_at: '2026-01-05 09:15:00',
    tags: ['物料', '进度'],
  },
  {
    id: 3,
    issue_no: 'IS20260104001',
    category: 'ACCEPTANCE',
    project_id: 2,
    project_code: 'PJ250105002',
    acceptance_order_id: 1,
    issue_type: 'DEFECT',
    severity: 'MINOR',
    priority: 'MEDIUM',
    title: '触摸屏响应延迟',
    description: '部分按钮响应延迟约0.5秒，用户体验不佳。',
    reporter_id: 5,
    reporter_name: '刘测试',
    report_date: '2026-01-04 16:45:00',
    assignee_id: 6,
    assignee_name: '陈工',
    due_date: '2026-01-06',
    status: 'RESOLVED',
    solution: '优化HMI程序响应逻辑，减少延迟。',
    resolved_at: '2026-01-05 11:00:00',
    resolved_by: 6,
    resolved_by_name: '陈工',
    is_blocking: false,
    impact_scope: '用户体验',
    impact_level: 'LOW',
    follow_up_count: 2,
    last_follow_up_at: '2026-01-05 11:00:00',
    tags: ['HMI', '用户体验'],
  },
]

const severityColors = {
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/30',
  MAJOR: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  MINOR: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
}

const priorityColors = {
  URGENT: 'bg-red-500/20 text-red-400',
  HIGH: 'bg-orange-500/20 text-orange-400',
  MEDIUM: 'bg-blue-500/20 text-blue-400',
  LOW: 'bg-gray-500/20 text-gray-400',
}

const statusColors = {
  OPEN: 'bg-blue-500/20 text-blue-400',
  PROCESSING: 'bg-yellow-500/20 text-yellow-400',
  RESOLVED: 'bg-green-500/20 text-green-400',
  CLOSED: 'bg-gray-500/20 text-gray-400',
  DEFERRED: 'bg-purple-500/20 text-purple-400',
}

const statusIcons = {
  OPEN: AlertCircle,
  PROCESSING: Clock,
  RESOLVED: CheckCircle2,
  CLOSED: CheckCircle2,
  DEFERRED: XCircle,
}

export default function IssueManagement() {
  const [issues, setIssues] = useState(mockIssues)
  const [filteredIssues, setFilteredIssues] = useState(mockIssues)
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [showDetail, setShowDetail] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [filterCategory, setFilterCategory] = useState('all')

  useEffect(() => {
    let filtered = issues

    // 搜索过滤
    if (searchKeyword) {
      filtered = filtered.filter(
        (issue) =>
          issue.title.toLowerCase().includes(searchKeyword.toLowerCase()) ||
          issue.issue_no.toLowerCase().includes(searchKeyword.toLowerCase()) ||
          issue.description.toLowerCase().includes(searchKeyword.toLowerCase())
      )
    }

    // 状态过滤
    if (filterStatus !== 'all') {
      filtered = filtered.filter((issue) => issue.status === filterStatus)
    }

    // 严重程度过滤
    if (filterSeverity !== 'all') {
      filtered = filtered.filter((issue) => issue.severity === filterSeverity)
    }

    // 分类过滤
    if (filterCategory !== 'all') {
      filtered = filtered.filter((issue) => issue.category === filterCategory)
    }

    setFilteredIssues(filtered)
  }, [issues, searchKeyword, filterStatus, filterSeverity, filterCategory])

  const handleCreateIssue = (issueData) => {
    const newIssue = {
      id: issues.length + 1,
      ...issueData,
      issue_no: `IS${new Date().toISOString().slice(0, 10).replace(/-/g, '')}${String(issues.length + 1).padStart(3, '0')}`,
      reporter_id: 1,
      reporter_name: '当前用户',
      report_date: new Date().toISOString(),
      status: 'OPEN',
      follow_up_count: 0,
      tags: issueData.tags || [],
    }
    setIssues([newIssue, ...issues])
    setShowCreate(false)
  }

  const statistics = {
    total: issues.length,
    open: issues.filter((i) => i.status === 'OPEN').length,
    processing: issues.filter((i) => i.status === 'PROCESSING').length,
    resolved: issues.filter((i) => i.status === 'RESOLVED').length,
    closed: issues.filter((i) => i.status === 'CLOSED').length,
    blocking: issues.filter((i) => i.is_blocking).length,
    overdue: issues.filter(
      (i) =>
        i.due_date &&
        new Date(i.due_date) < new Date() &&
        ['OPEN', 'PROCESSING'].includes(i.status)
    ).length,
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题管理中心"
        description="统一管理项目问题、任务问题、验收问题等"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4"
        >
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">总问题数</div>
              <div className="text-2xl font-bold text-white">{statistics.total}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">待处理</div>
              <div className="text-2xl font-bold text-blue-400">{statistics.open}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">处理中</div>
              <div className="text-2xl font-bold text-yellow-400">{statistics.processing}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已解决</div>
              <div className="text-2xl font-bold text-green-400">{statistics.resolved}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已关闭</div>
              <div className="text-2xl font-bold text-gray-400">{statistics.closed}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">阻塞问题</div>
              <div className="text-2xl font-bold text-red-400">{statistics.blocking}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已逾期</div>
              <div className="text-2xl font-bold text-red-400">{statistics.overdue}</div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 搜索和筛选 */}
        <Card className="bg-surface-50 border-white/5">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  placeholder="搜索问题编号、标题、描述..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-surface-100 border-white/10 text-white"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部状态</option>
                  <option value="OPEN">待处理</option>
                  <option value="PROCESSING">处理中</option>
                  <option value="RESOLVED">已解决</option>
                  <option value="CLOSED">已关闭</option>
                </select>
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部严重程度</option>
                  <option value="CRITICAL">严重</option>
                  <option value="MAJOR">主要</option>
                  <option value="MINOR">次要</option>
                </select>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部分类</option>
                  <option value="PROJECT">项目问题</option>
                  <option value="TASK">任务问题</option>
                  <option value="ACCEPTANCE">验收问题</option>
                  <option value="QUALITY">质量问题</option>
                  <option value="TECHNICAL">技术问题</option>
                </select>
                <Button
                  onClick={() => setShowCreate(true)}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  新建问题
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 问题列表 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-3"
        >
          {filteredIssues.map((issue) => {
            const StatusIcon = statusIcons[issue.status] || AlertCircle
            const isOverdue =
              issue.due_date &&
              new Date(issue.due_date) < new Date() &&
              ['OPEN', 'PROCESSING'].includes(issue.status)

            return (
              <motion.div
                key={issue.id}
                variants={fadeIn}
                onClick={() => {
                  setSelectedIssue(issue)
                  setShowDetail(true)
                }}
                className="cursor-pointer"
              >
                <Card className="bg-surface-50 border-white/5 hover:border-primary/50 transition-all">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-mono text-sm text-slate-400">{issue.issue_no}</span>
                          <Badge className={cn('border', severityColors[issue.severity])}>
                            {issue.severity}
                          </Badge>
                          <Badge className={cn(priorityColors[issue.priority])}>
                            {issue.priority}
                          </Badge>
                          <Badge className={cn(statusColors[issue.status])}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {issue.status}
                          </Badge>
                          {issue.is_blocking && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                              阻塞
                            </Badge>
                          )}
                          {isOverdue && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                              逾期
                            </Badge>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-2">{issue.title}</h3>
                        <p className="text-sm text-slate-400 mb-3 line-clamp-2">
                          {issue.description}
                        </p>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <span className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            {issue.reporter_name}
                          </span>
                          {issue.assignee_name && (
                            <span className="flex items-center gap-1">
                              <User className="w-4 h-4" />
                              负责人: {issue.assignee_name}
                            </span>
                          )}
                          {issue.due_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              {issue.due_date}
                            </span>
                          )}
                          {issue.project_name && (
                            <span className="text-primary">{issue.project_name}</span>
                          )}
                        </div>
                        {issue.tags && issue.tags.length > 0 && (
                          <div className="flex items-center gap-2 mt-2">
                            {issue.tags.map((tag, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs text-slate-400 border-slate-600"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedIssue(issue)
                          setShowDetail(true)
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </motion.div>

        {filteredIssues.length === 0 && (
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-12 text-center">
              <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">暂无问题数据</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 问题详情对话框 */}
      <AnimatePresence>
        {showDetail && selectedIssue && (
          <IssueDetailDialog
            issue={selectedIssue}
            onClose={() => {
              setShowDetail(false)
              setSelectedIssue(null)
            }}
          />
        )}
      </AnimatePresence>

      {/* 创建问题对话框 */}
      <AnimatePresence>
        {showCreate && (
          <CreateIssueDialog
            onClose={() => setShowCreate(false)}
            onSubmit={handleCreateIssue}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// 问题详情对话框组件
function IssueDetailDialog({ issue, onClose }) {
  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl bg-surface-50 border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-primary" />
            {issue.title}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400 mb-1">问题编号</div>
              <div className="font-mono text-white">{issue.issue_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">状态</div>
              <Badge className={cn(statusColors[issue.status])}>{issue.status}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">严重程度</div>
              <Badge className={cn(severityColors[issue.severity])}>{issue.severity}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">优先级</div>
              <Badge className={cn(priorityColors[issue.priority])}>{issue.priority}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">提出人</div>
              <div className="text-white">{issue.reporter_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">负责人</div>
              <div className="text-white">{issue.assignee_name || '未分配'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">要求完成日期</div>
              <div className="text-white">{issue.due_date || '未设置'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">提出时间</div>
              <div className="text-white">{issue.report_date}</div>
            </div>
          </div>

          {/* 问题描述 */}
          <div>
            <div className="text-sm text-slate-400 mb-2">问题描述</div>
            <div className="text-white bg-surface-100 p-3 rounded-lg">{issue.description}</div>
          </div>

          {/* 解决方案 */}
          {issue.solution && (
            <div>
              <div className="text-sm text-slate-400 mb-2">解决方案</div>
              <div className="text-white bg-surface-100 p-3 rounded-lg">{issue.solution}</div>
            </div>
          )}

          {/* 影响评估 */}
          {issue.impact_scope && (
            <div>
              <div className="text-sm text-slate-400 mb-2">影响范围</div>
              <div className="text-white">{issue.impact_scope}</div>
            </div>
          )}

          {/* 标签 */}
          {issue.tags && issue.tags.length > 0 && (
            <div>
              <div className="text-sm text-slate-400 mb-2">标签</div>
              <div className="flex items-center gap-2">
                {issue.tags.map((tag, idx) => (
                  <Badge
                    key={idx}
                    variant="outline"
                    className="text-slate-400 border-slate-600"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// 创建问题对话框组件
function CreateIssueDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    category: 'PROJECT',
    issue_type: 'DEFECT',
    severity: 'MAJOR',
    priority: 'MEDIUM',
    title: '',
    description: '',
    assignee_id: null,
    due_date: '',
    impact_scope: '',
    impact_level: 'MEDIUM',
    is_blocking: false,
    tags: [],
  })

  const handleSubmit = () => {
    if (!formData.title || !formData.description) {
      alert('请填写问题标题和描述')
      return
    }
    onSubmit(formData)
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-surface-50 border-white/10 text-white">
        <DialogHeader>
          <DialogTitle>新建问题</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题分类</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="PROJECT">项目问题</option>
                <option value="TASK">任务问题</option>
                <option value="ACCEPTANCE">验收问题</option>
                <option value="QUALITY">质量问题</option>
                <option value="TECHNICAL">技术问题</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题类型</label>
              <select
                value={formData.issue_type}
                onChange={(e) => setFormData({ ...formData, issue_type: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="DEFECT">缺陷</option>
                <option value="DEVIATION">偏差</option>
                <option value="RISK">风险</option>
                <option value="BLOCKER">阻塞</option>
                <option value="SUGGESTION">建议</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">严重程度</label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="CRITICAL">严重</option>
                <option value="MAJOR">主要</option>
                <option value="MINOR">次要</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">优先级</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="URGENT">紧急</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">问题标题 *</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="请输入问题标题"
              className="bg-surface-100 border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">问题描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="请详细描述问题情况"
              rows={4}
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">要求完成日期</label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                checked={formData.is_blocking}
                onChange={(e) => setFormData({ ...formData, is_blocking: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-sm text-slate-400">是否阻塞项目/任务</label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} className="bg-primary hover:bg-primary/90">
            创建问题
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

