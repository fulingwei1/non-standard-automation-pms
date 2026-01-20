import { motion } from "framer-motion";
import { Award, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button
} from "../../components/ui";
import { CustomerCard } from "../../components/sales";
import { fadeIn } from "../../lib/animations";

export function TopCustomersCard({ topCustomers }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Award className="h-5 w-5 text-amber-400" />
              重点客户
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              全部 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {topCustomers && topCustomers.length > 0 ? (
            topCustomers.map((customer) => (
              <CustomerCard
                key={customer.id}
                customer={customer}
                compact
                onClick={(_c) => {}}
              />
            ))
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>暂无重点客户数据</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
