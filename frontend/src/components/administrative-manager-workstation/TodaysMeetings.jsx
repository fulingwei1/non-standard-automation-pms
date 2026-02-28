import { motion } from "framer-motion";
import { Calendar, ChevronRight, MapPin, Clock, Users } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";

const TodaysMeetings = ({
  meetings,
  setSelectedMeeting,
  setShowMeetingDetail
}) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Calendar className="h-5 w-5 text-purple-400" />
              今日会议安排
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary">
              查看全部 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {(meetings || []).map((meeting) =>
            <div
              key={meeting.id}
              className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
              onClick={() => {
                setSelectedMeeting(meeting);
                setShowMeetingDetail(true);
              }}>

                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">
                        {meeting.title}
                      </span>
                      <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        meeting.status === "ongoing" &&
                        "bg-green-500/20 text-green-400 border-green-500/30",
                        meeting.status === "scheduled" &&
                        "bg-blue-500/20 text-blue-400 border-blue-500/30"
                      )}>
                        {meeting.status === "ongoing" ?
                      "进行中" :
                      "已安排"}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {meeting.organizer} · {meeting.department}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {meeting.room}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {meeting.time}
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {meeting.attendees} 人
                      </div>
                    </div>
                  </div>
                </div>
            </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default TodaysMeetings;
