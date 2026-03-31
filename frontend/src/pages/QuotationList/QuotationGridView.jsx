import { Building2, Target } from "lucide-react";
import { Card, CardContent, Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import { statusConfig } from "./statusConfig";

export function QuotationGridView({ quotations, onQuotationClick }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {(quotations || []).map((quote) => {
        const statusConf = statusConfig[quote.status];
        const isExpired =
          new Date(quote.validUntil) < new Date() &&
          quote.status !== "accepted";

        return (
          <Card
            key={quote.id}
            onClick={() => onQuotationClick(quote)}
            className="cursor-pointer hover:border-primary/30 transition-colors"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-white">{quote.name}</h3>
                    <Badge variant="secondary" className="text-xs">
                      V{quote.version}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500">{quote.id}</div>
                </div>
                <Badge
                  className={cn(
                    "text-xs",
                    statusConf.textColor,
                    "bg-transparent border-0"
                  )}
                >
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full mr-1",
                      statusConf.color
                    )}
                  />
                  {statusConf.label}
                </Badge>
              </div>

              <div className="space-y-2 mb-3">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Building2 className="w-4 h-4" />
                  {quote.customerShort}
                </div>
                <div className="flex items-center gap-2 text-sm text-blue-400">
                  <Target className="w-4 h-4" />
                  {quote.opportunityName}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-white/5">
                <div>
                  <div className="text-lg font-semibold text-amber-400">
                    ¥{(quote.finalAmount / 10000).toFixed(0)}万
                  </div>
                  {quote.discountPercent > 0 && (
                    <div className="text-xs text-red-400">
                      -{quote.discountPercent}%折扣
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div
                    className={cn(
                      "text-xs",
                      isExpired ? "text-red-400" : "text-slate-400"
                    )}
                  >
                    有效期: {quote.validUntil}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
