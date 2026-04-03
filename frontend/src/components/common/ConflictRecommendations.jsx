/**
 * 冲突调解建议面板
 *
 * 展示三类建议：替代人选、时间调整、负荷均衡
 * 用于嵌入冲突卡片或详情弹窗
 */

import { useState, useEffect } from "react";
import {
  UserPlus,
  Calendar,
  Scale,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Loader2,
  Lightbulb,
} from "lucide-react";
import { resourceConflictApi } from "../../services/api/resourcePlan";

// ============================================================================
// Score badge
function ScoreBadge({ score }) {
  const color =
    score >= 70
      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
      : score >= 40
      ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
      : "bg-slate-500/20 text-slate-400 border-slate-500/30";

  return (
    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${color}`}>
      {score}分
    </span>
  );
}

// ============================================================================
// Section wrapper
function Section({ icon: Icon, title, count, color, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-white/5 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/[0.02] transition-colors"
      >
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
        )}
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-sm font-medium text-slate-200">{title}</span>
        {count > 0 && (
          <span className="text-[10px] text-slate-500 ml-auto">{count} 条建议</span>
        )}
      </button>
      {open && <div className="px-3 pb-3 space-y-2">{children}</div>}
    </div>
  );
}

// ============================================================================
// Alternative Candidates
function AlternativeCandidates({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-xs text-slate-500 py-2">暂无合适的替代人选</div>;
  }

  return data.map((group, gi) => (
    <div key={gi} className="space-y-1.5">
      <div className="text-[11px] text-slate-400">
        {group.project_name} - {group.role_name || group.role_code}
      </div>
      {group.candidates.length === 0 ? (
        <div className="text-[11px] text-slate-500 ml-2">未找到合适候选人</div>
      ) : (
        group.candidates.map((c, ci) => (
          <div
            key={ci}
            className="flex items-center gap-2 ml-2 p-2 rounded-md bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-200">
                  {c.employee_name}
                </span>
                <ScoreBadge score={c.total_score} />
                {c.can_fit ? (
                  <CheckCircle className="w-3 h-3 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-3 h-3 text-amber-400" />
                )}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {c.is_same_role ? "同角色经验" : "同部门"} | 可用{" "}
                <span className="font-mono">{c.available_pct}%</span> | 需要{" "}
                <span className="font-mono">{c.needed_pct}%</span>
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5">{c.reason}</div>
            </div>
          </div>
        ))
      )}
    </div>
  ));
}

// ============================================================================
// Schedule Adjustments
function ScheduleAdjustments({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-xs text-slate-500 py-2">暂无时间调整建议</div>;
  }

  const typeLabels = {
    DELAY: { label: "延后", color: "text-amber-400", bg: "bg-amber-500/10" },
    ADVANCE: { label: "提前", color: "text-blue-400", bg: "bg-blue-500/10" },
    SPLIT: { label: "双向调整", color: "text-purple-400", bg: "bg-purple-500/10" },
    REDUCE_ALLOCATION: { label: "降低比例", color: "text-cyan-400", bg: "bg-cyan-500/10" },
  };

  return data.map((s, i) => {
    const style = typeLabels[s.type] || typeLabels.DELAY;
    return (
      <div key={i} className={`p-2 rounded-md ${style.bg} space-y-1`}>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${style.color} border border-current/20`}>
            {style.label}
          </span>
          <span className="text-xs text-slate-200">{s.description}</span>
        </div>
        {s.original_period && (
          <div className="text-[10px] text-slate-500 ml-2">
            原计划: {s.original_period} → 建议: {s.suggested_period}
          </div>
        )}
        {s.impact && (
          <div className="text-[10px] text-amber-400/80 ml-2">{s.impact}</div>
        )}
        <div className="text-[10px] text-slate-400 ml-2">{s.reason}</div>
      </div>
    );
  });
}

// ============================================================================
// Workload Balancing
function WorkloadBalancing({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-xs text-slate-500 py-2">暂无负荷均衡建议</div>;
  }

  return data.map((s, i) => (
    <div key={i} className="p-2 rounded-md bg-white/[0.02] space-y-1">
      <div className="flex items-center gap-2">
        <span
          className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${
            s.type === "TRANSFER"
              ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
              : "text-orange-400 border-orange-500/30 bg-orange-500/10"
          }`}
        >
          {s.type === "TRANSFER" ? "转交" : "拆分"}
        </span>
        <span className="text-xs text-slate-200">{s.description}</span>
      </div>
      {s.relief_effect && (
        <div className="text-[10px] text-emerald-400/80 ml-2">{s.relief_effect}</div>
      )}
      <div className="text-[10px] text-slate-400 ml-2">{s.reason}</div>
    </div>
  ));
}

// ============================================================================
// Main Component
export default function ConflictRecommendations({ conflictId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!conflictId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    resourceConflictApi
      .getRecommendations(conflictId)
      .then((res) => {
        if (!cancelled) {
          setData(res.data?.data || res.data || res);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "加载建议失败");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [conflictId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 justify-center text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-xs">正在生成调解建议...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-xs text-red-400 py-2 text-center">{error}</div>
    );
  }

  if (!data) return null;

  const altCount = (data.alternative_candidates || []).reduce(
    (sum, g) => sum + (g.candidates?.length || 0),
    0
  );
  const schedCount = (data.schedule_adjustments || []).length;
  const balCount = (data.workload_balancing || []).length;
  const totalCount = altCount + schedCount + balCount;

  return (
    <div className="space-y-2 mt-3">
      <div className="flex items-center gap-1.5 mb-1">
        <Lightbulb className="w-3.5 h-3.5 text-yellow-400" />
        <span className="text-xs font-medium text-yellow-400">
          建议方案 ({totalCount})
        </span>
      </div>

      <Section
        icon={UserPlus}
        title="替代人选"
        count={altCount}
        color="text-blue-400"
        defaultOpen={altCount > 0}
      >
        <AlternativeCandidates data={data.alternative_candidates} />
      </Section>

      <Section
        icon={Calendar}
        title="时间调整"
        count={schedCount}
        color="text-amber-400"
        defaultOpen={schedCount > 0 && altCount === 0}
      >
        <ScheduleAdjustments data={data.schedule_adjustments} />
      </Section>

      <Section
        icon={Scale}
        title="负荷均衡"
        count={balCount}
        color="text-emerald-400"
        defaultOpen={balCount > 0 && altCount === 0 && schedCount === 0}
      >
        <WorkloadBalancing data={data.workload_balancing} />
      </Section>
    </div>
  );
}
