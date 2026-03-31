import {
  ClipboardCheck,
  Package,
  Car,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent } from "../../components/ui";

/**
 * Four-card summary grid shown at the top of the page.
 *
 * Props:
 *   stats — { total, urgent, officeSupplies, vehicle }
 */
export function ApprovalStatsGrid({ stats }) {
  const cards = [
    {
      label: "待审批",
      value: stats.total,
      color: "text-amber-400",
      Icon: ClipboardCheck,
    },
    {
      label: "紧急事项",
      value: stats.urgent,
      color: "text-red-400",
      Icon: AlertTriangle,
    },
    {
      label: "办公用品",
      value: stats.officeSupplies,
      color: "text-blue-400",
      Icon: Package,
    },
    {
      label: "车辆申请",
      value: stats.vehicle,
      color: "text-cyan-400",
      Icon: Car,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map(({ label, value, color, Icon }) => (
        <Card key={label}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{label}</p>
                <p className={`text-2xl font-bold ${color} mt-1`}>{value}</p>
              </div>
              <Icon className={`h-8 w-8 ${color}`} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
