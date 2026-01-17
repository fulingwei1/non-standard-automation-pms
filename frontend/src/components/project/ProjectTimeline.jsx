/**
 * 项目时间线组件
 *
 * Issue 3.3: 显示项目关键事件时间线，支持筛选和搜索
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Badge,
  Button } from
"../ui";
import {
  Search,
  Filter,
  Calendar,
  User,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight } from
"lucide-react";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/utils";

// 事件类型配置
const EVENT_TYPES = {
  STAGE_CHANGE: { label: "阶段变更", icon: ArrowRight, color: "text-blue-400" },
  STATUS_CHANGE: { label: "状态变更", icon: Clock, color: "text-amber-400" },
  HEALTH_CHANGE: {
    label: "健康度变更",
    icon: AlertTriangle,
    color: "text-red-400"
  },
  MILESTONE: { label: "里程碑", icon: CheckCircle2, color: "text-emerald-400" },
  DOCUMENT: { label: "文档", icon: FileText, color: "text-purple-400" },
  OTHER: { label: "其他", icon: Calendar, color: "text-slate-400" }
};

export default function ProjectTimeline({
  projectId: _projectId,
  statusLogs = [],
  milestones = [],
  documents = []
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  // 合并所有事件
  const allEvents = useMemo(() => {
    const events = [];

    // 状态变更日志
    statusLogs.forEach((log) => {
      if (log.change_type === "STAGE_CHANGE" && log.new_stage) {
        events.push({
          id: `log-${log.id}`,
          type: "STAGE_CHANGE",
          title: `阶段变更: ${log.old_stage} → ${log.new_stage}`,
          description: log.change_reason || log.change_note || "",
          date: log.changed_at,
          user: log.changed_by_name,
          data: log
        });
      } else if (log.change_type === "STATUS_CHANGE" && log.new_status) {
        events.push({
          id: `log-${log.id}`,
          type: "STATUS_CHANGE",
          title: `状态变更: ${log.old_status} → ${log.new_status}`,
          description: log.change_reason || log.change_note || "",
          date: log.changed_at,
          user: log.changed_by_name,
          data: log
        });
      } else if (log.change_type === "HEALTH_CHANGE" && log.new_health) {
        events.push({
          id: `log-${log.id}`,
          type: "HEALTH_CHANGE",
          title: `健康度变更: ${log.old_health} → ${log.new_health}`,
          description: log.change_reason || log.change_note || "",
          date: log.changed_at,
          user: log.changed_by_name,
          data: log
        });
      }
    });

    // 里程碑
    milestones.forEach((milestone) => {
      events.push({
        id: `milestone-${milestone.id}`,
        type: "MILESTONE",
        title: milestone.milestone_name,
        description: milestone.description || "",
        date: milestone.planned_date || milestone.actual_date,
        user: null,
        data: milestone
      });
    });

    // 文档（可选，如果有重要文档）
    documents.
    filter((doc) => doc.status === "APPROVED").
    forEach((doc) => {
      events.push({
        id: `doc-${doc.id}`,
        type: "DOCUMENT",
        title: `文档审批通过: ${doc.doc_name || doc.document_name || doc.file_name || "未命名文档"}`,
        description: doc.doc_type || doc.document_type || "",
        date: doc.updated_at,
        user: null,
        data: doc
      });
    });

    // 按日期排序
    return events.sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      return dateB - dateA; // 最新的在前
    });
  }, [statusLogs, milestones, documents]);

  // 筛选和搜索
  const filteredEvents = useMemo(() => {
    let filtered = allEvents;

    // 类型筛选
    if (filterType !== "all") {
      filtered = filtered.filter((event) => event.type === filterType);
    }

    // 搜索
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (event) =>
        event.title.toLowerCase().includes(query) ||
        event.description.toLowerCase().includes(query) ||
        event.user && event.user.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [allEvents, filterType, searchQuery]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">项目时间线</CardTitle>
        <p className="text-sm text-slate-400 mt-1">
          显示项目关键事件和变更历史
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 搜索和筛选 */}
        <div className="flex items-center gap-2">
          <div className="flex-1">
            <Input
              icon={Search}
              placeholder="搜索事件..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)} />

          </div>
          <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
            <Button
              size="sm"
              variant={filterType === "all" ? "default" : "ghost"}
              onClick={() => setFilterType("all")}>

              全部
            </Button>
            {Object.entries(EVENT_TYPES).map(([key, config]) =>
            <Button
              key={key}
              size="sm"
              variant={filterType === key ? "default" : "ghost"}
              onClick={() => setFilterType(key)}>

                {config.label}
              </Button>
            )}
          </div>
        </div>

        {/* 时间线 */}
        {filteredEvents.length > 0 ?
        <div className="relative">
            {/* 时间线轴线 */}
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-white/10" />

            <div className="space-y-4">
              {filteredEvents.map((event, index) => {
              const eventConfig =
              EVENT_TYPES[event.type] || EVENT_TYPES.OTHER;
              const Icon = eventConfig.icon;

              return (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="relative flex gap-4">

                    {/* 时间点 */}
                    <div
                    className={cn(
                      "relative z-10 w-10 h-10 rounded-full flex items-center justify-center",
                      "bg-gradient-to-br from-primary/20 to-indigo-500/10",
                      "border-2 border-primary/30",
                      "shadow-lg shadow-primary/20"
                    )}>

                      <Icon className={cn("h-5 w-5", eventConfig.color)} />
                    </div>

                    {/* 事件内容 */}
                    <div className="flex-1 pb-4">
                      <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-colors">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="font-medium text-white mb-1">
                              {event.title}
                            </div>
                            {event.description &&
                          <div className="text-sm text-slate-400">
                                {event.description}
                              </div>
                          }
                          </div>
                          <Badge variant="secondary">{eventConfig.label}</Badge>
                        </div>

                        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(event.date)}</span>
                          </div>
                          {event.user &&
                        <div className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              <span>{event.user}</span>
                            </div>
                        }
                        </div>
                      </div>
                    </div>
                  </motion.div>);

            })}
            </div>
          </div> :

        <div className="text-center py-12 text-slate-400">
            {searchQuery || filterType !== "all" ?
          <div>
                <p className="mb-2">未找到匹配的事件</p>
                <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSearchQuery("");
                setFilterType("all");
              }}>

                  清除筛选
                </Button>
              </div> :

          <p>暂无事件记录</p>
          }
          </div>
        }
      </CardContent>
    </Card>);

}