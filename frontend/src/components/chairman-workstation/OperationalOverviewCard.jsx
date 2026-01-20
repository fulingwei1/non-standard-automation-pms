import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

export const OperationalOverviewCard = ({ companyStats }) => {
  if (!companyStats) {return null;}

  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="h-5 w-5 text-cyan-400" />
            运营概览
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">项目按时交付率</span>
              <span className="font-semibold text-emerald-400">
                {companyStats.onTimeDeliveryRate || 0}%
              </span>
            </div>
            <Progress
              value={companyStats.onTimeDeliveryRate || 0}
              className="h-2 bg-slate-700/50" />

          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">质量合格率</span>
              <span className="font-semibold text-emerald-400">
                {companyStats.qualityPassRate || 0}%
              </span>
            </div>
            <Progress
              value={companyStats.qualityPassRate || 0}
              className="h-2 bg-slate-700/50" />

          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">产能利用率</span>
              <span className="font-semibold text-blue-400">
                {companyStats.productionCapacity}%
              </span>
            </div>
            <Progress
              value={companyStats.productionCapacity}
              className="h-2 bg-slate-700/50" />

          </div>
          <div className="pt-3 border-t border-slate-700/50">
            <div className="grid grid-cols-2 gap-3 text-center">
              <div>
                <div className="text-2xl font-bold text-white">
                  {companyStats.totalEmployees}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  员工总数
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-white">
                  {companyStats.departments}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  部门数量
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default OperationalOverviewCard;
