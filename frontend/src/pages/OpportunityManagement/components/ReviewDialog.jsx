/**
 * 方案评审申请对话框
 */



export function ReviewDialog({
  open, onOpenChange,
  reviewForm, setReviewForm,
  reviewSubmitting,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>申请方案评审</DialogTitle>
          <DialogDescription>
            提交后将进入售前技术支持部的方案评审列表
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>申请标题 *</Label>
            <Input
              value={reviewForm.title}
              onChange={(e) =>
                setReviewForm({ ...reviewForm, title: e.target.value })
              }
              placeholder="请输入评审申请标题"
            />
          </div>
          <div>
            <Label>详细说明</Label>
            <Textarea
              value={reviewForm.description}
              onChange={(e) =>
                setReviewForm({ ...reviewForm, description: e.target.value })
              }
              placeholder="请输入评审说明或背景信息"
              rows={4}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>紧急程度</Label>
              <select
                value={reviewForm.urgency}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, urgency: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="NORMAL">普通</option>
                <option value="URGENT">紧急</option>
                <option value="VERY_URGENT">非常紧急</option>
              </select>
            </div>
            <div>
              <Label>期望完成日期</Label>
              <Input
                type="date"
                value={reviewForm.expected_date}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, expected_date: e.target.value })
                }
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={reviewSubmitting}
          >
            取消
          </Button>
          <Button onClick={onSubmit} disabled={reviewSubmitting}>
            {reviewSubmitting ? "提交中..." : "提交评审"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
