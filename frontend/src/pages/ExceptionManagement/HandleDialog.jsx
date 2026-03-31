import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";

/**
 * HandleDialog
 * Allows the user to update an exception's status and record a handling note.
 */
export function HandleDialog({
  open,
  onOpenChange,
  selectedException,
  handleData,
  setHandleData,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>处理异常</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedException && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">异常标题</div>
                <div className="font-medium">
                  {selectedException.event_title}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理状态
                </label>
                <Select
                  value={handleData.next_status}
                  onValueChange={(val) =>
                    setHandleData({ ...handleData, next_status: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PROCESSING">处理中</SelectItem>
                    <SelectItem value="RESOLVED">已解决</SelectItem>
                    <SelectItem value="CLOSED">已关闭</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理说明
                </label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={handleData.action_description}
                  onChange={(e) =>
                    setHandleData({
                      ...handleData,
                      action_description: e.target.value,
                    })
                  }
                  placeholder="填写处理措施和结果..."
                />
              </div>
            </div>
          )}
        </DialogBody>
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
