import { Eye, CheckSquare } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { formatDate } from "../../lib/utils";
import { typeConfigs } from "./constants";

export default function TemplateTable({
  loading,
  filteredTemplates,
  onViewDetail,
  onViewItems,
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>验收模板列表</CardTitle>
        <CardDescription>共 {filteredTemplates.length} 个模板</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无模板</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>模板名称</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>分类</TableHead>
                <TableHead>版本</TableHead>
                <TableHead>检查项数</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTemplates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell className="font-medium">
                    {template.template_name}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        typeConfigs[template.template_type]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {typeConfigs[template.template_type]?.label ||
                        template.template_type}
                    </Badge>
                  </TableCell>
                  <TableCell>{template.category || "-"}</TableCell>
                  <TableCell>{template.version || "1.0"}</TableCell>
                  <TableCell>{template.item_count || 0}</TableCell>
                  <TableCell className="text-slate-500 text-sm">
                    {template.created_at ? formatDate(template.created_at) : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(template.id)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewItems(template.id)}
                      >
                        <CheckSquare className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
