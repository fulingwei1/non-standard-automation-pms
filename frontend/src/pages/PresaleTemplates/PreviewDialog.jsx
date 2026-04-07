


import { cn } from "../../lib/utils";
import { CATEGORY_STYLE_MAP } from "./constants";

export function PreviewDialog({
  previewTemplate,
  previewLoading,
  applyingTemplateId,
  onClose,
  onApply,
}) {
  return (
    <Dialog
      open={Boolean(previewTemplate)}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{previewTemplate?.name || "模板预览"}</DialogTitle>
          <DialogDescription>
            查看模板结构与交付内容，确认后可直接应用到当前售前任务。
          </DialogDescription>
        </DialogHeader>

        <DialogBody className="space-y-6">
          {previewLoading ? (
            <div className="flex min-h-[220px] items-center justify-center text-slate-300">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              正在加载模板详情...
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  className={cn(
                    "border",
                    CATEGORY_STYLE_MAP[previewTemplate?.category] ||
                      "bg-slate-500/10 text-slate-300 border-slate-500/30",
                  )}
                >
                  {previewTemplate?.category || "通用模板"}
                </Badge>
                <Badge variant="outline">
                  <FileText className="mr-1 h-3 w-3" />
                  应用 {previewTemplate?.applyCount || 0} 次
                </Badge>
                <Badge variant="outline">
                  <Star className="mr-1 h-3 w-3 text-amber-400" />
                  {previewTemplate?.rating?.toFixed(1) || "0.0"}
                </Badge>
              </div>

              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-sm text-slate-200">
                  {previewTemplate?.description}
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium text-white">适用场景</h4>
                <div className="flex flex-wrap gap-2">
                  {(previewTemplate?.scenarios || []).length > 0 ? (
                    (previewTemplate?.scenarios || []).map((scenario) => (
                      <span
                        key={scenario}
                        className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-xs text-blue-200"
                      >
                        {scenario}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">
                      暂无适用场景描述
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium text-white">模板大纲</h4>
                {(previewTemplate?.outline || []).length > 0 ? (
                  <div className="space-y-3">
                    {(previewTemplate?.outline || []).map((section, index) => (
                      <div
                        key={`${section.title}-${index}`}
                        className="rounded-xl border border-white/10 bg-white/5 p-3"
                      >
                        <p className="text-sm font-medium text-white">
                          {index + 1}. {section.title}
                        </p>
                        {(section.bullets || []).length > 0 && (
                          <ul className="mt-2 space-y-1 text-xs text-slate-300">
                            {(section.bullets || []).map((bullet) => (
                              <li key={bullet}>- {bullet}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-slate-500">
                    暂无模板大纲数据
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-medium text-white">交付物清单</h4>
                {(previewTemplate?.deliverables || []).length > 0 ? (
                  <ul className="space-y-1 text-sm text-slate-300">
                    {(previewTemplate?.deliverables || []).map((item) => (
                      <li key={item}>- {item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-slate-500">
                    暂无交付物定义
                  </div>
                )}
              </div>
            </>
          )}
        </DialogBody>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
          <Button
            variant="success"
            loading={applyingTemplateId === previewTemplate?.id}
            onClick={async () => {
              await onApply(previewTemplate);
              onClose();
            }}
          >
            立即应用模板
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
