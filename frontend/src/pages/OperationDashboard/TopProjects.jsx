

import { cn } from "../../lib/utils";

const HEALTH_CONFIG = {
  H1: { label: "正常", className: "bg-emerald-500/20 text-emerald-400" },
  H2: { label: "风险", className: "bg-amber-500/20 text-amber-400" },
  H3: { label: "阻塞", className: "bg-red-500/20 text-red-400" },
};

export function TopProjects({ projects }) {
  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5" />
          重点项目
        </CardTitle>
        <CardDescription>当前在制的高价值项目</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          {projects?.length === 0 ? (
            <div className="text-sm text-slate-400 py-6 text-center">暂无重点项目</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-3 text-slate-400 font-medium">项目编号</th>
                  <th className="text-left p-3 text-slate-400 font-medium">项目名称</th>
                  <th className="text-left p-3 text-slate-400 font-medium">客户</th>
                  <th className="text-right p-3 text-slate-400 font-medium">合同金额</th>
                  <th className="text-center p-3 text-slate-400 font-medium">进度</th>
                  <th className="text-center p-3 text-slate-400 font-medium">状态</th>
                </tr>
              </thead>
              <tbody>
                {(projects || []).map((project) => {
                  const healthCfg = HEALTH_CONFIG[project.health] || HEALTH_CONFIG.H1;
                  return (
                    <tr
                      key={project.id}
                      className="border-b border-border/50 hover:bg-surface-2/30"
                    >
                      <td className="p-3">
                        <span className="font-mono text-accent">{project.id}</span>
                      </td>
                      <td className="p-3 text-white">{project.name}</td>
                      <td className="p-3 text-slate-400">{project.customer}</td>
                      <td className="p-3 text-right text-white font-medium">
                        ¥{project.value}万
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Progress value={project.progress} className="h-1.5 w-20" />
                          <span className="text-xs text-slate-400">{project.progress}%</span>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <Badge className={cn(healthCfg.className)}>
                          {healthCfg.label}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
