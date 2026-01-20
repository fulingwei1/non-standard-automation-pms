import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ClipboardCheck, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";
import { formatCurrency } from "./utils";

export const PendingApprovalsCard = ({ pendingApprovals }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <ClipboardCheck className="h-5 w-5 text-blue-400" />
              待审批事项
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-blue-500/20 text-blue-400 border-blue-500/30">

              {pendingApprovals ? pendingApprovals.length : 0}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {pendingApprovals && pendingApprovals.map((item) =>
          <Link
            key={item.id}
            to="/approvals"
            className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-blue-500/50 transition-colors cursor-pointer group">

            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      item.type === "contract" &&
                      "bg-blue-500/20 text-blue-400 border-blue-500/30",
                      item.type === "investment" &&
                      "bg-red-500/20 text-red-400 border-red-500/30",
                      item.type === "budget" &&
                      "bg-purple-500/20 text-purple-400 border-purple-500/30"
                    )}>

                    {item.type === "contract" ?
                    "合同" :
                    item.type === "investment" ?
                    "投资" :
                    "预算"}
                  </Badge>
                  {item.priority === "high" &&
                  <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                    紧急
                  </Badge>
                  }
                </div>
                <p className="font-medium text-white text-sm group-hover:text-blue-400 transition-colors">
                  {item.title}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  {item.department} · {item.submitter}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs mt-2">
              <span className="text-slate-400">
                {item.submitTime.split(" ")[1]}
              </span>
              <span className="font-medium text-amber-400">
                {formatCurrency(item.amount)}
              </span>
            </div>
          </Link>
          )}
          <Button variant="outline" className="w-full mt-3" asChild>
            <Link to="/approvals">
              审批中心 <ArrowRight className="w-3 h-3 ml-2" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default PendingApprovalsCard;
