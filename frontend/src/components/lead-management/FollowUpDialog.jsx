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

const QUICK_TEMPLATES = [
  { label: "已联系，待报价", content: "已与客户联系，了解初步需求，待发送报价单。" },
  { label: "已报价，待反馈", content: "报价单已发送，待客户反馈。" },
  { label: "需技术支援", content: "客户提出技术疑问，需安排售前工程师支持。" },
  { label: "待拜访", content: "客户邀请现场拜访，进一步了解需求。" },
];

const FOLLOWUP_TYPES = [
  { value: "CALL", label: "电话" },
  { value: "EMAIL", label: "邮件" },
  { value: "VISIT", label: "拜访" },
  { value: "MEETING", label: "会议" },
  { value: "OTHER", label: "其他" },
];

export default function FollowUpDialog({
  open,
  onOpenChange,
  data,
  setData,
  onSave,
  saving = false,
}) {
  const applyTemplate = (template) => {
    setData({ ...data, content: template.content });
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
          {/* 跟进类型 - 用 Badge 按钮替代下拉框 */}
          <div>
            <Label>跟进类型 *</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {FOLLOWUP_TYPES.map((type) => (
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

          {/* 快捷模板 */}
          <div>
            <Label>快捷模板</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {QUICK_TEMPLATES.map((tpl, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="cursor-pointer px-3 py-1.5 text-sm hover:bg-slate-700"
                  onClick={() => applyTemplate(tpl)}
                >
                  {tpl.label}
                </Badge>
              ))}
            </div>
          </div>

          {/* 跟进内容 */}
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

          {/* 下次行动 */}
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
