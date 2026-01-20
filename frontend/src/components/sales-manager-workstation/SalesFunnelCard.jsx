import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../../components/ui";
import { SalesFunnel } from "../../components/sales";
import { fadeIn } from "../../lib/animations";

export function SalesFunnelCard({ deptStats, salesFunnel }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-5 w-5 text-blue-400" />
              销售漏斗分析
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-blue-500/20 text-blue-400 border-blue-500/30"
            >
              {deptStats?.activeOpportunities || 0} 个商机
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {salesFunnel && Object.keys(salesFunnel).length > 0 ? (
            <SalesFunnel data={salesFunnel} />
          ) : (
            <div className="text-center py-8 text-slate-500">
              <p>暂无销售漏斗数据</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
