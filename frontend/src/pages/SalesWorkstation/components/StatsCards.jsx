import { motion } from "framer-motion";
import {
    DollarSign,
    TrendingUp,
    Target,
    Flame,
    AlertTriangle,
    Receipt,
    Building2,
    Plus
} from "lucide-react";
import { Card, CardContent, Progress } from "../../../components/ui";
import { fadeIn } from "../../../lib/animations";

export function StatsCards({ stats, achievementRate }) {
    return (
        <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Monthly Sales */}
            <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-slate-400">本月签约</p>
                            <p className="text-2xl font-bold text-amber-400 mt-1">
                                ¥{(stats.monthlyAchieved / 10000).toFixed(0)}万
                            </p>
                            <div className="flex items-center gap-1 mt-1">
                                <TrendingUp className="w-3 h-3 text-emerald-400" />
                                <span className="text-xs text-emerald-400">+15%</span>
                                <span className="text-xs text-slate-500">vs 上月</span>
                            </div>
                        </div>
                        <div className="p-2 bg-amber-500/20 rounded-lg">
                            <DollarSign className="w-5 h-5 text-amber-400" />
                        </div>
                    </div>
                    <div className="mt-3">
                        <Progress value={parseFloat(achievementRate)} className="h-1.5" />
                        <p className="text-xs text-slate-500 mt-1">目标完成率 {achievementRate}%</p>
                    </div>
                </CardContent>
            </Card>

            {/* Opportunities */}
            <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-slate-400">商机总数</p>
                            <p className="text-2xl font-bold text-white mt-1">{stats.opportunityCount}</p>
                            <div className="flex items-center gap-2 mt-1">
                                <Flame className="w-3 h-3 text-amber-500" />
                                <span className="text-xs text-amber-400">{stats.hotOpportunities}个热门商机</span>
                            </div>
                        </div>
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <Target className="w-5 h-5 text-blue-400" />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Pending Payment */}
            <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-slate-400">待回款</p>
                            <p className="text-2xl font-bold text-white mt-1">
                                ¥{(stats.pendingPayment / 10000).toFixed(0)}万
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                                <AlertTriangle className="w-3 h-3 text-red-400" />
                                <span className="text-xs text-red-400">{(stats.overduePayment / 10000).toFixed(0)}万逾期</span>
                            </div>
                        </div>
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                            <Receipt className="w-5 h-5 text-emerald-400" />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Customers */}
            <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
                <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="text-sm text-slate-400">客户总数</p>
                            <p className="text-2xl font-bold text-white mt-1">{stats.customerCount}</p>
                            <div className="flex items-center gap-2 mt-1">
                                <Plus className="w-3 h-3 text-emerald-400" />
                                <span className="text-xs text-emerald-400">本月新增{stats.newCustomers}</span>
                            </div>
                        </div>
                        <div className="p-2 bg-purple-500/20 rounded-lg">
                            <Building2 className="w-5 h-5 text-purple-400" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
