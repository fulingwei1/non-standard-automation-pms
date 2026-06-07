import { motion } from "framer-motion";
import {
  Building2,
  DollarSign,
  User,
  CheckCircle2,
  Edit,
  Eye,
  Calendar,
  Swords,
  LifeBuoy
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { stageConfig } from "./constants";

export default function OpportunityGrid({
  opportunities,
  stageUpdating,
  onViewDetail,
  onEdit,
  onOpenGate,
  onStageChange,
  onOpenReview
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {(opportunities || []).map((opp) =>
        <motion.div key={opp.id} whileHover={{ y: -4 }}>
          <Card className="h-full hover:border-blue-500 transition-colors">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{opp.opp_code}</CardTitle>
                  <p className="text-sm text-slate-400 mt-1">
                    {opp.opp_name}
                  </p>
                </div>
                <Badge className={cn(stageConfig[opp.stage]?.color)}>
                  {stageConfig[opp.stage]?.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-slate-300">
                  <span className="text-xs text-slate-400">阶段</span>
                  <select
                    value={opp.stage}
                    onChange={(e) => onStageChange(opp, e.target.value)}
                    disabled={!!stageUpdating[opp.id]}
                    className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white">

                    {Object.entries(stageConfig).map(([key, config]) =>
                      <option key={key} value={key || "unknown"}>
                        {config.label}
                      </option>
                    )}
                  </select>
                  {stageUpdating[opp.id] &&
                    <span className="text-xs text-slate-500">更新中...</span>
                  }
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <Building2 className="h-4 w-4 text-slate-400" />
                  {opp.customer_name}
                </div>
                {opp.est_amount &&
                  <div className="flex items-center gap-2 text-slate-300">
                    <DollarSign className="h-4 w-4 text-slate-400" />
                    {parseFloat(opp.est_amount).toLocaleString()} 元
                  </div>
                }
                {opp.owner_name &&
                  <div className="flex items-center gap-2 text-slate-300">
                    <User className="h-4 w-4 text-slate-400" />
                    负责人: {opp.owner_name}
                  </div>
                }
              </div>

              {/* Win Rate Indicator */}
              {opp.probability != null && (
                <div className="mt-3 p-2 bg-surface-50/50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-slate-400">赢单率</span>
                    <span className={cn("text-xs font-medium", opp.probability >= 70 ? "text-emerald-400" : opp.probability >= 40 ? "text-blue-400" : "text-amber-400")}>
                      {opp.probability}%
                    </span>
                  </div>
                  <Progress value={opp.probability} className="h-1.5" />
                </div>
              )}

              {/* Next Action Reminder */}
              {opp.expected_close_date && (
                <div className="mt-2 flex items-center gap-2 p-2 bg-amber-500/5 border border-amber-500/10 rounded-lg">
                  <Calendar className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                  <span className="text-xs text-amber-300">
                    预计成交: {String(opp.expected_close_date).slice(0, 10)}
                  </span>
                </div>
              )}

              {/* Competitor Info */}
              {opp.competitor_info && (
                <div className="mt-2 flex items-center gap-2">
                  <Swords className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                  <span className="text-xs text-slate-400 truncate">竞争: {opp.competitor_info}</span>
                </div>
              )}

              <div className="grid grid-cols-4 gap-2 mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onViewDetail(opp)}
                  className="w-full">

                  <Eye className="mr-2 h-4 w-4" />
                  详情
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEdit(opp)}
                  className="w-full">

                  <Edit className="mr-2 h-4 w-4" />
                  编辑
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onOpenGate(opp)}
                  className="w-full">

                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  阶段门
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onOpenReview(opp)}
                  className="w-full"
                  title="发起售前技术支持或方案评审">

                  <LifeBuoy className="mr-2 h-4 w-4" />
                  发起支持
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
