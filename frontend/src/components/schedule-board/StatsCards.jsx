import { motion } from "framer-motion";
import { Package, AlertTriangle, Zap, Users } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export default function StatsCards({ totalProjects, atRiskProjects, blockedProjects }) {
  const stats = [
    {
      label: "在制项目",
      value: totalProjects,
      icon: Package,
      color: "text-blue-400"
    },
    {
      label: "风险项目",
      value: atRiskProjects,
      icon: AlertTriangle,
      color: "text-amber-400"
    },
    {
      label: "阻塞项目",
      value: blockedProjects,
      icon: Zap,
      color: "text-red-400"
    },
    {
      label: "资源占用",
      value: "85%",
      icon: Users,
      color: "text-emerald-400"
    }
  ];

  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 md:grid-cols-4 gap-4"
    >
      {stats.map((stat, index) => (
        <Card key={index} className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {stat.value}
                </p>
              </div>
              <stat.icon className={cn("w-8 h-8", stat.color)} />
            </div>
          </CardContent>
        </Card>
      ))}
    </motion.div>
  );
}
