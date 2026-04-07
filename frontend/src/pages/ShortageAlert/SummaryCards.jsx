import { AlertTriangle, Package, CheckCircle2, BarChart3 } from "lucide-react";

export default function SummaryCards({ summary }) {
  if (!summary) return null;

  const cards = [
    {
      label: "待处理",
      value: summary.pending_count || 0,
      color: "text-blue-400",
      Icon: AlertTriangle,
    },
    {
      label: "处理中",
      value: summary.processing_count || 0,
      color: "text-purple-400",
      Icon: Package,
    },
    {
      label: "已解决",
      value: summary.resolved_count || 0,
      color: "text-emerald-400",
      Icon: CheckCircle2,
    },
    {
      label: "总缺料项",
      value: summary.total_count || 0,
      color: "text-slate-200",
      iconColor: "text-violet-400",
      Icon: BarChart3,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map(({ label, value, color, iconColor, Icon }) => (
        <Card key={label} className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400 mb-1">{label}</div>
                <div className={`text-2xl font-bold ${color}`}>{value}</div>
              </div>
              <Icon className={`w-8 h-8 ${iconColor || color}`} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
