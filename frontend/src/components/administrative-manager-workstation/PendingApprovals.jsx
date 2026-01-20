import { motion } from "framer-motion";
import { ClipboardCheck } from "lucide-react";
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
import { formatCurrency } from "./utils";

const PendingApprovals = ({
  pendingApprovals,
  setSelectedApproval,
  setShowApprovalDetail
}) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardCheck className="h-5 w-5 text-amber-400" />
              待审批事项
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-amber-500/20 text-amber-400 border-amber-500/30">
              {pendingApprovals.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {pendingApprovals.map((item) =>
          <div
            key={item.id}
            className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
            onClick={() => {
              setSelectedApproval(item);
              setShowApprovalDetail(true);
            }}>

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      item.type === "office_supplies" &&
                      "bg-blue-500/20 text-blue-400 border-blue-500/30",
                      item.type === "vehicle" &&
                      "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                      item.type === "asset" &&
                      "bg-purple-500/20 text-purple-400 border-purple-500/30",
                      item.type === "meeting" &&
                      "bg-green-500/20 text-green-400 border-green-500/30",
                      item.type === "leave" &&
                      "bg-pink-500/20 text-pink-400 border-pink-500/30"
                    )}>
                      {item.type === "office_supplies" ?
                    "办公用品" :
                    item.type === "vehicle" ?
                    "车辆" :
                    item.type === "asset" ?
                    "资产" :
                    item.type === "meeting" ?
                    "会议" :
                    "请假"}
                    </Badge>
                    {item.priority === "high" &&
                  <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                        紧急
                  </Badge>
                  }
                  </div>
                  <p className="font-medium text-white text-sm">
                    {item.title}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {item.department} · {item.applicant}
                  </p>
                  {(item.items ||
                item.purpose ||
                item.item ||
                item.room ||
                item.type) &&
                <p className="text-xs text-slate-500 mt-1">
                      {item.items?.join("、") ||
                  item.purpose ||
                  item.item ||
                  `${item.room} ${item.date} ${item.time}` ||
                  `${item.type} ${item.days}天`}
                </p>
                }
                </div>
              </div>
              {item.amount &&
            <div className="flex items-center justify-between text-xs mt-2">
                  <span className="text-slate-400">
                    {item.submitTime.split(" ")[1]}
                  </span>
                  <span className="font-medium text-amber-400">
                    {formatCurrency(item.amount)}
                  </span>
            </div>
            }
          </div>
          )}
          <Button
            variant="outline"
            className="w-full mt-3"
            onClick={() =>
            window.location.href = "/administrative-approvals"
            }>
            查看全部审批
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default PendingApprovals;
