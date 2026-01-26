import { motion } from "framer-motion";
import { Clock, Timer, Briefcase, Coffee } from "lucide-react";
import { Card, CardContent } from "../../../components/ui/card";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export function WeekSummaryCards({ weeklyTotal, entries }) {
    const stats = [
        {
            label: "本周工时",
            value: `${weeklyTotal}h`,
            icon: Clock,
            color: "text-blue-400",
            desc: `目标 40h`,
        },
        {
            label: "加班工时",
            value: `${Math.max(0, weeklyTotal - 40)}h`,
            icon: Timer,
            color: weeklyTotal > 40 ? "text-amber-400" : "text-slate-400",
            desc: "超出标准工时",
        },
        {
            label: "参与项目",
            value: new Set(entries.map((e) => e.project_id).filter(Boolean)).size,
            icon: Briefcase,
            color: "text-emerald-400",
            desc: "个项目",
        },
        {
            label: "休息时间",
            value: `${Math.max(0, 168 - weeklyTotal - 56)}h`,
            icon: Coffee,
            color: "text-purple-400",
            desc: "本周剩余",
        },
    ];

    return (
        <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
                <Card key={index} className="bg-surface-1/50">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-400">{stat.label}</p>
                                <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                                <p className="text-xs text-slate-500 mt-0.5">{stat.desc}</p>
                            </div>
                            <stat.icon className={cn("w-8 h-8", stat.color)} />
                        </div>
                    </CardContent>
                </Card>
            ))}
        </motion.div>
    );
}
