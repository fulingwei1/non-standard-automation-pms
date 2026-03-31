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
 * SubstitutionsTab
 *
 * Renders the 物料替代 (material substitution) applications list.
 *
 * Props:
 *   substitutions — array of substitution objects
 *   loading       — boolean
 */
export function SubstitutionsTab({ substitutions, loading }) {
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>物料替代</CardTitle>
            <CardDescription>物料替代申请记录</CardDescription>
          </div>
          <Button onClick={() => navigate("/shortage/substitutions/new")}>
            <Plus className="h-4 w-4 mr-2" />
            新建申请
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-muted-foreground">加载中...</div>
        ) : substitutions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            暂无物料替代申请
          </div>
        ) : (
          <div className="space-y-3">
            {substitutions.map((sub) => (
              <div
                key={sub.id}
                className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium">{sub.substitution_no}</span>
                    <Badge variant="outline">{sub.status}</Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {sub.original_material_name} → {sub.substitute_material_name}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {sub.project_name} | 原因: {sub.substitution_reason}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    navigate(`/shortage/substitutions/${sub.id}`)
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
