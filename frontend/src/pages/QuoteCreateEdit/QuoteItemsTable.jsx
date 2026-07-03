/**
 * QuoteItemsTable - 报价明细表格
 */
import { Plus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { formatCurrency } from "../../lib/utils";

export default function QuoteItemsTable({ items, onAddItem, onRemoveItem, onItemChange }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>报价明细</CardTitle>
          <Button variant="outline" size="sm" onClick={onAddItem}>
            <Plus className="w-4 h-4 mr-2" />
            添加明细
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {items?.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <Button variant="outline" onClick={onAddItem}>
              <Plus className="w-4 h-4 mr-2" />
              添加第一条明细
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>序号</TableHead>
                  <TableHead>物料编码</TableHead>
                  <TableHead>物料名称</TableHead>
                  <TableHead>规格</TableHead>
                  <TableHead>数量</TableHead>
                  <TableHead>单位</TableHead>
                  <TableHead>单价</TableHead>
                  <TableHead>金额</TableHead>
                  <TableHead>成本</TableHead>
                  <TableHead>成本金额</TableHead>
                  <TableHead>材料成本</TableHead>
                  <TableHead>人工成本</TableHead>
                  <TableHead>制造费用</TableHead>
                  <TableHead>备注</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(items || []).map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>
                      <Input
                        value={item.item_code || ""}
                        onChange={(e) =>
                          onItemChange(index, "item_code", e.target.value)
                        }
                        placeholder="编码"
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={item.item_name || ""}
                        onChange={(e) =>
                          onItemChange(index, "item_name", e.target.value)
                        }
                        placeholder="名称"
                        className="w-32"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={item.specification || ""}
                        onChange={(e) =>
                          onItemChange(index, "specification", e.target.value)
                        }
                        placeholder="规格"
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.qty ?? ""}
                        onChange={(e) =>
                          onItemChange(index, "qty", parseFloat(e.target.value) || 0)
                        }
                        className="w-20"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={item.unit || ""}
                        onChange={(e) =>
                          onItemChange(index, "unit", e.target.value)
                        }
                        placeholder="单位"
                        className="w-16"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.unit_price ?? ""}
                        onChange={(e) =>
                          onItemChange(index, "unit_price", parseFloat(e.target.value) || 0)
                        }
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatCurrency(item.amount || 0)}
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.cost ?? ""}
                        onChange={(e) =>
                          onItemChange(index, "cost", parseFloat(e.target.value) || 0)
                        }
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatCurrency(item.cost_amount || 0)}
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.material_cost || 0}
                        onChange={(e) =>
                          onItemChange(index, "material_cost", parseFloat(e.target.value) || 0)
                        }
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.labor_cost || 0}
                        onChange={(e) =>
                          onItemChange(index, "labor_cost", parseFloat(e.target.value) || 0)
                        }
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={item.overhead_cost || 0}
                        onChange={(e) =>
                          onItemChange(index, "overhead_cost", parseFloat(e.target.value) || 0)
                        }
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        value={item.remark || ""}
                        onChange={(e) =>
                          onItemChange(index, "remark", e.target.value)
                        }
                        placeholder="备注"
                        className="w-24"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onRemoveItem(index)}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
