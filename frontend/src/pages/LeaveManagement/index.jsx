import { motion } from "framer-motion";
import { Download, BarChart3 } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button, Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui";
import { staggerContainer } from "../../lib/animations";
import { useLeaveManagement } from "./hooks";
import {
    LeaveStatsCards,
    LeaveOverview,
    LeaveStatistics,
    LeaveApplicationList,
    LeaveFilters,
    LeaveBalanceTable
} from "./components";

export default function LeaveManagement() {
    const {
        searchText, setSearchText,
        statusFilter, setStatusFilter,
        typeFilter, setTypeFilter,
        filteredApplications,
        stats,
        leaveBalanceRows,
        leaveTypeChart,
        leaveStatusChart,
        monthlyLeaveTrend,
        leaveApplications
    } = useLeaveManagement();

    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <PageHeader
                title="请假管理"
                description="员工请假申请、审批流程、假期余额管理"
                actions={
                    <div className="flex gap-2">
                        <Button variant="outline">
                            <Download className="w-4 h-4 mr-2" />
                            导出
                        </Button>
                        <Button variant="outline">
                            <BarChart3 className="w-4 h-4 mr-2" />
                            统计分析
                        </Button>
                    </div>
                }
            />

            <LeaveStatsCards stats={stats} />

            <Tabs defaultValue="applications" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="applications">请假申请</TabsTrigger>
                    <TabsTrigger value="balance">假期余额</TabsTrigger>
                    <TabsTrigger value="statistics">统计分析</TabsTrigger>
                </TabsList>

                <TabsContent value="applications" className="space-y-4">
                    <LeaveOverview
                        leaveApplications={leaveApplications}
                        stats={stats}
                        monthlyLeaveTrend={monthlyLeaveTrend}
                    />
                    <LeaveFilters
                        searchText={searchText} setSearchText={setSearchText}
                        statusFilter={statusFilter} setStatusFilter={setStatusFilter}
                        typeFilter={typeFilter} setTypeFilter={setTypeFilter}
                    />
                    <LeaveApplicationList applications={filteredApplications} />
                </TabsContent>

                <TabsContent value="balance">
                    <LeaveBalanceTable balanceRows={leaveBalanceRows} />
                </TabsContent>

                <TabsContent value="statistics">
                    <LeaveStatistics
                        leaveTypeChart={leaveTypeChart}
                        leaveStatusChart={leaveStatusChart}
                        monthlyLeaveTrend={monthlyLeaveTrend}
                    />
                </TabsContent>
            </Tabs>
        </motion.div>
    );
}
