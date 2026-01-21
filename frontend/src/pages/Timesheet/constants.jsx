import { Edit3, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "../../components/ui";

export const DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

export const STATUS_CONFIGS = {
    DRAFT: { label: "草稿", variant: "secondary", icon: Edit3 },
    PENDING: { label: "待审批", variant: "default", icon: AlertCircle },
    SUBMITTED: { label: "已提交", variant: "default", icon: AlertCircle },
    APPROVED: { label: "已审批", variant: "default", icon: CheckCircle2 },
    REJECTED: { label: "已退回", variant: "destructive", icon: XCircle },
};

export const getStatusBadge = (status) => {
    const statusUpper = status?.toUpperCase() || "DRAFT";
    const config = STATUS_CONFIGS[statusUpper] || STATUS_CONFIGS.DRAFT;
    return (
        <Badge variant={config.variant} className="gap-1">
            <config.icon className="w-3 h-3" />
            {config.label}
        </Badge>
    );
};
