import { cn } from "../../lib/utils";
import { OpportunityUtils } from "../../components/opportunity-board";

export default function ListView({ sortedOpportunities, onOpportunityClick }) {
  return (
    <div className="bg-surface-1 rounded-xl border border-border">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-2 border-b border-border">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">机会名称</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">客户</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">阶段</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary">预期金额</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">负责人</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">优先级</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {(sortedOpportunities || []).map((opportunity) =>
          <tr key={opportunity.id} className="hover:bg-surface-2/50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {opportunity.isHot &&
                <Flame className="w-3 h-3 text-amber-400" />
                }
                    <span className="text-sm text-white font-medium">
                      {opportunity.name}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-white">
                  {opportunity.customerName}
                </td>
                <td className="px-4 py-3">
                  <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  OpportunityUtils.getStageConfig(opportunity.stage).textColor
                )}>

                    {OpportunityUtils.getStageConfig(opportunity.stage).label}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-right text-sm text-white">
                  ¥{OpportunityUtils.formatCurrency(opportunity.expectedAmount)}
                </td>
                <td className="px-4 py-3 text-sm text-white">
                  {opportunity.owner}
                </td>
                <td className="px-4 py-3">
                  <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  OpportunityUtils.getPriorityConfig(opportunity.priority).color
                )}>

                    {OpportunityUtils.getPriorityConfig(opportunity.priority).label}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <Button
                variant="ghost"
                size="sm"
                onClick={() => onOpportunityClick(opportunity)}>

                    <Eye className="w-4 h-4" />
                  </Button>
                </td>
          </tr>
          )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
