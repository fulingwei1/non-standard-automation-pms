/**
 * Template preview dialog component
 */

import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { formatCurrency } from "../../lib/utils";

export default function TemplatePreviewDialog({
  open,
  onOpenChange,
  template,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>模板预览</DialogTitle>
          <DialogDescription>{template?.template_name}</DialogDescription>
        </DialogHeader>

        {template && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>模板编码:</strong> {template.template_code}
              </div>
              <div>
                <strong>模板类型:</strong> {template.template_type}
              </div>
              <div>
                <strong>设备类型:</strong>{" "}
                {template.equipment_type || "-"}
              </div>
              <div>
                <strong>总成本:</strong>{" "}
                {formatCurrency(template.total_cost || 0)}
              </div>
            </div>

            {template.cost_structure && (
              <div className="space-y-4">
                {template.cost_structure.categories?.map(
                  (category, catIndex) => (
                    <div
                      key={catIndex}
                      className="border border-slate-700 rounded-lg p-4"
                    >
                      <h4 className="font-semibold mb-2">
                        {category.category}
                      </h4>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>项目名称</TableHead>
                            <TableHead>规格型号</TableHead>
                            <TableHead>单位</TableHead>
                            <TableHead>数量</TableHead>
                            <TableHead>单价</TableHead>
                            <TableHead>成本</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {category.items?.map((item, itemIndex) => (
                            <TableRow key={itemIndex}>
                              <TableCell>{item.item_name}</TableCell>
                              <TableCell>
                                {item.specification || "-"}
                              </TableCell>
                              <TableCell>{item.unit || "-"}</TableCell>
                              <TableCell>{item.default_qty}</TableCell>
                              <TableCell>
                                {formatCurrency(item.default_unit_price || 0)}
                              </TableCell>
                              <TableCell>
                                {formatCurrency(item.default_cost || 0)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
