



import { cn } from "../../lib/utils";

export default function PreviewDialog({
  open,
  onOpenChange,
  previewPayload,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>模板应用与 CPQ 预测</DialogTitle>
          <DialogDescription>
            自动计算的完工价格、折扣与调价轨迹。
          </DialogDescription>
        </DialogHeader>
        {previewPayload ? (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>价格预估</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                <div>
                  <div className="text-xs text-muted-foreground">基础价格</div>
                  <div className="text-lg font-semibold">
                    {previewPayload.cpq_preview?.base_price || 0}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">调价合计</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {previewPayload.cpq_preview?.adjustment_total || 0}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">最终报价</div>
                  <div className="text-lg font-semibold text-emerald-600">
                    {previewPayload.cpq_preview?.final_price || 0}
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>调价因子</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {(previewPayload.cpq_preview?.adjustments || []).map((adj) => (
                  <div
                    key={adj.key}
                    className="border rounded-md p-2 flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium">{adj.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {adj.reason}
                      </div>
                    </div>
                    <div
                      className={cn(
                        "font-semibold",
                        adj.value >= 0 ? "text-emerald-600" : "text-red-500"
                      )}
                    >
                      {adj.value}
                    </div>
                  </div>
                ))}
                {(previewPayload.cpq_preview?.adjustments || []).length === 0 && (
                  <div className="text-muted-foreground text-sm">
                    暂无调价轨迹
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="py-10 text-center text-muted-foreground">
            暂无预览数据
          </div>
        )}
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
