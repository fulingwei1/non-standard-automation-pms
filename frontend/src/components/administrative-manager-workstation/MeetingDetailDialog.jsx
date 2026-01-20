import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  Button,
  Badge
} from "../../components/ui";
import { cn } from "../../lib/utils";

const MeetingDetailDialog = ({
  open,
  onOpenChange,
  selectedMeeting
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>会议详情</DialogTitle>
          <DialogDescription>
            {selectedMeeting?.organizer} · {selectedMeeting?.department}
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          {selectedMeeting &&
          <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge
                variant="outline"
                className={cn(
                  selectedMeeting.status === "ongoing" &&
                  "bg-green-500/20 text-green-400 border-green-500/30",
                  selectedMeeting.status === "scheduled" &&
                  "bg-blue-500/20 text-blue-400 border-blue-500/30"
                )}>
                  {selectedMeeting.status === "ongoing" ? "进行中" : "已安排"}
                </Badge>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  {selectedMeeting.title}
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">会议室</p>
                    <p className="text-white">{selectedMeeting.room}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">时间</p>
                    <p className="text-white">{selectedMeeting.time}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">日期</p>
                    <p className="text-white">{selectedMeeting.date}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">参会人数</p>
                    <p className="text-white">
                      {selectedMeeting.attendees} 人
                    </p>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-700/50">
                <Button variant="outline" className="w-full">
                  查看完整信息
                </Button>
              </div>
          </div>
          }
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
};

export default MeetingDetailDialog;
