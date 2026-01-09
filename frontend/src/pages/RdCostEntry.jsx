import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { rdProjectApi } from '../services/api'
import { formatDate, formatCurrency } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui'
import {
  ArrowLeft,
  Plus,
  Save,
  Calculator,
  DollarSign,
  Calendar,
  FileText,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'

const costTypeMap = {
  LABOR: { label: '人工费用', color: 'primary' },
  MATERIAL: { label: '材料费用', color: 'blue' },
  EQUIPMENT: { label: '设备费用', color: 'purple' },
  DEPRECIATION: { label: '折旧费用', color: 'indigo' },
  AMORTIZATION: { label: '摊销费用', color: 'pink' },
  OTHER: { label: '其他费用', color: 'gray' },
}

export default function RdCostEntry() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [costTypes, setCostTypes] = useState([])
  const [costs, setCosts] = useState([])
  const [formOpen, setFormOpen] = useState(false)
  const [formData, setFormData] = useState({
    cost_type_id: '',
    cost_date: new Date().toISOString().split('T')[0],
    cost_amount: '',
    deductible_amount: '',
    cost_description: '',
    remark: '',
  })
  const [formLoading, setFormLoading] = useState(false)

  useEffect(() => {
    if (id) {
      fetchProject()
      fetchCostTypes()
      fetchCosts()
    }
  }, [id])

  const fetchProject = async () => {
    try {
      const response = await rdProjectApi.get(id)
      const projectData = response.data?.data || response.data || response
      setProject(projectData)
    } catch (err) {
      console.error('Failed to fetch project:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCostTypes = async () => {
    try {
      const response = await rdProjectApi.getCostTypes()
      const data = response.data?.data || response.data || response
      setCostTypes(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to fetch cost types:', err)
      setCostTypes([])
    }
  }

  const fetchCosts = async () => {
    try {
      const response = await rdProjectApi.getCosts({ rd_project_id: id, page_size: 100 })
      const data = response.data || response
      setCosts(data.items || data || [])
    } catch (err) {
      console.error('Failed to fetch costs:', err)
      setCosts([])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    try {
      const submitData = {
        rd_project_id: parseInt(id),
        cost_type_id: parseInt(formData.cost_type_id),
        cost_date: formData.cost_date,
        cost_amount: parseFloat(formData.cost_amount),
        deductible_amount: formData.deductible_amount
          ? parseFloat(formData.deductible_amount)
          : null,
        cost_description: formData.cost_description || '',
        remark: formData.remark || '',
      }

      await rdProjectApi.createCost(submitData)
      setFormOpen(false)
      setFormData({
        cost_type_id: '',
        cost_date: new Date().toISOString().split('T')[0],
        cost_amount: '',
        deductible_amount: '',
        cost_description: '',
        remark: '',
      })
      fetchCosts()
      fetchProject() // Refresh project to update total_cost
    } catch (err) {
      alert('录入费用失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setFormLoading(false)
    }
  }

  const handleCalculateLabor = async () => {
    if (!formData.cost_date) {
      alert('请先选择费用日期')
      return
    }

    try {
      setFormLoading(true)
      const response = await rdProjectApi.calculateLaborCost({
        rd_project_id: parseInt(id),
        cost_date: formData.cost_date,
      })
      const data = response.data?.data || response.data || response
      if (data.total_cost && data.total_cost > 0) {
        setFormData({
          ...formData,
          cost_amount: data.total_cost.toString(),
          cost_description: `人工费用自动计算（${data.total_hours || 0}小时）`,
        })
      } else {
        alert('该日期无工时数据，无法自动计算人工费用')
      }
    } catch (err) {
      alert('计算人工费用失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setFormLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">研发项目不存在</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/rd-projects')}>
          返回列表
        </Button>
      </div>
    )
  }

  const selectedCostType = costTypes.find((t) => t.id === parseInt(formData.cost_type_id))
  const isLaborType = selectedCostType?.cost_type_code === 'LABOR'

  return (
    <motion.div initial="hidden" animate="visible">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/rd-projects/${id}`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">研发费用录入</h1>
            <p className="text-sm text-slate-400 mt-1">{project.project_name}</p>
          </div>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          录入费用
        </Button>
      </div>

      {/* Summary Card */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">预算金额</p>
              <p className="text-xl font-semibold text-white">
                {formatCurrency(project.budget_amount || 0)}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">已归集费用</p>
              <p className="text-xl font-semibold text-emerald-400">
                {formatCurrency(project.total_cost || 0)}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">费用记录数</p>
              <p className="text-xl font-semibold text-white">{costs.length}</p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">剩余预算</p>
              <p className="text-xl font-semibold text-primary">
                {formatCurrency(
                  (project.budget_amount || 0) - (project.total_cost || 0)
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cost List */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">费用明细</h3>
          {costs.length > 0 ? (
            <div className="space-y-3">
              {costs.map((cost) => {
                const costType = costTypes.find((t) => t.id === cost.cost_type_id)
                return (
                  <div
                    key={cost.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-white">
                          {cost.cost_no || `费用-${cost.id}`}
                        </p>
                        <Badge variant="outline" className="text-xs">
                          {costType?.cost_type_name || '未知类型'}
                        </Badge>
                        {cost.cost_date && (
                          <Badge variant="secondary" className="text-xs">
                            {formatDate(cost.cost_date)}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-slate-400">
                        {cost.cost_description || '无描述'}
                      </p>
                      {cost.remark && (
                        <p className="text-xs text-slate-500 mt-1">{cost.remark}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-white">
                        {formatCurrency(cost.cost_amount || 0)}
                      </p>
                      {cost.deductible_amount && cost.deductible_amount > 0 && (
                        <p className="text-xs text-primary">
                          扣除: {formatCurrency(cost.deductible_amount)}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>暂无费用记录</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setFormOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                录入第一条费用
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Entry Form Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>录入研发费用</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <DialogBody className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    费用类型 <span className="text-red-500">*</span>
                  </label>
                  <Select
                    value={formData.cost_type_id?.toString() || ''}
                    onValueChange={(value) =>
                      setFormData({ ...formData, cost_type_id: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="请选择费用类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__empty__">请选择费用类型</SelectItem>
                      {costTypes.map((type) => (
                        <SelectItem key={type.id} value={type.id.toString()}>
                          {type.cost_type_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    费用日期 <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="date"
                    value={formData.cost_date}
                    onChange={(e) =>
                      setFormData({ ...formData, cost_date: e.target.value })
                    }
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    费用金额 <span className="text-red-500">*</span>
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      step="0.01"
                      value={formData.cost_amount}
                      onChange={(e) =>
                        setFormData({ ...formData, cost_amount: e.target.value })
                      }
                      placeholder="0.00"
                      required
                      className="flex-1"
                    />
                    {isLaborType && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleCalculateLabor}
                        disabled={formLoading}
                      >
                        <Calculator className="h-4 w-4 mr-2" />
                        自动计算
                      </Button>
                    )}
                  </div>
                  {isLaborType && (
                    <p className="text-xs text-slate-500 mt-1">
                      点击"自动计算"可根据该日期的工时数据自动计算人工费用
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    加计扣除金额
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.deductible_amount}
                    onChange={(e) =>
                      setFormData({ ...formData, deductible_amount: e.target.value })
                    }
                    placeholder="0.00"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    可加计扣除的费用金额（175%扣除）
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  费用描述
                </label>
                <textarea
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={3}
                  value={formData.cost_description}
                  onChange={(e) =>
                    setFormData({ ...formData, cost_description: e.target.value })
                  }
                  placeholder="请输入费用描述"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  备注
                </label>
                <textarea
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={2}
                  value={formData.remark}
                  onChange={(e) =>
                    setFormData({ ...formData, remark: e.target.value })
                  }
                  placeholder="请输入备注"
                />
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setFormOpen(false)}
              >
                取消
              </Button>
              <Button type="submit" loading={formLoading}>
                <Save className="h-4 w-4 mr-2" />
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

