/**
 * Sales Team Management Page - Team performance and management for sales directors
 * Features: Team member management, Performance tracking, Target assignment, Team analytics
 */

import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Users,
  UserPlus,
  Target,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Award,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  Mail,
  Phone,
  Calendar,
  Edit,
  MoreHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesStatisticsApi } from '../services/api'

// Mock team data
const mockTeamMembers = [
  {
    id: 1,
    name: '张销售',
    role: '销售工程师',
    department: '销售部',
    email: 'zhang@example.com',
    phone: '138****1234',
    monthlyTarget: 300000,
    monthlyAchieved: 285000,
    achievementRate: 95,
    yearTarget: 3600000,
    yearAchieved: 2850000,
    yearProgress: 79.2,
    activeProjects: 5,
    newCustomers: 2,
    status: 'excellent',
    joinDate: '2023-03-15',
    lastActivity: '2小时前',
  },
  {
    id: 2,
    name: '李销售',
    role: '销售工程师',
    department: '销售部',
    email: 'li@example.com',
    phone: '139****5678',
    monthlyTarget: 300000,
    monthlyAchieved: 245000,
    achievementRate: 81.7,
    yearTarget: 3600000,
    yearAchieved: 2450000,
    yearProgress: 68.1,
    activeProjects: 4,
    newCustomers: 1,
    status: 'good',
    joinDate: '2023-06-20',
    lastActivity: '1天前',
  },
  {
    id: 3,
    name: '王销售',
    role: '销售工程师',
    department: '销售部',
    email: 'wang@example.com',
    phone: '137****9012',
    monthlyTarget: 300000,
    monthlyAchieved: 198000,
    achievementRate: 66,
    yearTarget: 3600000,
    yearAchieved: 1980000,
    yearProgress: 55,
    activeProjects: 3,
    newCustomers: 0,
    status: 'warning',
    joinDate: '2024-01-10',
    lastActivity: '3天前',
  },
  {
    id: 4,
    name: '刘销售',
    role: '销售经理',
    department: '销售部',
    email: 'liu@example.com',
    phone: '136****3456',
    monthlyTarget: 800000,
    monthlyAchieved: 720000,
    achievementRate: 90,
    yearTarget: 9600000,
    yearAchieved: 7200000,
    yearProgress: 75,
    activeProjects: 8,
    newCustomers: 3,
    status: 'excellent',
    joinDate: '2022-05-12',
    lastActivity: '30分钟前',
  },
  {
    id: 5,
    name: '陈销售',
    role: '销售工程师',
    department: '销售部',
    email: 'chen@example.com',
    phone: '135****7890',
    monthlyTarget: 300000,
    monthlyAchieved: 320000,
    achievementRate: 106.7,
    yearTarget: 3600000,
    yearAchieved: 3200000,
    yearProgress: 88.9,
    activeProjects: 6,
    newCustomers: 2,
    status: 'excellent',
    joinDate: '2023-09-01',
    lastActivity: '1小时前',
  },
]

