/**
 * Lead Management Page - Sales lead management
 * Features: Lead list, creation, update, convert to opportunity
 */

import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  LayoutGrid,
  List,
  Calendar,
  Building2,
  User,
  Phone,
  Mail,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Edit,
  Eye,
  ArrowRight,
  X,
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
import { leadApi, customerApi } from '../services/api'

// 线索状态配置
const statusConfig = {
  NEW: { label: '待跟进', color: 'bg-blue-500', textColor: 'text-blue-400' },
  QUALIFYING: { label: '资格评估中', color: 'bg-amber-500', textColor: 'text-amber-400' },
  INVALID: { label: '无效', color: 'bg-red-500', textColor: 'text-red-400' },
  CONVERTED: { label: '已转商机', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
}

export default function LeadManagement() {
  const [leads, setLeads] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedLead, setSelectedLead] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showConvertDialog, setShowConvertDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showFollowUpDialog, setShowFollowUpDialog] = useState(false)
  const [followUps, setFollowUps] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  // 表单数据
  const [formData, setFormData] = useState({
    customer_name: '',
    source: '',
    industry: '',
    contact_name: '',
    contact_phone: '',
    demand_summary: '',
    status: 'NEW',
  })

  // 跟进记录表单
  const [followUpData, setFollowUpData] = useState({
    follow_up_type: 'CALL',
    content: '',
    next_action: '',
    next_action_at: '',
  })

  // 加载线索列表
  const loadLeads = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }
      const response = await leadApi.list(params)
      if (response.data && response.data.items) {
        setLeads(response.data.items)
        setTotal(response.data.total || 0)
      }
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 加载客户列表
  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 })
      if (response.data && response.data.items) {
        setCustomers(response.data.items)
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  useEffect(() => {
    loadLeads()
  }, [page, searchTerm, statusFilter])

  useEffect(() => {
    loadCustomers()
  }, [])

  // 筛选线索
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const matchesSearch =
        lead.lead_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.contact_name?.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === 'all' || lead.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [leads, searchTerm, statusFilter])

  // 统计数据
  const stats = useMemo(() => {
    return {
      total: total,
      new: leads.filter((l) => l.status === 'NEW').length,
      qualifying: leads.filter((l) => l.status === 'QUALIFYING').length,
      converted: leads.filter((l) => l.status === 'CONVERTED').length,
    }
  }, [leads, total])

  // 创建线索
  const handleCreate = async () => {
    try {
      await leadApi.create(formData)
      setShowCreateDialog(false)
      setFormData({
        customer_name: '',
        source: '',
        industry: '',
        contact_name: '',
        contact_phone: '',
        demand_summary: '',
        status: 'NEW',
      })
      loadLeads()
    } catch (error) {
      alert('创建线索失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 更新线索
  const handleUpdate = async () => {
    if (!selectedLead) return
    try {
      await leadApi.update(selectedLead.id, formData)
      setShowEditDialog(false)
      setSelectedLead(null)
      loadLeads()
    } catch (error) {
      alert('更新线索失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 打开编辑对话框
  const handleEdit = (lead) => {
    setSelectedLead(lead)
    setFormData({
      customer_name: lead.customer_name || '',
      source: lead.source || '',
      industry: lead.industry || '',
      contact_name: lead.contact_name || '',
      contact_phone: lead.contact_phone || '',
      demand_summary: lead.demand_summary || '',
      status: lead.status || 'NEW',
    })
    setShowEditDialog(true)
  }

  // 线索转商机
  const handleConvert = async (customerId) => {
    if (!selectedLead) return
    try {
      await leadApi.convert(selectedLead.id, customerId)
      setShowConvertDialog(false)
      setSelectedLead(null)
      loadLeads()
      alert('线索已成功转为商机')
    } catch (error) {
      alert('转商机失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 查看详情
  const handleViewDetail = async (lead) => {
    setSelectedLead(lead)
    setShowDetailDialog(true)
    // 加载跟进记录
    try {
      const response = await leadApi.getFollowUps(lead.id)
      if (response.data) {
        setFollowUps(response.data)
      }
    } catch (error) {
      setFollowUps([])
    }
  }

  // 添加跟进记录
  const handleAddFollowUp = async () => {
    if (!selectedLead) return
    try {
      await leadApi.createFollowUp(selectedLead.id, followUpData)
      setShowFollowUpDialog(false)
      setFollowUpData({
        follow_up_type: 'CALL',
        content: '',
        next_action: '',
        next_action_at: '',
      })
      // 重新加载跟进记录
      const response = await leadApi.getFollowUps(selectedLead.id)
      if (response.data) {
        setFollowUps(response.data)
      }
      loadLeads() // 刷新列表
    } catch (error) {
      alert('添加跟进记录失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="线索管理"
        description="管理销售线索，跟进潜在客户需求"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建线索
          </Button>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总线索数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Building2 className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">待跟进</p>
                <p className="text-2xl font-bold text-white">{stats.new}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">评估中</p>
                <p className="text-2xl font-bold text-white">{stats.qualifying}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已转化</p>
                <p className="text-2xl font-bold text-white">{stats.converted}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
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
                placeholder="搜索线索编码、客户名称、联系人..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  状态: {statusFilter === 'all' ? '全部' : statusConfig[statusFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStatusFilter('all')}>全部</DropdownMenuItem>
                {Object.entries(statusConfig).map(([key, config]) => (
                  <DropdownMenuItem key={key} onClick={() => setStatusFilter(key)}>
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('grid')}
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="icon"
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 线索列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : filteredLeads.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无线索数据</p>
          </CardContent>
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredLeads.map((lead) => (
            <motion.div
              key={lead.id}
              variants={fadeIn}
              whileHover={{ y: -4 }}
              className="cursor-pointer"
            >
              <Card className="h-full hover:border-blue-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{lead.lead_code}</CardTitle>
                      <p className="text-sm text-slate-400 mt-1">{lead.customer_name}</p>
                    </div>
                    <Badge className={cn(statusConfig[lead.status]?.color)}>
                      {statusConfig[lead.status]?.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {lead.contact_name && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <User className="h-4 w-4 text-slate-400" />
                        {lead.contact_name}
                      </div>
                    )}
                    {lead.contact_phone && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <Phone className="h-4 w-4 text-slate-400" />
                        {lead.contact_phone}
                      </div>
                    )}
                    {lead.source && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <MapPin className="h-4 w-4 text-slate-400" />
                        来源: {lead.source}
                      </div>
                    )}
                    {lead.demand_summary && (
                      <p className="text-slate-400 line-clamp-2 mt-2">{lead.demand_summary}</p>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDetail(lead)}
                      className="flex-1"
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      详情
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(lead)}
                      className="flex-1"
                    >
                      <Edit className="mr-2 h-4 w-4" />
                      编辑
                    </Button>
                    {lead.status !== 'CONVERTED' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedLead(lead)
                          setShowConvertDialog(true)
                        }}
                        className="flex-1"
                      >
                        <ArrowRight className="mr-2 h-4 w-4" />
                        转商机
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="text-left p-4 text-slate-400">线索编码</th>
                    <th className="text-left p-4 text-slate-400">客户名称</th>
                    <th className="text-left p-4 text-slate-400">联系人</th>
                    <th className="text-left p-4 text-slate-400">联系电话</th>
                    <th className="text-left p-4 text-slate-400">来源</th>
                    <th className="text-left p-4 text-slate-400">状态</th>
                    <th className="text-left p-4 text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLeads.map((lead) => (
                    <tr key={lead.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="p-4 text-white">{lead.lead_code}</td>
                      <td className="p-4 text-slate-300">{lead.customer_name}</td>
                      <td className="p-4 text-slate-300">{lead.contact_name || '-'}</td>
                      <td className="p-4 text-slate-300">{lead.contact_phone || '-'}</td>
                      <td className="p-4 text-slate-300">{lead.source || '-'}</td>
                      <td className="p-4">
                        <Badge className={cn(statusConfig[lead.status]?.color)}>
                          {statusConfig[lead.status]?.label}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm" onClick={() => handleViewDetail(lead)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(lead)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          {lead.status !== 'CONVERTED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedLead(lead)
                                setShowConvertDialog(true)
                              }}
                            >
                              <ArrowRight className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
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

      {/* 创建线索对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建线索</DialogTitle>
            <DialogDescription>创建新的销售线索</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>客户名称 *</Label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  placeholder="请输入客户名称"
                />
              </div>
              <div>
                <Label>来源</Label>
                <Input
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  placeholder="展会/转介绍/网络等"
                />
              </div>
              <div>
                <Label>行业</Label>
                <Input
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  placeholder="请输入行业"
                />
              </div>
              <div>
                <Label>联系人</Label>
                <Input
                  value={formData.contact_name}
                  onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                  placeholder="请输入联系人"
                />
              </div>
              <div>
                <Label>联系电话</Label>
                <Input
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                  placeholder="请输入联系电话"
                />
              </div>
              <div>
                <Label>状态</Label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  {Object.entries(statusConfig).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <Label>需求摘要</Label>
              <Textarea
                value={formData.demand_summary}
                onChange={(e) => setFormData({ ...formData, demand_summary: e.target.value })}
                placeholder="请输入需求摘要"
                rows={4}
              />
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

      {/* 编辑线索对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑线索</DialogTitle>
            <DialogDescription>更新线索信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>客户名称 *</Label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                />
              </div>
              <div>
                <Label>来源</Label>
                <Input
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                />
              </div>
              <div>
                <Label>行业</Label>
                <Input
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                />
              </div>
              <div>
                <Label>联系人</Label>
                <Input
                  value={formData.contact_name}
                  onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                />
              </div>
              <div>
                <Label>联系电话</Label>
                <Input
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                />
              </div>
              <div>
                <Label>状态</Label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  {Object.entries(statusConfig).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <Label>需求摘要</Label>
              <Textarea
                value={formData.demand_summary}
                onChange={(e) => setFormData({ ...formData, demand_summary: e.target.value })}
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 转商机对话框 */}
      <Dialog open={showConvertDialog} onOpenChange={setShowConvertDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>线索转商机</DialogTitle>
            <DialogDescription>
              选择客户后，将线索转为商机
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>选择客户 *</Label>
              <select
                id="customer-select"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                onChange={(e) => {
                  const customerId = parseInt(e.target.value)
                  if (customerId) {
                    handleConvert(customerId)
                  }
                }}
              >
                <option value="">请选择客户</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.customer_name} ({customer.customer_code})
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConvertDialog(false)}>
              取消
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>线索详情</DialogTitle>
            <DialogDescription>查看线索详细信息和跟进记录</DialogDescription>
          </DialogHeader>
          {selectedLead && (
            <div className="space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">基本信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">线索编码</Label>
                    <p className="text-white">{selectedLead.lead_code}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">状态</Label>
                    <Badge className={cn(statusConfig[selectedLead.status]?.color, 'mt-1')}>
                      {statusConfig[selectedLead.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-slate-400">客户名称</Label>
                    <p className="text-white">{selectedLead.customer_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">来源</Label>
                    <p className="text-white">{selectedLead.source || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">行业</Label>
                    <p className="text-white">{selectedLead.industry || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">联系人</Label>
                    <p className="text-white">{selectedLead.contact_name || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">联系电话</Label>
                    <p className="text-white">{selectedLead.contact_phone || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">创建时间</Label>
                    <p className="text-white">
                      {selectedLead.created_at
                        ? new Date(selectedLead.created_at).toLocaleString('zh-CN')
                        : '-'}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">需求摘要</Label>
                    <p className="text-white mt-1">{selectedLead.demand_summary || '-'}</p>
                  </div>
                </div>
              </div>

              {/* 跟进记录 */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">跟进记录</h3>
                  {selectedLead.status !== 'CONVERTED' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowFollowUpDialog(true)}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      添加跟进
                    </Button>
                  )}
                </div>
                {followUps.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">暂无跟进记录</p>
                ) : (
                  <div className="space-y-3">
                    {followUps.map((followUp) => (
                      <Card key={followUp.id}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline">{followUp.follow_up_type}</Badge>
                                <span className="text-sm text-slate-400">
                                  {followUp.creator_name || '未知'}
                                </span>
                                <span className="text-sm text-slate-500">
                                  {followUp.created_at
                                    ? new Date(followUp.created_at).toLocaleString('zh-CN')
                                    : ''}
                                </span>
                              </div>
                              <p className="text-white mb-2">{followUp.content}</p>
                              {followUp.next_action && (
                                <p className="text-sm text-slate-400">
                                  下次行动: {followUp.next_action}
                                </p>
                              )}
                              {followUp.next_action_at && (
                                <p className="text-sm text-slate-400">
                                  行动时间:{' '}
                                  {new Date(followUp.next_action_at).toLocaleDateString('zh-CN')}
                                </p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 添加跟进记录对话框 */}
      <Dialog open={showFollowUpDialog} onOpenChange={setShowFollowUpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加跟进记录</DialogTitle>
            <DialogDescription>记录线索跟进情况</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>跟进类型 *</Label>
              <select
                value={followUpData.follow_up_type}
                onChange={(e) =>
                  setFollowUpData({ ...followUpData, follow_up_type: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="CALL">电话</option>
                <option value="EMAIL">邮件</option>
                <option value="VISIT">拜访</option>
                <option value="MEETING">会议</option>
                <option value="OTHER">其他</option>
              </select>
            </div>
            <div>
              <Label>跟进内容 *</Label>
              <Textarea
                value={followUpData.content}
                onChange={(e) => setFollowUpData({ ...followUpData, content: e.target.value })}
                placeholder="请输入跟进内容"
                rows={4}
              />
            </div>
            <div>
              <Label>下次行动</Label>
              <Input
                value={followUpData.next_action}
                onChange={(e) =>
                  setFollowUpData({ ...followUpData, next_action: e.target.value })
                }
                placeholder="如：发送报价单"
              />
            </div>
            <div>
              <Label>行动时间</Label>
              <Input
                type="date"
                value={followUpData.next_action_at}
                onChange={(e) =>
                  setFollowUpData({ ...followUpData, next_action_at: e.target.value })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFollowUpDialog(false)}>
              取消
            </Button>
            <Button onClick={handleAddFollowUp}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}



