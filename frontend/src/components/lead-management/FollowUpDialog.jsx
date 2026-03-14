import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label,
  Textarea,
  Badge,
} from "../../components/ui";
import {
  FOLLOW_UP_TYPES,
  LEAD_QUICK_FOLLOW_UP_TEMPLATES,
} from "@/lib/constants/leadFollowUp";

export default function FollowUpDialog({
  open,
  onOpenChange,
  data,
  setData,
  onSave,
  saving = false,
}) {
  const applyTemplate = (template) => {
    setData({
      ...data,
      follow_up_type: template.follow_up_type || data.follow_up_type,
      content: template.content,
      next_action: template.next_action || data.next_action,
    });
  };

  const setNextActionTomorrow = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.toISOString().split("T")[0];
    setData({ ...data, next_action_at: dateStr });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>添加跟进记录</DialogTitle>
          <DialogDescription>快捷记录线索跟进情况</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>跟进类型 *</Label>
            <div className="mt-2 flex flex-wrap gap-2">
              {FOLLOW_UP_TYPES.map((type) => (
                <Badge
                  key={type.value}
                  variant={data.follow_up_type === type.value ? "default" : "outline"}
                  className="cursor-pointer px-3 py-1.5 text-sm"
                  onClick={() => setData({ ...data, follow_up_type: type.value })}
                >
                  {type.label}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <Label>快捷模板</Label>
            <div className="mt-2 flex flex-wrap gap-2">
              {LEAD_QUICK_FOLLOW_UP_TEMPLATES.map((tpl) => (
                <Badge
                  key={tpl.key}
                  variant="secondary"
                  className="cursor-pointer px-3 py-1.5 text-sm hover:bg-slate-700"
                  onClick={() => applyTemplate(tpl)}
                >
                  {tpl.label}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <Label>跟进内容 *</Label>
            <Textarea
              value={data.content}
              onChange={(e) => setData({ ...data, content: e.target.value })}
              placeholder="请输入跟进内容，或使用上方快捷模板"
              rows={4}
              className="resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>下次行动</Label>
              <Input
                value={data.next_action}
                onChange={(e) => setData({ ...data, next_action: e.target.value })}
                placeholder="如：发送报价单"
              />
            </div>
            <div>
              <Label>行动时间</Label>
              <div className="flex gap-2">
                <Input
                  type="datetime-local"
                  value={data.next_action_at || ""}
                  onChange={(e) => setData({ ...data, next_action_at: e.target.value })}
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={setNextActionTomorrow}
                  type="button"
                  title="设为明天"
                >
                  明天
                </Button>
              </div>
            </div>
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            取消
          </Button>
          <Button
            variant="secondary"
            onClick={() => onSave({ keepOpen: true })}
            disabled={saving || !data.content?.trim()}
          >
            保存并下一条
          </Button>
          <Button onClick={() => onSave({ keepOpen: false })} disabled={saving || !data.content?.trim()}>
            {saving ? "保存中..." : "保存"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
