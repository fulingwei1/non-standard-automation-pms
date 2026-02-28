import { useMemo } from "react";
import { Card, CardContent } from "../ui";
import { TrendingUp, Award, Clock, CheckCircle2 } from "lucide-react";
import { formatCurrency } from "../../lib/utils";

export default function ContributionChart({ contributions = [] }) {
  const stats = useMemo(() => {
    const total = contributions.length;
    const totalScore = contributions.reduce(
      (sum, c) => sum + (c.contribution_score || 0),
      0,
    );
    const totalHours = contributions.reduce(
      (sum, c) => sum + (c.actual_hours || 0),
      0,
    );
    const totalBonus = contributions.reduce(
      (sum, c) => sum + (c.bonus_amount || 0),
      0,
    );
    const totalTasks = contributions.reduce(
      (sum, c) => sum + (c.task_count || 0),
      0,
    );

    return {
      total,
      avgScore: total > 0 ? totalScore / total : 0,
      totalHours,
      totalBonus,
      totalTasks,
    };
  }, [contributions]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">平均贡献度</p>
              <p className="text-2xl font-bold">{stats.avgScore.toFixed(1)}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">总工时</p>
              <p className="text-2xl font-bold">
                {stats.totalHours.toFixed(1)}h
              </p>
            </div>
            <Clock className="h-8 w-8 text-purple-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">总任务数</p>
              <p className="text-2xl font-bold">{stats.totalTasks}</p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">总奖金</p>
              <p className="text-2xl font-bold">
                {formatCurrency(stats.totalBonus)}
              </p>
            </div>
            <Award className="h-8 w-8 text-yellow-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
