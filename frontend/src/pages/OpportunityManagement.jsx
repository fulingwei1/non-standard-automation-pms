/**
 * Opportunity Management Page - Sales opportunity management
 * Features: Opportunity list, creation, update, gate management
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  Target,
  DollarSign,
  Calendar,
  User,
  Building2,
  CheckCircle2,
  XCircle,
  Clock,
  Edit,
  Eye,
  ArrowRight,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label,
  Textarea,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { opportunityApi, customerApi } from '../services/api'

// 商机阶段配置
const stageConfig = {
  DISCOVERY: { label: '需求澄清', color: 'bg-blue-500', textColor: 'text-blue-400' },
  QUALIFIED: { label: '商机合格', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  PROPOSAL: { label: '方案/报价中', color: 'bg-amber-500', textColor: 'text-amber-400' },
  NEGOTIATION: { label: '商务谈判', color: 'bg-purple-500', textColor: 'text-purple-400' },
  WON: { label: '赢单', color: 'bg-green-500', textColor: 'text-green-400' },
  LOST: { label: '丢单', color: 'bg-red-500', textColor: 'text-red-400' },
  ON_HOLD: { label: '暂停', color: 'bg-slate-500', textColor: 'text-slate-400' },
}

export default function OpportunityManagement() {
  const [opportunities, setOpportunities] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [stageFilter, setStageFilter] = useState('all')
  const [selectedOpp, setSelectedOpp] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showGateDialog, setShowGateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const [formData, setFormData] = useState({
    customer_id: '',
    opp_name: '',
    project_type: '',
    equipment_type: '',
    stage: 'DISCOVERY',
    est_amount: '',
    est_margin: '',
    budget_range: '',
    decision_chain: '',
    delivery_window: '',
    acceptance_basis: '',
    requirement: {
      product_object: '',
      ct_seconds: '',
      interface_desc: '',
      site_constraints: '',
      acceptance_criteria: '',
    },
  })

  const [gateData, setGateData] = useState({
    gate_status: 'PASS',
    remark: '',
  })

  const loadOpportunities = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        stage: stageFilter !== 'all' ? stageFilter : undefined,
      }
      const response = await opportunityApi.list(params)
      if (response.data && response.data.items) {
        setOpportunities(response.data.items)
        setTotal(response.data.total || 0)
      }
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 })
      if (response.data && response.data.items) {
        setCustomers(response.data.items)
      }
    } catch (error) {
    }
  }

  useEffect(() => {
    loadOpportunities()
  }, [page, searchTerm, stageFilter])

  useEffect(() => {
    loadCustomers()
  }, [])

  const handleCreate = async () => {
    try {
      await opportunityApi.create(formData)
      setShowCreateDialog(false)
      resetForm()
      loadOpportunities()
    } catch (error) {
      alert('创建商机失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleUpdate = async () => {
    if (!selectedOpp) return
    try {
      await opportunityApi.update(selectedOpp.id, formData)
      setShowEditDialog(false)
      setSelectedOpp(null)
      loadOpportunities()
    } catch (error) {
      alert('更新商机失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSubmitGate = async () => {
    if (!selectedOpp) return
    try {
      await opportunityApi.submitGate(selectedOpp.id, gateData)
      setShowGateDialog(false)
      setSelectedOpp(null)
      loadOpportunities()
    } catch (error) {
      alert('提交阶段门失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEdit = (opp) => {
    setSelectedOpp(opp)
    setFormData({
      customer_id: opp.customer_id || '',
      opp_name: opp.opp_name || '',
      project_type: opp.project_type || '',
      equipment_type: opp.equipment_type || '',
      stage: opp.stage || 'DISCOVERY',
      est_amount: opp.est_amount || '',
      est_margin: opp.est_margin || '',
      budget_range: opp.budget_range || '',
      decision_chain: opp.decision_chain || '',
      delivery_window: opp.delivery_window || '',
      acceptance_basis: opp.acceptance_basis || '',
      requirement: opp.requirement || {
        product_object: '',
        ct_seconds: '',
        interface_desc: '',
        site_constraints: '',
        acceptance_criteria: '',
      },
    })
    setShowEditDialog(true)
  }

  const resetForm = () => {
    setFormData({
      customer_id: '',
      opp_name: '',
      project_type: '',
      equipment_type: '',
      stage: 'DISCOVERY',
      est_amount: '',
      est_margin: '',
      budget_range: '',
      decision_chain: '',
      delivery_window: '',
      acceptance_basis: '',
      requirement: {
        product_object: '',
        ct_seconds: '',
        interface_desc: '',
        site_constraints: '',
        acceptance_criteria: '',
      },
    })
  }

  // 查看详情
  const handleViewDetail = async (opp) => {
    try {
      const response = await opportunityApi.get(opp.id)
      if (response.data) {
        setSelectedOpp(response.data)
        setShowDetailDialog(true)
      }
    } catch (error) {
      setSelectedOpp(opp)
      setShowDetailDialog(true)
    }
  }

  const stats = useMemo(() => {
    return {
      total: total,
      discovery: opportunities.filter((o) => o.stage === 'DISCOVERY').length,
      proposal: opportunities.filter((o) => o.stage === 'PROPOSAL').length,
      won: opportunities.filter((o) => o.stage === 'WON').length,
      totalAmount: opportunities.reduce((sum, o) => sum + (parseFloat(o.est_amount) || 0), 0),
    }
  }, [opportunities, total])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="商机管理"
        description="管理销售商机，跟踪项目进展"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建商机
          </Button>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总商机数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">需求澄清</p>
                <p className="text-2xl font-bold text-white">{stats.discovery}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">报价中</p>
                <p className="text-2xl font-bold text-white">{stats.proposal}</p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">预估金额</p>
                <p className="text-2xl font-bold text-white">
                  {(stats.totalAmount / 10000).toFixed(1)}万
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索商机编码、名称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  阶段: {stageFilter === 'all' ? '全部' : stageConfig[stageFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStageFilter('all')}>全部</DropdownMenuItem>
                {Object.entries(stageConfig).map(([key, config]) => (
                  <DropdownMenuItem key={key} onClick={() => setStageFilter(key)}>
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>

      {/* 商机列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : opportunities.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无商机数据</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {opportunities.map((opp) => (
            <motion.div key={opp.id} variants={fadeIn} whileHover={{ y: -4 }}>
              <Card className="h-full hover:border-blue-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{opp.opp_code}</CardTitle>
                      <p className="text-sm text-slate-400 mt-1">{opp.opp_name}</p>
                    </div>
                    <Badge className={cn(stageConfig[opp.stage]?.color)}>
                      {stageConfig[opp.stage]?.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-300">
                      <Building2 className="h-4 w-4 text-slate-400" />
                      {opp.customer_name}
                    </div>
                    {opp.est_amount && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <DollarSign className="h-4 w-4 text-slate-400" />
                        {parseFloat(opp.est_amount).toLocaleString()} 元
                      </div>
                    )}
                    {opp.owner_name && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <User className="h-4 w-4 text-slate-400" />
                        负责人: {opp.owner_name}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDetail(opp)}
                      className="flex-1"
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      详情
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(opp)}
                      className="flex-1"
                    >
                      <Edit className="mr-2 h-4 w-4" />
                      编辑
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedOpp(opp)
                        setShowGateDialog(true)
                      }}
                      className="flex-1"
                    >
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      阶段门
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 创建商机对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建商机</DialogTitle>
            <DialogDescription>创建新的销售商机</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>客户 *</Label>
                <select
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择客户</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.customer_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>商机名称 *</Label>
                <Input
                  value={formData.opp_name}
                  onChange={(e) => setFormData({ ...formData, opp_name: e.target.value })}
                  placeholder="请输入商机名称"
                />
              </div>
              <div>
                <Label>项目类型</Label>
                <Input
                  value={formData.project_type}
                  onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                  placeholder="单机/线体/改造"
                />
              </div>
              <div>
                <Label>设备类型</Label>
                <Input
                  value={formData.equipment_type}
                  onChange={(e) => setFormData({ ...formData, equipment_type: e.target.value })}
                  placeholder="ICT/FCT/EOL"
                />
              </div>
              <div>
                <Label>阶段</Label>
                <select
                  value={formData.stage}
                  onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  {Object.entries(stageConfig).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>预估金额</Label>
                <Input
                  type="number"
                  value={formData.est_amount}
                  onChange={(e) => setFormData({ ...formData, est_amount: e.target.value })}
                  placeholder="请输入预估金额"
                />
              </div>
              <div>
                <Label>预估毛利率 (%)</Label>
                <Input
                  type="number"
                  value={formData.est_margin}
                  onChange={(e) => setFormData({ ...formData, est_margin: e.target.value })}
                  placeholder="请输入预估毛利率"
                />
              </div>
              <div>
                <Label>预算范围</Label>
                <Input
                  value={formData.budget_range}
                  onChange={(e) => setFormData({ ...formData, budget_range: e.target.value })}
                  placeholder="如: 80-120万"
                />
              </div>
            </div>
            <div>
              <Label>决策链</Label>
              <Textarea
                value={formData.decision_chain}
                onChange={(e) => setFormData({ ...formData, decision_chain: e.target.value })}
                placeholder="请输入决策链信息"
                rows={2}
              />
            </div>
            <div>
              <Label>交付窗口</Label>
              <Input
                value={formData.delivery_window}
                onChange={(e) => setFormData({ ...formData, delivery_window: e.target.value })}
                placeholder="如: 2026年Q2"
              />
            </div>
            <div>
              <Label>验收依据</Label>
              <Textarea
                value={formData.acceptance_basis}
                onChange={(e) => setFormData({ ...formData, acceptance_basis: e.target.value })}
                placeholder="请输入验收依据"
                rows={2}
              />
            </div>
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-sm font-semibold mb-2">需求信息</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>产品对象</Label>
                  <Input
                    value={formData.requirement.product_object}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        requirement: { ...formData.requirement, product_object: e.target.value },
                      })
                    }
                    placeholder="如: PCB板"
                  />
                </div>
                <div>
                  <Label>节拍 (秒)</Label>
                  <Input
                    type="number"
                    value={formData.requirement.ct_seconds}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        requirement: { ...formData.requirement, ct_seconds: e.target.value },
                      })
                    }
                    placeholder="如: 1"
                  />
                </div>
                <div className="col-span-2">
                  <Label>接口/通信协议</Label>
                  <Textarea
                    value={formData.requirement.interface_desc}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        requirement: { ...formData.requirement, interface_desc: e.target.value },
                      })
                    }
                    placeholder="如: RS232/以太网"
                    rows={2}
                  />
                </div>
                <div className="col-span-2">
                  <Label>现场约束</Label>
                  <Textarea
                    value={formData.requirement.site_constraints}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        requirement: { ...formData.requirement, site_constraints: e.target.value },
                      })
                    }
                    placeholder="请输入现场约束条件"
                    rows={2}
                  />
                </div>
                <div className="col-span-2">
                  <Label>验收依据</Label>
                  <Textarea
                    value={formData.requirement.acceptance_criteria}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        requirement: { ...formData.requirement, acceptance_criteria: e.target.value },
                      })
                    }
                    placeholder="如: 节拍≤1秒，良率≥99.5%"
                    rows={2}
                  />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 阶段门对话框 */}
      <Dialog open={showGateDialog} onOpenChange={setShowGateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>提交阶段门</DialogTitle>
            <DialogDescription>提交商机阶段门审核</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>阶段门状态 *</Label>
              <select
                value={gateData.gate_status}
                onChange={(e) => setGateData({ ...gateData, gate_status: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="PASS">通过</option>
                <option value="REJECT">拒绝</option>
              </select>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={gateData.remark}
                onChange={(e) => setGateData({ ...gateData, remark: e.target.value })}
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitGate}>提交</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>商机详情</DialogTitle>
            <DialogDescription>查看商机详细信息和需求</DialogDescription>
          </DialogHeader>
          {selectedOpp && (
            <div className="space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">基本信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">商机编码</Label>
                    <p className="text-white">{selectedOpp.opp_code}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">商机名称</Label>
                    <p className="text-white">{selectedOpp.opp_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">客户</Label>
                    <p className="text-white">{selectedOpp.customer_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">阶段</Label>
                    <Badge className={cn(stageConfig[selectedOpp.stage]?.color, 'mt-1')}>
                      {stageConfig[selectedOpp.stage]?.label}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-slate-400">项目类型</Label>
                    <p className="text-white">{selectedOpp.project_type || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">设备类型</Label>
                    <p className="text-white">{selectedOpp.equipment_type || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">预估金额</Label>
                    <p className="text-white">
                      {selectedOpp.est_amount
                        ? parseFloat(selectedOpp.est_amount).toLocaleString() + ' 元'
                        : '-'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">预估毛利率</Label>
                    <p className="text-white">
                      {selectedOpp.est_margin ? selectedOpp.est_margin + '%' : '-'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">预算范围</Label>
                    <p className="text-white">{selectedOpp.budget_range || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">交付窗口</Label>
                    <p className="text-white">{selectedOpp.delivery_window || '-'}</p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">决策链</Label>
                    <p className="text-white mt-1">{selectedOpp.decision_chain || '-'}</p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">验收依据</Label>
                    <p className="text-white mt-1">{selectedOpp.acceptance_basis || '-'}</p>
                  </div>
                </div>
              </div>

              {/* 需求信息 */}
              {selectedOpp.requirement && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">需求信息</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-400">产品对象</Label>
                      <p className="text-white">
                        {selectedOpp.requirement.product_object || '-'}
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">节拍 (秒)</Label>
                      <p className="text-white">{selectedOpp.requirement.ct_seconds || '-'}</p>
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">接口/通信协议</Label>
                      <p className="text-white mt-1">
                        {selectedOpp.requirement.interface_desc || '-'}
                      </p>
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">现场约束</Label>
                      <p className="text-white mt-1">
                        {selectedOpp.requirement.site_constraints || '-'}
                      </p>
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">验收依据</Label>
                      <p className="text-white mt-1">
                        {selectedOpp.requirement.acceptance_criteria || '-'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}



