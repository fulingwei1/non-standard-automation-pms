import { Key, Package, Shield } from "lucide-react";
import { ANIMATION_VARIANTS, STAT_CARD_DELAYS } from "./constants";

export function StatsCards({ stats }) {
  const cards = [
    { label: "权限总数", value: stats.total, icon: Key, iconColor: "text-blue-400" },
    { label: "模块数量", value: stats.modules, icon: Package, iconColor: "text-green-400" },
    { label: "启用权限", value: stats.active, icon: Shield, iconColor: "text-purple-400" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.label}
            initial={ANIMATION_VARIANTS.initial}
            animate={ANIMATION_VARIANTS.animate}
            transition={{ delay: STAT_CARD_DELAYS[index] }}
          >
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">{card.label}</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {card.value}
                    </p>
                  </div>
                  <Icon className={`h-8 w-8 ${card.iconColor}`} />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
