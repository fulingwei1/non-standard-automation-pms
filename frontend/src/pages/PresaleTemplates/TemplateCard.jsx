import { Calendar, Eye, Star, Wand2 } from "lucide-react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui";
import { cn, formatDate } from "../../lib/utils";
import { CATEGORY_STYLE_MAP } from "./constants";
import { RatingStars } from "./RatingStars";

export function TemplateCard({
  template,
  applyingTemplateId,
  ratingTemplateId,
  myRatings,
  onPreview,
  onApply,
  onRate,
}) {
  return (
    <Card className="bg-surface-1/50">
      <CardHeader className="space-y-3 pb-0">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <Badge
              className={cn(
                "border",
                CATEGORY_STYLE_MAP[template.category] ||
                  "bg-slate-500/10 text-slate-300 border-slate-500/30",
              )}
            >
              {template.category}
            </Badge>
            <CardTitle className="text-base text-white">
              {template.name}
            </CardTitle>
          </div>
          <Badge variant="outline" className="shrink-0">
            {template.owner}
          </Badge>
        </div>
        <CardDescription className="min-h-[40px] text-slate-400">
          {template.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {(template.tags || []).length > 0 ? (
            (template.tags || []).map((tag) => (
              <span
                key={tag}
                className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300"
              >
                {tag}
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-500">暂无标签</span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-2 text-sm text-slate-300 md:grid-cols-3">
          <div className="flex items-center gap-2">
            <Star className="h-4 w-4 text-amber-400" />
            <span>
              {template.rating.toFixed(1)} ({template.ratingCount}人)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-emerald-400" />
            <span>{template.applyCount} 次应用</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-blue-400" />
            <span>{formatDate(template.updatedAt)}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <RatingStars value={template.rating} />
          <span className="text-xs text-slate-400">团队评分</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onPreview(template)}
          >
            <Eye className="h-4 w-4" />
            模板预览
          </Button>
          <Button
            size="sm"
            variant="success"
            loading={applyingTemplateId === template.id}
            onClick={() => onApply(template)}
          >
            <Wand2 className="h-4 w-4" />
            应用模板
          </Button>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="mb-2 text-xs text-slate-400">请为模板评分</p>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((score) => (
              <button
                key={`${template.id}-score-${score}`}
                type="button"
                disabled={ratingTemplateId === template.id}
                className="rounded p-1 transition hover:bg-white/10 disabled:opacity-50"
                onClick={() => onRate(template, score)}
              >
                <Star
                  className={cn(
                    "h-4 w-4",
                    score <= (myRatings[template.id] || 0)
                      ? "fill-amber-400 text-amber-400"
                      : "text-slate-600 hover:text-amber-300",
                  )}
                />
              </button>
            ))}
            <span className="ml-2 text-xs text-slate-400">
              {myRatings[template.id]
                ? `你已评分 ${myRatings[template.id]} 星`
                : "点击星级提交评分"}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
