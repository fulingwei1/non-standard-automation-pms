import { formatDate, formatCurrency } from "../../lib/utils";
import { Card, CardContent, Button, Progress } from "../../components/ui";
import { FileText, Download, Plus } from "lucide-react";

export default function BudgetTab({
  normalizedProject: p,
  costs,
  documents,
  budgetUtilization,
  onOpenAddMember,
}) {
  const totalCosts = (costs || []).reduce((sum, c) => sum + (c.amount || 0), 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 预算概览 */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">预算概览</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">项目预算</span>
                <span className="font-bold">{formatCurrency(p.budget)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">已使用</span>
                <span className="font-bold">{formatCurrency(totalCosts)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">使用率</span>
                <span className="font-bold">{budgetUtilization}%</span>
              </div>
              <Progress value={budgetUtilization} className="mt-2" />
            </div>
          </CardContent>
        </Card>

        {/* 成本明细 */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">成本明细</h3>
              <Button variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                添加成本
              </Button>
            </div>
            <div className="space-y-2">
              {(costs || []).slice(0, 5).map((cost) => (
                <div key={cost.id} className="flex justify-between py-2 border-b">
                  <span>{cost.name || cost.description}</span>
                  <span className="font-medium">{formatCurrency(cost.amount)}</span>
                </div>
              ))}
              {costs.length === 0 && (
                <p className="text-center text-gray-500 py-4">暂无成本记录</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 项目文档 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">项目文档</h3>
            <Button variant="outline" size="sm" onClick={onOpenAddMember}>
              <Plus className="mr-2 h-4 w-4" />
              上传文档
            </Button>
          </div>
          <div className="space-y-3">
            {(documents || []).map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 border rounded"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="font-medium">{doc.name}</p>
                    <p className="text-sm text-gray-600">{doc.type}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">{formatDate(doc.created_at)}</span>
                  <Button variant="ghost" size="sm">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
            {documents?.length === 0 && (
              <p className="text-center text-gray-500 py-4">暂无文档</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
