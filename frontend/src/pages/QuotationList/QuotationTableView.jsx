import { Target, Eye, Copy, Send } from "lucide-react";
import { Card, CardContent, Button, Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import { statusConfig } from "./statusConfig";

export function QuotationTableView({ quotations, onQuotationClick }) {
  return (
    <Card>
      <CardContent className="p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                报价单
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                客户
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                关联商机
              </th>
              <th className="text-right p-4 text-sm font-medium text-slate-400">
                报价金额
              </th>
              <th className="text-center p-4 text-sm font-medium text-slate-400">
                折扣
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                有效期
              </th>
              <th className="text-left p-4 text-sm font-medium text-slate-400">
                状态
              </th>
              <th className="text-center p-4 text-sm font-medium text-slate-400">
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            {(quotations || []).map((quote) => {
              const statusConf = statusConfig[quote.status];
              const isExpired =
                new Date(quote.validUntil) < new Date() &&
                quote.status !== "accepted";

              return (
                <tr
                  key={quote.id}
                  onClick={() => onQuotationClick(quote)}
                  className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                >
                  <td className="p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">
                          {quote.name}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          V{quote.version}
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-500">{quote.id}</div>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {quote.customerShort}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-1 text-sm text-blue-400">
                      <Target className="w-3 h-3" />
                      {quote.opportunityName}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <div className="text-amber-400 font-medium">
                      ¥{(quote.finalAmount / 10000).toFixed(0)}万
                    </div>
                    {quote.discountPercent > 0 && (
                      <div className="text-xs text-slate-500 line-through">
                        ¥{(quote.totalAmount / 10000).toFixed(0)}万
                      </div>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    {quote.discountPercent > 0 ? (
                      <Badge
                        variant="secondary"
                        className="text-xs bg-red-500/20 text-red-400"
                      >
                        -{quote.discountPercent}%
                      </Badge>
                    ) : (
                      <span className="text-slate-500">-</span>
                    )}
                  </td>
                  <td className="p-4">
                    <span
                      className={cn(
                        "text-sm",
                        isExpired ? "text-red-400" : "text-slate-400"
                      )}
                    >
                      {quote.validUntil}
                    </span>
                  </td>
                  <td className="p-4">
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
                  </td>
                  <td className="p-4">
                    <div className="flex justify-center gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Copy className="w-4 h-4" />
                      </Button>
                      {quote.status === "approved" && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                        >
                          <Send className="w-4 h-4 text-blue-400" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
