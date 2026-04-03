/**
 * PaginationControls - 分页控件
 */
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
} from "../../components/ui/card";

export function PaginationControls({ pagination, setPagination }) {
  if (pagination.total <= pagination.page_size) {
    return null;
  }

  return (
    <Card>
      <CardContent className="flex items-center justify-between py-4">
        <div className="text-sm text-gray-500">
          共 {pagination.total} 条记录，第 {pagination.page} /{" "}
          {Math.ceil(pagination.total / pagination.page_size)} 页
        </div>
        <div className="flex gap-2">
          <Button
          variant="outline"
          size="sm"
          onClick={() =>
          setPagination((prev) => ({
            ...prev,
            page: Math.max(1, prev.page - 1)
          }))
          }
          disabled={pagination.page === 1}>

            上一页
          </Button>
          <Button
          variant="outline"
          size="sm"
          onClick={() =>
          setPagination((prev) => ({
            ...prev,
            page: Math.min(
              Math.ceil(prev.total / prev.page_size),
              prev.page + 1
            )
          }))
          }
          disabled={
          pagination.page >=
          Math.ceil(pagination.total / pagination.page_size)
          }>

            下一页
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
