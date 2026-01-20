import { motion } from "framer-motion";
import { Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export default function ResourceHeatMap() {
  const engineers = [
    { name: "张工 (ME)", loads: [100, 100, 80, 100, 60, 0, 0] },
    { name: "李工 (EE)", loads: [80, 100, 100, 80, 80, 40, 0] },
    { name: "王工 (SW)", loads: [60, 60, 80, 100, 100, 0, 0] },
    { name: "陈工 (TE)", loads: [40, 60, 80, 100, 80, 60, 0] }
  ];

  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-surface-1/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            资源负荷热力图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2 mb-4">
            {["周一", "周二", "周三", "周四", "周五", "周六", "周日"].map(
              (day) => (
                <div key={day} className="text-center text-xs text-slate-500">
                  {day}
                </div>
              )
            )}
          </div>
          <div className="space-y-2">
            {engineers.map((engineer, index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="w-24 text-sm text-slate-400 truncate">
                  {engineer.name}
                </div>
                <div className="flex-1 grid grid-cols-7 gap-1">
                  {engineer.loads.map((load, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-8 rounded flex items-center justify-center text-xs font-medium",
                        load === 0
                          ? "bg-slate-800 text-slate-500"
                          : load <= 60
                          ? "bg-emerald-500/30 text-emerald-400"
                          : load <= 80
                          ? "bg-amber-500/30 text-amber-400"
                          : "bg-red-500/30 text-red-400"
                      )}
                    >
                      {load > 0 ? `${load}%` : "-"}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
