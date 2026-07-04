/**
 * Attendance Management - Employee attendance management
 * Features: Attendance records, statistics, leave management, overtime tracking
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  UserCheck,
  Calendar,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Download,
  BarChart3 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress } from
"../components/ui";
import { staggerContainer } from "../lib/animations";


import { adminApi } from "../services/api";

export default function AttendanceManagement() {
  const [_searchText, _setSearchText] = useState("");
  const [dateFilter, _setDateFilter] = useState("today");
  const [_loading, setLoading] = useState(false);
  const [attendanceStats, setAttendanceStats] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await adminApi.attendance.list({ date: dateFilter });
        if (res.data?.items) {
          setAttendanceStats(res.data.items);
        } else if (Array.isArray(res.data)) {
          setAttendanceStats(res.data);
        }
      } catch (_err) {
        console.log("Attendance API unavailable, using mock data");
      }
      setLoading(false);
    };
    fetchData();
  }, [dateFilter]);

  const overallStats = useMemo(() => {
    const total = (attendanceStats || []).reduce((sum, s) => sum + s.total, 0);
    const present = (attendanceStats || []).reduce((sum, s) => sum + s.present, 0);
    const leave = (attendanceStats || []).reduce((sum, s) => sum + s.leave, 0);
    const late = (attendanceStats || []).reduce((sum, s) => sum + s.late, 0);
    const attendanceRate = total > 0 ? present / total * 100 : 0;
    return { total, present, leave, late, attendanceRate };
  }, [attendanceStats]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="员工考勤管理"
        description="员工考勤记录、统计分析"
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
        } />


      {/* Overall Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总人数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {overallStats.total}
                </p>
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
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  {overallStats.present}
                </p>
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
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {overallStats.leave}
                </p>
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
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {overallStats.late}
                </p>
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
                <p className="text-2xl font-bold text-cyan-400 mt-1">
                  {overallStats.attendanceRate.toFixed(1)}%
                </p>
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
        </TabsList>

        <TabsContent value="statistics" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {(attendanceStats || []).map((stat, index) =>
            <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-1">
                        {stat.department}
                      </h3>
                      <p className="text-sm text-slate-400">
                        总人数: {stat.total}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-emerald-400">
                        {stat.attendanceRate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-slate-400">出勤率</p>
                    </div>
                  </div>
                  <Progress value={stat.attendanceRate} className="h-2 mb-4" />
                  <div className="grid grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-slate-400">出勤</p>
                      <p className="text-emerald-400 font-medium">
                        {stat.present}
                      </p>
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
                      <p className="text-orange-400 font-medium">
                        {stat.earlyLeave}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">缺勤</p>
                      <p className="text-red-500 font-medium">{stat.absence}</p>
                    </div>
                  </div>
                </CardContent>
            </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="records">
          <Card>
            <CardHeader>
              <CardTitle>考勤记录</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-slate-400 text-sm py-6 text-center">
                暂无考勤明细记录（当前仅展示部门考勤统计）
              </div>
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>
    </motion.div>);

}
