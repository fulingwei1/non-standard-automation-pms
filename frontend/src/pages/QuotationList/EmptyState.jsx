import { FileText, Plus } from "lucide-react";
import { Button } from "../../components/ui";

export function EmptyState({ onCreateClick }) {
  return (
    <div className="text-center py-16">
      <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
      <h3 className="text-lg font-medium text-white mb-2">暂无报价</h3>
      <p className="text-slate-400 mb-4">没有找到符合条件的报价单</p>
      <Button onClick={onCreateClick}>
        <Plus className="w-4 h-4 mr-2" />
        新建报价
      </Button>
    </div>
  );
}
