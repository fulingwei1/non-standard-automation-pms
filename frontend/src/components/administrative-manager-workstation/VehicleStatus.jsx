import { motion } from "framer-motion";
import { Car, ChevronRight } from "lucide-react";
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

const VehicleStatus = ({ vehicles }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Car className="h-5 w-5 text-cyan-400" />
              车辆使用状态
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary">
              详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {vehicles.map((vehicle) =>
          <div
            key={vehicle.id}
            className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white">
                      {vehicle.plateNumber}
                    </span>
                    <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      vehicle.status === "in_use" &&
                      "bg-blue-500/20 text-blue-400 border-blue-500/30",
                      vehicle.status === "available" &&
                      "bg-green-500/20 text-green-400 border-green-500/30",
                      vehicle.status === "maintenance" &&
                      "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    )}>
                      {vehicle.status === "in_use" ?
                    "使用中" :
                    vehicle.status === "available" ?
                    "可用" :
                    "保养中"}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-400">
                    {vehicle.brand}
                  </div>
                  {vehicle.driver &&
                <div className="text-xs text-slate-500 mt-1">
                      驾驶员: {vehicle.driver}
                </div>
                }
                  {vehicle.purpose &&
                <div className="text-xs text-slate-500 mt-1">
                      {vehicle.purpose} · {vehicle.destination}
                </div>
                }
                  {vehicle.maintenanceReason &&
                <div className="text-xs text-slate-500 mt-1">
                      {vehicle.maintenanceReason} · 预计归还:{" "}
                      {vehicle.returnDate}
                </div>
                }
                  {vehicle.nextMaintenance &&
                <div className="text-xs text-slate-500 mt-1">
                      下次保养: {vehicle.nextMaintenance}
                </div>
                }
                </div>
              </div>
          </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default VehicleStatus;
