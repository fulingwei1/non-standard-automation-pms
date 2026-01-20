import React from "react";
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
} from "../../components/ui";

export default function FollowUpDialog({
  open,
  onOpenChange,
  data,
  setData,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>添加跟进记录</DialogTitle>
          <DialogDescription>记录线索跟进情况</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>跟进类型 *</Label>
            <select
              value={data.follow_up_type}
              onChange={(e) =>
                setData({
                  ...data,
                  follow_up_type: e.target.value,
                })
              }
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
            >
              <option value="CALL">电话</option>
              <option value="EMAIL">邮件</option>
              <option value="VISIT">拜访</option>
              <option value="MEETING">会议</option>
              <option value="OTHER">其他</option>
            </select>
          </div>
          <div>
            <Label>跟进内容 *</Label>
            <Textarea
              value={data.content}
              onChange={(e) =>
                setData({ ...data, content: e.target.value })
              }
              placeholder="请输入跟进内容"
              rows={4}
            />
          </div>
          <div>
            <Label>下次行动</Label>
            <Input
              value={data.next_action}
              onChange={(e) =>
                setData({
                  ...data,
                  next_action: e.target.value,
                })
              }
              placeholder="如：发送报价单"
            />
          </div>
          <div>
            <Label>行动时间</Label>
            <Input
              type="date"
              value={data.next_action_at}
              onChange={(e) =>
                setData({
                  ...data,
                  next_action_at: e.target.value,
                })
              }
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSave}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
