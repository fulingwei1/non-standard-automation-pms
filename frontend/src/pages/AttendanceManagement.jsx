/**
 * Attendance Management - Employee attendance management
 * Features: Attendance records, statistics, leave management, overtime tracking
 */

import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Search,
  Filter,
  UserCheck,
  Calendar,
  Clock,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Download,
  BarChart3,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
} from '../components/ui'
import { cn } from '../lib/utils'
import { staggerContainer } from '../lib/animations'
import { SimpleBarChart, MonthlyTrendChart, TrendComparisonCard } from '../components/administrative/StatisticsCharts'
import { adminApi } from '../services/api'

export default function AttendanceManagement() {
  const [searchText, setSearchText] = useState('')
  const [dateFilter, setDateFilter] = useState('today')
  const [loading, setLoading] = useState(false)
  const [attendanceStats, setAttendanceStats] = useState([])

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await adminApi.attendance.list({ date: dateFilter })
        if (res.data?.items) {
          setAttendanceStats(res.data.items)
        } else if (Array.isArray(res.data)) {
          setAttendanceStats(res.data)
        }
      } catch (err) {
        console.log('Attendance API unavailable, using mock data')
      }
      setLoading(false)
    }
    fetchData()
  }, [dateFilter])

  const overallStats = useMemo(() => {
    const total = attendanceStats.reduce((sum, s) => sum + s.total, 0)
    const present = attendanceStats.reduce((sum, s) => sum + s.present, 0)
    const leave = attendanceStats.reduce((sum, s) => sum + s.leave, 0)
    const late = attendanceStats.reduce((sum, s) => sum + s.late, 0)
    const attendanceRate = total > 0 ? (present / total) * 100 : 0
    return { total, present, leave, late, attendanceRate }
  }, [attendanceStats])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="员工考勤管理"
        description="员工考勤记录、统计分析、请假管理、加班管理"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出报表
            </Button>
            <Button variant="outline">
              <BarChart3 className="w-4 h-4 mr-2" />
              统计分析
            </Button>
          </div>
        }
      />

      {/* Overall Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总人数</p>
                <p className="text-2xl font-bold text-white mt-1">{overallStats.total}</p>
              </div>
              <UserCheck className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">出勤</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{overallStats.present}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">请假</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{overallStats.leave}</p>
              </div>
              <Calendar className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">迟到</p>
                <p className="text-2xl font-bold text-red-400 mt-1">{overallStats.late}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">出勤率</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">{overallStats.attendanceRate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-cyan-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="statistics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="statistics">部门统计</TabsTrigger>
          <TabsTrigger value="records">考勤记录</TabsTrigger>
          <TabsTrigger value="leave">请假管理</TabsTrigger>
          <TabsTrigger value="overtime">加班管理</TabsTrigger>
        </TabsList>

        <TabsContent value="statistics" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {attendanceStats.map((stat, index) => (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">{stat.department}</h3>
                      <p className="text-sm text-slate-400">总人数: {stat.total}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-400">{stat.attendanceRate.toFixed(1)}%</p>
                      <p className="text-xs text-slate-400">出勤率</p>
                    </div>
                  </div>
                  <Progress value={stat.attendanceRate} className="h-2 mb-4" />
                  <div className="grid grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">出勤</p>
                      <p className="text-emerald-400 font-medium">{stat.present}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">请假</p>
                      <p className="text-amber-400 font-medium">{stat.leave}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">迟到</p>
                      <p className="text-red-400 font-medium">{stat.late}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">早退</p>
                      <p className="text-orange-400 font-medium">{stat.earlyLeave}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">缺勤</p>
                      <p className="text-red-500 font-medium">{stat.absence}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="records">
          <Card>
            <CardHeader>
              <CardTitle>考勤记录</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400">TODO: 考勤记录列表</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leave" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>请假申请</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockLeaveApplications.map((app) => (
                  <div key={app.id} className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-white">{app.employee}</span>
                          <Badge variant="outline">{app.department}</Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              app.status === 'pending' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                              app.status === 'approved' && 'bg-green-500/20 text-green-400 border-green-500/30'
                            )}
                          >
                            {app.status === 'pending' ? '待审批' : '已批准'}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400 space-y-1">
                          <p>类型: {app.type} · 天数: {app.days} 天</p>
                          <p>时间: {app.startDate} 至 {app.endDate}</p>
                          <p>原因: {app.reason}</p>
                          <p className="text-xs text-slate-500">提交时间: {app.submitTime}</p>
                        </div>
                      </div>
                      {app.status === 'pending' && (
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">批准</Button>
                          <Button size="sm" variant="outline">拒绝</Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overtime">
          <Card>
            <CardHeader>
              <CardTitle>加班管理</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400">TODO: 加班申请列表</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}

