import { motion } from "framer-motion";
import { Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

export const StrategicTargetCard = () => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-5 w-5 text-purple-400" />
            战略目标
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {/* Strategic metrics - 需要从API获取数据 */}
            <div className="text-center py-8 text-slate-500">
              <p>战略目标数据需要从API获取</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default StrategicTargetCard;
