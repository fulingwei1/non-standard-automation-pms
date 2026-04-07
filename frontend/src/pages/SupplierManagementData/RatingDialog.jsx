


export default function RatingDialog({
  open,
  onOpenChange,
  supplierName,
  ratingData,
  onRatingChange,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">
            供应商评级 - {supplierName}
          </DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="quality-rating"
              className="text-right text-slate-400"
            >
              质量评分
            </Label>
            <Input
              id="quality-rating"
              type="number"
              min="0"
              max="5"
              step="0.1"
              value={ratingData.quality_rating}
              onChange={(e) =>
                onRatingChange("quality_rating", parseFloat(e.target.value) || 0)
              }
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="delivery-rating"
              className="text-right text-slate-400"
            >
              交期评分
            </Label>
            <Input
              id="delivery-rating"
              type="number"
              min="0"
              max="5"
              step="0.1"
              value={ratingData.delivery_rating}
              onChange={(e) =>
                onRatingChange("delivery_rating", parseFloat(e.target.value) || 0)
              }
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label
              htmlFor="service-rating"
              className="text-right text-slate-400"
            >
              服务评分
            </Label>
            <Input
              id="service-rating"
              type="number"
              min="0"
              max="5"
              step="0.1"
              value={ratingData.service_rating}
              onChange={(e) =>
                onRatingChange("service_rating", parseFloat(e.target.value) || 0)
              }
              className="col-span-3 bg-slate-800 border-slate-700 text-slate-200"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
