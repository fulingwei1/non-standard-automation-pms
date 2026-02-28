import { useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
} from "../../components/ui";
import {
  Globe,
  Users,
  Phone,
  Building2,
  Megaphone,
  Handshake,
  MapPin,
  MoreHorizontal,
  Flame,
  Calendar,
  Clock,
  ChevronRight,
  Star,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { sourceOptions } from "@/lib/constants/leadManagement";

// 来源图���映射
const sourceIcons = {
  exhibition: Building2,
  referral: Handshake,
  website: Globe,
  cold_call: Phone,
  social_media: Megaphone,
  advertising: Megaphone,
  partner: Users,
  other: MoreHorizontal,
};

// 来源颜色映射
const sourceColors = {
  exhibition: "text-purple-400",
  referral: "text-emerald-400",
  website: "text-blue-400",
  cold_call: "text-amber-400",
  social_media: "text-cyan-400",
  advertising: "text-pink-400",
  partner: "text-orange-400",
  other: "text-slate-400",
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.ceil((date - now) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "今天";
  if (diffDays === 1) return "明天";
  if (diffDays < 0) return `已过期 ${Math.abs(diffDays)} 天`;
  if (diffDays <= 7) return `${diffDays} 天后`;

  return date.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
};

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-blue-400";
  if (score >= 40) return "text-amber-400";
  return "text-red-400";
};

// 获取评分背景
const getScoreBg = (score) => {
  if (score >= 80) return "bg-emerald-500/20";
  if (score >= 60) return "bg-blue-500/20";
  if (score >= 40) return "bg-amber-500/20";
  return "bg-red-500/20";
};

export default function LeadInsights({ leads = [], onViewLead, onViewAll }) {
  // 来源分布统计
  const sourceDistribution = useMemo(() => {
    const dist = {};
    sourceOptions.forEach((s) => {
      dist[s.value] = { count: 0, label: s.label };
    });

    leads.forEach((lead) => {
      if (lead.source && dist[lead.source]) {
        dist[lead.source].count++;
      }
    });

    return Object.entries(dist)
      .map(([key, val]) => ({
        key,
        ...val,
        percentage: leads.length > 0 ? ((val.count / leads.length) * 100).toFixed(0) : 0,
      }))
      .sort((a, b) => b.count - a.count);
  }, [leads]);

  // 热门线索 (评分 >= 80)
  const hotLeads = useMemo(() => {
    return leads
      .filter((lead) => (lead.priority_score || 0) >= 80 && lead.status !== "CONVERTED")
      .sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0))
      .slice(0, 5);
  }, [leads]);

  // 即将跟进 (7天内)
  const upcomingFollowUps = useMemo(() => {
    const now = new Date();
    const weekLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    return leads
      .filter((lead) => {
        if (!lead.next_action_at || lead.status === "CONVERTED") return false;
        const nextDate = new Date(lead.next_action_at);
        return nextDate <= weekLater;
      })
      .sort((a, b) => new Date(a.next_action_at) - new Date(b.next_action_at))
      .slice(0, 5);
  }, [leads]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* 来源分布 */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <MapPin className="h-4 w-4 text-blue-400" />
            来源分布
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-2">
            {sourceDistribution.slice(0, 6).map((source) => {
              const Icon = sourceIcons[source.key] || MoreHorizontal;
              const colorClass = sourceColors[source.key] || "text-slate-400";

              return (
                <div key={source.key} className="flex items-center gap-2">
                  <Icon className={cn("h-4 w-4 shrink-0", colorClass)} />
                  <span className="text-sm text-slate-300 w-16 truncate">
                    {source.label}
                  </span>
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        colorClass.replace("text-", "bg-")
                      )}
                      style={{ width: `${source.percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-8 text-right">
                    {source.count}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 热门线索 */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Flame className="h-4 w-4 text-red-400" />
              热门线索
            </CardTitle>
            {hotLeads.length > 0 && (
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={onViewAll}>
                查看全部 <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {hotLeads.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">暂无热门线索</p>
          ) : (
            <div className="space-y-2">
              {hotLeads.map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition-colors"
                  onClick={() => onViewLead?.(lead)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      {lead.is_key_lead && (
                        <Star className="h-3 w-3 text-yellow-500 fill-yellow-500 shrink-0" />
                      )}
                      <span className="text-sm text-white truncate">
                        {lead.customer_name}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 truncate">
                      {lead.contact_name || "-"} · {lead.industry || "未知行业"}
                    </p>
                  </div>
                  <Badge
                    className={cn(
                      "shrink-0",
                      getScoreBg(lead.priority_score),
                      getScoreColor(lead.priority_score)
                    )}
                  >
                    {lead.priority_score}分
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 即将跟进 */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="h-4 w-4 text-amber-400" />
              即将跟进
            </CardTitle>
            {upcomingFollowUps.length > 0 && (
              <Button variant="ghost" size="sm" className="h-6 px-2 text-xs" onClick={onViewAll}>
                查看全部 <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {upcomingFollowUps.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">暂无即将跟进</p>
          ) : (
            <div className="space-y-2">
              {upcomingFollowUps.map((lead) => {
                const dateText = formatDate(lead.next_action_at);
                const isOverdue = dateText.includes("已过期");
                const isToday = dateText === "今天";

                return (
                  <div
                    key={lead.id}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition-colors"
                    onClick={() => onViewLead?.(lead)}
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full shrink-0",
                        isOverdue ? "bg-red-500" : isToday ? "bg-amber-500" : "bg-blue-500"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-white truncate block">
                        {lead.customer_name}
                      </span>
                      <p className="text-xs text-slate-500 truncate">
                        {lead.next_action || "待跟进"}
                      </p>
                    </div>
                    <div
                      className={cn(
                        "text-xs shrink-0 flex items-center gap-1",
                        isOverdue ? "text-red-400" : isToday ? "text-amber-400" : "text-slate-400"
                      )}
                    >
                      <Clock className="h-3 w-3" />
                      {dateText}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
