/**
 * 跨项目资源全景视图
 * - 人员资源时间线（甘特图式）
 * - 冲突高亮（>100%标红）
 * - 部门筛选 + 冲突过滤
 * - 点击人员查看详情
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  AlertTriangle,
  Filter,
  ChevronDown,
  ChevronRight,
  Calendar,
  Activity,
  TrendingUp,
  Flame,
  Shield,
  X,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { resourceOverviewApi } from "../services/api/resourceOverview";
// ============================================================================
// Color palette for projects

// ============================================================================
// Module-level constant for today marker
const TODAYMS = Date.now();


const PROJECT_COLORS = [
  { bg: "bg-blue-500/30", border: "border-blue-500", text: "text-blue-400", hex: "#3b82f6" },
  { bg: "bg-emerald-500/30", border: "border-emerald-500", text: "text-emerald-400", hex: "#10b981" },
  { bg: "bg-purple-500/30", border: "border-purple-500", text: "text-purple-400", hex: "#8b5cf6" },
  { bg: "bg-amber-500/30", border: "border-amber-500", text: "text-amber-400", hex: "#f59e0b" },
  { bg: "bg-rose-500/30", border: "border-rose-500", text: "text-rose-400", hex: "#f43f5e" },
  { bg: "bg-cyan-500/30", border: "border-cyan-500", text: "text-cyan-400", hex: "#06b6d4" },
  { bg: "bg-orange-500/30", border: "border-orange-500", text: "text-orange-400", hex: "#f97316" },
  { bg: "bg-pink-500/30", border: "border-pink-500", text: "text-pink-400", hex: "#ec4899" },
];

function getProjectColor(index) {
  return PROJECT_COLORS[index % PROJECT_COLORS.length];
}
// ============================================================================
// Stats Card

// ============================================================================
function StatCard({ icon: Icon, label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}
// ============================================================================
// Timeline Bar (single project allocation for one person)

// ============================================================================
function TimelineBar({ allocation, timeRange, color, onClick }) {
  const { start_date, end_date, project_name, allocation_pct } = allocation;
  if (!start_date || !end_date) return null;

  const startMs = new Date(start_date).getTime();
  const endMs = new Date(end_date).getTime();
  const rangeMs = timeRange.endMs - timeRange.startMs;

  if (rangeMs <= 0) return null;

  const leftPct = Math.max(0, ((startMs - timeRange.startMs) / rangeMs) * 100);
  const widthPct = Math.min(100 - leftPct, ((endMs - startMs) / rangeMs) * 100);

  if (widthPct <= 0) return null;

  return (
    <div
      className={`absolute top-0.5 h-7 rounded-md ${color.bg} border ${color.border} cursor-pointer
        hover:brightness-125 transition-all flex items-center overflow-hidden px-1`}
      style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
      title={`${project_name} (${allocation_pct}%)\n${start_date} ~ ${end_date}`}
      onClick={() => onClick?.(allocation)}
    >
      {widthPct > 8 && (
        <span className={`text-[10px] font-medium ${color.text} truncate`}>
          {project_name.length > 6 ? project_name.slice(0, 6) + "…" : project_name}
          <span className="ml-1 opacity-70">{allocation_pct}%</span>
        </span>
      )}
    </div>
  );
}
// ============================================================================
// Conflict Marker

// ============================================================================
function ConflictMarker({ conflict, timeRange }) {
  const startMs = new Date(conflict.start_date).getTime();
  const endMs = new Date(conflict.end_date).getTime();
  const rangeMs = timeRange.endMs - timeRange.startMs;

  if (rangeMs <= 0) return null;

  const leftPct = Math.max(0, ((startMs - timeRange.startMs) / rangeMs) * 100);
  const widthPct = Math.min(100 - leftPct, ((endMs - startMs) / rangeMs) * 100);

  if (widthPct <= 0) return null;

  return (
    <div
      className="absolute -top-1 h-10 rounded border-2 border-red-500/60 bg-red-500/10 pointer-events-none"
      style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
    >
      <div className="absolute -top-3 left-0 text-[9px] text-red-400 font-bold whitespace-nowrap">
        ⚠ {Math.round(conflict.total_allocation)}%
      </div>
    </div>
  );
}
// ============================================================================
// Employee Row

// ============================================================================
function EmployeeRow({ employee, timeRange, projectColorMap, onSelect, isExpanded, onToggle }) {
  const isOverloaded = employee.current_allocation > 100;

  return (
    <div className="border-b border-white/5 last:border-b-0">
      {/* Main row */}
      <div className="flex items-center hover:bg-white/[0.02] transition-colors">
        {/* Left: employee info */}
        <div
          className="w-48 flex-shrink-0 p-3 flex items-center gap-2 cursor-pointer"
          onClick={onToggle}
        >
          {isExpanded ? (
            <ChevronDown className="w-3 h-3 text-slate-500" />
          ) : (
            <ChevronRight className="w-3 h-3 text-slate-500" />
          )}
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-medium text-slate-200">{employee.real_name}</span>
              {employee.has_conflict && (
                <AlertTriangle className="w-3 h-3 text-red-400" />
              )}
            </div>
            <div className="text-[10px] text-slate-500">{employee.department || "未分配"}</div>
          </div>
        </div>

        {/* Center: allocation bar */}
        <div className="w-24 flex-shrink-0 px-2">
          <div className="flex items-center gap-1.5">
            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  isOverloaded
                    ? "bg-red-500"
                    : employee.current_allocation > 80
                    ? "bg-amber-500"
                    : employee.current_allocation > 0
                    ? "bg-emerald-500"
                    : "bg-slate-700"
                }`}
                style={{ width: `${Math.min(100, employee.current_allocation)}%` }}
              />
            </div>
            <span
              className={`text-xs font-mono ${
                isOverloaded ? "text-red-400 font-bold" : "text-slate-400"
              }`}
            >
              {Math.round(employee.current_allocation)}%
            </span>
          </div>
        </div>

        {/* Right: timeline */}
        <div className="flex-1 h-8 relative mx-2">
          {/* Conflict markers (below bars) */}
          {(employee.conflicts || []).map((c, i) => (
            <ConflictMarker key={`c-${i}`} conflict={c} timeRange={timeRange} />
          ))}
          {/* Project bars */}
          {(employee.allocations || []).map((a, i) => (
            <TimelineBar
              key={i}
              allocation={a}
              timeRange={timeRange}
              color={projectColorMap[a.project_id] || getProjectColor(0)}
              onClick={() => onSelect(employee, a)}
            />
          ))}
        </div>
      </div>

      {/* Expanded detail */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pl-14 pr-4 pb-3 space-y-1">
              {(employee.allocations || []).map((a, i) => {
                const color = projectColorMap[a.project_id] || getProjectColor(0);
                return (
                  <div key={i} className="flex items-center gap-3 text-xs">
                    <div className={`w-2 h-2 rounded-full ${color.bg} ${color.border} border`} />
                    <span className={`${color.text} font-medium w-36 truncate`}>{a.project_name}</span>
                    <span className="text-slate-400 w-16">{a.role || "-"}</span>
                    <span className="text-slate-500">{a.start_date} ~ {a.end_date}</span>
                    <span className={`font-mono ${a.allocation_pct > 80 ? "text-amber-400" : "text-slate-400"}`}>
                      {a.allocation_pct}%
                    </span>
                  </div>
                );
              })}
              {employee.conflicts.length > 0 && (
                <div className="mt-2 pt-2 border-t border-red-500/20">
                  <div className="text-[10px] text-red-400 font-medium mb-1">⚠ 资源冲突</div>
                  {employee.conflicts.map((c, i) => (
                    <div key={i} className="text-[10px] text-red-300/80 ml-2">
                      {c.start_date} ~ {c.end_date}: 总分配 {Math.round(c.total_allocation)}%
                      ({(c.projects || []).join(" + ")})
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
// ============================================================================
// Month markers for timeline header

// ============================================================================
function TimelineHeader({ timeRange }) {
  const months = [];
  const d = new Date(timeRange.startMs);
  d.setDate(1);
  while (d.getTime() < timeRange.endMs) {
    const ms = d.getTime();
    const leftPct = ((ms - timeRange.startMs) / (timeRange.endMs - timeRange.startMs)) * 100;
    if (leftPct >= 0 && leftPct < 100) {
      months.push({
        label: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
        leftPct,
      });
    }
    d.setMonth(d.getMonth() + 1);
  }

  // Today marker
  const todayPct = ((TODAYMS - timeRange.startMs) / (timeRange.endMs - timeRange.startMs)) * 100;

  return (
    <div className="flex items-center border-b border-white/10">
      <div className="w-48 flex-shrink-0 p-2 text-xs text-slate-400 font-medium">人员</div>
      <div className="w-24 flex-shrink-0 px-2 text-xs text-slate-400">负荷</div>
      <div className="flex-1 h-6 relative mx-2">
        {months.map((m, i) => (
          <div
            key={i}
            className="absolute top-0 h-full border-l border-white/10 text-[10px] text-slate-500 pl-1"
            style={{ left: `${m.leftPct}%` }}
          >
            {m.label}
          </div>
        ))}
        {todayPct > 0 && todayPct < 100 && (
          <div
            className="absolute top-0 h-full w-px bg-emerald-500/60"
            style={{ left: `${todayPct}%` }}
          >
            <div className="absolute -top-0 -translate-x-1/2 text-[8px] text-emerald-400 bg-surface-1 px-1 rounded">
              今天
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
// ============================================================================
// Main Page

// ============================================================================
export default function ResourceOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [department, setDepartment] = useState("");
  const [onlyConflicts, setOnlyConflicts] = useState(false);
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [selectedDetail, setSelectedDetail] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params = { only_assigned: true };
      if (department) params.department = department;
      if (onlyConflicts) params.only_conflicts = true;
      const res = await resourceOverviewApi.list(params);
      setData(res.data || res);
    } catch (err) {
      console.error("Failed to load resource overview:", err);
    } finally {
      setLoading(false);
    }
  }, [department, onlyConflicts]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Build project color map
  const projectColorMap = useMemo(() => {
    if (!data?.employees) return {};
    const ids = new Set();
    data.employees.forEach((e) =>
      (e.allocations || []).forEach((a) => ids.add(a.project_id))
    );
    const map = {};
    [...ids].sort().forEach((id, i) => {
      map[id] = getProjectColor(i);
    });
    return map;
  }, [data]);

  // Project legend
  const projectLegend = useMemo(() => {
    if (!data?.employees) return [];
    const map = {};
    data.employees.forEach((e) =>
      (e.allocations || []).forEach((a) => {
        if (!map[a.project_id]) {
          map[a.project_id] = a.project_name;
        }
      })
    );
    return Object.entries(map)
      .sort(([a], [b]) => Number(a) - Number(b))
      .map(([id, name]) => ({
        id: Number(id),
        name,
        color: projectColorMap[Number(id)] || getProjectColor(0),
      }));
  }, [data, projectColorMap]);

  // Time range: 3 months before today to 6 months after
  const timeRange = useMemo(() => {
    const now = new Date();
    const start = new Date(now.getFullYear(), now.getMonth() - 3, 1);
    const end = new Date(now.getFullYear(), now.getMonth() + 7, 0);
    return { startMs: start.getTime(), endMs: end.getTime() };
  }, []);

  // Departments from data
  const departments = useMemo(() => {
    if (!data?.employees) return [];
    const set = new Set();
    data.employees.forEach((e) => e.department && set.add(e.department));
    return [...set].sort();
  }, [data]);

  const toggleExpand = (userId) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(userId)) next.delete(userId);
      else next.add(userId);
      return next;
    });
  };

  const employees = data?.employees || [];

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="资源全景视图"
        subtitle="跨项目人员分配 · 冲突检测 · 负荷分析"
      />

      {/* Stats */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="参与项目人员"
          value={data?.total_employees || 0}
          color="text-blue-400"
        />
        <StatCard
          icon={AlertTriangle}
          label="存在冲突"
          value={data?.employees_with_conflicts || 0}
          sub={`${data?.total_conflicts || 0} 个冲突时段`}
          color={data?.employees_with_conflicts > 0 ? "text-red-400" : "text-emerald-400"}
        />
        <StatCard
          icon={Activity}
          label="平均负荷"
          value={`${data?.avg_utilization || 0}%`}
          color={
            (data?.avg_utilization || 0) > 90
              ? "text-red-400"
              : (data?.avg_utilization || 0) > 70
              ? "text-amber-400"
              : "text-emerald-400"
          }
        />
        <StatCard
          icon={Flame}
          label="过载人员"
          value={employees.filter((e) => e.current_allocation > 100).length}
          sub="当前分配 > 100%"
          color="text-orange-400"
        />
      </motion.div>

      {/* Filters + Legend */}
      <motion.div variants={fadeIn} className="flex flex-wrap items-center gap-3">
        {/* Department filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            className="bg-surface-1 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={department || "unknown"}
            onChange={(e) => setDepartment(e.target.value)}
          >
            <option value="">全部部门</option>
            {departments.map((d) => (
              <option key={d} value={d || "unknown"}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* Conflict toggle */}
        <button
          onClick={() => setOnlyConflicts(!onlyConflicts)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
            onlyConflicts
              ? "bg-red-500/20 border-red-500/50 text-red-400"
              : "bg-surface-1 border-white/10 text-slate-400 hover:text-slate-300"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          仅看冲突
        </button>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Project legend */}
        <div className="flex flex-wrap items-center gap-2">
          {projectLegend.map((p) => (
            <div key={p.id} className="flex items-center gap-1">
              <div className={`w-2.5 h-2.5 rounded ${p.color.bg} border ${p.color.border}`} />
              <span className={`text-[10px] ${p.color.text}`}>{p.name}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Timeline */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-1/50 border border-white/5 rounded-xl overflow-hidden"
      >
        {loading ? (
          <div className="p-12 text-center text-slate-500">加载中...</div>
        ) : employees.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            {onlyConflicts ? "没有发现资源冲突 🎉" : "暂无资源分配数据"}
          </div>
        ) : (
          <>
            <TimelineHeader timeRange={timeRange} />
            <div className="max-h-[calc(100vh-380px)] overflow-y-auto">
              {employees.map((emp) => (
                <EmployeeRow
                  key={emp.user_id}
                  employee={emp}
                  timeRange={timeRange}
                  projectColorMap={projectColorMap}
                  onSelect={(e, a) => setSelectedDetail({ employee: e, allocation: a })}
                  isExpanded={expandedIds.has(emp.user_id)}
                  onToggle={() => toggleExpand(emp.user_id)}
                />
              ))}
            </div>
          </>
        )}
      </motion.div>

      {/* Detail panel */}
      <AnimatePresence>
        {selectedDetail && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-4 right-4 w-80 bg-surface-1 border border-white/10 rounded-xl shadow-2xl p-4 z-50"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white">
                {selectedDetail.employee.real_name} · {selectedDetail.allocation.project_name}
              </h3>
              <button onClick={() => setSelectedDetail(null)}>
                <X className="w-4 h-4 text-slate-400 hover:text-white" />
              </button>
            </div>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">角色</span>
                <span>{selectedDetail.allocation.role || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">分配比例</span>
                <span className="font-mono">{selectedDetail.allocation.allocation_pct}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">时间段</span>
                <span>{selectedDetail.allocation.start_date} ~ {selectedDetail.allocation.end_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">阶段</span>
                <span>{selectedDetail.allocation.stage || "-"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">当前总负荷</span>
                <span className={`font-mono font-bold ${
                  selectedDetail.employee.current_allocation > 100 ? "text-red-400" : "text-emerald-400"
                }`}>
                  {Math.round(selectedDetail.employee.current_allocation)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">参与项目数</span>
                <span>{selectedDetail.employee.total_projects}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
