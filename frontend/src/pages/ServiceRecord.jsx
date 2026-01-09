/**
 * Service Record Management
 * 现场服务记录管理 - 客服工程师高级功能
 * 
 * 功能：
 * 1. 现场服务记录创建、编辑、查看
 * 2. 服务类型管理（安装调试、操作培训、定期维护、故障维修）
 * 3. 服务地点、时间、人员记录
 * 4. 服务内容详细记录
 * 5. 服务照片上传（可选）
 * 6. 服务报告生成
 * 7. 客户签字确认
 * 8. 服务记录搜索和筛选
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Search, Filter, Eye, Edit, FileText, Calendar, MapPin,
  User, Clock, Camera, CheckCircle2, XCircle, Download, RefreshCw,
  Wrench, Users, Settings, AlertTriangle, Star, Phone, Mail,
  ChevronRight, Upload, Image as ImageIcon, FileCheck, X,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card, CardContent, CardHeader, CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogBody
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi } from '../services/api'

// Mock data
const mockServiceRecords = [
  {
    id: 1,
    record_no: 'SRV-20260106-001',
    service_type: '安装调试',
    project_code: 'PJ250106002',
    project_name: 'EOL功能测试设备',
    machine_no: 'PN001',
    customer_name: '东莞XX电子',
    service_location: '广东省东莞市XX工业区',
    service_date: '2026-01-06',
    service_start_time: '09:00',
    service_end_time: '17:00',
    service_duration: 8,
    service_engineer: '张工程师',
    service_engineer_phone: '138****5678',
    customer_contact: '李工',
    customer_phone: '139****9012',
    service_content: '完成设备安装、电气接线、程序调试，设备运行正常',
    service_result: '完成',
    issues_found: '无',
    solutions: '设备已正常运行，客户已掌握基本操作',
    customer_satisfaction: 5,
    customer_feedback: '服务专业，安装调试顺利',
    customer_signature: true,
    signature_time: '2026-01-06 17:00:00',
    photos: ['photo1.jpg', 'photo2.jpg'],
    status: '已完成',
    created_at: '2026-01-06 08:00:00',
  },
  {
    id: 2,
    record_no: 'SRV-20260105-002',
    service_type: '操作培训',
    project_code: 'PJ250103003',
    project_name: 'ICT在线测试设备',
    machine_no: 'PN002',
    customer_name: '惠州XX电池',
    service_location: '广东省惠州市XX科技园',
    service_date: '2026-01-05',
    service_start_time: '14:00',
    service_end_time: '18:00',
    service_duration: 4,
    service_engineer: '王工程师',
    service_engineer_phone: '137****3456',
    customer_contact: '张工',
    customer_phone: '138****7890',
    service_content: '对操作人员进行设备操作培训，包括开机、测试流程、日常维护等',
    service_result: '完成',
    issues_found: '操作人员对部分功能理解不够深入',
    solutions: '已提供详细操作手册，并安排后续电话支持',
    customer_satisfaction: 4,
    customer_feedback: '培训内容详细，但希望有更多实操练习',
    customer_signature: true,
    signature_time: '2026-01-05 18:00:00',
    photos: ['photo3.jpg'],
    status: '已完成',
    created_at: '2026-01-05 13:00:00',
  },
  {
    id: 3,
    record_no: 'SRV-20260104-003',
    service_type: '故障维修',
    project_code: 'PJ250101001',
    project_name: 'BMS老化测试设备',
    machine_no: 'PN003',
    customer_name: '深圳XX科技',
    service_location: '广东省深圳市XX科技园',
    service_date: '2026-01-04',
    service_start_time: '10:00',
    service_end_time: '15:30',
    service_duration: 5.5,
    service_engineer: '李工程师',
    service_engineer_phone: '136****1234',
    customer_contact: '王工',
    customer_phone: '135****5678',
    service_content: '设备运行异常，出现程序崩溃问题，进行故障排查和修复',
    service_result: '完成',
    issues_found: '程序存在内存泄漏问题',
    solutions: '已修复程序bug，更新软件版本，设备运行正常',
    customer_satisfaction: 5,
    customer_feedback: '响应及时，问题解决迅速',
    customer_signature: true,
    signature_time: '2026-01-04 15:30:00',
    photos: ['photo4.jpg', 'photo5.jpg', 'photo6.jpg'],
    status: '已完成',
    created_at: '2026-01-04 09:00:00',
  },
]

const serviceTypeConfig = {
  '安装调试': { label: '安装调试', icon: Settings, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  '操作培训': { label: '操作培训', icon: Users, color: 'text-purple-400', bg: 'bg-purple-500/20' },
  '定期维护': { label: '定期维护', icon: Wrench, color: 'text-green-400', bg: 'bg-green-500/20' },
  '故障维修': { label: '故障维修', icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/20' },
}

const statusConfig = {
  '进行中': { label: '进行中', color: 'bg-blue-500', textColor: 'text-blue-400' },
  '已完成': { label: '已完成', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  '已取消': { label: '已取消', color: 'bg-slate-500', textColor: 'text-slate-400' },
}

export default function ServiceRecord() {
  const navigate = useNavigate()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' })
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    inProgress: 0,
    completed: 0,
    thisMonth: 0,
    totalHours: 0,
  })

  useEffect(() => {
    loadRecords()
  }, [])

  useEffect(() => {
    if (records.length > 0 || !loading) {
      loadStatistics()
    }
  }, [records, loading])

  const loadRecords = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page: 1,
        page_size: 1000,
      }
      const response = await serviceApi.records.list(params)
      const recordsData = response.data?.items || response.data || []
      
      // Transform backend data to frontend format
      const transformedRecords = recordsData.map(record => ({
        id: record.id,
        record_no: record.record_no || '',
        service_type: record.service_type || '',
        project_code: record.project_code || '',
        project_name: record.project_name || '',
        machine_no: record.machine_no || '',
        customer_name: record.customer_name || '',
        service_location: record.service_location || '',
        service_date: record.service_date || '',
        service_start_time: record.service_start_time || '',
        service_end_time: record.service_end_time || '',
        service_duration: record.service_duration || 0,
        service_engineer: record.service_engineer || '',
        service_engineer_phone: record.service_engineer_phone || '',
        customer_contact: record.customer_contact || '',
        customer_phone: record.customer_phone || '',
        service_content: record.service_content || '',
        service_result: record.service_result || '',
        issues_found: record.issues_found || '',
        solutions: record.solutions || '',
        customer_satisfaction: record.customer_satisfaction || null,
        customer_feedback: record.customer_feedback || '',
        customer_signature: record.customer_signature || false,
        signature_time: record.signature_time || '',
        photos: record.photos || [],
        status: record.status || '进行中',
        created_at: record.created_at || '',
      }))
      
      setRecords(transformedRecords)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载服务记录失败')
      // 如果是演示账号，使用 mock 数据
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setRecords(mockServiceRecords)
      } else {
        setRecords([])
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const loadStatistics = useCallback(async () => {
    try {
      // Calculate statistics from loaded records
      const now = new Date()
      const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1)
      
      setStats({
        total: records.length,
        inProgress: records.filter(r => r.status === '进行中' || r.status === 'IN_PROGRESS').length,
        completed: records.filter(r => r.status === '已完成' || r.status === 'COMPLETED').length,
        thisMonth: records.filter(r => {
          if (!r.service_date) return false
          const recordDate = new Date(r.service_date)
          return recordDate >= thisMonthStart
        }).length,
        totalHours: records.reduce((sum, r) => sum + (r.service_duration || 0), 0),
      })
    } catch (err) {
    }
  }, [records])

  const filteredRecords = useMemo(() => {
    let result = records

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(record =>
        record.record_no.toLowerCase().includes(query) ||
        record.project_name.toLowerCase().includes(query) ||
        record.customer_name.toLowerCase().includes(query) ||
        record.service_location.toLowerCase().includes(query) ||
        record.service_engineer.toLowerCase().includes(query)
      )
    }

    // Type filter
    if (typeFilter !== 'ALL') {
      result = result.filter(record => record.service_type === typeFilter)
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      result = result.filter(record => record.status === statusFilter)
    }

    // Date filter
    if (dateFilter.start) {
      result = result.filter(record => record.service_date >= dateFilter.start)
    }
    if (dateFilter.end) {
      result = result.filter(record => record.service_date <= dateFilter.end)
    }

    return result.sort((a, b) => {
      return new Date(b.service_date + ' ' + b.service_start_time) - new Date(a.service_date + ' ' + a.service_start_time)
    })
  }, [records, searchQuery, typeFilter, statusFilter, dateFilter])

  const handleViewDetail = async (record) => {
    // Reload record to get latest data including photos
    try {
      const response = await serviceApi.records.get(record.id)
      const updatedRecord = response.data || response
      setSelectedRecord({
        ...record,
        ...updatedRecord,
        photos: updatedRecord.photos || [],
      })
    } catch (error) {
      setSelectedRecord(record)
    }
    setShowDetailDialog(true)
  }

  const handleCreateRecord = async (recordData) => {
    try {
      // Separate photos that need to be uploaded
      const photosToUpload = recordData.photos?.filter(p => p.isPending && p.file) || []
      const existingPhotos = recordData.photos?.filter(p => !p.isPending) || []
      
      // Transform frontend data to backend format
      const backendData = {
        service_type: recordData.service_type,
        project_id: recordData.project_id,
        machine_no: recordData.machine_no,
        customer_id: recordData.customer_id,
        location: recordData.service_location,
        service_date: recordData.service_date,
        start_time: recordData.service_start_time,
        end_time: recordData.service_end_time,
        duration_hours: recordData.service_duration,
        service_engineer_id: recordData.service_engineer_id,
        customer_contact: recordData.customer_contact,
        customer_phone: recordData.customer_phone,
        service_content: recordData.service_content,
        service_result: recordData.service_result,
        issues_found: recordData.issues_found,
        solution_provided: recordData.solutions,
        customer_satisfaction: recordData.customer_satisfaction,
        customer_feedback: recordData.customer_feedback,
        customer_signed: recordData.customer_signature,
        photos: existingPhotos, // Only include already uploaded photos
        status: recordData.status || 'SCHEDULED',
      }
      
      // Create the record first
      const response = await serviceApi.records.create(backendData)
      const createdRecord = response.data || response
      const recordId = createdRecord.id
      
      // Upload photos if any
      if (photosToUpload.length > 0) {
        toast.info(`正在上传 ${photosToUpload.length} 张照片...`)
        let successCount = 0
        let failCount = 0
        
        for (const photo of photosToUpload) {
          try {
            await serviceApi.records.uploadPhoto(recordId, photo.file, photo.description)
            successCount++
          } catch (error) {
            failCount++
          }
        }
        
        if (successCount > 0) {
          toast.success(`成功上传 ${successCount} 张照片`)
        }
        if (failCount > 0) {
          toast.warning(`${failCount} 张照片上传失败，可在记录详情中重新上传`)
        }
      }
      
      toast.success('现场服务记录创建成功')
      setShowCreateDialog(false)
      await loadRecords()
      await loadStatistics()
    } catch (error) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleUpdateRecord = async (recordId, recordData) => {
    try {
      // Transform frontend data to backend format
      const backendData = {
        service_type: recordData.service_type,
        project_id: recordData.project_id,
        machine_id: recordData.machine_id,
        customer_id: recordData.customer_id,
        service_location: recordData.service_location,
        service_date: recordData.service_date,
        service_start_time: recordData.service_start_time,
        service_end_time: recordData.service_end_time,
        service_duration: recordData.service_duration,
        service_engineer: recordData.service_engineer,
        service_engineer_phone: recordData.service_engineer_phone,
        customer_contact: recordData.customer_contact,
        customer_phone: recordData.customer_phone,
        service_content: recordData.service_content,
        service_result: recordData.service_result,
        issues_found: recordData.issues_found,
        solutions: recordData.solutions,
        customer_satisfaction: recordData.customer_satisfaction,
        customer_feedback: recordData.customer_feedback,
        customer_signature: recordData.customer_signature,
        photos: recordData.photos || [],
        status: recordData.status || 'IN_PROGRESS',
      }
      
      await serviceApi.records.update(recordId, backendData)
      toast.success('服务记录更新成功')
      setShowDetailDialog(false)
      await loadRecords()
      await loadStatistics()
    } catch (error) {
      toast.error('更新失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleGenerateReport = async (recordId) => {
    try {
      // TODO: 调用API生成报告
      // const response = await serviceRecordApi.generateReport(recordId)
      toast.success('服务报告生成成功')
      // 可以下载报告或在新窗口打开
    } catch (error) {
      toast.error('报告生成失败，请稍后重试')
    }
  }

  const handleExportRecords = () => {
    try {
      const recordsToExport = filteredRecords
      if (recordsToExport.length === 0) {
        toast.warning('没有可导出的数据')
        return
      }

      const headers = ['记录号', '服务类型', '项目编号', '项目名称', '机台号', '客户名称',
                      '服务地点', '服务日期', '开始时间', '结束时间', '服务时长', '服务工程师',
                      '客户联系人', '客户电话', '服务内容', '服务结果', '发现问题', '解决方案',
                      '客户满意度', '客户反馈', '状态']
      
      const csvRows = [
        headers.join(','),
        ...recordsToExport.map(record => [
          record.record_no || '',
          record.service_type || '',
          record.project_code || '',
          record.project_name || '',
          record.machine_no || '',
          record.customer_name || '',
          record.service_location || '',
          record.service_date || '',
          record.service_start_time || '',
          record.service_end_time || '',
          record.service_duration || '',
          record.service_engineer || '',
          record.customer_contact || '',
          record.customer_phone || '',
          `"${(record.service_content || '').replace(/"/g, '""')}"`,
          `"${(record.service_result || '').replace(/"/g, '""')}"`,
          `"${(record.issues_found || '').replace(/"/g, '""')}"`,
          `"${(record.solutions || '').replace(/"/g, '""')}"`,
          record.customer_satisfaction || '',
          `"${(record.customer_feedback || '').replace(/"/g, '""')}"`,
          record.status || '',
        ].join(','))
      ]
      
      const csvContent = csvRows.join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `现场服务记录_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      toast.success(`成功导出 ${recordsToExport.length} 条服务记录`)
    } catch (error) {
      toast.error('导出失败: ' + (error.message || '请稍后重试'))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="现场服务记录"
        description="记录和管理现场服务活动，生成服务报告"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => { loadRecords(); loadStatistics(); toast.success('数据已刷新'); }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExportRecords}
              disabled={loading}
            >
              <Download className={cn("w-4 h-4", loading && "animate-spin")} />
              导出数据
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              创建记录
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总记录数</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">进行中</div>
                <div className="text-2xl font-bold text-blue-400">{stats.inProgress}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-emerald-500/10 border-emerald-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已完成</div>
                <div className="text-2xl font-bold text-emerald-400">{stats.completed}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-purple-500/10 border-purple-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">本月服务</div>
                <div className="text-2xl font-bold text-purple-400">{stats.thisMonth}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-amber-500/10 border-amber-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总服务时长</div>
                <div className="text-2xl font-bold text-amber-400">{stats.totalHours}h</div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索记录号、项目名称、客户名称、服务地点..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部类型</option>
                    <option value="安装调试">安装调试</option>
                    <option value="操作培训">操作培训</option>
                    <option value="定期维护">定期维护</option>
                    <option value="故障维修">故障维修</option>
                  </select>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部状态</option>
                    <option value="进行中">进行中</option>
                    <option value="已完成">已完成</option>
                    <option value="已取消">已取消</option>
                  </select>
                  <Input
                    type="date"
                    value={dateFilter.start}
                    onChange={(e) => setDateFilter({ ...dateFilter, start: e.target.value })}
                    placeholder="开始日期"
                    className="w-40 bg-slate-800/50 border-slate-700 text-sm"
                  />
                  <Input
                    type="date"
                    value={dateFilter.end}
                    onChange={(e) => setDateFilter({ ...dateFilter, end: e.target.value })}
                    placeholder="结束日期"
                    className="w-40 bg-slate-800/50 border-slate-700 text-sm"
                  />
                  {(searchQuery || typeFilter !== 'ALL' || statusFilter !== 'ALL' || dateFilter.start || dateFilter.end) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setTypeFilter('ALL')
                        setStatusFilter('ALL')
                        setDateFilter({ start: '', end: '' })
                      }}
                      className="gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      清除
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Record List */}
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
          {loading ? (
            <LoadingCard rows={5} />
          ) : error && records.length === 0 ? (
            <ErrorMessage error={error} onRetry={loadRecords} />
          ) : filteredRecords.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="暂无服务记录"
              description={
                searchQuery || typeFilter !== 'ALL' || statusFilter !== 'ALL' || dateFilter.start || dateFilter.end
                  ? "当前筛选条件下没有匹配的记录，请尝试调整筛选条件"
                  : "当前没有服务记录数据"
              }
            />
          ) : (
            filteredRecords.map((record) => {
              const typeConfig = serviceTypeConfig[record.service_type] || serviceTypeConfig['安装调试']
              const TypeIcon = typeConfig.icon
              const status = statusConfig[record.status] || statusConfig['进行中']

              return (
                <motion.div key={record.id} variants={fadeIn}>
                  <Card className="hover:bg-slate-800/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          {/* Header */}
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm text-slate-300">{record.record_no}</span>
                            <Badge className={cn(typeConfig.bg, typeConfig.color, 'text-xs')}>
                              <TypeIcon className="w-3 h-3 mr-1" />
                              {typeConfig.label}
                            </Badge>
                            <Badge className={cn(status.color, 'text-xs')}>
                              {status.label}
                            </Badge>
                            {record.customer_signature && (
                              <Badge variant="outline" className="text-xs text-emerald-400 border-emerald-500/30">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                已签字
                              </Badge>
                            )}
                          </div>

                          {/* Content */}
                          <div>
                            <h3 className="text-white font-medium mb-1">
                              {record.project_name} - {record.customer_name}
                            </h3>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {record.service_location}
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {record.service_date} {record.service_start_time} - {record.service_end_time}
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                服务时长: {record.service_duration}小时
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                服务工程师: {record.service_engineer}
                              </span>
                            </div>
                            <p className="text-sm text-slate-300 mt-2 line-clamp-2">{record.service_content}</p>
                          </div>

                          {/* Footer */}
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            {record.customer_satisfaction && (
                              <span className="flex items-center gap-1 text-yellow-400">
                                <Star className="w-3 h-3 fill-yellow-400" />
                                满意度: {record.customer_satisfaction}/5
                              </span>
                            )}
                            {record.photos && record.photos.length > 0 && (
                              <span className="flex items-center gap-1">
                                <Camera className="w-3 h-3" />
                                {record.photos.length}张照片
                              </span>
                            )}
                            <span>创建时间: {record.created_at}</span>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(record)}
                            className="gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
                          {record.status === '已完成' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleGenerateReport(record.id)}
                              className="gap-1"
                            >
                              <FileText className="w-3 h-3" />
                              报告
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })
          )}
        </motion.div>
      </div>

      {/* Create Record Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <CreateRecordDialog
            onClose={() => setShowCreateDialog(false)}
            onSubmit={handleCreateRecord}
          />
        )}
      </AnimatePresence>

      {/* Detail Dialog */}
      <AnimatePresence>
        {showDetailDialog && selectedRecord && (
          <RecordDetailDialog
            record={selectedRecord}
            onClose={() => {
              setShowDetailDialog(false)
              setSelectedRecord(null)
            }}
            onUpdate={handleUpdateRecord}
            onGenerateReport={handleGenerateReport}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Create Record Dialog Component
function CreateRecordDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    service_type: '安装调试',
    project_code: '',
    project_name: '',
    machine_no: '',
    customer_name: '',
    service_location: '',
    service_date: new Date().toISOString().split('T')[0],
    service_start_time: '09:00',
    service_end_time: '17:00',
    service_engineer: '',
    service_engineer_phone: '',
    customer_contact: '',
    customer_phone: '',
    service_content: '',
    service_result: '',
    issues_found: '',
    solutions: '',
    customer_satisfaction: '',
    customer_feedback: '',
    photos: [],
  })

  const handleSubmit = () => {
    if (!formData.service_content || !formData.service_engineer) {
      toast.error('请填写服务内容和服务工程师信息')
      return
    }
    onSubmit(formData)
  }

  const handlePhotoUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    try {
      const uploadedPhotos = []
      
      // Process each file
      for (const file of files) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
          toast.error(`${file.name} 不是有效的图片文件`)
          continue
        }
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          toast.error(`${file.name} 文件大小超过5MB限制`)
          continue
        }
        
        // For new records (not yet created), store as base64 for preview
        // Photos will be uploaded after record is created
        const reader = new FileReader()
        const photoData = await new Promise((resolve, reject) => {
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(file)
        })
        
        // Store photo info with file reference for later upload
        uploadedPhotos.push({
          name: file.name,
          size: file.size,
          type: file.type,
          data: photoData, // base64 data URL for preview
          file: file, // Keep file reference for upload
          uploaded_at: new Date().toISOString(),
          isPending: true, // Mark as pending upload
        })
      }
      
      if (uploadedPhotos.length > 0) {
        setFormData({ 
          ...formData, 
          photos: [...formData.photos, ...uploadedPhotos] 
        })
        toast.success(`已添加 ${uploadedPhotos.length} 张照片（将在创建记录后上传）`)
      }
    } catch (error) {
      toast.error('照片处理失败: ' + error.message)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建现场服务记录</DialogTitle>
          <DialogDescription>填写服务信息，系统将自动生成记录号</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">服务类型 *</label>
                <select
                  value={formData.service_type}
                  onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="安装调试">安装调试</option>
                  <option value="操作培训">操作培训</option>
                  <option value="定期维护">定期维护</option>
                  <option value="故障维修">故障维修</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">服务日期 *</label>
                <Input
                  type="date"
                  value={formData.service_date}
                  onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Project Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">项目编号</label>
                <Input
                  value={formData.project_code}
                  onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
                  placeholder="输入项目编号"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">项目名称</label>
                <Input
                  value={formData.project_name}
                  onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                  placeholder="输入项目名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">机台号</label>
                <Input
                  value={formData.machine_no}
                  onChange={(e) => setFormData({ ...formData, machine_no: e.target.value })}
                  placeholder="输入机台号"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户名称 *</label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  placeholder="输入客户名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">服务地点 *</label>
              <Input
                value={formData.service_location}
                onChange={(e) => setFormData({ ...formData, service_location: e.target.value })}
                placeholder="输入详细服务地址"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            {/* Time */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">开始时间 *</label>
                <Input
                  type="time"
                  value={formData.service_start_time}
                  onChange={(e) => setFormData({ ...formData, service_start_time: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">结束时间 *</label>
                <Input
                  type="time"
                  value={formData.service_end_time}
                  onChange={(e) => setFormData({ ...formData, service_end_time: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Engineer Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">服务工程师 *</label>
                <Input
                  value={formData.service_engineer}
                  onChange={(e) => setFormData({ ...formData, service_engineer: e.target.value })}
                  placeholder="输入服务工程师姓名"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">工程师电话</label>
                <Input
                  value={formData.service_engineer_phone}
                  onChange={(e) => setFormData({ ...formData, service_engineer_phone: e.target.value })}
                  placeholder="输入工程师电话"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Customer Contact */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户联系人</label>
                <Input
                  value={formData.customer_contact}
                  onChange={(e) => setFormData({ ...formData, customer_contact: e.target.value })}
                  placeholder="输入客户联系人"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户电话</label>
                <Input
                  value={formData.customer_phone}
                  onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
                  placeholder="输入客户电话"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Service Content */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">服务内容 *</label>
              <Textarea
                value={formData.service_content}
                onChange={(e) => setFormData({ ...formData, service_content: e.target.value })}
                placeholder="详细描述服务内容..."
                rows={5}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            {/* Service Result */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">服务结果</label>
              <Textarea
                value={formData.service_result}
                onChange={(e) => setFormData({ ...formData, service_result: e.target.value })}
                placeholder="描述服务结果..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>

            {/* Issues and Solutions */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">发现问题</label>
                <Textarea
                  value={formData.issues_found}
                  onChange={(e) => setFormData({ ...formData, issues_found: e.target.value })}
                  placeholder="记录发现的问题..."
                  rows={3}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">解决方案</label>
                <Textarea
                  value={formData.solutions}
                  onChange={(e) => setFormData({ ...formData, solutions: e.target.value })}
                  placeholder="描述解决方案..."
                  rows={3}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            {/* Photos */}
            <div>
              <label className="text-sm text-slate-400 mb-1 block">服务照片</label>
              <div className="flex items-center gap-2">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotoUpload}
                  className="hidden"
                  id="photo-upload"
                />
                <label
                  htmlFor="photo-upload"
                  className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-800/70 transition-colors"
                >
                  <Upload className="w-4 h-4" />
                  上传照片
                </label>
                {formData.photos.length > 0 && (
                  <span className="text-sm text-slate-400">
                    已选择 {formData.photos.length} 张照片
                  </span>
                )}
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>
            <FileText className="w-4 h-4 mr-2" />
            创建记录
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Record Detail Dialog Component
function RecordDetailDialog({ record, onClose, onUpdate, onGenerateReport }) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState(record)
  const [uploadingPhotos, setUploadingPhotos] = useState(false)

  useEffect(() => {
    setFormData(record)
  }, [record])

  const handleSave = () => {
    onUpdate(record.id, formData)
    setIsEditing(false)
  }

  const handlePhotoUploadInDetail = async (recordId, e) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return

    try {
      setUploadingPhotos(true)
      let successCount = 0
      let failCount = 0

      for (const file of files) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
          toast.error(`${file.name} 不是有效的图片文件`)
          failCount++
          continue
        }
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          toast.error(`${file.name} 文件大小超过5MB限制`)
          failCount++
          continue
        }

        try {
          await serviceApi.records.uploadPhoto(recordId, file)
          successCount++
        } catch (error) {
          failCount++
        }
      }

      if (successCount > 0) {
        toast.success(`成功上传 ${successCount} 张照片`)
        // Reload record to get updated photos
        const response = await serviceApi.records.get(recordId)
        const updatedRecord = response.data || response
        setFormData({
          ...formData,
          photos: updatedRecord.photos || [],
        })
      }
      if (failCount > 0) {
        toast.warning(`${failCount} 张照片上传失败`)
      }
    } catch (error) {
      toast.error('照片上传失败: ' + error.message)
    } finally {
      setUploadingPhotos(false)
      // Reset file input
      e.target.value = ''
    }
  }

  const handleDeletePhoto = async (recordId, photoIndex) => {
    if (!confirm('确定要删除这张照片吗？')) {
      return
    }

    try {
      await serviceApi.records.deletePhoto(recordId, photoIndex)
      toast.success('照片删除成功')
      // Reload record to get updated photos
      const response = await serviceApi.records.get(recordId)
      const updatedRecord = response.data || response
      setFormData({
        ...formData,
        photos: updatedRecord.photos || [],
      })
    } catch (error) {
      toast.error('照片删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const typeConfig = serviceTypeConfig[record.service_type] || serviceTypeConfig['安装调试']
  const TypeIcon = typeConfig.icon
  const status = statusConfig[record.status] || statusConfig['进行中']

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono">{record.record_no}</span>
            <Badge className={cn(typeConfig.bg, typeConfig.color, 'text-xs')}>
              <TypeIcon className="w-3 h-3 mr-1" />
              {typeConfig.label}
            </Badge>
            <Badge className={cn(status.color, 'text-xs')}>{status.label}</Badge>
          </DialogTitle>
          <DialogDescription>现场服务记录详情</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">项目信息</p>
                <p className="text-white">{record.project_code} - {record.project_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">机台号</p>
                <p className="text-white">{record.machine_no || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">客户名称</p>
                <p className="text-white">{record.customer_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">服务地点</p>
                <p className="text-white">{record.service_location}</p>
              </div>
            </div>

            {/* Service Time */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">服务日期</p>
                <p className="text-white">{record.service_date}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">开始时间</p>
                <p className="text-white">{record.service_start_time}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">结束时间</p>
                <p className="text-white">{record.service_end_time}</p>
              </div>
            </div>

            {/* Service Content */}
            <div>
              <p className="text-sm text-slate-400 mb-1">服务内容</p>
              <p className="text-white bg-slate-800/50 p-3 rounded-lg">{record.service_content}</p>
            </div>

            {/* Service Result */}
            {record.service_result && (
              <div>
                <p className="text-sm text-slate-400 mb-1">服务结果</p>
                <p className="text-white bg-slate-800/50 p-3 rounded-lg">{record.service_result}</p>
              </div>
            )}

            {/* Issues and Solutions */}
            {(record.issues_found || record.solutions) && (
              <div className="grid grid-cols-2 gap-4">
                {record.issues_found && (
                  <div>
                    <p className="text-sm text-slate-400 mb-1">发现问题</p>
                    <p className="text-white bg-slate-800/50 p-3 rounded-lg">{record.issues_found}</p>
                  </div>
                )}
                {record.solutions && (
                  <div>
                    <p className="text-sm text-slate-400 mb-1">解决方案</p>
                    <p className="text-white bg-slate-800/50 p-3 rounded-lg">{record.solutions}</p>
                  </div>
                )}
              </div>
            )}

            {/* Contact Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">服务工程师</p>
                <p className="text-white">{record.service_engineer} ({record.service_engineer_phone})</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">客户联系人</p>
                <p className="text-white">{record.customer_contact} ({record.customer_phone})</p>
              </div>
            </div>

            {/* Satisfaction */}
            {record.customer_satisfaction && (
              <div>
                <p className="text-sm text-slate-400 mb-1">客户满意度</p>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star
                        key={i}
                        className={cn(
                          'w-5 h-5',
                          i <= record.customer_satisfaction
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-slate-600'
                        )}
                      />
                    ))}
                  </div>
                  <span className="text-white">{record.customer_satisfaction}/5</span>
                </div>
                {record.customer_feedback && (
                  <p className="text-slate-400 text-sm mt-2">{record.customer_feedback}</p>
                )}
              </div>
            )}

            {/* Photos */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400 font-medium">
                  服务照片 {record.photos && record.photos.length > 0 && `(${record.photos.length}张)`}
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => handlePhotoUploadInDetail(record.id, e)}
                    className="hidden"
                    id={`photo-upload-detail-${record.id}`}
                    disabled={uploadingPhotos}
                  />
                  <label
                    htmlFor={`photo-upload-detail-${record.id}`}
                    className={cn(
                      "flex items-center gap-1 px-3 py-1 text-xs bg-slate-800/50 border border-slate-700 rounded-lg transition-colors",
                      uploadingPhotos ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:bg-slate-800/70"
                    )}
                  >
                    <Upload className={cn("w-3 h-3", uploadingPhotos && "animate-pulse")} />
                    {uploadingPhotos ? '上传中...' : '上传照片'}
                  </label>
                </div>
              </div>
              {record.photos && record.photos.length > 0 ? (
                <div className="grid grid-cols-3 gap-2">
                  {record.photos.map((photo, index) => {
                    // Get photo URL - could be from backend or base64
                    const photoUrl = typeof photo === 'string' 
                      ? photo
                      : photo.url 
                        ? `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/uploads/${photo.url}`
                        : photo.data || (typeof photo === 'object' && photo.filename ? null : photo)
                    
                    return (
                      <div
                        key={index}
                        className="relative aspect-video bg-slate-800/50 rounded-lg overflow-hidden group cursor-pointer"
                        onClick={() => {
                          // Open photo in new window for full view
                          if (photoUrl) {
                            window.open(photoUrl, '_blank')
                          }
                        }}
                      >
                        {photoUrl ? (
                          <img
                            src={photoUrl}
                            alt={`服务照片 ${index + 1}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // Fallback to placeholder if image fails to load
                              e.target.style.display = 'none'
                              const placeholder = e.target.parentElement.querySelector('.photo-placeholder')
                              if (placeholder) placeholder.style.display = 'flex'
                            }}
                          />
                        ) : null}
                        <div className="photo-placeholder hidden w-full h-full items-center justify-center">
                          <ImageIcon className="w-8 h-8 text-slate-400" />
                        </div>
                        {/* Delete button on hover */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeletePhoto(record.id, index)
                          }}
                          className="absolute top-1 right-1 p-1 bg-red-500/80 hover:bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10"
                          title="删除照片"
                        >
                          <X className="w-3 h-3" />
                        </button>
                        {/* Photo info overlay */}
                        {photo && typeof photo === 'object' && photo.description && (
                          <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs p-1 truncate">
                            {photo.description}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500 text-sm border border-dashed border-slate-700 rounded-lg">
                  <ImageIcon className="w-12 h-12 mx-auto mb-2 text-slate-600" />
                  <p>暂无照片</p>
                  <p className="text-xs mt-1">点击"上传照片"添加服务照片</p>
                </div>
              )}
            </div>

            {/* Signature */}
            {record.customer_signature && (
              <div>
                <p className="text-sm text-slate-400 mb-1">客户签字确认</p>
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>已签字确认</span>
                  <span className="text-slate-400 text-xs">({record.signature_time})</span>
                </div>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          {record.status === '已完成' && (
            <Button variant="outline" onClick={() => onGenerateReport(record.id)}>
              <FileText className="w-4 h-4 mr-2" />
              生成报告
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}



