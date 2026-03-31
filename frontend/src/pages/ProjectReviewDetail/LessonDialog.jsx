/**
 * Lesson edit/create dialog for ProjectReviewDetail
 */
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui";
import { Input, Textarea } from "../../components/ui/input";
import { Label } from "../../components/ui/label";

export default function LessonDialog({
  lessonDialog,
  setLessonDialog,
  lessonForm,
  setLessonForm,
  saving,
  onSave,
}) {
  return (
    <Dialog
      open={lessonDialog.open}
      onOpenChange={(open) => setLessonDialog({ open, lesson: null })}>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {lessonDialog.lesson ? "编辑经验教训" : "添加经验教训"}
          </DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div>
            <Label htmlFor="lessonTitle">标题</Label>
            <Input
              id="lessonTitle"
              value={lessonForm.title}
              onChange={(e) =>
              setLessonForm({ ...lessonForm, title: e.target.value })
              }
              placeholder="请输入经验教训标题" />

          </div>
          <div>
            <Label htmlFor="lessonDescription">描述</Label>
            <Textarea
              id="lessonDescription"
              value={lessonForm.description}
              onChange={(e) =>
              setLessonForm({ ...lessonForm, description: e.target.value })
              }
              placeholder="请详细描述经验教训"
              rows={4} />

          </div>
          <div>
            <Label htmlFor="lessonCategory">类别</Label>
            <Input
              id="lessonCategory"
              value={lessonForm.category}
              onChange={(e) =>
              setLessonForm({ ...lessonForm, category: e.target.value })
              }
              placeholder="如：项目管理、技术实现、团队协作等" />

          </div>
          <div>
            <Label htmlFor="lessonImpact">影响</Label>
            <Input
              id="lessonImpact"
              value={lessonForm.impact}
              onChange={(e) =>
              setLessonForm({ ...lessonForm, impact: e.target.value })
              }
              placeholder="对项目的影响" />

          </div>
          <div>
            <Label htmlFor="lessonActions">改进措施</Label>
            <Textarea
              id="lessonActions"
              value={lessonForm.actions}
              onChange={(e) =>
              setLessonForm({ ...lessonForm, actions: e.target.value })
              }
              placeholder="具体的改进措施和行动计划"
              rows={3} />

          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setLessonDialog({ open: false, lesson: null })}>

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
