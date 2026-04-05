import { useState, useEffect, useCallback } from "react";
import {
    CheckCircle2,
    XCircle,
    AlertTriangle,
    RefreshCw,
    Bell,
    BookOpen,
    Loader2,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import { Card, CardContent, Button } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { pmoApi } from "../../../services/api";

const CHECK_ICONS = {
    stage_completion: "📋",
    deliverable_upload: "📦",
    customer_acceptance: "✍️",
    cost_settlement: "💰",
    document_completeness: "📄",
};

const CHECK_LABELS = {
    stage_completion: "阶段完成",
    deliverable_upload: "交付物上传",
    customer_acceptance: "客户验收",
    cost_settlement: "成本归集",
    document_completeness: "文档齐全",
};

function ScoreRing({ score }) {
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;
    const color =
        score === 100
            ? "text-emerald-400"
            : score >= 80
              ? "text-amber-400"
              : "text-red-400";

    return (
        <div className="relative inline-flex items-center justify-center">
            <svg width="100" height="100" className="-rotate-90">
                <circle
                    cx="50"
                    cy="50"
                    r={radius}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="6"
                    className="text-white/5"
                />
                <circle
                    cx="50"
                    cy="50"
                    r={radius}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    className={color}
                    style={{ transition: "stroke-dashoffset 0.6s ease" }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={cn("text-2xl font-bold", color)}>{score}</span>
                <span className="text-[10px] text-slate-500">/ 100</span>
            </div>
        </div>
    );
}

function CheckItem({ check, expanded, onToggle }) {
    return (
        <div className="border border-white/5 rounded-lg overflow-hidden">
            <button
                onClick={onToggle}
                className="w-full flex items-center gap-3 p-3 hover:bg-white/[0.02] transition-colors text-left"
            >
                <span className="text-lg">{CHECK_ICONS[check.key] || "📋"}</span>
                {check.passed ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                ) : (
                    <XCircle className="h-4 w-4 text-red-400 shrink-0" />
                )}
                <span className="flex-1 text-sm font-medium text-white">
                    {check.label}
                </span>
                <span className="text-xs text-slate-500">{check.detail}</span>
                {expanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-500" />
                ) : (
                    <ChevronDown className="h-4 w-4 text-slate-500" />
                )}
            </button>
            {expanded && (check.missing?.length > 0 || check.recommendations?.length > 0) && (
                <div className="px-3 pb-3 space-y-2 border-t border-white/5 pt-2">
                    {check.missing?.length > 0 && (
                        <div className="space-y-1">
                            {check.missing.map((item, i) => (
                                <div key={i} className="flex items-start gap-2 text-xs">
                                    <AlertTriangle className="h-3 w-3 text-amber-400 mt-0.5 shrink-0" />
                                    <span className="text-slate-400">{item}</span>
                                </div>
                            ))}
                        </div>
                    )}
                    {check.recommendations?.length > 0 && (
                        <div className="space-y-1">
                            {check.recommendations.map((rec, i) => (
                                <div key={i} className="text-xs text-blue-400/80">
                                    → {rec}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export function ClosureReadinessPanel({ projectId }) {
    const [readiness, setReadiness] = useState(null);
    const [loading, setLoading] = useState(false);
    const [notifying, setNotifying] = useState(false);
    const [collecting, setCollecting] = useState(false);
    const [expandedChecks, setExpandedChecks] = useState({});
    const [actionMessage, setActionMessage] = useState(null);

    const fetchReadiness = useCallback(async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const res = await pmoApi.closures.checkReadiness(projectId);
            setReadiness(res.data || res);
        } catch (err) {
            console.error("Failed to check readiness:", err);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        fetchReadiness();
    }, [fetchReadiness]);

    const handleNotify = async () => {
        setNotifying(true);
        setActionMessage(null);
        try {
            const res = await pmoApi.closures.notifyReadiness(projectId);
            const data = res.data || res;
            setActionMessage({
                type: data.notified ? "success" : "info",
                text: data.message,
            });
        } catch (err) {
            setActionMessage({
                type: "error",
                text: "通知发送失败: " + (err.response?.data?.detail || err.message),
            });
        } finally {
            setNotifying(false);
        }
    };

    const handleCollectLessons = async () => {
        setCollecting(true);
        setActionMessage(null);
        try {
            const res = await pmoApi.closures.autoCollectLessons(projectId);
            const data = res.data || res;
            setActionMessage({
                type: "success",
                text: data.message,
            });
        } catch (err) {
            setActionMessage({
                type: "error",
                text: "收集失败: " + (err.response?.data?.detail || err.message),
            });
        } finally {
            setCollecting(false);
        }
    };

    const toggleCheck = (key) => {
        setExpandedChecks((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    if (loading && !readiness) {
        return (
            <Card>
                <CardContent className="p-6 flex items-center justify-center gap-2">
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    <span className="text-slate-400">检查结项准备度...</span>
                </CardContent>
            </Card>
        );
    }

    if (!readiness) return null;

    const passedCount = readiness.checks?.filter((c) => c.passed).length || 0;
    const totalCount = readiness.checks?.length || 0;

    return (
        <Card>
            <CardContent className="p-6 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between">
                    <div>
                        <h3 className="text-base font-semibold text-white">
                            结项准备度
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                            自动检查结项所需条件，{readiness.checked_at
                                ? `最后检查: ${new Date(readiness.checked_at).toLocaleString("zh-CN")}`
                                : ""}
                        </p>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={fetchReadiness}
                        disabled={loading}
                    >
                        <RefreshCw
                            className={cn(
                                "h-4 w-4",
                                loading && "animate-spin"
                            )}
                        />
                    </Button>
                </div>

                {/* Score + Summary */}
                <div className="flex items-center gap-6">
                    <ScoreRing score={readiness.score} />
                    <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                            {readiness.ready ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-medium">
                                    <CheckCircle2 className="h-3 w-3" />
                                    可以结项
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium">
                                    <AlertTriangle className="h-3 w-3" />
                                    条件未满足
                                </span>
                            )}
                        </div>
                        <p className="text-sm text-slate-400">
                            已通过 {passedCount}/{totalCount} 项检查
                            {readiness.missing_items?.length > 0 &&
                                `，还有 ${readiness.missing_items.length} 项待完成`}
                        </p>
                    </div>
                </div>

                {/* Check Items */}
                <div className="space-y-2">
                    {readiness.checks?.map((check) => (
                        <CheckItem
                            key={check.key}
                            check={check}
                            expanded={!!expandedChecks[check.key]}
                            onToggle={() => toggleCheck(check.key)}
                        />
                    ))}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNotify}
                        disabled={notifying}
                        className="gap-1.5"
                    >
                        {notifying ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <Bell className="h-3.5 w-3.5" />
                        )}
                        发送结项提醒
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCollectLessons}
                        disabled={collecting}
                        className="gap-1.5"
                    >
                        {collecting ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <BookOpen className="h-3.5 w-3.5" />
                        )}
                        自动收集经验
                    </Button>
                </div>

                {/* Action Message */}
                {actionMessage && (
                    <div
                        className={cn(
                            "text-xs px-3 py-2 rounded-md",
                            actionMessage.type === "success" && "bg-emerald-500/10 text-emerald-400",
                            actionMessage.type === "error" && "bg-red-500/10 text-red-400",
                            actionMessage.type === "info" && "bg-blue-500/10 text-blue-400"
                        )}
                    >
                        {actionMessage.text}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
