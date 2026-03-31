import {
  Card,
  CardContent,
} from "../../components/ui";
import {
  Clock,
  AlertCircle,
} from "lucide-react";

export default function TimesheetTab({ project, timesheetSummary }) {
  if (timesheetSummary) {
    return (
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            工时汇总
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">总工时</p>
              <p className="text-2xl font-semibold text-white">
                {timesheetSummary.total_hours?.toFixed(1) || 0} 小时
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">参与人数</p>
              <p className="text-2xl font-semibold text-white">
                {timesheetSummary.total_participants || 0} 人
              </p>
            </div>
          </div>

          {timesheetSummary.by_user &&
            timesheetSummary.by_user?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-slate-400 mb-3">
                  按人员统计
                </h4>
                <div className="space-y-2">
                  {(timesheetSummary.by_user || []).map((user, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]"
                    >
                      <div>
                        <p className="font-medium text-white">
                          {user.user_name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {user.days} 天
                        </p>
                      </div>
                      <p className="text-lg font-semibold text-white">
                        {user.total_hours?.toFixed(1) || 0} 小时
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center py-12 text-slate-500">
          {project.linked_project_id ? (
            <>
              <Clock className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>暂无工时数据</p>
              <p className="text-xs mt-2">
                工时数据从关联的非标项目中统计
              </p>
            </>
          ) : (
            <>
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>未关联非标项目</p>
              <p className="text-xs mt-2">
                关联非标项目后可统计工时数据
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
