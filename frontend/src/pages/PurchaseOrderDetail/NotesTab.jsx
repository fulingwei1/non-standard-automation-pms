/**
 * Notes / remarks tab
 */

import { motion } from "framer-motion";
import { Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

const NotesTab = ({ po }) => (
  <Card className="bg-slate-800/50 border-slate-700/50">
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-slate-200">
        <Info className="w-5 h-5 text-amber-400" />
        {"\u5907\u6ce8\u4fe1\u606f"}
      </CardTitle>
    </CardHeader>
    <CardContent>
      <motion.div variants={fadeIn} className="space-y-4">
        <div>
          <p className="text-sm text-slate-400 mb-2">{"\u5907\u6ce8"}</p>
          <p className="text-slate-200 leading-relaxed">{po.remarks}</p>
        </div>
        <div className="pt-4 border-t border-slate-700">
          <p className="text-sm text-slate-400 mb-2">{"\u5173\u8054\u9879\u76ee"}</p>
          <Badge className="bg-slate-700/50 text-slate-200">
            {po.attachedProject.id} - {po.attachedProject.name}
          </Badge>
          <p className="text-xs text-slate-500 mt-1">
            {po.attachedProject.stage}
          </p>
        </div>
      </motion.div>
    </CardContent>
  </Card>
);

export default NotesTab;
