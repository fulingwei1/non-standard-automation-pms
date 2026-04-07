import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { POSITION_CATEGORIES } from "./categoryConstants";

export default function StatsCards({ positions }) {
  const stats = POSITION_CATEGORIES.reduce((acc, cat) => {
    acc[cat.value] = (positions || []).filter((p) => p.position_category === cat.value).length;
    return acc;
  }, {});

  return (
    <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-6 gap-4">
      {POSITION_CATEGORIES.map((cat) => (
        <Card key={cat.value}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Briefcase className={cn("h-5 w-5", cat.color.split(" ")[0])} />
              <div>
                <div className="text-2xl font-bold">{stats[cat.value] || 0}</div>
                <p className="text-xs text-muted-foreground">{cat.label}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </motion.div>
  );
}
