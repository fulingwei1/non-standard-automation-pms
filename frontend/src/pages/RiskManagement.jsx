import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { pmoApi, projectApi } from '../services/api'
import { formatDate } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonCard,
} from '../components/ui'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui'
import {
  Plus,
  Search,
  AlertTriangle,
  ArrowRight,
  Eye,
  Edit,
  CheckCircle2,
  XCircle,
  Clock,
  Target,
  FileText,
  User,
} from 'lucide-react'

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
}

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const getRiskLevelBadge = (level) => {
  const badges = {
    CRITICAL: {
      label: '严重',
      variant: 'danger',
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/30',
    },
    HIGH: {
      label: '高',
      variant: 'danger',
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
      borderColor: 'border-orange-500/30',
    },
    MEDIUM: {
      label: '中',
      variant: 'warning',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/30',
    },
    LOW: {
      label: '低',
      variant: 'info',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/30',
    },
  }
  return badges[level] || badges.LOW
}

const getStatusBadge = (status) => {
  const badges = {
    IDENTIFIED: { label: '已识别', variant: 'secondary' },
    ANALYZING: { label: '分析中', variant: 'info' },
    RESPONDING: { label: '应对中', variant: 'warning' },
    MONITORING: { label: '监控中', variant: 'info' },
    CLOSED: { label: '已关闭', variant: 'success' },
  }
  return badges[status] || badges.IDENTIFIED
}

const getProbabilityLabel = (prob) => {
  const labels = {
    HIGH: '高',
    MEDIUM: '中',
    LOW: '低',
  }
  return labels[prob] || '未知'
}

const getImpactLabel = (impact) => {
  const labels = {
    HIGH: '高',
    MEDIUM: '中',
    LOW: '低',
  }
  return labels[impact] || '未知'
}

