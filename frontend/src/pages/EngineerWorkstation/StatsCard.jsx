/**
 * StatsCard - Summary stat card with click-to-filter behavior
 */

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

export default function StatsCard({ label, value, icon: Icon, color, onClick, active }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "cursor-pointer rounded-xl border p-4 transition-all",
        active ?
        "bg-primary/10 border-primary/30" :
        "bg-surface-1/50 border-border hover:border-border/80"
      )}>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <Icon className={cn("w-6 h-6", color)} />
      </div>
    </motion.div>);

}
