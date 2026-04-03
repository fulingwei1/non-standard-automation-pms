/**
 * Documents/attachments tab
 */

import { motion } from "framer-motion";
import { FileText, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button } from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";

const DocumentsTab = ({ po }) => (
  <Card className="bg-slate-800/50 border-slate-700/50">
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-slate-200">
        <FileText className="w-5 h-5 text-purple-400" />
        {"\u9644\u4ef6\u6587\u4ef6"} ({po.documents?.length})
      </CardTitle>
    </CardHeader>
    <CardContent>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {(po.documents || []).map((doc) => (
          <motion.div
            key={doc.id}
            variants={fadeIn}
            className="flex items-center justify-between p-3 rounded-lg border border-slate-700 bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-blue-400" />
              <div>
                <p className="font-medium text-slate-100">{doc.name}</p>
                <p className="text-xs text-slate-500">
                  {doc.size} &bull; {doc.uploadDate}
                </p>
              </div>
            </div>
            <Button size="sm" variant="ghost">
              <Download className="w-4 h-4" />
            </Button>
          </motion.div>
        ))}
      </motion.div>
    </CardContent>
  </Card>
);

export default DocumentsTab;
