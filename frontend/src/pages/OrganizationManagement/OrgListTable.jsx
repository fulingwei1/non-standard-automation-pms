import { Edit3, Trash2, Eye } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { getUnitTypeConfig } from "./unitTypeConfig";

export default function OrgListTable({ orgList, onView, onEdit, onDelete }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-border">
        <thead>
          <tr className="bg-muted/50">
            <th className="px-4 py-2 text-left text-sm font-semibold">组织编码</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">组织名称</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">类型</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">上级组织</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">负责人</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">状态</th>
            <th className="px-4 py-2 text-left text-sm font-semibold">操作</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {(orgList || []).map((unit) => {
            const typeConfig = getUnitTypeConfig(unit.unit_type);
            const Icon = typeConfig.icon;
            return (
              <tr key={unit.id}>
                <td className="px-4 py-2 text-sm font-mono">{unit.unit_code}</td>
                <td className="px-4 py-2 text-sm font-medium">{unit.unit_name}</td>
                <td className="px-4 py-2 text-sm">
                  <Badge variant="outline" className={typeConfig.color}>
                    <Icon className="h-3 w-3 mr-1" />
                    {typeConfig.label}
                  </Badge>
                </td>
                <td className="px-4 py-2 text-sm text-muted-foreground">
                  {unit.parent_name || "-"}
                </td>
                <td className="px-4 py-2 text-sm text-muted-foreground">
                  {unit.manager_name || "-"}
                </td>
                <td className="px-4 py-2 text-sm">
                  <Badge variant={unit.is_active ? "default" : "secondary"}>
                    {unit.is_active ? "启用" : "禁用"}
                  </Badge>
                </td>
                <td className="px-4 py-2 text-sm">
                  <div className="flex items-center space-x-1">
                    <Button variant="ghost" size="sm" onClick={() => onView(unit)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => onEdit(unit)}>
                      <Edit3 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive"
                      onClick={() => onDelete(unit)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {orgList.length === 0 && (
        <p className="p-4 text-center text-muted-foreground">没有找到符合条件的组织单元</p>
      )}
    </div>
  );
}
