/**
 * Bottom action bar with context-sensitive buttons
 */

import { Send, Eye, Download, Edit } from "lucide-react";
import { Card, CardContent, Button } from "../../components/ui";

const ActionBar = ({ po }) => (
  <Card className="bg-gradient-to-r from-slate-800 to-slate-900 border-slate-700">
    <CardContent className="pt-6">
      <div className="flex flex-wrap gap-2">
        {po.status !== "draft" && (
          <>
            <Button className="gap-2">
              <Send className="w-4 h-4" />
              {"\u53d1\u9001\u63d0\u9192"}
            </Button>
            <Button variant="outline" className="gap-2">
              <Eye className="w-4 h-4" />
              {"\u67e5\u770b\u53d1\u7968"}
            </Button>
            <Button variant="outline" className="gap-2">
              <Download className="w-4 h-4" />
              {"\u5bfc\u51faPDF"}
            </Button>
          </>
        )}
        {po.status === "draft" && (
          <>
            <Button className="gap-2">
              <Send className="w-4 h-4" />
              {"\u63d0\u4ea4\u8ba2\u5355"}
            </Button>
            <Button variant="outline" className="gap-2">
              <Edit className="w-4 h-4" />
              {"\u7f16\u8f91\u8ba2\u5355"}
            </Button>
          </>
        )}
      </div>
    </CardContent>
  </Card>
);

export default ActionBar;
