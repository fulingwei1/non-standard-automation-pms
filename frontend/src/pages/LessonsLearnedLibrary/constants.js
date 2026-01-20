import { CheckCircle2, AlertCircle } from "lucide-react";

export const LESSON_TYPE_BADGES = {
    SUCCESS: {
        label: "成功经验",
        variant: "success",
        icon: CheckCircle2,
        color: "text-emerald-400"
    },
    FAILURE: {
        label: "失败教训",
        variant: "destructive",
        icon: AlertCircle,
        color: "text-red-400"
    }
};

export const STATUS_BADGES = {
    OPEN: { label: "待处理", variant: "secondary", color: "text-slate-400" },
    IN_PROGRESS: { label: "处理中", variant: "info", color: "text-blue-400" },
    RESOLVED: { label: "已解决", variant: "success", color: "text-emerald-400" },
    CLOSED: { label: "已关闭", variant: "secondary", color: "text-slate-500" }
};

export const PRIORITY_BADGES = {
    LOW: { label: "低", variant: "secondary", color: "text-slate-400" },
    MEDIUM: { label: "中", variant: "info", color: "text-blue-400" },
    HIGH: { label: "高", variant: "destructive", color: "text-red-400" }
};

export const getLessonTypeBadge = (type) => LESSON_TYPE_BADGES[type] || LESSON_TYPE_BADGES.SUCCESS;
export const getStatusBadge = (status) => STATUS_BADGES[status] || STATUS_BADGES.OPEN;
export const getPriorityBadge = (priority) => PRIORITY_BADGES[priority] || PRIORITY_BADGES.MEDIUM;
