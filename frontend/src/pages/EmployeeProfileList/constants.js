import { UserCheck, Briefcase, Clock, User, UserX } from "lucide-react";

export const STATUS_TABS = [
    {
        key: "active",
        label: "在职",
        icon: UserCheck,
        color: "text-green-400",
        bgColor: "bg-green-500/10",
    },
    {
        key: "regular",
        label: "正式",
        icon: Briefcase,
        color: "text-blue-400",
        bgColor: "bg-blue-500/10",
    },
    {
        key: "probation",
        label: "试用期",
        icon: Clock,
        color: "text-yellow-400",
        bgColor: "bg-yellow-500/10",
    },
    {
        key: "intern",
        label: "实习期",
        icon: User,
        color: "text-purple-400",
        bgColor: "bg-purple-500/10",
    },
    {
        key: "resigned",
        label: "离职",
        icon: UserX,
        color: "text-slate-400",
        bgColor: "bg-slate-500/10",
    },
];

export const getEmployeeStatusBadge = (status, type) => {
    if (status === "resigned") {
        return {
            label: "离职",
            variant: "secondary",
            className: "bg-slate-500/20 text-slate-400",
        };
    }
    if (type === "probation") {
        return {
            label: "试用期",
            variant: "secondary",
            className: "bg-yellow-500/20 text-yellow-400",
        };
    }
    if (type === "intern") {
        return {
            label: "实习期",
            variant: "secondary",
            className: "bg-purple-500/20 text-purple-400",
        };
    }
    return {
        label: "正式",
        variant: "secondary",
        className: "bg-green-500/20 text-green-400",
    };
};

export const getWorkloadColor = (pct) => {
    if (pct >= 90) return "text-red-400";
    if (pct >= 70) return "text-yellow-400";
    return "text-green-400";
};
