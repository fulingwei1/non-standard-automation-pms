/**
 * Feedback Manager Component (Refactored to shadcn/Tailwind)
 * 反馈管理组件
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Star, RefreshCw } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "../ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { FEEDBACK_CATEGORIES, SATISFACTION_LEVELS } from "@/lib/constants/customer";

const FeedbackManager = ({
  responses = [],
  loading = false,
  onRefresh,
}) => {
  const getLevelConfig = (level) => {
    const config = SATISFACTION_LEVELS[level];
    if (!config)
      return {
        icon: "😐",
        label: "未知",
        color: "text-slate-400",
      };

    const colorMap = {
      "#52c41a": "text-emerald-400",
      "#1890ff": "text-blue-400",
      "#faad14": "text-amber-400",
      "#ff7a45": "text-orange-400",
      "#ff4d4f": "text-red-400",
    };

    return {
      icon: config.icon,
      label: config.label,
      color: colorMap[config.color] || "text-slate-400",
    };
  };

  const getCategoryLabel = (category) => {
    const config = FEEDBACK_CATEGORIES[category?.toUpperCase()];
    return config?.label || category || "-";
  };

  const StarRating = ({ value }) => {
    const numericValue = Number(value || 0);
    return (
      <div className="flex items-center gap-2">
        <div className="flex gap-0.5">
          {[1, 2, 3, 4, 5].map((star) => (
            <Star
              key={star}
              className={cn(
                "w-4 h-4",
                star <= numericValue
                  ? "fill-amber-400 text-amber-400"
                  : "text-slate-600"
              )}
            />
          ))}
        </div>
        <span className="text-sm text-slate-400">{numericValue.toFixed(1)}</span>
      </div>
    );
  };

  if (loading && responses.length === 0) {
    return (
      <Card className="bg-slate-900/50 border-white/10">
        <CardContent className="p-8 text-center">
          <div className="animate-pulse text-slate-400">加载中...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible">
      <Card className="bg-slate-900/50 border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-lg">反馈管理</CardTitle>
            <Button variant="outline" onClick={() => onRefresh?.()} disabled={loading}>
              <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {responses.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-slate-600 mb-4">
                <Star className="w-12 h-12 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">暂无反馈</h3>
              <p className="text-slate-400">还没有收到任何客户反馈</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      客户
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      日期
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      评分
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      类别
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      反馈内容
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {responses.map((response) => {
                    const levelConfig = getLevelConfig(response.satisfactionLevel);

                    return (
                      <tr
                        key={response.id}
                        className="border-b border-white/5 hover:bg-slate-800/30 transition-colors"
                      >
                        <td className="p-4">
                          <div className="text-white">
                            {response.customerName || "-"}
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="text-slate-400 text-sm">
                            {response.createdDate || "-"}
                          </div>
                        </td>
                        <td className="p-4">
                          <StarRating value={response.satisfactionLevel} />
                        </td>
                        <td className="p-4">
                          <Badge variant="secondary" className="text-xs">
                            {getCategoryLabel(response.category)}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <div className="text-slate-400 text-sm max-w-md truncate">
                            {response.feedback || "-"}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default FeedbackManager;
