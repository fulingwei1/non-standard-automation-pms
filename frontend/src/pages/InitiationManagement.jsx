import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { pmoApi } from '../services/api'
import { formatDate, formatCurrency } from '../lib/utils'
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
  FileText,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  AlertCircle,
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

const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: '草稿', variant: 'secondary' },
    SUBMITTED: { label: '已提交', variant: 'info' },
    REVIEWING: { label: '评审中', variant: 'warning' },
    APPROVED: { label: '已通过', variant: 'success' },
    REJECTED: { label: '已驳回', variant: 'danger' },
  }
  return badges[status] || badges.DRAFT
}

export default function InitiationManagement() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [initiations, setInitiations] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchData()
  }, [page, keyword, statusFilter])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
        status: statusFilter || undefined,
      }
      const res = await pmoApi.initiations.list(params)
      console.log('[立项管理] API响应完整对象:', res)
      console.log('[立项管理] res.data类型:', typeof res.data)
      console.log('[立项管理] res.data:', res.data)
      console.log('[立项管理] res.data是否为对象:', res.data && typeof res.data === 'object')
      console.log('[立项管理] res.data是否有items:', res.data && 'items' in res.data)
      
      // axios 返回的响应结构: { data: {...}, status: 200, ... }
      // FastAPI 直接返回 PaginatedResponse，所以 res.data 就是 PaginatedResponse
      const data = res.data
      console.log('[立项管理] 处理后的data:', data)
      console.log('[立项管理] data.items类型:', Array.isArray(data?.items) ? '数组' : typeof data?.items)
      // Handle PaginatedResponse format
      if (data && typeof data === 'object' && 'items' in data) {
        console.log('[立项管理] 找到items字段，数量:', data.items?.length || 0)
        console.log('[立项管理] items内容:', data.items)
        console.log('[立项管理] total:', data.total)
        const itemsArray = Array.isArray(data.items) ? data.items : []
        console.log('[立项管理] 准备设置的数据，数量:', itemsArray.length)
        setInitiations(itemsArray)
        setTotal(data.total || 0)
        console.log('[立项管理] 状态已更新，initiations数量:', itemsArray.length)
      } else if (Array.isArray(data)) {
        console.log('[立项管理] data是数组，数量:', data.length)
        setInitiations(data)
        setTotal(data.length)
      } else {
        console.warn('[立项管理] 无法识别数据格式:', data)
        setInitiations([])
        setTotal(0)
      }
    } catch (err) {
      console.error('[立项管理] 获取数据失败:', err)
      console.error('[立项管理] 错误详情:', err.response?.data)
      console.error('[立项管理] 错误状态码:', err.response?.status)
      setError(err.response?.data?.detail || err.message || '加载数据失败')
      setInitiations([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (formData) => {
    try {
      await pmoApi.initiations.create(formData)
      setCreateDialogOpen(false)
      fetchData()
    } catch (err) {
      console.error('Failed to create initiation:', err)
      alert('创建失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleSubmit = async (id) => {
    try {
      await pmoApi.initiations.submit(id)
      fetchData()
    } catch (err) {
      console.error('Failed to submit initiation:', err)
      alert('提交失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  return (
    <div>
      <PageHeader
        title="立项管理"
        description="项目立项申请与评审管理"
        action={
          <Button
            onClick={() => setCreateDialogOpen(true)}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            新建申请
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="搜索申请编号、项目名称..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full"
                icon={Search}
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部状态</option>
              <option value="DRAFT">草稿</option>
              <option value="SUBMITTED">已提交</option>
              <option value="REVIEWING">评审中</option>
              <option value="APPROVED">已通过</option>
              <option value="REJECTED">已驳回</option>
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
                onClick={fetchData}
                className="border-red-500/30 text-red-400 hover:bg-red-500/20"
              >
                重试
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* List */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {Array(5)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      ) : error ? null : (
        <>
          {console.log('[立项管理] 渲染时 - loading:', loading, 'error:', error, 'initiations.length:', initiations.length)}
          {console.log('[立项管理] initiations内容:', initiations)}
          {initiations.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {initiations.map((initiation, index) => {
            console.log(`[立项管理] 渲染第${index}项:`, initiation)
            console.log(`[立项管理] 第${index}项 - id:`, initiation?.id, 'project_name:', initiation?.project_name)
            if (!initiation || !initiation.id) {
              console.warn(`[立项管理] 第${index}项数据无效:`, initiation)
              return null
            }
            const statusBadge = getStatusBadge(initiation.status)
            return (
              <motion.div key={initiation.id} variants={staggerChild}>
                <Card className="hover:bg-white/[0.02] transition-colors">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20">
                          <FileText className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">
                            {initiation.project_name}
                          </h3>
                          <p className="text-xs text-slate-500">
                            {initiation.application_no}
                          </p>
                        </div>
                      </div>
                      <Badge variant={statusBadge.variant}>
                        {statusBadge.label}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-slate-400">客户名称</span>
                        <p className="text-white mt-1">{initiation.customer_name}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">合同金额</span>
                        <p className="text-white mt-1">
                          {initiation.contract_amount
                            ? formatCurrency(initiation.contract_amount)
                            : '未设置'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">申请人</span>
                        <p className="text-white mt-1">
                          {initiation.applicant_name || '未知'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-400">申请时间</span>
                        <p className="text-white mt-1">
                          {initiation.apply_time
                            ? formatDate(initiation.apply_time)
                            : '未设置'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2">
                        {initiation.status === 'DRAFT' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleSubmit(initiation.id)}
                          >
                            提交评审
                          </Button>
                        )}
                        {initiation.status === 'APPROVED' && initiation.project_id && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/projects/${initiation.project_id}`)}
                          >
                            查看项目
                          </Button>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/pmo/initiations/${initiation.id}`)}
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
      ) : (
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            {console.log('[立项管理] 显示空状态')}
            暂无立项申请
          </CardContent>
        </Card>
      )}
        </>
      )}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            上一页
          </Button>
          <span className="text-sm text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(total / pageSize)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* Create Dialog */}
      <CreateInitiationDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate}
      />
    </div>
  )
}

function CreateInitiationDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    project_name: '',
    project_type: 'NEW',
    project_level: '',
    customer_name: '',
    contract_no: '',
    contract_amount: '',
    required_start_date: '',
    required_end_date: '',
    requirement_summary: '',
    technical_difficulty: '',
    estimated_hours: '',
    resource_requirements: '',
    risk_assessment: '',
  })

  const handleSubmit = () => {
    if (!formData.project_name || !formData.customer_name) {
      alert('请填写项目名称和客户名称')
      return
    }
    onSubmit(formData)
    setFormData({
      project_name: '',
      project_type: 'NEW',
      project_level: '',
      customer_name: '',
      contract_no: '',
      contract_amount: '',
      required_start_date: '',
      required_end_date: '',
      requirement_summary: '',
      technical_difficulty: '',
      estimated_hours: '',
      resource_requirements: '',
      risk_assessment: '',
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建立项申请</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  项目名称 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.project_name}
                  onChange={(e) =>
                    setFormData({ ...formData, project_name: e.target.value })
                  }
                  placeholder="请输入项目名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  客户名称 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_name: e.target.value })
                  }
                  placeholder="请输入客户名称"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  合同编号
                </label>
                <Input
                  value={formData.contract_no}
                  onChange={(e) =>
                    setFormData({ ...formData, contract_no: e.target.value })
                  }
                  placeholder="请输入合同编号"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  合同金额
                </label>
                <Input
                  type="number"
                  value={formData.contract_amount}
                  onChange={(e) =>
                    setFormData({ ...formData, contract_amount: e.target.value })
                  }
                  placeholder="请输入合同金额"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  要求开始日期
                </label>
                <Input
                  type="date"
                  value={formData.required_start_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      required_start_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  要求交付日期
                </label>
                <Input
                  type="date"
                  value={formData.required_end_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      required_end_date: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                需求概述
              </label>
              <textarea
                value={formData.requirement_summary}
                onChange={(e) =>
                  setFormData({ ...formData, requirement_summary: e.target.value })
                }
                placeholder="请输入需求概述"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={3}
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

