import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Clock, UserCheck, AlertCircle,
  BarChart3, Download, Calendar } from
'lucide-react';
import StatCard from '../common/StatCard';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

/**
 * 考勤趋势项
 */
const AttendanceTrendItem = ({ date, attendanceRate, lateCount, leaveCount }) =>
<div className="space-y-2">
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium text-slate-300">{date}</span>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-sm text-emerald-400">{attendanceRate}%</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-amber-400">{lateCount}人迟到</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-blue-400">{leaveCount}人请假</span>
        </div>
      </div>
    </div>
    <Progress value={attendanceRate} className="h-2" />
</div>;


/**
 * 考勤统计标签页组件
 * 
 * @param {Object} props
 * @param {Object} props.stats - 考勤统计数据
 * @param {Array} props.trends - 考勤趋势数据
 * @param {Function} props.onExport - 导出回调
 * @param {Function} props.onViewDetails - 查看详情回调
 */
export const HRAttendanceTab = ({
  stats = {
    todayAttendanceRate: 0,
    monthlyAttendanceRate: 0,
    lateCount: 0,
    absentCount: 0
  },
  trends = [],
  onExport,
  onViewDetails
}) => {
  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="今日出勤率"
          value={`${stats.todayAttendanceRate}%`}
          layout="row"
          valueClassName="text-lg"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:border-white/20 hover:shadow-none bg-none p-6"
        >
          <Progress value={stats.todayAttendanceRate} className="h-2" />
        </StatCard>

        <StatCard
          title="本月出勤率"
          value={`${stats.monthlyAttendanceRate}%`}
          layout="row"
          valueClassName="text-lg"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:border-white/20 hover:shadow-none bg-none p-6"
        >
          <Progress value={stats.monthlyAttendanceRate} className="h-2" />
        </StatCard>

        <StatCard
          title="今日迟到"
          value={`${stats.lateCount}人`}
          layout="row"
          valueClassName="text-lg"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:border-white/20 hover:shadow-none bg-none p-6"
        />

        <StatCard
          title="今日缺勤"
          value={`${stats.absentCount}人`}
          layout="row"
          valueClassName="text-lg"
          showDecoration={false}
          cardClassName="bg-surface-50 border-white/10 hover:border-white/20 hover:shadow-none bg-none p-6"
        />

      </div>

      {/* 考勤趋势 */}
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              最近7天考勤趋势
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary"
              onClick={onViewDetails}>

              查看详情
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {trends.length > 0 ?
            trends.map((trend, index) =>
            <AttendanceTrendItem key={index} {...trend} />
            ) :

            <div className="text-center py-8 text-slate-400">
                暂无考勤趋势数据
            </div>
            }
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="text-base">快速操作</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button
            className="flex items-center gap-2"
            onClick={onExport}>

            <Download className="w-4 h-4" />
            导出考勤
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            考勤日历
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            考勤分析
          </Button>
        </CardContent>
      </Card>
    </motion.div>);

};

export default HRAttendanceTab;
