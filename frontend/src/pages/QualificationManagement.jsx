/**
 * Qualification Management - 任职资格管理主页面
 * Features: 等级管理、能力模型管理、员工任职资格管理、评估记录
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Award,
  Users,
  FileText,
  TrendingUp,
  Plus,
  Edit,
  Trash2,
  Eye,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  Search,
  ArrowRight,
  Settings,
  UserCheck,
  BarChart3,
  Download,
  Upload,
  MoreVertical,
  CheckSquare,
  XSquare,
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
import { Badge } from '../components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { Input } from '../components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { qualificationApi } from '../services/api'
import { toast } from '../components/ui/toast'
import { CompetencyRadarChart } from '../components/qualification/CompetencyRadarChart'
export default function QualificationManagement() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('levels')
  const [loading, setLoading] = useState(false)
  
  // 等级管理
  const [levels, setLevels] = useState([])
  const [levelFilter, setLevelFilter] = useState({ role_type: '', is_active: true })
  
  // 能力模型管理
  const [models, setModels] = useState([])
  const [modelFilter, setModelFilter] = useState({ position_type: '', level_id: '' })
  
  // 员工任职资格
  const [qualifications, setQualifications] = useState([])
  const [qualificationFilter, setQualificationFilter] = useState({ position_type: '', status: '' })
  
  // 统计数据
  const [stats, setStats] = useState({
    total_levels: 0,
    total_models: 0,
    total_qualifications: 0,
    pending_certifications: 0,
  })

  useEffect(() => {
    loadData()
  }, [activeTab, levelFilter, modelFilter, qualificationFilter, pagination.page])

  const loadData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'levels') {
        await loadLevels()
      } else if (activeTab === 'models') {
        await loadModels()
      } else if (activeTab === 'employees') {
        await loadQualifications()
      }
      await loadStats()
    } catch (error) {
      console.error('加载数据失败:', error)
      toast.error('加载数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const loadLevels = async () => {
    try {
      const response = await qualificationApi.getLevels({
        page: 1,
        page_size: 100,
        ...levelFilter,
      })
      if (response.data?.code === 200) {
        setLevels(response.data.data?.items || [])
      }
    } catch (error) {
      console.error('加载等级列表失败:', error)
    }
  }

  const loadModels = async () => {
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
        ...modelFilter,
      }
      if (modelSearch) {
        params.keyword = modelSearch
      }
      const response = await qualificationApi.getModels(params)
      if (response.data?.code === 200) {
        setModels(response.data.data?.items || [])
        setPagination(prev => ({
          ...prev,
          total: response.data.data?.total || 0,
        }))
      }
    } catch (error) {
      console.error('加载能力模型失败:', error)
    }
  }

  const loadQualifications = async () => {
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
        ...qualificationFilter,
      }
      if (qualificationSearch) {
        params.keyword = qualificationSearch
      }
      const response = await qualificationApi.getEmployeeQualifications(params)
      if (response.data?.code === 200) {
        setQualifications(response.data.data?.items || [])
        setPagination(prev => ({
          ...prev,
          total: response.data.data?.total || 0,
        }))
      }
    } catch (error) {
      console.error('加载员工任职资格失败:', error)
    }
  }

  const loadStats = async () => {
    try {
      // 加载统计数据
      const [levelsRes, modelsRes, qualificationsRes] = await Promise.all([
        qualificationApi.getLevels({ page: 1, page_size: 1 }),
        qualificationApi.getModels({ page: 1, page_size: 1 }),
        qualificationApi.getEmployeeQualifications({ page: 1, page_size: 1, status: 'PENDING' }),
      ])
      
      setStats({
        total_levels: levelsRes.data?.data?.total || 0,
        total_models: modelsRes.data?.data?.total || 0,
        total_qualifications: qualificationsRes.data?.data?.total || 0,
        pending_certifications: qualificationsRes.data?.data?.total || 0,
      })
    } catch (error) {
      console.error('加载统计数据失败:', error)
    }
  }

  const handleDeleteLevel = async (id) => {
    if (!confirm('确定要删除该等级吗？')) return
    
    try {
      await qualificationApi.deleteLevel(id)
      toast.success('等级删除成功')
      loadLevels()
    } catch (error) {
      toast.error(error.response?.data?.detail || '删除失败')
    }
  }

  const getLevelBadgeColor = (levelCode) => {
    const colors = {
      ASSISTANT: 'bg-gray-100 text-gray-800',
      JUNIOR: 'bg-blue-100 text-blue-800',
      MIDDLE: 'bg-green-100 text-green-800',
      SENIOR: 'bg-purple-100 text-purple-800',
      EXPERT: 'bg-yellow-100 text-yellow-800',
    }
    return colors[levelCode] || 'bg-gray-100 text-gray-800'
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      PENDING: { label: '待认证', color: 'bg-yellow-100 text-yellow-800' },
      APPROVED: { label: '已认证', color: 'bg-green-100 text-green-800' },
      EXPIRED: { label: '已过期', color: 'bg-red-100 text-red-800' },
      REVOKED: { label: '已撤销', color: 'bg-gray-100 text-gray-800' },
    }
    const statusInfo = statusMap[status] || { label: status, color: 'bg-gray-100 text-gray-800' }
    return <Badge className={statusInfo.color}>{statusInfo.label}</Badge>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="任职资格管理"
        description="管理任职资格等级、能力模型和员工认证"
        icon={Award}
      />

      {/* 统计卡片 */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">等级总数</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_levels}</div>
            <p className="text-xs text-muted-foreground">任职资格等级</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">能力模型</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_models}</div>
            <p className="text-xs text-muted-foreground">岗位能力模型</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">已认证员工</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_qualifications}</div>
            <p className="text-xs text-muted-foreground">获得任职资格</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">待认证</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending_certifications}</div>
            <p className="text-xs text-muted-foreground">待处理认证</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* 主要内容区域 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>任职资格管理</CardTitle>
              <CardDescription>管理等级、能力模型和员工认证</CardDescription>
            </div>
            <div className="flex gap-2">
              {activeTab === 'levels' && (
                <Button onClick={() => navigate('/qualifications/levels/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建等级
                </Button>
              )}
              {activeTab === 'models' && (
                <Button onClick={() => navigate('/qualifications/models/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建能力模型
                </Button>
              )}
              {activeTab === 'employees' && (
                <Button onClick={() => navigate('/qualifications/employees/certify')}>
                  <UserCheck className="h-4 w-4 mr-2" />
                  认证员工
                </Button>
              )}
              {activeTab === 'levels' && (
                <Button onClick={() => navigate('/qualifications/levels/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建等级
                </Button>
              )}
              {activeTab === 'models' && (
                <Button onClick={() => navigate('/qualifications/models/new')}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建能力模型
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="levels">等级管理</TabsTrigger>
              <TabsTrigger value="models">能力模型</TabsTrigger>
              <TabsTrigger value="employees">员工认证</TabsTrigger>
            </TabsList>

            {/* 等级管理 */}
            <TabsContent value="levels" className="space-y-4">
              <div className="flex gap-2">
                <Select
                  value={levelFilter.role_type}
                  onValueChange={(value) => setLevelFilter({ ...levelFilter, role_type: value })}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="筛选角色类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部</SelectItem>
                    <SelectItem value="ENGINEER">工程师</SelectItem>
                    <SelectItem value="SALES">销售</SelectItem>
                    <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
                    <SelectItem value="WORKER">生产工人</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={levelFilter.is_active?.toString()}
                  onValueChange={(value) => setLevelFilter({ ...levelFilter, is_active: value === 'true' })}
                >
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部</SelectItem>
                    <SelectItem value="true">启用</SelectItem>
                    <SelectItem value="false">停用</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedLevels.length === levels.length && levels.length > 0}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedLevels(levels.map(l => l.id))
                          } else {
                            setSelectedLevels([])
                          }
                        }}
                      />
                    </TableHead>
                    <TableHead>等级编码</TableHead>
                    <TableHead>等级名称</TableHead>
                    <TableHead>排序</TableHead>
                    <TableHead>适用角色</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {levels.map((level) => (
                    <TableRow key={level.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedLevels.includes(level.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedLevels([...selectedLevels, level.id])
                            } else {
                              setSelectedLevels(selectedLevels.filter(id => id !== level.id))
                            }
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Badge className={getLevelBadgeColor(level.level_code)}>
                          {level.level_code}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">{level.level_name}</TableCell>
                      <TableCell>{level.level_order}</TableCell>
                      <TableCell>{level.role_type || '通用'}</TableCell>
                      <TableCell>
                        {level.is_active ? (
                          <Badge className="bg-green-100 text-green-800">启用</Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-800">停用</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/levels/${level.id}`)}
                            title="查看详情"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/levels/${level.id}/edit`)}
                            title="编辑"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteLevel(level.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>

            {/* 能力模型管理 */}
            <TabsContent value="models" className="space-y-4">
              <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="搜索岗位类型、子类型..."
                    value={modelSearch}
                    onChange={(e) => setModelSearch(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        setPagination(prev => ({ ...prev, page: 1 }))
                        loadModels()
                      }
                    }}
                    className="pl-10"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => {
                    setModelSearch('')
                    setPagination(prev => ({ ...prev, page: 1 }))
                    loadModels()
                  }}
                >
                  <Search className="h-4 w-4 mr-2" />
                  搜索
                </Button>
                <Button
                  variant="outline"
                  onClick={handleExportModels}
                >
                  <Download className="h-4 w-4 mr-2" />
                  导出
                </Button>
              </div>
              <div className="flex gap-2">
                <Select
                  value={modelFilter.position_type}
                  onValueChange={(value) => setModelFilter({ ...modelFilter, position_type: value })}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="筛选岗位类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部</SelectItem>
                    <SelectItem value="ENGINEER">工程师</SelectItem>
                    <SelectItem value="SALES">销售</SelectItem>
                    <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
                    <SelectItem value="WORKER">生产工人</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>岗位类型</TableHead>
                    <TableHead>子类型</TableHead>
                    <TableHead>等级</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.map((model) => (
                    <TableRow key={model.id}>
                      <TableCell>{model.position_type}</TableCell>
                      <TableCell>{model.position_subtype || '-'}</TableCell>
                      <TableCell>
                        <Badge>{model.level?.level_name || model.level_id}</Badge>
                      </TableCell>
                      <TableCell>
                        {model.created_at ? formatDate(model.created_at) : '-'}
                      </TableCell>
                      <TableCell>
                        {model.is_active ? (
                          <Badge className="bg-green-100 text-green-800">启用</Badge>
                        ) : (
                          <Badge className="bg-gray-100 text-gray-800">停用</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/models/${model.id}`)}
                            title="查看详情"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/models/${model.id}/edit`)}
                            title="编辑"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>

            {/* 员工认证管理 */}
            <TabsContent value="employees" className="space-y-4">
              <div className="flex gap-2">
                <Select
                  value={qualificationFilter.position_type}
                  onValueChange={(value) => setQualificationFilter({ ...qualificationFilter, position_type: value })}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="筛选岗位类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部</SelectItem>
                    <SelectItem value="ENGINEER">工程师</SelectItem>
                    <SelectItem value="SALES">销售</SelectItem>
                    <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
                    <SelectItem value="WORKER">生产工人</SelectItem>
                  </SelectContent>
                </Select>
                <Select
                  value={qualificationFilter.status}
                  onValueChange={(value) => setQualificationFilter({ ...qualificationFilter, status: value })}
                >
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="状态" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">全部</SelectItem>
                    <SelectItem value="PENDING">待认证</SelectItem>
                    <SelectItem value="APPROVED">已认证</SelectItem>
                    <SelectItem value="EXPIRED">已过期</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>员工</TableHead>
                    <TableHead>岗位类型</TableHead>
                    <TableHead>当前等级</TableHead>
                    <TableHead>认证日期</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {qualifications.map((qual) => (
                    <TableRow key={qual.id}>
                      <TableCell className="font-medium">员工 #{qual.employee_id}</TableCell>
                      <TableCell>{qual.position_type}</TableCell>
                      <TableCell>
                        <Badge className={getLevelBadgeColor(qual.level?.level_code)}>
                          {qual.level?.level_name || qual.current_level_id}
                        </Badge>
                      </TableCell>
                      <TableCell>{qual.certified_date ? formatDate(qual.certified_date) : '-'}</TableCell>
                      <TableCell>{getStatusBadge(qual.status)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/employees/${qual.employee_id}/view`)}
                            title="查看详情"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/qualifications/employees/${qual.employee_id}/promote`)}
                            title="晋升评估"
                          >
                            <TrendingUp className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* 可视化图表区域 */}
      {activeTab === 'employees' && qualifications.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 能力维度分析 - 平均分 */}
          <Card>
            <CardHeader>
              <CardTitle>平均能力维度</CardTitle>
              <CardDescription>所有已认证员工的平均能力得分</CardDescription>
            </CardHeader>
            <CardContent>
              {(() => {
                // 计算所有员工的能力维度平均值
                const dimensionScores = {}
                let count = 0
                qualifications.forEach(qual => {
                  if (qual.assessment_details) {
                    Object.keys(qual.assessment_details).forEach(key => {
                      if (!dimensionScores[key]) {
                        dimensionScores[key] = { total: 0, count: 0 }
                      }
                      const score = typeof qual.assessment_details[key] === 'object' 
                        ? qual.assessment_details[key].score 
                        : qual.assessment_details[key]
                      if (typeof score === 'number') {
                        dimensionScores[key].total += score
                        dimensionScores[key].count += 1
                      }
                    })
                    count++
                  }
                })
                
                const avgScores = {}
                Object.keys(dimensionScores).forEach(key => {
                  avgScores[key] = dimensionScores[key].count > 0
                    ? dimensionScores[key].total / dimensionScores[key].count
                    : 0
                })
                
                return Object.keys(avgScores).length > 0 ? (
                  <CompetencyRadarChart 
                    data={avgScores}
                    size={300}
                  />
                ) : (
                  <div className="flex items-center justify-center h-64 text-gray-400">
                    暂无评估数据
                  </div>
                )
              })()}
            </CardContent>
          </Card>

          {/* 等级分布 */}
          <Card>
            <CardHeader>
              <CardTitle>等级分布统计</CardTitle>
              <CardDescription>已认证员工的等级分布情况</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['ASSISTANT', 'JUNIOR', 'MIDDLE', 'SENIOR', 'EXPERT'].map((levelCode) => {
                  const count = qualifications.filter(
                    q => q.level?.level_code === levelCode
                  ).length
                  const percentage = qualifications.length > 0 
                    ? (count / qualifications.length * 100).toFixed(1) 
                    : 0
                  return (
                    <div key={levelCode} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {levelCode === 'ASSISTANT' ? '助理级' :
                           levelCode === 'JUNIOR' ? '初级' :
                           levelCode === 'MIDDLE' ? '中级' :
                           levelCode === 'SENIOR' ? '高级' :
                           '专家级'}
                        </span>
                        <span className="text-sm text-gray-500">
                          {count} 人 ({percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* 岗位类型分布 */}
          <Card>
            <CardHeader>
              <CardTitle>岗位类型分布</CardTitle>
              <CardDescription>不同岗位类型的认证人数</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['ENGINEER', 'SALES', 'CUSTOMER_SERVICE', 'WORKER'].map((positionType) => {
                  const count = qualifications.filter(
                    q => q.position_type === positionType
                  ).length
                  const percentage = qualifications.length > 0 
                    ? (count / qualifications.length * 100).toFixed(1) 
                    : 0
                  const labels = {
                    ENGINEER: '工程师',
                    SALES: '销售',
                    CUSTOMER_SERVICE: '客服',
                    WORKER: '生产工人',
                  }
                  return (
                    <div key={positionType} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{labels[positionType]}</span>
                        <span className="text-sm text-gray-500">
                          {count} 人 ({percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 分页 */}
      {pagination.total > pagination.page_size && (
        <Card>
          <CardContent className="flex items-center justify-between py-4">
            <div className="text-sm text-gray-500">
              共 {pagination.total} 条记录，第 {pagination.page} / {Math.ceil(pagination.total / pagination.page_size)} 页
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                disabled={pagination.page === 1}
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPagination(prev => ({ ...prev, page: Math.min(Math.ceil(prev.total / prev.page_size), prev.page + 1) }))}
                disabled={pagination.page >= Math.ceil(pagination.total / pagination.page_size)}
              >
                下一页
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

  const handleBatchCertify = async () => {
    if (selectedQualifications.length === 0) {
      toast.error('请先选择要认证的员工')
      return
    }
    // 跳转到批量认证页面或打开对话框
    navigate('/qualifications/employees/batch-certify', {
      state: { selectedIds: selectedQualifications }
    })
  }

  const handleExportModels = () => {
    try {
      const exportData = models.map(model => ({
        岗位类型: model.position_type,
        岗位子类型: model.position_subtype || '-',
        等级: model.level?.level_name || model.level_id,
        状态: model.is_active ? '启用' : '停用',
        创建时间: model.created_at ? formatDate(model.created_at) : '-',
      }))

      const headers = Object.keys(exportData[0] || {})
      const csvContent = [
        headers.join(','),
        ...exportData.map(row =>
          headers.map(header => `"${row[header] || ''}"`).join(',')
        ),
      ].join('\n')

      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `能力模型列表_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      toast.error('导出失败')
    }
  }

  const handleExportQualifications = () => {
    try {
      const exportData = qualifications.map(qual => ({
        员工ID: qual.employee_id,
        岗位类型: qual.position_type,
        当前等级: qual.level?.level_name || qual.current_level_id,
        认证日期: qual.certified_date ? formatDate(qual.certified_date) : '-',
        有效期至: qual.valid_until ? formatDate(qual.valid_until) : '-',
        状态: qual.status,
        综合得分: qual.total_score || '-',
      }))

      const headers = Object.keys(exportData[0] || {})
      const csvContent = [
        headers.join(','),
        ...exportData.map(row =>
          headers.map(header => `"${row[header] || ''}"`).join(',')
        ),
      ].join('\n')

      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `员工任职资格列表_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      toast.error('导出失败')
    }
  }

