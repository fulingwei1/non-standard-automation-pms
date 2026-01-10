/**
 * HRRecruitmentTab Component
 * 招聘管理 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle, Button } from "../../ui";
import {
  UserPlus,
  UserCheck,
  Target,
  FileText,
  BarChart3,
  ChevronRight,
} from "lucide-react";
import { cn } from "../../../lib/utils";

export default function HRRecruitmentTab({
  mockHRStats,
  mockRecruitmentTrends,
}) {
  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">进行中招聘</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.inProgressRecruitments}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                <UserPlus className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">已完成招聘</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.completedRecruitments}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <UserCheck className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">招聘成功率</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.recruitmentSuccessRate}%
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <Target className="w-6 h-6 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">待审批</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.pendingRecruitments}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <FileText className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recruitment Trends */}
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              招聘趋势分析
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              查看详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockRecruitmentTrends.map((item, index) => {
              const successRate =
                item.positions > 0 ? (item.hired / item.positions) * 100 : 0;
              const maxPositions = Math.max(
                ...mockRecruitmentTrends.map((t) => t.positions),
              );
              const positionPercentage = (item.positions / maxPositions) * 100;

              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-300">
                      {item.month}
                    </span>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">发布</span>
                        <span className="text-sm font-semibold text-white">
                          {item.positions}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">录用</span>
                        <span className="text-sm font-semibold text-emerald-400">
                          {item.hired}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">成功率</span>
                        <span
                          className={cn(
                            "text-sm font-semibold",
                            successRate >= 80
                              ? "text-emerald-400"
                              : successRate >= 60
                                ? "text-amber-400"
                                : "text-red-400",
                          )}
                        >
                          {successRate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full bg-blue-500/50 rounded-full transition-all"
                          style={{ width: `${positionPercentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400 w-12 text-right">
                        发布数
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full bg-emerald-500/50 rounded-full transition-all"
                          style={{ width: `${successRate}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400 w-12 text-right">
                        成功率
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>
                最近6个月平均成功率:{" "}
                {(
                  mockRecruitmentTrends.reduce(
                    (sum, item) =>
                      sum +
                      (item.positions > 0
                        ? (item.hired / item.positions) * 100
                        : 0),
                    0,
                  ) / mockRecruitmentTrends.length
                ).toFixed(1)}
                %
              </span>
              <span>
                总发布:{" "}
                {mockRecruitmentTrends.reduce(
                  (sum, item) => sum + item.positions,
                  0,
                )}{" "}
                | 总录用:{" "}
                {mockRecruitmentTrends.reduce(
                  (sum, item) => sum + item.hired,
                  0,
                )}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