export default function RiskManagement() {
  const { projectId } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [project, setProject] = useState(null)
  const [risks, setRisks] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState(
    projectId ? parseInt(projectId) : null
  )
  const [projectSearch, setProjectSearch] = useState('')
  const [projectList, setProjectList] = useState([])
  const [showProjectSelect, setShowProjectSelect] = useState(!projectId)
  const [statusFilter, setStatusFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState('')

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [assessDialog, setAssessDialog] = useState({ open: false, riskId: null })
  const [responseDialog, setResponseDialog] = useState({ open: false, riskId: null })
  const [statusDialog, setStatusDialog] = useState({ open: false, riskId: null })
  const [closeDialog, setCloseDialog] = useState({ open: false, riskId: null })
  const [detailDialog, setDetailDialog] = useState({ open: false, risk: null })

  useEffect(() => {
    if (selectedProjectId) {
      fetchProjectData()
      fetchRisks()
    } else {
      fetchProjectList()
    }
  }, [selectedProjectId, statusFilter, levelFilter])

  const fetchProjectData = async () => {
    if (!selectedProjectId) return
    try {
      const res = await projectApi.get(selectedProjectId)
      const data = res.data || res
      setProject(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载项目信息失败')
    }
  }

  const fetchRisks = async () => {
    if (!selectedProjectId) return
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (statusFilter) {
        params.status = statusFilter
      }
      if (levelFilter) {
        params.risk_level = levelFilter
      }
      const res = await pmoApi.risks.list(selectedProjectId, params)
      const data = res.data || res
      setRisks(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载风险数据失败')
      setRisks([])
    } finally {
      setLoading(false)
    }
  }

  const fetchProjectList = async () => {
    try {
      const res = await projectApi.list({
        page: 1,
        page_size: 50,
        keyword: projectSearch,
      })
      const data = res.data || res
      // Handle PaginatedResponse format
      if (data && typeof data === 'object' && 'items' in data) {
        setProjectList(data.items || [])
      } else if (Array.isArray(data)) {
        setProjectList(data)
      } else {
        setProjectList([])
      }
    } catch (err) {
      setProjectList([])
    }
  }

  const handleCreate = async (formData) => {
    try {
      await pmoApi.risks.create(selectedProjectId, formData)
      setCreateDialogOpen(false)
      fetchRisks()
    } catch (err) {
      alert('创建失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleAssess = async (riskId, data) => {
    try {
      await pmoApi.risks.assess(riskId, data)
      setAssessDialog({ open: false, riskId: null })
      fetchRisks()
    } catch (err) {
      alert('评估失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleResponse = async (riskId, data) => {
    try {
      await pmoApi.risks.response(riskId, data)
      setResponseDialog({ open: false, riskId: null })
      fetchRisks()
    } catch (err) {
      alert('更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleStatusUpdate = async (riskId, data) => {
    try {
      await pmoApi.risks.updateStatus(riskId, data)
      setStatusDialog({ open: false, riskId: null })
      fetchRisks()
    } catch (err) {
      alert('更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleClose = async (riskId, data) => {
    try {
      await pmoApi.risks.close(riskId, data)
      setCloseDialog({ open: false, riskId: null })
      fetchRisks()
    } catch (err) {
      alert('关闭失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  if (showProjectSelect) {
    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
      >
        <PageHeader
          title="风险管理"
          description="选择项目以管理其风险"
        />

        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-6">
            <div className="mb-4">
              <Input
                placeholder="搜索项目名称或编码..."
                value={projectSearch}
                onChange={(e) => {
                  setProjectSearch(e.target.value)
                  fetchProjectList()
                }}
                className="w-full"
                icon={Search}
              />
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {projectList.map((proj) => (
                <div
                  key={proj.id}
                  onClick={() => {
                    setSelectedProjectId(proj.id)
                    setShowProjectSelect(false)
                    navigate(`/pmo/risks/${proj.id}`)
                  }}
                  className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 cursor-pointer transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-white">{proj.project_name}</h3>
                      <p className="text-sm text-slate-400">{proj.project_code}</p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-500" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="风险管理"
        description={project ? `${project.project_name} - 项目风险管理` : '项目风险管理'}
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowProjectSelect(true)
                navigate('/pmo/risks')
              }}
            >
              选择项目
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              新建风险
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部状态</option>
              <option value="IDENTIFIED">已识别</option>
              <option value="ANALYZING">分析中</option>
              <option value="RESPONDING">应对中</option>
              <option value="MONITORING">监控中</option>
              <option value="CLOSED">已关闭</option>
            </select>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部等级</option>
              <option value="CRITICAL">严重</option>
              <option value="HIGH">高</option>
              <option value="MEDIUM">中</option>
              <option value="LOW">低</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="mb-6 border-red-500/30 bg-red-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-400">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setError(null)
                  if (selectedProjectId) {
                    fetchProjectData()
                    fetchRisks()
                  }
                }}
                className="border-red-500/30 text-red-400 hover:bg-red-500/20"
              >
                重试
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Risk List */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {Array(3)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      ) : error ? null : risks.length > 0 ? (
        <div className="space-y-4">
          {risks.map((risk) => {
            const levelBadge = getRiskLevelBadge(risk.risk_level)
            const statusBadge = getStatusBadge(risk.status)

            return (
              <motion.div key={risk.id} variants={staggerChild}>
                <Card
                  className={cn(
                    'hover:bg-white/[0.02] transition-colors border-l-4',
                    levelBadge.borderColor
                  )}
                >
                  <CardContent className="p-5">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'p-2.5 rounded-xl',
                            levelBadge.bgColor,
                            'ring-1',
                            levelBadge.borderColor
                          )}
                        >
                          <AlertTriangle
                            className={cn('h-5 w-5', levelBadge.color)}
                          />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-white">
                              {risk.risk_name}
                            </h3>
                            <Badge
                              variant={levelBadge.variant}
                              className={levelBadge.bgColor}
                            >
                              {levelBadge.label}
                            </Badge>
                            <Badge variant={statusBadge.variant}>
                              {statusBadge.label}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">
                            {risk.risk_no} • {risk.risk_category}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    {risk.description && (
                      <p className="text-sm text-slate-300 mb-4 line-clamp-2">
                        {risk.description}
                      </p>
                    )}

                    {/* Risk Matrix */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <div>
                        <span className="text-xs text-slate-400">发生概率</span>
                        <p className="text-white font-medium">
                          {getProbabilityLabel(risk.probability)}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400">影响程度</span>
                        <p className="text-white font-medium">
                          {getImpactLabel(risk.impact)}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400">负责人</span>
                        <p className="text-white font-medium">
                          {risk.owner_name || '未分配'}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400">跟踪日期</span>
                        <p className="text-white font-medium">
                          {risk.follow_up_date
                            ? formatDate(risk.follow_up_date)
                            : '未设置'}
                        </p>
                      </div>
                    </div>

                    {/* Response Plan */}
                    {risk.response_strategy && (
                      <div className="mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-xs text-slate-400">应对策略</span>
                        <p className="text-sm text-white mt-1">
                          {risk.response_strategy}
                        </p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 flex-wrap">
                        {risk.status === 'IDENTIFIED' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              setAssessDialog({ open: true, riskId: risk.id })
                            }
                          >
                            <Target className="h-4 w-4 mr-2" />
                            风险评估
                          </Button>
                        )}
                        {risk.status === 'ANALYZING' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              setResponseDialog({ open: true, riskId: risk.id })
                            }
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            制定应对
                          </Button>
                        )}
                        {risk.status !== 'CLOSED' && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setStatusDialog({ open: true, riskId: risk.id })
                              }
                            >
                              <Clock className="h-4 w-4 mr-2" />
                              更新状态
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setCloseDialog({ open: true, riskId: risk.id })
                              }
                            >
                              <CheckCircle2 className="h-4 w-4 mr-2" />
                              关闭风险
                            </Button>
                          </>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setDetailDialog({ open: true, risk })}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      ) : !error ? (
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            该项目暂无风险数据
          </CardContent>
        </Card>
      ) : null}

      {/* Create Dialog */}
      <CreateRiskDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate}
      />

      {/* Assess Dialog */}
      <AssessRiskDialog
        open={assessDialog.open}
        onOpenChange={(open) => setAssessDialog({ open, riskId: null })}
        onSubmit={(data) => handleAssess(assessDialog.riskId, data)}
      />

      {/* Response Dialog */}
      <ResponseRiskDialog
        open={responseDialog.open}
        onOpenChange={(open) => setResponseDialog({ open, riskId: null })}
        onSubmit={(data) => handleResponse(responseDialog.riskId, data)}
      />

      {/* Status Dialog */}
      <StatusRiskDialog
        open={statusDialog.open}
        onOpenChange={(open) => setStatusDialog({ open, riskId: null })}
        onSubmit={(data) => handleStatusUpdate(statusDialog.riskId, data)}
      />

      {/* Close Dialog */}
      <CloseRiskDialog
        open={closeDialog.open}
        onOpenChange={(open) => setCloseDialog({ open, riskId: null })}
        onSubmit={(data) => handleClose(closeDialog.riskId, data)}
      />

      {/* Detail Dialog */}
      <RiskDetailDialog
        open={detailDialog.open}
        onOpenChange={(open) => setDetailDialog({ open, risk: null })}
        risk={detailDialog.risk}
      />
    </motion.div>
  )
}

// Create Risk Dialog
function CreateRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    risk_category: '',
    risk_name: '',
    description: '',
    probability: '',
    impact: '',
    owner_id: '',
    trigger_condition: '',
  })

  const handleSubmit = () => {
    if (!formData.risk_name.trim() || !formData.risk_category.trim()) {
      alert('请填写风险名称和类别')
      return
    }
    onSubmit(formData)
    setFormData({
      risk_category: '',
      risk_name: '',
      description: '',
      probability: '',
      impact: '',
      owner_id: '',
      trigger_condition: '',
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建风险</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  风险类别 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.risk_category}
                  onChange={(e) =>
                    setFormData({ ...formData, risk_category: e.target.value })
                  }
                  placeholder="如：技术风险、进度风险等"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  风险名称 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.risk_name}
                  onChange={(e) =>
                    setFormData({ ...formData, risk_name: e.target.value })
                  }
                  placeholder="请输入风险名称"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                风险描述
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请详细描述风险情况"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  发生概率
                </label>
                <select
                  value={formData.probability}
                  onChange={(e) =>
                    setFormData({ ...formData, probability: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">请选择</option>
                  <option value="HIGH">高</option>
                  <option value="MEDIUM">中</option>
                  <option value="LOW">低</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  影响程度
                </label>
                <select
                  value={formData.impact}
                  onChange={(e) =>
                    setFormData({ ...formData, impact: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">请选择</option>
                  <option value="HIGH">高</option>
                  <option value="MEDIUM">中</option>
                  <option value="LOW">低</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                触发条件
              </label>
              <Input
                value={formData.trigger_condition}
                onChange={(e) =>
                  setFormData({ ...formData, trigger_condition: e.target.value })
                }
                placeholder="描述风险触发条件（可选）"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Assess Risk Dialog
function AssessRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    probability: '',
    impact: '',
    risk_level: '',
  })

  const handleSubmit = () => {
    if (!formData.probability || !formData.impact) {
      alert('请选择发生概率和影响程度')
      return
    }
    onSubmit(formData)
    setFormData({ probability: '', impact: '', risk_level: '' })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>风险评估</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                发生概率 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.probability}
                onChange={(e) =>
                  setFormData({ ...formData, probability: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                影响程度 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.impact}
                onChange={(e) =>
                  setFormData({ ...formData, impact: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Response Risk Dialog
function ResponseRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    response_strategy: '',
    response_plan: '',
    owner_id: '',
  })

  const handleSubmit = () => {
    if (!formData.response_strategy.trim() || !formData.response_plan.trim()) {
      alert('请填写应对策略和应对措施')
      return
    }
    onSubmit(formData)
    setFormData({ response_strategy: '', response_plan: '', owner_id: '' })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>制定应对计划</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                应对策略 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.response_strategy}
                onChange={(e) =>
                  setFormData({ ...formData, response_strategy: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="AVOID">规避</option>
                <option value="MITIGATE">减轻</option>
                <option value="TRANSFER">转移</option>
                <option value="ACCEPT">接受</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                应对措施 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.response_plan}
                onChange={(e) =>
                  setFormData({ ...formData, response_plan: e.target.value })
                }
                placeholder="请详细描述应对措施"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={5}
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Status Risk Dialog
function StatusRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    status: '',
    last_update: '',
    follow_up_date: '',
  })

  const handleSubmit = () => {
    if (!formData.status) {
      alert('请选择状态')
      return
    }
    onSubmit(formData)
    setFormData({ status: '', last_update: '', follow_up_date: '' })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>更新风险状态</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                状态 <span className="text-red-400">*</span>
              </label>
              <select
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">请选择</option>
                <option value="IDENTIFIED">已识别</option>
                <option value="ANALYZING">分析中</option>
                <option value="RESPONDING">应对中</option>
                <option value="MONITORING">监控中</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                最新进展
              </label>
              <textarea
                value={formData.last_update}
                onChange={(e) =>
                  setFormData({ ...formData, last_update: e.target.value })
                }
                placeholder="请输入最新进展"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                跟踪日期
              </label>
              <Input
                type="date"
                value={formData.follow_up_date}
                onChange={(e) =>
                  setFormData({ ...formData, follow_up_date: e.target.value })
                }
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Close Risk Dialog
function CloseRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    closed_reason: '',
  })

  const handleSubmit = () => {
    if (!formData.closed_reason.trim()) {
      alert('请填写关闭原因')
      return
    }
    onSubmit(formData)
    setFormData({ closed_reason: '' })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>关闭风险</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              关闭原因 <span className="text-red-400">*</span>
            </label>
            <textarea
              value={formData.closed_reason}
              onChange={(e) =>
                setFormData({ ...formData, closed_reason: e.target.value })
              }
              placeholder="请说明风险关闭的原因"
              className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              rows={4}
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Risk Detail Dialog
function RiskDetailDialog({ open, onOpenChange, risk }) {
  if (!risk) return null

  const levelBadge = getRiskLevelBadge(risk.risk_level)
  const statusBadge = getStatusBadge(risk.status)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>风险详情 - {risk.risk_name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">风险编号</span>
                <p className="text-white font-medium">{risk.risk_no}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">风险类别</span>
                <p className="text-white font-medium">{risk.risk_category}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">风险等级</span>
                <p className="mt-1">
                  <Badge
                    variant={levelBadge.variant}
                    className={levelBadge.bgColor}
                  >
                    {levelBadge.label}
                  </Badge>
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">状态</span>
                <p className="mt-1">
                  <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
                </p>
              </div>
            </div>

            {/* Description */}
            {risk.description && (
              <div>
                <span className="text-sm text-slate-400">风险描述</span>
                <p className="text-white mt-1 whitespace-pre-wrap">
                  {risk.description}
                </p>
              </div>
            )}

            {/* Risk Matrix */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <h4 className="text-sm font-medium text-white mb-3">风险评估矩阵</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-400">发生概率</span>
                  <p className="text-white font-medium">
                    {getProbabilityLabel(risk.probability)}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">影响程度</span>
                  <p className="text-white font-medium">
                    {getImpactLabel(risk.impact)}
                  </p>
                </div>
              </div>
            </div>

            {/* Response Plan */}
            {risk.response_strategy && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">应对计划</h4>
                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-xs text-slate-400">应对策略</span>
                    <p className="text-white mt-1">{risk.response_strategy}</p>
                  </div>
                  {risk.response_plan && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">应对措施</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {risk.response_plan}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Owner & Tracking */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">负责人</span>
                <p className="text-white font-medium">
                  {risk.owner_name || '未分配'}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">跟踪日期</span>
                <p className="text-white font-medium">
                  {risk.follow_up_date
                    ? formatDate(risk.follow_up_date)
                    : '未设置'}
                </p>
              </div>
              {risk.last_update && (
                <div className="col-span-2">
                  <span className="text-sm text-slate-400">最新进展</span>
                  <p className="text-white mt-1 whitespace-pre-wrap">
                    {risk.last_update}
                  </p>
                </div>
              )}
            </div>

            {/* Trigger Condition */}
            {risk.trigger_condition && (
              <div>
                <span className="text-sm text-slate-400">触发条件</span>
                <p className="text-white mt-1">{risk.trigger_condition}</p>
              </div>
            )}

            {/* Close Info */}
            {risk.status === 'CLOSED' && (
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span className="text-xs text-slate-400">关闭信息</span>
                <div className="mt-2 space-y-1">
                  {risk.closed_date && (
                    <p className="text-white text-sm">
                      关闭日期: {formatDate(risk.closed_date)}
                    </p>
                  )}
                  {risk.closed_reason && (
                    <p className="text-white text-sm whitespace-pre-wrap">
                      关闭原因: {risk.closed_reason}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}



