import { motion } from "framer-motion";
import { ArrowLeft, Share2, Download, Edit, MoreHorizontal, Copy, Send, Archive, Trash2 } from "lucide-react";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "../../../components/ui/dropdown-menu";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { getStatusStyle } from "../constants";

function appendContextParam(params, key, value) {
    if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value));
    }
}

function buildSolutionListUrl(solution) {
    const params = new URLSearchParams();
    params.set("tab", "solutions");

    if (solution.ticketId || solution.leadId || solution.opportunityId || solution.projectId) {
        params.set("type", "support");
    }
    appendContextParam(params, "ticket_id", solution.ticketId);
    appendContextParam(params, "lead_id", solution.leadId);
    appendContextParam(params, "opportunity_id", solution.opportunityId);
    appendContextParam(params, "project_id", solution.projectId);

    return `/presales/technical-solutions?${params.toString()}`;
}

export function SolutionHeader({ solution, navigate, onSubmitReview, submittingReview = false }) {
    const statusStyle = getStatusStyle(solution.status);
    const canSubmitReview = ["draft", "rejected"].includes(solution.status);

    return (
        <motion.div variants={fadeIn} className="flex items-center gap-4">
            <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(buildSolutionListUrl(solution))}
                className="text-slate-400 hover:text-white"
            >
                <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                    <Badge className={cn("text-xs", statusStyle.bg)}>
                        {statusStyle.text}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                        {solution.version}
                    </Badge>
                    <span className="text-sm text-slate-500">{solution.code}</span>
                </div>
                <h1 className="text-2xl font-bold text-white">{solution.name}</h1>
            </div>
            <div className="flex items-center gap-2">
                <Button variant="outline" className="flex items-center gap-2">
                    <Share2 className="w-4 h-4" />
                    分享
                </Button>
                <Button variant="outline" className="flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    导出
                </Button>
                <Button className="flex items-center gap-2">
                    <Edit className="w-4 h-4" />
                    编辑
                </Button>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon" aria-label="更多操作">
                            <MoreHorizontal className="w-4 h-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                            <Copy className="w-4 h-4 mr-2" />
                            复制方案
                        </DropdownMenuItem>
                        <DropdownMenuItem
                            disabled={!canSubmitReview || submittingReview}
                            onSelect={() => onSubmitReview?.("提交评审")}
                        >
                            <Send className="w-4 h-4 mr-2" />
                            {submittingReview ? "提交中..." : "提交评审"}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>
                            <Archive className="w-4 h-4 mr-2" />
                            归档
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-400">
                            <Trash2 className="w-4 h-4 mr-2" />
                            删除
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </motion.div>
    );
}
