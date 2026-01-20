import { motion } from "framer-motion";
import { Package, ChevronRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";

const OfficeSuppliesStatus = ({ officeSupplies }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Package className="h-5 w-5 text-blue-400" />
              办公用品库存预警
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
            {officeSupplies.map((item) =>
            <div
              key={item.id}
              className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">
                        {item.name}
                      </span>
                      <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        item.status === "low" &&
                        "bg-red-500/20 text-red-400 border-red-500/30",
                        item.status === "normal" && "bg-slate-700/40"
                      )}>
                        {item.status === "low" ? "库存不足" : "正常"}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-400">
                      {item.category} · 供应商: {item.supplier}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">
                      {item.currentStock} {item.unit}
                    </div>
                    <div className="text-xs text-slate-400">
                      最低库存: {item.minStock} {item.unit}
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">库存率</span>
                    <span className="text-slate-300">
                      {(
                    item.currentStock / item.minStock *
                    100).
                    toFixed(0)}
                      %
                    </span>
                  </div>
                  <Progress
                  value={item.currentStock / item.minStock * 100}
                  className={cn(
                    "h-1.5 bg-slate-700/50",
                    item.status === "low" && "bg-red-500/20"
                  )} />

                </div>
            </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default OfficeSuppliesStatus;
