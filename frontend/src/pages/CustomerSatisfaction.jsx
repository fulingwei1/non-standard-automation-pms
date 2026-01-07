/**
 * Customer Satisfaction Survey
 * 客户满意度调查 - 客服工程师高级功能
 * 
 * 功能：
 * 1. 满意度调查创建、发送、跟踪
 * 2. 调查问卷模板管理
 * 3. 调查结果统计和分析
 * 4. 客户反馈查看和管理
 * 5. 满意度趋势分析
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Search, Filter, Eye, Send, Star, TrendingUp, TrendingDown,
  Calendar, User, CheckCircle2, XCircle, RefreshCw, Download, BarChart3,
  MessageSquare, FileText, Mail, Phone, AlertCircle, ChevronRight,
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
const mockSurveys = [
  {
    id: 1,
    survey_no: 'SUR-20260106-001',
    survey_type: '项目满意度',
    customer_name: '东莞XX电子',
    customer_contact: '李工',
    customer_email: 'li@example.com',
    project_code: 'PJ250106002',
    project_name: 'EOL功能测试设备',
    survey_date: '2026-01-06',
    send_date: '2026-01-06',
    send_method: '邮件',
    status: '已完成',
    response_date: '2026-01-07',
    overall_score: 4.5,
    scores: {
      service_quality: 5,
      response_speed: 4,
      technical_support: 5,
      problem_resolution: 4,
      communication: 5,
    },
    feedback: '整体服务满意，响应及时，技术支持专业',
    suggestions: '希望提供更多操作培训视频',
    created_by: '当前用户',
    created_at: '2026-01-06 10:00:00',
  },
  {
    id: 2,
    survey_no: 'SUR-20260105-002',
    survey_type: '服务满意度',
    customer_name: '惠州XX电池',
    customer_contact: '张工',
    customer_phone: '139****9012',
    project_code: 'PJ250103003',
    project_name: 'ICT在线测试设备',
    survey_date: '2026-01-05',
    send_date: '2026-01-05',
    send_method: '电话',
    status: '已完成',
    response_date: '2026-01-05',
    overall_score: 4.0,
    scores: {
      service_quality: 4,
      response_speed: 4,
      technical_support: 4,
      problem_resolution: 4,
      communication: 4,
    },
    feedback: '服务态度好，但问题解决速度可以更快',
    suggestions: null,
    created_by: '当前用户',
    created_at: '2026-01-05 14:00:00',
  },
  {
    id: 3,
    survey_no: 'SUR-20260104-003',
    survey_type: '项目满意度',
    customer_name: '深圳XX科技',
    customer_contact: '王工',
    customer_email: 'wang@example.com',
    project_code: 'PJ250101001',
    project_name: 'BMS老化测试设备',
    survey_date: '2026-01-04',
    send_date: '2026-01-04',
    send_method: '邮件',
    status: '待回复',
    response_date: null,
    overall_score: null,
    scores: null,
    feedback: null,
    suggestions: null,
    created_by: '当前用户',
    created_at: '2026-01-04 09:00:00',
  },
]

const statusConfig = {
  '待发送': { label: '待发送', color: 'bg-slate-500', textColor: 'text-slate-400' },
  '已发送': { label: '已发送', color: 'bg-blue-500', textColor: 'text-blue-400' },
  '待回复': { label: '待回复', color: 'bg-amber-500', textColor: 'text-amber-400' },
  '已完成': { label: '已完成', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  '已过期': { label: '已过期', color: 'bg-red-500', textColor: 'text-red-400' },
}

const surveyTypeConfig = {
  '项目满意度': { label: '项目满意度', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  '服务满意度': { label: '服务满意度', color: 'text-purple-400', bg: 'bg-purple-500/20' },
  '产品满意度': { label: '产品满意度', color: 'text-green-400', bg: 'bg-green-500/20' },
}

const sendMethodConfig = {
  '邮件': { label: '邮件', icon: Mail, color: 'text-blue-400' },
  '电话': { label: '电话', icon: Phone, color: 'text-green-400' },
  '微信': { label: '微信', icon: MessageSquare, color: 'text-emerald-400' },
  '现场': { label: '现场', icon: User, color: 'text-purple-400' },
}

export default function CustomerSatisfaction() {
  const [surveys, setSurveys] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' })
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedSurvey, setSelectedSurvey] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    sent: 0,
    pending: 0,
    completed: 0,
    averageScore: 0,
    responseRate: 0,
  })

  useEffect(() => {
    loadSurveys()
    loadStatistics()
  }, [])

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      'DRAFT': '草稿',
      'SENT': '已发送',
      'PENDING': '待回复',
      'COMPLETED': '已完成',
    }
    return statusMap[backendStatus] || backendStatus
  }

  const loadSurveys = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        page: 1,
        page_size: 100,
      }
      
      if (statusFilter !== 'ALL') {
        const statusMap = {
          '草稿': 'DRAFT',
          '已发送': 'SENT',
          '待回复': 'PENDING',
          '已完成': 'COMPLETED',
        }
        params.status = statusMap[statusFilter] || statusFilter
      }
      
      if (typeFilter !== 'ALL') {
        params.survey_type = typeFilter
      }
      
      if (dateFilter.start) {
        params.date_from = dateFilter.start
      }
      
      if (dateFilter.end) {
        params.date_to = dateFilter.end
      }
      
      if (searchQuery) {
        params.keyword = searchQuery
      }
      
      const response = await serviceApi.satisfaction.list(params)
      const surveysData = response.data?.items || response.data || []
      
      // Transform backend data to frontend format
      const transformedSurveys = surveysData.map(survey => ({
        id: survey.id,
        survey_no: survey.survey_no || '',
        survey_type: survey.survey_type || '',
        customer_name: survey.customer_name || '',
        customer_contact: survey.customer_contact || '',
        customer_email: survey.customer_email || '',
        project_code: survey.project_code || '',
        project_name: survey.project_name || '',
        survey_date: survey.survey_date || '',
        send_date: survey.send_date || '',
        send_method: survey.send_method || '',
        status: mapBackendStatus(survey.status),
        response_date: survey.response_date || '',
        overall_score: survey.overall_score || null,
        scores: survey.scores || {},
        feedback: survey.feedback || '',
      }))
      
      setSurveys(transformedSurveys)
    } catch (err) {
      console.error('Failed to load surveys:', err)
      setError(err.response?.data?.detail || err.message || '加载满意度调查失败')
      setSurveys([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [statusFilter, typeFilter, dateFilter, searchQuery])

  const loadStatistics = useCallback(async () => {
    try {
      const response = await serviceApi.satisfaction.statistics()
      const statsData = response.data || {}
      
      setStats({
        total: statsData.total || 0,
        sent: statsData.sent || 0,
        pending: statsData.pending || 0,
        completed: statsData.completed || 0,
        averageScore: statsData.average_score || 0,
        responseRate: statsData.response_rate || 0,
      })
    } catch (err) {
      console.error('Failed to load statistics:', err)
      // Calculate from local surveys as fallback
      const completed = surveys.filter(s => s.status === '已完成')
      const totalScores = completed.reduce((sum, s) => sum + (s.overall_score || 0), 0)
      
      setStats({
        total: surveys.length,
        sent: surveys.filter(s => ['已发送', '待回复', '已完成'].includes(s.status)).length,
        pending: surveys.filter(s => s.status === '待回复').length,
        completed: completed.length,
        averageScore: completed.length > 0 ? (totalScores / completed.length).toFixed(1) : 0,
        responseRate: surveys.length > 0 ? ((completed.length / surveys.length) * 100).toFixed(1) : 0,
      })
    }
  }, [surveys])

  const filteredSurveys = useMemo(() => {
    let result = surveys

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(survey =>
        survey.survey_no.toLowerCase().includes(query) ||
        survey.customer_name.toLowerCase().includes(query) ||
        survey.project_name.toLowerCase().includes(query)
      )
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      result = result.filter(survey => survey.status === statusFilter)
    }

    // Type filter
    if (typeFilter !== 'ALL') {
      result = result.filter(survey => survey.survey_type === typeFilter)
    }

    // Date filter
    if (dateFilter.start) {
      result = result.filter(survey => survey.survey_date >= dateFilter.start)
    }
    if (dateFilter.end) {
      result = result.filter(survey => survey.survey_date <= dateFilter.end)
    }

    return result.sort((a, b) => {
      return new Date(b.survey_date) - new Date(a.survey_date)
    })
  }, [surveys, searchQuery, statusFilter, typeFilter, dateFilter])

  const handleViewDetail = (survey) => {
    setSelectedSurvey(survey)
    setShowDetailDialog(true)
  }

  const handleCreateSurvey = async (surveyData) => {
    try {
      await serviceApi.satisfaction.create(surveyData)
      toast.success('满意度调查创建成功')
      setShowCreateDialog(false)
      await loadSurveys()
      await loadStatistics()
    } catch (error) {
      console.error('Failed to create survey:', error)
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleSendSurvey = async (surveyId, sendData) => {
    try {
      await serviceApi.satisfaction.send(surveyId, sendData || {})
      toast.success('调查已发送')
      await loadSurveys()
      await loadStatistics()
    } catch (error) {
      console.error('Failed to send survey:', error)
      toast.error('发送失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="客户满意度调查"
        description="创建和管理客户满意度调查，跟踪客户反馈"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => { loadSurveys(); loadStatistics(); toast.success('数据已刷新'); }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              创建调查
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
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总调查数</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已发送</div>
                <div className="text-2xl font-bold text-blue-400">{stats.sent}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-amber-500/10 border-amber-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待回复</div>
                <div className="text-2xl font-bold text-amber-400">{stats.pending}</div>
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
            <Card className="bg-yellow-500/10 border-yellow-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">平均分</div>
                <div className="flex items-center gap-1">
                  <div className="text-2xl font-bold text-yellow-400">{stats.averageScore}</div>
                  <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-purple-500/10 border-purple-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">回复率</div>
                <div className="text-2xl font-bold text-purple-400">{stats.responseRate}%</div>
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
                      placeholder="搜索调查号、客户名称、项目名称..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部状态</option>
                    <option value="待发送">待发送</option>
                    <option value="已发送">已发送</option>
                    <option value="待回复">待回复</option>
                    <option value="已完成">已完成</option>
                    <option value="已过期">已过期</option>
                  </select>
                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部类型</option>
                    <option value="项目满意度">项目满意度</option>
                    <option value="服务满意度">服务满意度</option>
                    <option value="产品满意度">产品满意度</option>
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
                  {(searchQuery || statusFilter !== 'ALL' || typeFilter !== 'ALL' || dateFilter.start || dateFilter.end) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setStatusFilter('ALL')
                        setTypeFilter('ALL')
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

        {/* Survey List */}
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
          {loading ? (
            <LoadingCard rows={5} />
          ) : error && surveys.length === 0 ? (
            <ErrorMessage error={error} onRetry={loadSurveys} />
          ) : filteredSurveys.length === 0 ? (
            <EmptyState
              icon={Star}
              title="暂无满意度调查"
              description={
                searchQuery || statusFilter !== 'ALL' || typeFilter !== 'ALL' || dateFilter.start || dateFilter.end
                  ? "当前筛选条件下没有匹配的调查，请尝试调整筛选条件"
                  : "当前没有满意度调查数据"
              }
            />
          ) : (
            filteredSurveys.map((survey) => {
              const status = statusConfig[survey.status] || statusConfig['待发送']
              const typeConfig = surveyTypeConfig[survey.survey_type] || surveyTypeConfig['项目满意度']
              const methodConfig = sendMethodConfig[survey.send_method] || sendMethodConfig['邮件']
              const MethodIcon = methodConfig.icon

              return (
                <motion.div key={survey.id} variants={fadeIn}>
                  <Card className="hover:bg-slate-800/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          {/* Header */}
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className="font-mono text-sm text-slate-300">{survey.survey_no}</span>
                            <Badge className={cn(status.color, 'text-xs')}>
                              {status.label}
                            </Badge>
                            <Badge className={cn(typeConfig.bg, typeConfig.color, 'text-xs')}>
                              {typeConfig.label}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              <MethodIcon className="w-3 h-3 mr-1" />
                              {methodConfig.label}
                            </Badge>
                            {survey.overall_score && (
                              <Badge variant="outline" className="text-xs text-yellow-400 border-yellow-500/30">
                                <Star className="w-3 h-3 mr-1 fill-yellow-400" />
                                {survey.overall_score}/5.0
                              </Badge>
                            )}
                          </div>

                          {/* Content */}
                          <div>
                            <h3 className="text-white font-medium mb-1">
                              {survey.customer_name} - {survey.project_name}
                            </h3>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {survey.customer_contact}
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                调查日期: {survey.survey_date}
                              </span>
                              {survey.send_date && (
                                <span className="flex items-center gap-1">
                                  <Send className="w-3 h-3" />
                                  发送: {survey.send_date}
                                </span>
                              )}
                              {survey.response_date && (
                                <span className="flex items-center gap-1 text-emerald-400">
                                  <CheckCircle2 className="w-3 h-3" />
                                  回复: {survey.response_date}
                                </span>
                              )}
                            </div>
                            {survey.feedback && (
                              <p className="text-sm text-slate-300 mt-2 line-clamp-2">{survey.feedback}</p>
                            )}
                          </div>

                          {/* Scores */}
                          {survey.scores && (
                            <div className="grid grid-cols-5 gap-2 text-xs">
                              {Object.entries(survey.scores).map(([key, score]) => (
                                <div key={key} className="flex items-center gap-1">
                                  <span className="text-slate-400">{key === 'service_quality' ? '服务质量' : 
                                    key === 'response_speed' ? '响应速度' :
                                    key === 'technical_support' ? '技术支持' :
                                    key === 'problem_resolution' ? '问题解决' :
                                    key === 'communication' ? '沟通' : key}:</span>
                                  <div className="flex items-center gap-0.5">
                                    {[1, 2, 3, 4, 5].map((i) => (
                                      <Star
                                        key={i}
                                        className={cn(
                                          'w-3 h-3',
                                          i <= score
                                            ? 'fill-yellow-400 text-yellow-400'
                                            : 'text-slate-600'
                                        )}
                                      />
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          {survey.status === '待发送' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleSendSurvey(survey.id)}
                              className="gap-1"
                            >
                              <Send className="w-3 h-3" />
                              发送
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(survey)}
                            className="gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
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

      {/* Create Survey Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <CreateSurveyDialog
            onClose={() => setShowCreateDialog(false)}
            onSubmit={handleCreateSurvey}
          />
        )}
      </AnimatePresence>

      {/* Detail Dialog */}
      <AnimatePresence>
        {showDetailDialog && selectedSurvey && (
          <SurveyDetailDialog
            survey={selectedSurvey}
            onClose={() => {
              setShowDetailDialog(false)
              setSelectedSurvey(null)
            }}
            onSend={handleSendSurvey}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Create Survey Dialog Component
function CreateSurveyDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    survey_type: '项目满意度',
    customer_name: '',
    customer_contact: '',
    customer_email: '',
    customer_phone: '',
    project_code: '',
    project_name: '',
    survey_date: new Date().toISOString().split('T')[0],
    send_method: '邮件',
    deadline: '',
    notes: '',
  })

  const handleSubmit = () => {
    if (!formData.customer_name || !formData.survey_date) {
      toast.error('请填写客户名称和调查日期')
      return
    }
    onSubmit(formData)
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建满意度调查</DialogTitle>
          <DialogDescription>填写调查信息，系统将自动生成调查号</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">调查类型 *</label>
                <select
                  value={formData.survey_type}
                  onChange={(e) => setFormData({ ...formData, survey_type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="项目满意度">项目满意度</option>
                  <option value="服务满意度">服务满意度</option>
                  <option value="产品满意度">产品满意度</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">发送方式 *</label>
                <select
                  value={formData.send_method}
                  onChange={(e) => setFormData({ ...formData, send_method: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="邮件">邮件</option>
                  <option value="电话">电话</option>
                  <option value="微信">微信</option>
                  <option value="现场">现场</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户名称 *</label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  placeholder="输入客户名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户联系人</label>
                <Input
                  value={formData.customer_contact}
                  onChange={(e) => setFormData({ ...formData, customer_contact: e.target.value })}
                  placeholder="输入客户联系人"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户邮箱</label>
                <Input
                  type="email"
                  value={formData.customer_email}
                  onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
                  placeholder="输入客户邮箱"
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
                <label className="text-sm text-slate-400 mb-1 block">调查日期 *</label>
                <Input
                  type="date"
                  value={formData.survey_date}
                  onChange={(e) => setFormData({ ...formData, survey_date: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">截止日期</label>
                <Input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1 block">备注</label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="输入备注信息..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>
            <Send className="w-4 h-4 mr-2" />
            创建调查
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Survey Detail Dialog Component
function SurveyDetailDialog({ survey, onClose, onSend }) {
  const status = statusConfig[survey.status] || statusConfig['待发送']
  const typeConfig = surveyTypeConfig[survey.survey_type] || surveyTypeConfig['项目满意度']
  const methodConfig = sendMethodConfig[survey.send_method] || sendMethodConfig['邮件']
  const MethodIcon = methodConfig.icon

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono">{survey.survey_no}</span>
            <Badge className={cn(status.color, 'text-xs')}>{status.label}</Badge>
            <Badge className={cn(typeConfig.bg, typeConfig.color, 'text-xs')}>
              {typeConfig.label}
            </Badge>
          </DialogTitle>
          <DialogDescription>满意度调查详情</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">客户名称</p>
                <p className="text-white">{survey.customer_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">客户联系人</p>
                <p className="text-white">{survey.customer_contact || '-'}</p>
              </div>
              {survey.customer_email && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户邮箱</p>
                  <p className="text-white">{survey.customer_email}</p>
                </div>
              )}
              {survey.customer_phone && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户电话</p>
                  <p className="text-white">{survey.customer_phone}</p>
                </div>
              )}
            </div>

            {/* Project Info */}
            {survey.project_name && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目编号</p>
                  <p className="text-white">{survey.project_code || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目名称</p>
                  <p className="text-white">{survey.project_name}</p>
                </div>
              </div>
            )}

            {/* Survey Info */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">调查日期</p>
                <p className="text-white">{survey.survey_date}</p>
              </div>
              {survey.send_date && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">发送日期</p>
                  <p className="text-white">{survey.send_date}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-slate-400 mb-1">发送方式</p>
                <div className="flex items-center gap-1">
                  <MethodIcon className="w-4 h-4" />
                  <p className="text-white">{methodConfig.label}</p>
                </div>
              </div>
            </div>

            {/* Overall Score */}
            {survey.overall_score && (
              <div>
                <p className="text-sm text-slate-400 mb-2">总体满意度</p>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star
                        key={i}
                        className={cn(
                          'w-6 h-6',
                          i <= Math.floor(survey.overall_score)
                            ? 'fill-yellow-400 text-yellow-400'
                            : i === Math.ceil(survey.overall_score) && survey.overall_score % 1 >= 0.5
                            ? 'fill-yellow-400/50 text-yellow-400'
                            : 'text-slate-600'
                        )}
                      />
                    ))}
                  </div>
                  <span className="text-2xl font-bold text-yellow-400">{survey.overall_score}/5.0</span>
                </div>
              </div>
            )}

            {/* Detailed Scores */}
            {survey.scores && (
              <div>
                <p className="text-sm text-slate-400 mb-2">详细评分</p>
                <div className="space-y-3">
                  {Object.entries(survey.scores).map(([key, score]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-white">
                        {key === 'service_quality' ? '服务质量' : 
                         key === 'response_speed' ? '响应速度' :
                         key === 'technical_support' ? '技术支持' :
                         key === 'problem_resolution' ? '问题解决' :
                         key === 'communication' ? '沟通' : key}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-0.5">
                          {[1, 2, 3, 4, 5].map((i) => (
                            <Star
                              key={i}
                              className={cn(
                                'w-4 h-4',
                                i <= score
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-slate-600'
                              )}
                            />
                          ))}
                        </div>
                        <span className="text-white font-medium w-8 text-right">{score}/5</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Feedback */}
            {survey.feedback && (
              <div>
                <p className="text-sm text-slate-400 mb-1">客户反馈</p>
                <p className="text-white bg-slate-800/50 p-3 rounded-lg">{survey.feedback}</p>
              </div>
            )}

            {/* Suggestions */}
            {survey.suggestions && (
              <div>
                <p className="text-sm text-slate-400 mb-1">改进建议</p>
                <p className="text-white bg-slate-800/50 p-3 rounded-lg">{survey.suggestions}</p>
              </div>
            )}

            {/* Response Info */}
            {survey.response_date && (
              <div>
                <p className="text-sm text-slate-400 mb-1">回复时间</p>
                <p className="text-white">{survey.response_date}</p>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          {survey.status === '待发送' && (
            <Button variant="outline" onClick={() => onSend(survey.id)}>
              <Send className="w-4 h-4 mr-2" />
              发送调查
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

