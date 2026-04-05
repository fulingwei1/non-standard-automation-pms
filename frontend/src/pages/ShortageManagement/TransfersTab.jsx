import { useNavigate } from "react-router-dom";
import { Plus, Eye } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";

/**
 * TransfersTab
 *
 * Renders the 物料调拨 (material transfer) applications list.
 *
 * Props:
 *   transfers — array of transfer objects
 *   loading   — boolean
 */
export function TransfersTab({ transfers, loading }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>物料调拨</CardTitle>
            <CardDescription>物料调拨申请记录</CardDescription>
          </div>
          <Button onClick={() => navigate("/shortage/transfers/new")}>
            <Plus className="h-4 w-4 mr-2" />
            新建申请
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">加载中...</div>
        ) : transfers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无物料调拨申请
          </div>
        ) : (
          <div className="space-y-3">
            {transfers.map((transfer) => (
              <div
                key={transfer.id}
                className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium">{transfer.transfer_no}</span>
                    <Badge variant="outline">{transfer.status}</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {transfer.from_project_name || "总库存"} →{" "}
                    {transfer.to_project_name}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {transfer.material_name} | 数量: {transfer.transfer_qty}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    navigate(`/shortage/transfers/${transfer.id}`)
                  }
                >
                  <Eye className="h-4 w-4 mr-2" />
                  查看
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
