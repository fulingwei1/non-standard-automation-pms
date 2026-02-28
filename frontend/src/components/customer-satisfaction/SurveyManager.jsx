/**
 * Survey Manager Component (Refactored to shadcn/Tailwind)
 * 调查管理组件
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { MoreHorizontal, Eye, FileText, XCircle, Edit } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "../ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { SURVEY_STATUS, SURVEY_TYPES } from "@/lib/constants/customer";

const SurveyManager = ({
  surveys = [],
  loading = false,
  onCreate,
  onEdit,
  onDelete,
}) => {
  const getStatusConfig = (status) => {
    const config = SURVEY_STATUS[status?.toUpperCase()];
    if (!config)
      return {
        label: "未知",
        className: "bg-slate-500/20 text-slate-400 border-slate-500/30",
      };

    const colorMap = {
      "#d9d9d9": "bg-slate-500/20 text-slate-400 border-slate-500/30",
      "#52c41a": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      "#1890ff": "bg-blue-500/20 text-blue-400 border-blue-500/30",
      "#ff4d4f": "bg-red-500/20 text-red-400 border-red-500/30",
    };

    return {
      label: config.label,
      className: colorMap[config.color] || "bg-slate-500/20 text-slate-400",
    };
  };

  const getTypeLabel = (type) => {
    const config = SURVEY_TYPES[type?.toUpperCase()];
    return config?.label || type || "-";
  };

  if (loading && surveys.length === 0) {
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
            <CardTitle className="text-white text-lg">调查管理</CardTitle>
            <Button onClick={() => onCreate?.()} disabled={loading}>
              新建调查
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {surveys.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">暂无调查</h3>
              <p className="text-slate-400 mb-4">
                还没有创建任何满意度调查
              </p>
              <Button onClick={() => onCreate?.()}>创建第一个调查</Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      调查
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      状态
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      平均评分
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">
                      完成率
                    </th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {surveys.map((survey) => {
                    const statusConfig = getStatusConfig(survey.status);
                    const percent = survey.targetCount
                      ? (survey.responseCount / survey.targetCount) * 100
                      : 0;

                    return (
                      <tr
                        key={survey.id}
                        className="border-b border-white/5 hover:bg-slate-800/30 transition-colors"
                      >
                        <td className="p-4">
                          <div>
                            <div className="font-medium text-white mb-1">
                              {survey.title}
                            </div>
                            <div className="text-xs text-slate-500">
                              {getTypeLabel(survey.type)} · {survey.createdDate || "-"}
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant="outline" className={statusConfig.className}>
                            {statusConfig.label}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1">
                            <span className="text-white">
                              {survey.avgScore ?? "-"}
                            </span>
                            <span className="text-slate-500 text-sm">/ 5.0</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="space-y-1">
                            <Progress
                              value={Number(percent.toFixed(1))}
                              className="h-2"
                            />
                            <div className="text-xs text-slate-500">
                              {survey.responseCount}/{survey.targetCount}
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onEdit?.(survey)}
                            >
                              <Edit className="w-4 h-4 mr-1" />
                              编辑
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300"
                              onClick={() => onDelete?.(survey.id)}
                            >
                              <XCircle className="w-4 h-4 mr-1" />
                              删除
                            </Button>
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

export default SurveyManager;