const mockTeamStats = {
  totalMembers: 18,
  activeMembers: 16,
  totalTarget: 5400000,
  totalAchieved: 3850000,
  avgAchievementRate: 77.2,
  totalProjects: 45,
  totalCustomers: 156,
  newCustomersThisMonth: 12,
}

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const statusConfig = {
  excellent: { label: '优秀', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  good: { label: '良好', color: 'bg-blue-500', textColor: 'text-blue-400' },
  warning: { label: '需关注', color: 'bg-amber-500', textColor: 'text-amber-400' },
  poor: { label: '待改进', color: 'bg-red-500', textColor: 'text-red-400' },
}

export default function SalesTeam() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMember, setSelectedMember] = useState(null)
  const [showMemberDialog, setShowMemberDialog] = useState(false)
  const [loading, setLoading] = useState(false)
  const [teamMembers, setTeamMembers] = useState(mockTeamMembers)

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await salesStatisticsApi.getBySalesperson()
        if (res.data?.items) {
          setTeamMembers(res.data.items)
        } else if (Array.isArray(res.data)) {
          setTeamMembers(res.data)
        }
      } catch (err) {
        console.log('Sales team API unavailable, using mock data')
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  const filteredMembers = useMemo(() => {
    if (!searchTerm) return teamMembers
    return teamMembers.filter(member =>
      member.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      member.role.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [teamMembers, searchTerm])

  const handleViewMember = (member) => {
    setSelectedMember(member)
    setShowMemberDialog(true)
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="团队管理"
        description={`团队规模: ${mockTeamStats.totalMembers}人 | 活跃成员: ${mockTeamStats.activeMembers}人 | 平均完成率: ${mockTeamStats.avgAchievementRate}%`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              团队报表
            </Button>
            <Button className="flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              添加成员
            </Button>
          </motion.div>
        }
      />

      {/* Team Stats */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">团队目标</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(mockTeamStats.totalTarget)}
                </p>
                <p className="text-xs text-slate-500 mt-1">本月总目标</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">团队完成</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(mockTeamStats.totalAchieved)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">
                    {mockTeamStats.avgAchievementRate}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">进行中项目</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {mockTeamStats.totalProjects}
                </p>
                <p className="text-xs text-slate-500 mt-1">团队项目总数</p>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">客户总数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {mockTeamStats.totalCustomers}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  本月新增 {mockTeamStats.newCustomersThisMonth}
                </p>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Users className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Search and Filter */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Input
                  placeholder="搜索团队成员..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
                <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Team Members List */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-400" />
              团队成员 ({filteredMembers.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredMembers.map((member, index) => {
                const status = statusConfig[member.status]
                return (
                  <div
                    key={member.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3 flex-1">
                        <div className={cn(
                          'w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold',
                          index === 0 && 'bg-gradient-to-br from-amber-500 to-orange-500',
                          index === 1 && 'bg-gradient-to-br from-blue-500 to-cyan-500',
                          index === 2 && 'bg-gradient-to-br from-purple-500 to-pink-500',
                          index >= 3 && 'bg-slate-600',
                        )}>
                          {member.name[0]}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{member.name}</span>
                            <Badge variant="outline" className="text-xs bg-slate-700/40">
                              {member.role}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={cn('text-xs', status.textColor)}
                            >
                              {status.label}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <span>{member.activeProjects} 个项目</span>
                            <span>{member.newCustomers} 个新客户</span>
                            <span>最后活动: {member.lastActivity}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right mr-4">
                        <div className="text-lg font-bold text-white">
                          {formatCurrency(member.monthlyAchieved)}
                        </div>
                        <div className="text-xs text-slate-400">
                          目标: {formatCurrency(member.monthlyTarget)}
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewMember(member)}>
                            <BarChart3 className="w-4 h-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="w-4 h-4 mr-2" />
                            编辑目标
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Mail className="w-4 h-4 mr-2" />
                            发送邮件
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Phone className="w-4 h-4 mr-2" />
                            拨打电话
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Performance Metrics */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">本月完成率</span>
                        <span className={cn(
                          'font-medium',
                          member.achievementRate >= 90 ? 'text-emerald-400' :
                          member.achievementRate >= 70 ? 'text-amber-400' :
                          'text-red-400'
                        )}>
                          {member.achievementRate}%
                        </span>
                      </div>
                      <Progress
                        value={member.achievementRate}
                        className="h-1.5 bg-slate-700/50"
                      />
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">年度进度</span>
                        <span className="text-slate-400">
                          {formatCurrency(member.yearAchieved)} / {formatCurrency(member.yearTarget)}
                        </span>
                      </div>
                      <Progress
                        value={member.yearProgress}
                        className="h-1.5 bg-slate-700/50"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Member Detail Dialog */}
      <Dialog open={showMemberDialog} onOpenChange={setShowMemberDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedMember?.name} - 详细信息</DialogTitle>
            <DialogDescription>
              查看团队成员的详细业绩和活动信息
            </DialogDescription>
          </DialogHeader>
          {selectedMember && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">角色</p>
                  <p className="text-white font-medium">{selectedMember.role}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">部门</p>
                  <p className="text-white font-medium">{selectedMember.department}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">邮箱</p>
                  <p className="text-white font-medium">{selectedMember.email}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">电话</p>
                  <p className="text-white font-medium">{selectedMember.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">入职日期</p>
                  <p className="text-white font-medium">{selectedMember.joinDate}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">最后活动</p>
                  <p className="text-white font-medium">{selectedMember.lastActivity}</p>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-700">
                <h4 className="text-sm font-medium text-white mb-3">业绩概览</h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-400">本月完成</span>
                      <span className="text-white font-medium">
                        {formatCurrency(selectedMember.monthlyAchieved)} / {formatCurrency(selectedMember.monthlyTarget)}
                      </span>
                    </div>
                    <Progress value={selectedMember.achievementRate} className="h-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-400">年度完成</span>
                      <span className="text-white font-medium">
                        {formatCurrency(selectedMember.yearAchieved)} / {formatCurrency(selectedMember.yearTarget)}
                      </span>
                    </div>
                    <Progress value={selectedMember.yearProgress} className="h-2" />
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMemberDialog(false)}>
              关闭
            </Button>
            <Button>编辑目标</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

