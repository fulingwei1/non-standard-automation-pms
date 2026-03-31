import { LayoutGrid, List, TrendingUp, BarChart3 } from "lucide-react";
import { cn } from "../../lib/utils";

const VIEW_TABS = [
  { key: "board", label: "看板视图", icon: LayoutGrid },
  { key: "overview", label: "概览统计", icon: BarChart3 },
  { key: "funnel", label: "销售漏斗", icon: TrendingUp },
  { key: "list", label: "列表视图", icon: List },
];

export default function ViewModeTabs({ viewMode, setViewMode }) {
  return (
    <div className="flex border-b border-border mb-6">
      {VIEW_TABS.map(({ key, label, icon: Icon }) =>
        <button
          key={key}
          onClick={() => setViewMode(key)}
          className={cn(
            "flex items-center gap-2 px-4 py-2 border-b-2 transition-colors",
            viewMode === key ?
            "border-accent text-accent" :
            "border-transparent text-text-secondary hover:text-white"
          )}>

            <Icon className="w-4 h-4" />
            {label}
        </button>
      )}
    </div>
  );
}
