
import { Button } from "../ui/button";
import { CheckSquare, Users } from "lucide-react";

export default function DispatchBatchActions({
  selectedCount,
  onBatchAssign,
  onCancelSelection,
}) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center justify-between p-4 bg-muted rounded-lg mb-4">
      <div className="flex items-center space-x-2">
        <CheckSquare className="h-4 w-4" />
        <span className="text-sm font-medium">
          已选择 {selectedCount} 个派工单
        </span>
      </div>
      <div className="flex space-x-2">
        <Button variant="outline" size="sm" onClick={onBatchAssign}>
          <Users className="mr-2 h-4 w-4" />
          批量派工
        </Button>
        <Button variant="outline" size="sm" onClick={onCancelSelection}>
          取消选择
        </Button>
      </div>
    </div>
  );
}
