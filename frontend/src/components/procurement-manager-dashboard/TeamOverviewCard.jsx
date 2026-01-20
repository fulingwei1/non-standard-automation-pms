import { Card, CardHeader, CardTitle, CardContent, Progress } from "../../components/ui";
import { Users } from "lucide-react";

export default function TeamOverviewCard({ stats }) {
  return (
    <Card className="bg-surface-50 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5 text-primary" />
          团队概览
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-slate-400">团队人数</p>
            <p className="text-lg font-bold text-white">
              {stats?.activeTeamMembers}/{stats?.teamSize}
            </p>
          </div>
          <Progress
            value={
              stats?.teamSize > 0
                ? (stats.activeTeamMembers / stats.teamSize) * 100
                : 0
            }
            className="h-2"
          />
        </div>
        <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-slate-400">平均完成率</p>
            <p className="text-lg font-bold text-white">90.7%</p>
          </div>
          <Progress value={90.7} className="h-2" />
        </div>
        <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-slate-400">平均到货率</p>
            <p className="text-lg font-bold text-white">93.7%</p>
          </div>
          <Progress value={93.7} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
