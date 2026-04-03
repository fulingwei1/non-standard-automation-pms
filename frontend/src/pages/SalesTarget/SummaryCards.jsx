import { motion } from "framer-motion";
import { Card, CardContent } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

export default function SummaryCards({ summaryCards }) {
  return (
    <motion.div variants={fadeIn}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {summaryCards.map((card) => (
          <Card key={card.label}>
            <CardContent className="p-4 space-y-2">
              <div className="text-slate-400 text-sm">{card.label}</div>
              <div className="text-white text-lg font-semibold">{formatCurrency(card.targetValue)}</div>
              <div className="text-slate-400 text-xs">实际 {formatCurrency(card.actualValue)} · 完成 {card.completion.toFixed(1)}%</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}
