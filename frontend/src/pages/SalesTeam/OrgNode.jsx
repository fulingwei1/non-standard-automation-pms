/**
 * Organization tree node component (recursive)
 */

import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import { Badge } from "../../components/ui";
import { LEVEL_COLORS } from "./constants";
import { getRateColor } from "./utils";

export default function OrgNode({ node, level, onSelect, selectedId }) {
  const [expanded, setExpanded] = useState(level < 2);

  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;

  const levelColor = LEVEL_COLORS[node.level] || LEVEL_COLORS.Sales;

  return (
    <div className="ml-4">
      <div
        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-all ${levelColor} ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
        onClick={() => onSelect(node)}
      >
        {hasChildren ? (
          <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}>
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        ) : (
          <div className="w-4" />
        )}

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{node.name}</span>
            <Badge variant="outline" className="text-xs">{node.level}</Badge>
          </div>
          {node.person && (
            <div className="text-xs text-slate-400">{node.person.name} · {node.person.title}</div>
          )}
        </div>

        {node.metrics && (
          <div className="text-right">
            <div className={`text-sm font-bold ${getRateColor(node.metrics.achievement_rate || node.metrics.rate)}`}>
              {node.metrics.achievement_rate || node.metrics.rate}%
            </div>
            {node.metrics.achieved_ytd && (
              <div className="text-xs text-slate-400">
                ¥{(node.metrics.achieved_ytd / 1000000).toFixed(1)}M / ¥{(node.metrics.quota_annual / 1000000).toFixed(0)}M
              </div>
            )}
          </div>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="mt-2 border-l-2 border-slate-700 pl-2">
          {node.children.map((child) => (
            <OrgNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
