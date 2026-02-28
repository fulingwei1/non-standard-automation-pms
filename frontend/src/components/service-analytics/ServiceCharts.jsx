import { motion } from "framer-motion";
import {
  BarChart3,
  AlertCircle,
  Clock,
  Star,
  TrendingUp,
  TrendingDown
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export function ServiceCharts({ analytics }) {
  if (!analytics) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Service Type Distribution */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              服务类型分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.serviceTypeDistribution.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white">{item.type}</span>
                    <span className="text-slate-400">
                      {item.count}次 ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/50 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Problem Type Distribution */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              问题类型分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.problemTypeDistribution.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white">{item.type}</span>
                    <span className="text-slate-400">
                      {item.count}次 ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/50 rounded-full h-2">
                    <div
                      className="bg-red-500 h-2 rounded-full transition-all"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Response Time Distribution */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              响应时间分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.responseTimeDistribution.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white">{item.range}</span>
                    <span className="text-slate-400">
                      {item.count}次 ({item.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-800/50 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Satisfaction Trend */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
              满意度趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics.satisfactionTrends.map((item, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm text-slate-400">
                    {item.month}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-0.5">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                          key={i}
                          className={cn(
                            "w-3 h-3",
                            i <= Math.floor(item.score)
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-slate-600"
                          )}
                        />
                      ))}
                    </div>
                    <span className="text-white font-medium w-12 text-right">
                      {item.score}/5.0
                    </span>
                    {index > 0 && (
                      <span
                        className={cn(
                          "text-xs",
                          item.score >
                            analytics.satisfactionTrends[index - 1].score
                            ? "text-emerald-400"
                            : item.score <
                              analytics.satisfactionTrends[index - 1]
                                .score
                            ? "text-red-400"
                            : "text-slate-400"
                        )}
                      >
                        {item.score >
                        analytics.satisfactionTrends[index - 1].score ? (
                          <TrendingUp className="w-3 h-3 inline" />
                        ) : item.score <
                          analytics.satisfactionTrends[index - 1].score ? (
                          <TrendingDown className="w-3 h-3 inline" />
                        ) : null}
                      </span>
                    )}
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
