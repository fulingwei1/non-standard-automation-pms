/**
 * Survey Templates Component (Refactored to shadcn/Tailwind)
 * 问卷模板组件
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { FileText, CheckCircle2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
} from "../ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { SURVEY_TYPES } from "@/lib/constants/customer";

const SurveyTemplates = ({ loading = false, onUseTemplate }) => {
  const templates = useMemo(() => {
    return [
      {
        id: "tpl_service",
        title: "标准服务满意度问卷",
        type: "service",
        description: "适用于服务交付后的满意度回访",
        questions: 8,
        usage: 156,
      },
      {
        id: "tpl_product",
        title: "产品满意度问卷",
        type: "product",
        description: "适用于产品交付后的体验反馈",
        questions: 10,
        usage: 203,
      },
      {
        id: "tpl_overall",
        title: "综合满意度问卷",
        type: "overall",
        description: "适用于周期性客户满意度盘点",
        questions: 15,
        usage: 89,
      },
      {
        id: "tpl_support",
        title: "技术支持满意度问卷",
        type: "support",
        description: "适用于技术支持服务后的评价收集",
        questions: 6,
        usage: 124,
      },
    ];
  }, []);

  const getTypeLabel = (type) => {
    const config = SURVEY_TYPES[type?.toUpperCase()];
    return config?.label || type;
  };

  const getTypeColor = (type) => {
    const colorMap = {
      service: "bg-blue-500/20 text-blue-400 border-blue-500/30",
      product: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      overall: "bg-purple-500/20 text-purple-400 border-purple-500/30",
      support: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    };
    return colorMap[type] || "bg-slate-500/20 text-slate-400";
  };

  if (loading) {
    return (
      <Card className="bg-slate-900/50 border-white/10">
        <CardContent className="p-8 text-center">
          <div className="animate-pulse text-slate-400">加载中...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <Card className="bg-slate-900/50 border-white/10">
        <CardHeader>
          <CardTitle className="text-white text-lg">问卷模板</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template, index) => (
              <motion.div
                key={template.id}
                variants={fadeIn}
                custom={index}
              >
                <Card className="bg-slate-800/50 border-white/5 hover:border-primary/30 transition-colors group">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/20 rounded-lg group-hover:scale-110 transition-transform">
                          <FileText className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <h3 className="font-medium text-white mb-1">
                            {template.title}
                          </h3>
                          <Badge
                            variant="outline"
                            className={getTypeColor(template.type)}
                          >
                            {getTypeLabel(template.type)}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <p className="text-sm text-slate-400 mb-4">
                      {template.description}
                    </p>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <span>{template.questions} 个问题</span>
                        <span>{template.usage} 次使用</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => onUseTemplate?.(template)}
                        className="gap-2"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        使用模板
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default SurveyTemplates;
