import { Eye, Edit } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { getMaterialTypeLabel } from "../../components/material-readiness";
import { formatDate } from "../../lib/utils";
import { getStatusBadge, getPriorityBadge, getTypeIcon } from "./BadgeHelpers";

export default function MaterialListView({ loading, materials, onViewMaterial }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>物料列表</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>物料名称</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>数量</TableHead>
                <TableHead>预计到货</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    加载中...
                  </TableCell>
                </TableRow>
              ) : materials?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    暂无物料数据
                  </TableCell>
                </TableRow>
              ) : (
                (materials || []).map((material) => (
                  <TableRow key={material.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center space-x-2">
                        {getTypeIcon(material.type)}
                        <span>{material.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getMaterialTypeLabel(material.type)}
                    </TableCell>
                    <TableCell>{getStatusBadge(material.status)}</TableCell>
                    <TableCell>{getPriorityBadge(material.priority)}</TableCell>
                    <TableCell>
                      {material.quantity} {material.unit}
                    </TableCell>
                    <TableCell>
                      {material.expected_date
                        ? formatDate(material.expected_date)
                        : "-"}
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewMaterial(material)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
