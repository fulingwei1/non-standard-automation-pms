import { Circle, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

export const statusConfigs = {
    PENDING: { label: "待开始", color: "bg-slate-500", icon: Circle },
    IN_PROGRESS: { label: "进行中", color: "bg-blue-500", icon: Clock },
    BLOCKED: { label: "阻塞", color: "bg-red-500", icon: AlertTriangle },
    COMPLETED: { label: "已完成", color: "bg-emerald-500", icon: CheckCircle2 }
};

export const stageOptions = [
    { value: "S1", label: "S1-立项" },
    { value: "S2", label: "S2-设计" },
    { value: "S3", label: "S3-采购" },
    { value: "S4", label: "S4-生产" },
    { value: "S5", label: "S5-调试" },
    { value: "S6", label: "S6-验收" }
];
