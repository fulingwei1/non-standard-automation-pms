/**
 * AiSidebarPanel - AI智能定价侧边栏
 */
import { Sparkles, ChevronRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import IntelligentQuoteSidebar from "../../components/quote/IntelligentQuoteSidebar";

export default function AiSidebarPanel({ selectedOpportunity, currentPrice, currentCost, onApplyPrice, onClose }) {
  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-slate-950 border-l border-slate-800 overflow-y-auto p-4 pt-20">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          AI智能定价
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-6 w-6 p-0"
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
      <IntelligentQuoteSidebar
        opportunity={selectedOpportunity}
        currentPrice={currentPrice}
        currentCost={currentCost}
        onApplyPrice={onApplyPrice}
      />
    </div>
  );
}
