import { motion } from "framer-motion";
import { Users, Star } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function ServicePerformance({ analytics }) {
  if (!analytics) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Top Customers */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              主要客户
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.topCustomers.map((customer, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-white font-medium">
                      {customer.customer}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      工单数: {customer.tickets}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-0.5">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                          key={i}
                          className={cn(
                            "w-3 h-3",
                            i <= Math.floor(customer.satisfaction)
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-slate-600"
                          )}
                        />
                      ))}
                    </div>
                    <span className="text-white font-medium w-12 text-right">
                      {customer.satisfaction}/5
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Engineer Performance */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              工程师绩效
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.engineerPerformance.map((engineer, index) => (
                <div key={index} className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-white font-medium">
                      {engineer.engineer}
                    </p>
                    <Badge variant="secondary" className="text-xs">
                      {engineer.tickets}个工单
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400">平均时长:</span>
                      <span className="text-white ml-1">
                        {engineer.avgTime}小时
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-slate-400">满意度:</span>
                      <div className="flex items-center gap-0.5">
                        {[1, 2, 3, 4, 5].map((i) => (
                          <Star
                            key={i}
                            className={cn(
                              "w-3 h-3",
                              i <= Math.floor(engineer.satisfaction)
                                ? "fill-yellow-400 text-yellow-400"
                                : "text-slate-600"
                            )}
                          />
                        ))}
                      </div>
                      <span className="text-white ml-1">
                        {engineer.satisfaction}/5
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
