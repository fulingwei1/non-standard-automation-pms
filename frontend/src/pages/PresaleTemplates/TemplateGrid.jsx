import { Loader2 } from "lucide-react";

import { Card, CardContent } from "../../components/ui";
import { TemplateCard } from "./TemplateCard";

export function TemplateGrid({
  loading,
  filteredTemplates,
  applyingTemplateId,
  ratingTemplateId,
  myRatings,
  onPreview,
  onApply,
  onRate,
}) {
  if (loading) {
    return (
      <Card className="xl:col-span-2 bg-surface-1/50">
        <CardContent className="flex min-h-[220px] items-center justify-center">
          <div className="flex items-center gap-2 text-slate-300">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>正在加载模板库...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (filteredTemplates.length === 0) {
    return (
      <Card className="xl:col-span-2 bg-surface-1/50">
        <CardContent className="flex min-h-[220px] items-center justify-center text-slate-400">
          未找到符合条件的模板，请调整分类或关键词。
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      {filteredTemplates.map((template) => (
        <TemplateCard
          key={template.id}
          template={template}
          applyingTemplateId={applyingTemplateId}
          ratingTemplateId={ratingTemplateId}
          myRatings={myRatings}
          onPreview={onPreview}
          onApply={onApply}
          onRate={onRate}
        />
      ))}
    </>
  );
}
