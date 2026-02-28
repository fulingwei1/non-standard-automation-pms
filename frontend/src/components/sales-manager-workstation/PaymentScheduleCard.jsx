import { motion } from "framer-motion";
import { Receipt, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button
} from "../../components/ui";
import { PaymentTimeline } from "../../components/sales";
import { fadeIn } from "../../lib/animations";

export function PaymentScheduleCard({ payments }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Receipt className="h-5 w-5 text-emerald-400" />
              近期回款计划
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              全部回款 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {payments && payments?.length > 0 ? (
            <PaymentTimeline payments={payments} compact />
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>暂无回款计划</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
