import { FileText, Cpu, Package, Paperclip, DollarSign, History, CheckCircle, Clock, AlertTriangle } from "lucide-react";

export const TABS = [
    { id: "overview", name: "概览", icon: FileText },
    { id: "specs", name: "技术规格", icon: Cpu },
    { id: "equipment", name: "设备配置", icon: Package },
    { id: "deliverables", name: "交付物", icon: Paperclip },
    { id: "cost", name: "成本估算", icon: DollarSign },
    { id: "history", name: "版本历史", icon: History },
];

export const getStatusStyle = (status) => {
    switch (status) {
        case "draft":
            return { bg: "bg-slate-500", text: "草稿" };
        case "in_progress":
            return { bg: "bg-blue-500", text: "编写中" };
        case "reviewing":
            return { bg: "bg-amber-500", text: "评审中" };
        case "published":
            return { bg: "bg-emerald-500", text: "已发布" };
        case "archived":
            return { bg: "bg-slate-600", text: "已归档" };
        default:
            return { bg: "bg-slate-500", text: status };
    }
};

export const getDeliverableStatus = (status) => {
    switch (status) {
        case "completed":
            return { icon: CheckCircle, color: "text-emerald-500", text: "已完成" };
        case "in_progress":
            return { icon: Clock, color: "text-blue-500", text: "进行中" };
        case "pending":
            return { icon: AlertTriangle, color: "text-slate-500", text: "待开始" };
        default:
            return { icon: AlertTriangle, color: "text-slate-500", text: status };
    }
};
