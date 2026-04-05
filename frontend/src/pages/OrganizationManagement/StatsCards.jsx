import { motion } from "framer-motion";
import { Card, CardContent } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { UNIT_TYPES } from "./unitTypeConfig";

export default function StatsCards({ stats }) {
  return (
    <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <Card>
        <CardContent className="pt-4">
          <div className="text-2xl font-bold">{stats.total}</div>
          <p className="text-xs text-muted-foreground">组织单元总数</p>
        </CardContent>
      </Card>
      {UNIT_TYPES.map((type) => {
        const Icon = type.icon;
        return (
          <Card key={type.value}>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Icon className={cn("h-5 w-5", type.color)} />
                <div>
                  <div className="text-2xl font-bold">{stats.byType[type.value] || 0}</div>
                  <p className="text-xs text-muted-foreground">{type.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </motion.div>
  );
}
