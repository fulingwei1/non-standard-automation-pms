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

// Mock data
const mockAttendanceStats = [
  {
    department: '销售部',
    total: 45,
    present: 43,
    leave: 2,
    late: 1,
    earlyLeave: 0,
    absence: 0,
    attendanceRate: 95.6,
  },
  {
    department: '项目部',
    total: 38,
    present: 37,
    leave: 1,
    late: 0,
    earlyLeave: 0,
    absence: 0,
    attendanceRate: 97.4,
  },
  {
    department: '技术开发部',
    total: 52,
    present: 51,
    leave: 1,
    late: 0,
    earlyLeave: 0,
    absence: 0,
    attendanceRate: 98.1,
  },
  {
    department: '生产部',
    total: 28,
    present: 28,
    leave: 0,
    late: 0,
    earlyLeave: 0,
    absence: 0,
    attendanceRate: 100,
  },
]

const mockLeaveApplications = [
  {
    id: 1,
    employee: '赵工程师',
    department: '机械部',
    type: '年假',
    days: 3,
    startDate: '2025-01-10',
    endDate: '2025-01-12',
    reason: '个人事务',
    status: 'pending',
    submitTime: '2025-01-06 11:30',
  },
  {
    id: 2,
    employee: '钱工程师',
    department: '电气部',
    type: '病假',
    days: 1,
    startDate: '2025-01-08',
    endDate: '2025-01-08',
    reason: '身体不适',
    status: 'approved',
    submitTime: '2025-01-07 09:00',
  },
]

export default function AttendanceManagement() {
  const [searchText, setSearchText] = useState('')
  const [dateFilter, setDateFilter] = useState('today')
  const [loading, setLoading] = useState(false)
  const [attendanceStats, setAttendanceStats] = useState(mockAttendanceStats)

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
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">员工</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">部门</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">日期</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">上班打卡</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">下班打卡</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">工时</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">状态</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { name: '赵工程师', dept: '机械部', date: '2025-01-08', checkIn: '08:55', checkOut: '18:10', hours: 9.25, status: 'normal' },
                      { name: '钱工程师', dept: '电气部', date: '2025-01-08', checkIn: '09:15', checkOut: '18:30', hours: 9.25, status: 'late' },
                      { name: '孙工程师', dept: '软件部', date: '2025-01-08', checkIn: '08:45', checkOut: '17:30', hours: 8.75, status: 'early' },
                      { name: '李工程师', dept: '项目部', date: '2025-01-08', checkIn: '08:50', checkOut: '18:00', hours: 9.17, status: 'normal' },
                      { name: '周工程师', dept: '测试部', date: '2025-01-08', checkIn: '-', checkOut: '-', hours: 0, status: 'absent' },
                      { name: '吴工程师', dept: '销售部', date: '2025-01-08', checkIn: '08:58', checkOut: '20:30', hours: 11.53, status: 'overtime' },
                    ].map((record, idx) => (
                      <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/30">
                        <td className="py-3 px-4 text-white">{record.name}</td>
                        <td className="py-3 px-4 text-slate-400">{record.dept}</td>
                        <td className="py-3 px-4 text-center text-slate-300">{record.date}</td>
                        <td className="py-3 px-4 text-center text-slate-300">{record.checkIn}</td>
                        <td className="py-3 px-4 text-center text-slate-300">{record.checkOut}</td>
                        <td className="py-3 px-4 text-center text-slate-300">{record.hours > 0 ? record.hours.toFixed(2) : '-'}</td>
                        <td className="py-3 px-4 text-center">
                          <Badge
                            variant="outline"
                            className={cn(
                              record.status === 'normal' && 'bg-green-500/20 text-green-400 border-green-500/30',
                              record.status === 'late' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                              record.status === 'early' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              record.status === 'absent' && 'bg-red-500/20 text-red-400 border-red-500/30',
                              record.status === 'overtime' && 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                            )}
                          >
                            {record.status === 'normal' ? '正常' :
                             record.status === 'late' ? '迟到' :
                             record.status === 'early' ? '早退' :
                             record.status === 'absent' ? '缺勤' : '加班'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
              <div className="space-y-4">
                {[
                  { id: 1, employee: '吴工程师', dept: '销售部', date: '2025-01-08', hours: 2.5, reason: '客户紧急需求跟进', status: 'approved' },
                  { id: 2, employee: '郑工程师', dept: '项目部', date: '2025-01-07', hours: 3, reason: '项目上线准备', status: 'pending' },
                  { id: 3, employee: '王工程师', dept: '技术部', date: '2025-01-06', hours: 4, reason: '系统故障排查', status: 'approved' },
                  { id: 4, employee: '陈工程师', dept: '生产部', date: '2025-01-05', hours: 2, reason: '生产任务赶工', status: 'rejected' },
                ].map((ot) => (
                  <div key={ot.id} className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-white">{ot.employee}</span>
                          <Badge variant="outline">{ot.dept}</Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              ot.status === 'pending' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                              ot.status === 'approved' && 'bg-green-500/20 text-green-400 border-green-500/30',
                              ot.status === 'rejected' && 'bg-red-500/20 text-red-400 border-red-500/30'
                            )}
                          >
                            {ot.status === 'pending' ? '待审批' : ot.status === 'approved' ? '已批准' : '已拒绝'}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400 space-y-1">
                          <p>日期: {ot.date} · 时长: {ot.hours} 小时</p>
                          <p>原因: {ot.reason}</p>
                        </div>
                      </div>
                      {ot.status === 'pending' && (
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
      </Tabs>
    </motion.div>
  )
}

