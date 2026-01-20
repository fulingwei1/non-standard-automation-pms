import { motion } from "framer-motion";
import { Crown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

export const KeyDecisionsCard = () => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Crown className="h-5 w-5 text-amber-400" />
              重大决策事项
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-amber-500/20 text-amber-400 border-amber-500/30">

              {/* Key decisions count - 需要从API获取 */}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Key decisions - 需要从API获取数据 */}
          <div className="text-center py-8 text-slate-500">
            <p>暂无重大决策事项</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default KeyDecisionsCard;
