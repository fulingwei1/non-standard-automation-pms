import React from "react";
import { Save } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from "../../components/ui/table";
import { Input } from "../../components/ui/input";
import { formatCurrency } from "../../lib/utils";

export function CostBreakdown({
  groupedItems,
  items,
  onSave,
  onItemChange
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>成本明细</CardTitle>
            <CardDescription>
              编辑成本项，系统将自动计算总成本和毛利率
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onSave}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {Object.entries(groupedItems).map(([category, categoryItems]) => (
          <div key={category} className="mb-6">
            <h3 className="text-lg font-semibold mb-3 text-slate-300">
              {category}
            </h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>项目名称</TableHead>
                  <TableHead>规格型号</TableHead>
                  <TableHead>单位</TableHead>
                  <TableHead>数量</TableHead>
                  <TableHead>单价</TableHead>
                  <TableHead>成本</TableHead>
                  <TableHead>小计</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(categoryItems || []).map((item) => {
                  const subtotal =
                    parseFloat(item.unit_price || 0) *
                    parseFloat(item.qty || 0);
                  const costSubtotal =
                    parseFloat(item.cost || 0) * parseFloat(item.qty || 0);
                  return (
                    <TableRow key={item.id}>
                      <TableCell>{item.item_name}</TableCell>
                      <TableCell>{item.specification || "-"}</TableCell>
                      <TableCell>{item.unit || "-"}</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          value={item.qty || ""}
                          onChange={(e) =>
                            onItemChange(item.id, "qty", e.target.value)
                          }
                          className="w-20"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          value={item.unit_price || ""}
                          onChange={(e) =>
                            onItemChange(item.id, "unit_price", e.target.value)
                          }
                          className="w-24"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          value={item.cost || ""}
                          onChange={(e) =>
                            onItemChange(item.id, "cost", e.target.value)
                          }
                          className="w-24"
                        />
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="text-sm">
                            {formatCurrency(subtotal)}
                          </div>
                          <div className="text-xs text-slate-500">
                            成本: {formatCurrency(costSubtotal)}
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ))}

        {items?.length === 0 && (
          <div className="text-center py-8 text-slate-400">
            暂无成本明细，请应用成本模板或手动添加
          </div>
        )}
      </CardContent>
    </Card>
  );
}
