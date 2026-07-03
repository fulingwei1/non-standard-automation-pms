import { Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import { OpportunityCard } from "../../components/sales";
import { OPPORTUNITY_STAGE_CONFIGS } from "../../components/opportunity-board";

export default function BoardView({
  groupedOpportunities,
  hideLost,
  onOpportunityClick,
  onStageChange,
}) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
      {Object.entries(OPPORTUNITY_STAGE_CONFIGS).
        filter(([, stage]) => !hideLost || stage.frontendKey !== "lost").
        map(([stageCode, stage]) => {
          const stageOpps = groupedOpportunities[stage.frontendKey] || [];
          const stageTotal = (stageOpps || []).reduce(
            (sum, o) => sum + (o.expectedAmount || 0),
            0
          );

          return (
            <div key={`${stageCode}-${stage.frontendKey}`} className="flex-shrink-0 w-80">
                  {/* Column Header */}
                  <div className="flex items-center justify-between mb-3 p-3 bg-surface-1 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div
                    className={cn("w-3 h-3 rounded-full", stage.color)} />

                      <span className="font-medium text-white">
                        {stage.label}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {stageOpps.length}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-400">
                      ¥{(stageTotal / 10000).toFixed(0)}万
                    </span>
                  </div>

                  {/* Column Content */}
                  <div className="space-y-3 min-h-[200px]">
                    {(stageOpps || []).map((opportunity, index) =>
                <OpportunityCard
                  key={`${stage.frontendKey}-${opportunity.id ?? opportunity.opp_code ?? index}`}
                  opportunity={opportunity}
                  onClick={onOpportunityClick}
                  draggable
                  onDragEnd={(newStage) => {
                    // Handle drag end to change stage
                    onStageChange(opportunity, newStage);
                  }} />

                )}
                  </div>
            </div>);

        })}
    </div>
  );
}
