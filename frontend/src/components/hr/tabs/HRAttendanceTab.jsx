/**
 * HRAttendanceTab Component
 * 考勤管理 Tab 组件
 */
import { Card, CardContent } from "../../ui";
import { Progress } from "../../ui";
import { Clock, AlertTriangle } from "lucide-react";

export default function HRAttendanceTab({ mockHRStats }) {
  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-slate-400">今日出勤率</p>
              <p className="text-lg font-bold text-white">
                {mockHRStats.todayAttendanceRate}%
              </p>
            </div>
            <Progress value={mockHRStats.todayAttendanceRate} className="h-2" />
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-slate-400">月度出勤率</p>
              <p className="text-lg font-bold text-white">
                {mockHRStats.monthlyAttendanceRate}%
              </p>
            </div>
            <Progress
              value={mockHRStats.monthlyAttendanceRate}
              className="h-2"
            />
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">迟到人数</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.lateCount}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <Clock className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">缺勤人数</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.absentCount}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
