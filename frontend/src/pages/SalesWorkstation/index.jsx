import { motion } from "framer-motion";
import {
    Users,
    Target,
    Clock,
    ChevronRight,
    AlertTriangle,
    Phone,
    FileText,
    DollarSign,
    Building2,
    CheckCircle2,
    Send,
    Receipt,
    Calendar
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Button,
    Badge
} from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { cn } from "../../lib/utils";
import {
    SalesFunnel,
    CustomerCard,
    PaymentTimeline,
    PaymentStats,
    AdvantageProducts
} from "../../components/sales";
import { ApiIntegrationError } from "../../components/ui";
import { useSalesWorkstation } from "./hooks";
import { StatsCards } from "./components";
import { todoTypeConfig, healthColors } from "./constants";

// Icon mapping for todo types
const iconMap = {
    Phone, FileText, DollarSign, Building2, CheckCircle2, AlertTriangle, Clock
};

export default function SalesWorkstation() {
    const {
        todos,
        stats,
        customers,
        projects,
        payments,
        funnelData,
        error,
        achievementRate,
        toggleTodo,
        refresh
    } = useSalesWorkstation();

    // Show error state
    if (error && !funnelData) {
        return (
            <div className="space-y-6">
                <PageHeader title="销售工作台" description="销售业绩、商机管理、客户跟进" />
                <ApiIntegrationError error={error} apiEndpoint="/api/v1/sales/statistics/summary" onRetry={refresh} />
            </div>
        );
    }

    return (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
            {/* Page Header */}
            <PageHeader
                title="销售工作台"
                description={`业绩目标: ¥${(stats.monthlyTarget / 10000).toFixed(0)}万 | 已完成: ¥${(stats.monthlyAchieved / 10000).toFixed(0)}万 (${achievementRate}%)`}
                actions={
                    <motion.div variants={fadeIn} className="flex gap-2">
                        <Button variant="outline" className="flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            新建客户
                        </Button>
                        <Button className="flex items-center gap-2">
                            <Target className="w-4 h-4" />
                            新建商机
                        </Button>
                    </motion.div>
                }
            />

            {/* Stats Cards */}
            <StatsCards stats={stats} achievementRate={achievementRate} />

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Funnel & Todos */}
                <motion.div variants={fadeIn} className="space-y-6">
                    {/* Sales Funnel */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">销售漏斗</CardTitle>
                                <Button variant="ghost" size="sm" className="text-xs text-primary">
                                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <SalesFunnel data={funnelData || undefined} onStageClick={() => { }} />
                        </CardContent>
                    </Card>

                    {/* Today's Todos */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">今日待办</CardTitle>
                                <Badge variant="secondary">{todos.filter((t) => !t.done).length}</Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {todos.length === 0 ? (
                                <div className="text-center py-8 text-slate-500 text-sm">暂无待办事项</div>
                            ) : (
                                todos.map((todo) => {
                                    const config = todoTypeConfig[todo.type] || { icon: "Clock", color: "text-slate-400", bg: "bg-slate-500/20" };
                                    const Icon = iconMap[config.icon] || Clock;
                                    return (
                                        <motion.div
                                            key={todo.id}
                                            variants={fadeIn}
                                            onClick={() => toggleTodo(todo.id)}
                                            className={cn(
                                                "flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all hover:bg-surface-100",
                                                todo.done && "opacity-50"
                                            )}
                                        >
                                            <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", config.bg)}>
                                                <Icon className={cn("w-4 h-4", config.color)} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn("font-medium text-sm", todo.done ? "line-through text-slate-500" : "text-white")}>
                                                        {todo.title}
                                                    </span>
                                                    {todo.priority === "high" && !todo.done && <AlertTriangle className="w-3 h-3 text-red-400" />}
                                                </div>
                                                <span className="text-xs text-slate-400">{todo.target}</span>
                                            </div>
                                            <span className="text-xs text-slate-500">{todo.time}</span>
                                        </motion.div>
                                    );
                                })
                            )}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Middle Column - Projects & Payments */}
                <motion.div variants={fadeIn} className="space-y-6">
                    {/* My Projects */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">我的项目进度</CardTitle>
                                <Button variant="ghost" size="sm" className="text-xs text-primary">
                                    全部项目 <ChevronRight className="w-3 h-3 ml-1" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {projects.map((project) => (
                                <motion.div
                                    key={project.id}
                                    variants={fadeIn}
                                    className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <div>
                                            <h4 className="font-medium text-white text-sm">{project.name}</h4>
                                            <span className="text-xs text-slate-400">{project.customer}</span>
                                        </div>
                                        <Badge variant="secondary" className="text-xs">{project.stageLabel}</Badge>
                                    </div>
                                    <div className="flex items-center gap-1 mb-2">
                                        {["方案", "设计", "采购", "装配", "验收"].map((step, index) => {
                                            const stepProgress = index * 20 + 20;
                                            const isActive = project.progress >= stepProgress;
                                            const isCurrent = project.progress >= stepProgress - 20 && project.progress < stepProgress;
                                            return (
                                                <div key={step} className="flex items-center">
                                                    <div className={cn("w-2 h-2 rounded-full", isActive ? "bg-primary" : isCurrent ? "bg-amber-500" : "bg-slate-600")} />
                                                    {index < 4 && <div className={cn("w-6 h-0.5", isActive ? "bg-primary" : "bg-slate-600")} />}
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-2">
                                            <div className={cn("w-2 h-2 rounded-full", healthColors[project.health])} />
                                            <span className="text-slate-400">进度 {project.progress}%</span>
                                        </div>
                                        <span className="text-slate-400">验收: {project.acceptanceDate}</span>
                                    </div>
                                </motion.div>
                            ))}
                        </CardContent>
                    </Card>

                    {/* Payment Schedule */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">近期回款计划</CardTitle>
                                <Button variant="ghost" size="sm" className="text-xs text-primary">
                                    全部回款 <ChevronRight className="w-3 h-3 ml-1" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <PaymentTimeline payments={payments} compact />
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Right Column - Customers */}
                <motion.div variants={fadeIn} className="space-y-6">
                    {/* Quick Customer List */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">重点客户</CardTitle>
                                <Button variant="ghost" size="sm" className="text-xs text-primary">
                                    客户管理 <ChevronRight className="w-3 h-3 ml-1" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {customers.map((customer) => (
                                <CustomerCard key={customer.id} customer={customer} compact onClick={() => { }} />
                            ))}
                        </CardContent>
                    </Card>

                    {/* Payment Stats */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">回款概览</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <PaymentStats payments={payments} />
                        </CardContent>
                    </Card>

                    {/* Advantage Products */}
                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base">优势产品</CardTitle>
                                <Badge variant="secondary" className="text-xs">推荐</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <AdvantageProducts compact showSearch maxHeight="320px" onProductSelect={(product) => console.log("Selected product:", product)} />
                        </CardContent>
                    </Card>

                    {/* Quick Actions */}
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">快捷操作</CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-2 gap-2">
                            <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                                <FileText className="w-4 h-4 text-amber-400" />
                                <span className="text-xs">新建报价</span>
                            </Button>
                            <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                                <Send className="w-4 h-4 text-blue-400" />
                                <span className="text-xs">发送方案</span>
                            </Button>
                            <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                                <Receipt className="w-4 h-4 text-emerald-400" />
                                <span className="text-xs">申请开票</span>
                            </Button>
                            <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                                <Calendar className="w-4 h-4 text-purple-400" />
                                <span className="text-xs">安排拜访</span>
                            </Button>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </motion.div>
    );
}
