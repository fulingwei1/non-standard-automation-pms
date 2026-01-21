import { motion } from "framer-motion";
import {
    TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { Card, CardContent, Progress } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";

export function StatCard({ title, value, subtitle, trend, icon: Icon, color, bg }) {
    return (
        <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <div className={cn("p-2 rounded-lg", bg)}>
                            <Icon className={cn("w-4 h-4", color)} />
                        </div>
                        {trend !== undefined && (
                            <div className={cn("flex items-center text-xs", trend >= 0 ? "text-emerald-400" : "text-red-400")}>
                                {trend >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                                {Math.abs(trend)}%
                            </div>
                        )}
                    </div>
                    <div className="text-2xl font-bold text-white">{value}</div>
                    <p className="text-xs text-slate-400 mt-1">{title}</p>
                    {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
                </CardContent>
            </Card>
        </motion.div>
    );
}
