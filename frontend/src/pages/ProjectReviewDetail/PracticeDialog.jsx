/**
 * Practice edit/create dialog for ProjectReviewDetail
 */



export default function PracticeDialog({
  practiceDialog,
  setPracticeDialog,
  practiceForm,
  setPracticeForm,
  saving,
  onSave,
}) {
  return (
    <Dialog
      open={practiceDialog.open}
      onOpenChange={(open) => setPracticeDialog({ open, practice: null })}>

      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {practiceDialog.practice ? "编辑最佳实践" : "添加最佳实践"}
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <Label htmlFor="practiceTitle">标题</Label>
            <Input
              id="practiceTitle"
              value={practiceForm.title}
              onChange={(e) =>
              setPracticeForm({ ...practiceForm, title: e.target.value })
              }
              placeholder="请输入最佳实践标题" />

          </div>
          <div>
            <Label htmlFor="practiceDescription">描述</Label>
            <Textarea
              id="practiceDescription"
              value={practiceForm.description}
              onChange={(e) =>
              setPracticeForm({ ...practiceForm, description: e.target.value })
              }
              placeholder="请详细描述最佳实践"
              rows={4} />

          </div>
          <div>
            <Label htmlFor="practiceCategory">类别</Label>
            <Input
              id="practiceCategory"
              value={practiceForm.category}
              onChange={(e) =>
              setPracticeForm({ ...practiceForm, category: e.target.value })
              }
              placeholder="如：项目管理、技术实践、团队协作等" />

          </div>
          <div>
            <Label htmlFor="practiceApplicability">适用范围</Label>
            <Textarea
              id="practiceApplicability"
              value={practiceForm.applicability}
              onChange={(e) =>
              setPracticeForm({
                ...practiceForm,
                applicability: e.target.value
              })
              }
              placeholder="这个实践适用的项目类型或场景"
              rows={2} />

          </div>
          <div>
            <Label htmlFor="practiceBenefits">预期收益</Label>
            <Textarea
              id="practiceBenefits"
              value={practiceForm.benefits}
              onChange={(e) =>
              setPracticeForm({ ...practiceForm, benefits: e.target.value })
              }
              placeholder="实施这个实践预期带来的收益"
              rows={2} />

          </div>
          <div>
            <Label htmlFor="practiceImplementation">实施要点</Label>
            <Textarea
              id="practiceImplementation"
              value={practiceForm.implementation}
              onChange={(e) =>
              setPracticeForm({
                ...practiceForm,
                implementation: e.target.value
              })
              }
              placeholder="实施这个实践的关键步骤和注意事项"
              rows={3} />

          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setPracticeDialog({ open: false, practice: null })}>

            取消
          </Button>
          <Button onClick={onSave} disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
