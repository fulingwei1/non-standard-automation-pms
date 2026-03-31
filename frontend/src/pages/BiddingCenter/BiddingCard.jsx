/**
 * 投标卡片组件
 */
import { motion } from "framer-motion";
import {
  Calendar,
  Building2,
  FileText,
  Eye,
  Edit,
  MoreHorizontal,
  Timer,
  DollarSign,
  Award,
  ThumbsDown,
  Swords,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { getStageStyle, getStageName } from "./constants";

export function BiddingCard({ bidding, onClick }) {
  const isUrgent = bidding.daysLeft > 0 && bidding.daysLeft <= 7;
  const isOverdue =
    bidding.daysLeft === 0 && !["won", "lost"].includes(bidding.stage);

  return (
    <motion.div
      variants={fadeIn}
      className={cn(
        "p-4 rounded-xl bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group",
        isUrgent && "border-amber-500/30",
        isOverdue && "border-red-500/30"
      )}
      onClick={() => onClick(bidding)}>

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", getStageStyle(bidding.stage))}>
              {getStageName(bidding.stage)}
            </Badge>
            {isUrgent &&
            <Badge className="text-xs bg-amber-500">
                <Timer className="w-3 h-3 mr-1" />
                紧急
            </Badge>
            }
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {bidding.name}
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">{bidding.code}</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}>

              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem>
              <FileText className="w-4 h-4 mr-2" />
              查看方案
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {bidding.customer}
        </span>
        <span className="flex items-center gap-1">
          <DollarSign className="w-3 h-3" />¥{bidding.amount}万
        </span>
      </div>

      {bidding.stage !== "won" && bidding.stage !== "lost" &&
      <div className="space-y-1 mb-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">准备进度</span>
            <span className="text-white">{bidding.progress}%</span>
          </div>
          <Progress value={bidding.progress} className="h-1.5" />
      </div>
      }

      {bidding.competitors?.length > 0 &&
      <div className="flex items-center gap-2 mb-3">
          <Swords className="w-3 h-3 text-red-400" />
          <span className="text-xs text-slate-500">
            {bidding.competitors?.length} 个竞争对手
          </span>
      </div>
      }

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <span className="text-slate-500 flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          {bidding.deadline}
        </span>
        {bidding.daysLeft > 0 && !["won", "lost"].includes(bidding.stage) &&
        <span
          className={cn(
            "flex items-center gap-1",
            isUrgent ? "text-amber-400" : "text-slate-400"
          )}>

            <Timer className="w-3 h-3" />
            剩余 {bidding.daysLeft} 天
        </span>
        }
        {bidding.stage === "won" &&
        <span className="flex items-center gap-1 text-emerald-400">
            <Award className="w-3 h-3" />
            已中标
        </span>
        }
        {bidding.stage === "lost" &&
        <span className="flex items-center gap-1 text-red-400">
            <ThumbsDown className="w-3 h-3" />
            未中标
        </span>
        }
      </div>
    </motion.div>);

}
