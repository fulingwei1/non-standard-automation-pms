import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { FileText } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { staggerContainer, fadeIn } from "../../lib/animations";
import { useSolutionDetail } from "./hooks";
import {
    SolutionHeader,
    SolutionStatsCards,
    SolutionTabs,
    SolutionOverviewTab,
    SolutionSpecsTab,
    SolutionEquipmentTab,
    SolutionCostTab,
    SolutionDeliverablesTab,
    SolutionHistoryTab,
} from "./components";

export default function SolutionDetail() {
    const navigate = useNavigate();
    const {
        activeTab,
        setActiveTab,
        solution,
        loading,
        error,
        costEstimate,
    } = useSolutionDetail();

    if (loading) {
        return (
            <div className="space-y-6">
                <PageHeader title="方案详情" description="加载中..." />
                <div className="text-center py-16 text-slate-400">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
                    <p className="text-lg font-medium">加载中...</p>
                </div>
            </div>
        );
    }

    if (error || !solution) {
        return (
            <div className="space-y-6">
                <PageHeader title="方案详情" description="加载失败" />
                <div className="text-center py-16 text-red-400">
                    <div className="text-lg font-medium">加载失败</div>
                    <div className="text-sm mt-2">{error || "方案不存在"}</div>
                    <Button className="mt-4" onClick={() => navigate("/solutions")}>
                        返回方案列表
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <SolutionHeader solution={solution} navigate={navigate} />

            <SolutionStatsCards solution={solution} />

            <SolutionTabs activeTab={activeTab} setActiveTab={setActiveTab} />

            <motion.div variants={fadeIn}>
                {activeTab === "overview" && <SolutionOverviewTab solution={solution} />}
                {activeTab === "specs" && <SolutionSpecsTab solution={solution} />}
                {activeTab === "equipment" && <SolutionEquipmentTab solution={solution} />}
                {activeTab === "deliverables" && <SolutionDeliverablesTab solution={solution} />}
                {activeTab === "cost" && <SolutionCostTab costEstimate={costEstimate} />}
                {activeTab === "history" && <SolutionHistoryTab solution={solution} />}
            </motion.div>
        </motion.div>
    );
}
