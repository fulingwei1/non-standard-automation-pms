import { motion } from "framer-motion";
import { UserCheck, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Progress
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";

const AttendanceStatistics = ({ attendanceStats }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <UserCheck className="h-5 w-5 text-emerald-400" />
              部门出勤统计
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary">
              详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {(attendanceStats || []).map((stat, index) =>
          <div
            key={index}
            className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white text-sm">
                      {stat.department}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                    <span>总人数: {stat.total}</span>
                    <span>出勤: {stat.present}</span>
                    {stat.leave > 0 &&
                  <span className="text-amber-400">
                        请假: {stat.leave}
                  </span>
                  }
                    {stat.late > 0 &&
                  <span className="text-red-400">
                        迟到: {stat.late}
                  </span>
                  }
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-emerald-400">
                    {stat.attendanceRate}%
                  </div>
                  <div className="text-xs text-slate-400">出勤率</div>
                </div>
              </div>
              <Progress
              value={stat.attendanceRate}
              className="h-1.5 bg-slate-700/50 mt-2" />

          </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default AttendanceStatistics;
