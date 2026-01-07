import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Plus,
  Edit,
  Trash2,
  ToggleLeft,
  ToggleRight,
  AlertTriangle,
  Search,
  Filter,
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
import { fadeIn, staggerContainer } from '../lib/animations'
import { alertApi } from '../services/api'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'

const alertCategories = [
  { value: 'PROJECT', label: '项目类' },
  { value: 'TASK', label: '任务类' },
  { value: 'PURCHASE', label: '采购类' },
  { value: 'OUTSOURCING', label: '外协类' },
  { value: 'COST', label: '成本类' },
  { value: 'QUALITY', label: '质量类' },
]

const checkIntervals = [
  { value: 'realtime', label: '实时' },
  { value: 'hourly', label: '每小时' },
  { value: 'daily', label: '每日' },
]

export default function AlertRuleConfig() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [showDialog, setShowDialog] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [formData, setFormData] = useState({
    rule_code: '',
    rule_name: '',
    rule_type: '',
    category: '',
    description: '',
    threshold_warning: '',
    threshold_critical: '',
    threshold_urgent: '',
    check_interval: 'daily',
    is_active: true,
  })

  useEffect(() => {
    loadRules()
  }, [selectedCategory])

  const loadRules = async () => {
    try {
      setLoading(true)
      const res = await alertApi.rules.list({
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
      })
      setRules(res.data.items || res.data || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load rules:', err)
      const errorMessage = err.response?.data?.detail || err.message || '加载规则失败'
      setError(errorMessage)
      // 如果是演示账号，使用空数组
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setRules([])
        setError(null) // Clear error for demo accounts
      } else {
        setRules([])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingRule(null)
    setFormData({
      rule_code: '',
      rule_name: '',
      rule_type: '',
      category: '',
      description: '',
      threshold_warning: '',
      threshold_critical: '',
      threshold_urgent: '',
      check_interval: 'daily',
      is_active: true,
    })
    setShowDialog(true)
  }

  const handleEdit = (rule) => {
    setEditingRule(rule)
    setFormData({
      rule_code: rule.rule_code,
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      category: rule.category,
      description: rule.description || '',
      threshold_warning: rule.threshold_warning || '',
      threshold_critical: rule.threshold_critical || '',
      threshold_urgent: rule.threshold_urgent || '',
      check_interval: rule.check_interval || 'daily',
      is_active: rule.is_active !== false,
    })
    setShowDialog(true)
  }

  const handleSave = async () => {
    try {
      if (editingRule) {
        await alertApi.rules.update(editingRule.id, formData)
        toast.success('规则更新成功')
      } else {
        await alertApi.rules.create(formData)
        toast.success('规则创建成功')
      }
      await loadRules()
      setShowDialog(false)
    } catch (error) {
      console.error('Failed to save rule:', error)
      const errorMessage = error.response?.data?.detail || error.message || '保存失败，请稍后重试'
      toast.error(errorMessage)
    }
  }

  const handleToggle = async (ruleId, enabled) => {
    try {
      await alertApi.rules.toggle(ruleId, enabled)
      await loadRules()
    } catch (error) {
      console.error('Failed to toggle rule:', error)
      const errorMessage = error.response?.data?.detail || error.message || '操作失败，请稍后重试'
      toast.error(errorMessage)
    }
  }

  const handleDelete = async (ruleId) => {
    if (!confirm('确定要删除此规则吗？')) return
    try {
      await alertApi.rules.delete(ruleId)
      await loadRules()
      toast.success('规则已删除')
    } catch (error) {
      console.error('Failed to delete rule:', error)
      const errorMessage = error.response?.data?.detail || error.message || '删除失败，请稍后重试'
      toast.error(errorMessage)
    }
  }

  const filteredRules = rules.filter((rule) => {
    const matchesSearch =
      !searchQuery ||
      rule.rule_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rule.rule_code.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSearch
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警规则配置"
        actions={
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="w-4 h-4" />
            新建规则
          </Button>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索规则..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-slate-800/50 border-slate-700"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                {['ALL', ...alertCategories.map((c) => c.value)].map((cat) => (
                  <Button
                    key={cat}
                    variant={selectedCategory === cat ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat === 'ALL' ? '全部' : alertCategories.find((c) => c.value === cat)?.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Rules List */}
        {loading ? (
          <LoadingSpinner text="加载规则配置..." />
        ) : error ? (
          <ErrorMessage
            error={error}
            onRetry={loadRules}
            title="加载规则失败"
          />
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {filteredRules.length === 0 ? (
              <EmptyState
                icon={AlertTriangle}
                title="暂无规则"
                description="还没有配置任何预警规则"
              />
            ) : (
              filteredRules.map((rule) => (
                <motion.div key={rule.id} variants={fadeIn}>
                  <Card className="hover:bg-slate-800/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-3">
                            <h3 className="text-white font-medium">{rule.rule_name}</h3>
                            <Badge variant="outline">{rule.rule_code}</Badge>
                            <Badge variant="secondary">
                              {alertCategories.find((c) => c.value === rule.category)?.label || rule.category}
                            </Badge>
                          </div>
                          {rule.description && (
                            <p className="text-sm text-slate-400">{rule.description}</p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span>检查频率: {checkIntervals.find((i) => i.value === rule.check_interval)?.label || rule.check_interval}</span>
                            <span>
                              阈值: 黄色≥{rule.threshold_warning} 橙色≥{rule.threshold_critical} 红色≥{rule.threshold_urgent}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggle(rule.id, !rule.is_active)}
                            className="gap-1"
                          >
                            {rule.is_active ? (
                              <ToggleRight className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <ToggleLeft className="w-4 h-4 text-slate-500" />
                            )}
                            {rule.is_active ? '启用' : '禁用'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(rule)}
                            className="gap-1"
                          >
                            <Edit className="w-3 h-3" />
                            编辑
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(rule.id)}
                            className="gap-1 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </motion.div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? '编辑规则' : '新建规则'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">规则编码</label>
              <Input
                value={formData.rule_code}
                onChange={(e) => setFormData({ ...formData, rule_code: e.target.value })}
                placeholder="PROJ_DELAY"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">规则名称</label>
              <Input
                value={formData.rule_name}
                onChange={(e) => setFormData({ ...formData, rule_name: e.target.value })}
                placeholder="项目进度延期预警"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">规则分类</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="">请选择</option>
                  {alertCategories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">检查频率</label>
                <select
                  value={formData.check_interval}
                  onChange={(e) => setFormData({ ...formData, check_interval: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  {checkIntervals.map((interval) => (
                    <option key={interval.value} value={interval.value}>
                      {interval.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">规则描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="项目实际进度落后于计划进度时触发"
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white min-h-[80px]"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">🟡 黄色预警阈值</label>
                <Input
                  type="number"
                  value={formData.threshold_warning}
                  onChange={(e) => setFormData({ ...formData, threshold_warning: e.target.value })}
                  placeholder="3"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">🟠 橙色预警阈值</label>
                <Input
                  type="number"
                  value={formData.threshold_critical}
                  onChange={(e) => setFormData({ ...formData, threshold_critical: e.target.value })}
                  placeholder="7"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">🔴 红色预警阈值</label>
                <Input
                  type="number"
                  value={formData.threshold_urgent}
                  onChange={(e) => setFormData({ ...formData, threshold_urgent: e.target.value })}
                  placeholder="14"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

