/**
 * KPI 卡片组件
 */
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  RefreshCw,
  Activity,
  Calendar,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
} from "lucide-react";
import {
  Button,
  Badge,
  Progress,
  Skeleton,
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { kpiApi } from "../../services/api/strategy";
import { HEALTH_STATUS, COLLECTION_FREQUENCY } from "./constants";

export default function KPICard({ kpi, onUpdate, onCollect, color }) {
  const [expanded, setExpanded] = useState(false);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const status = kpi.status || "ON_TRACK";
  const statusConfig = HEALTH_STATUS[status] || HEALTH_STATUS.ON_TRACK;
  const progress = kpi.target_value
    ? Math.min(100, ((kpi.current_value || 0) / kpi.target_value) * 100)
    : 0;

  const loadHistory = async () => {
    if (!kpi.id || loadingHistory) return;

    try {
      setLoadingHistory(true);
      const res = await kpiApi.getHistory(kpi.id, 6);
      setHistory(res.data || []);
    } catch (error) {
      console.error("加载历史数据失败:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleExpand = () => {
    if (!expanded) {
      loadHistory();
    }
    setExpanded(!expanded);
  };

  const FreqIcon =
    COLLECTION_FREQUENCY[kpi.collection_frequency]?.icon || Calendar;

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-xl border border-white/10 bg-slate-800/50 overflow-hidden"
    >
      {/* 卡片头部 */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ backgroundColor: `${color}20`, color }}
              >
                {kpi.code || `KPI-${kpi.id}`}
              </span>
              <Badge
                variant="outline"
                className={`${statusConfig.bgColor} ${statusConfig.borderColor} ${statusConfig.color} border`}
              >
                <statusConfig.icon className="w-3 h-3 mr-1" />
                {statusConfig.label}
              </Badge>
            </div>
            <h4 className="text-sm font-semibold text-white mb-1">
              {kpi.name}
            </h4>
            {kpi.description && (
              <p className="text-xs text-slate-400 line-clamp-1">
                {kpi.description}
              </p>
            )}
          </div>
          <button
            onClick={handleExpand}
            className="text-slate-400 hover:text-white transition-colors"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* 进度条 */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400">进度</span>
            <span className="text-white font-medium">
              {kpi.current_value || 0} / {kpi.target_value} {kpi.unit || "%"}
            </span>
          </div>
          <Progress
            value={progress || "unknown"}
            className="h-2"
            indicatorClassName={
              status === "ON_TRACK"
                ? "bg-gradient-to-r from-emerald-500 to-green-500"
                : status === "AT_RISK"
                  ? "bg-gradient-to-r from-amber-500 to-orange-500"
                  : "bg-gradient-to-r from-red-500 to-rose-500"
            }
          />
        </div>

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <FreqIcon className="w-3.5 h-3.5" />
              <span>
                {COLLECTION_FREQUENCY[kpi.collection_frequency]?.label || "每月"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onUpdate(kpi)}
            >
              更新值
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onCollect(kpi)}
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              采集
            </Button>
          </div>
        </div>
      </div>

      {/* 展开的历史数据 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5 bg-slate-900/30"
          >
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-slate-500" />
                <span className="text-xs font-medium text-slate-400">
                  历史数据 (最近 6 期)
                </span>
              </div>

              {loadingHistory ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : history.length > 0 ? (
                <div className="space-y-2">
                  {history.map((item, index) => (
                    <div
                      key={item.id || index}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50"
                    >
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-xs text-slate-400">
                          {item.collection_date || item.date || `第${index + 1}期`}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-white">
                          {item.value || item.current_value} {kpi.unit || "%"}
                        </span>
                        {item.value >= (kpi.target_value * 0.9) && (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-4">
                  暂无历史数据
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
