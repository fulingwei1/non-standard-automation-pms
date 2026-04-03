/**
 * LevelsTab - 等级管理标签页
 */
import { useNavigate } from "react-router-dom";
import { Eye, Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { Checkbox } from "../../components/ui/checkbox";
import { getLevelBadgeColor } from "./constants";

export function LevelsTab({
  levels,
  levelFilter,
  setLevelFilter,
  selectedLevels,
  setSelectedLevels,
  onDeleteLevel,
}) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Select
          value={levelFilter.role_type}
          onValueChange={(value) =>
          setLevelFilter({ ...levelFilter, role_type: value })
          }>

          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="筛选角色类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="ENGINEER">工程师</SelectItem>
            <SelectItem value="SALES">销售</SelectItem>
            <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
            <SelectItem value="WORKER">生产工人</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={levelFilter.is_active?.toString()}
          onValueChange={(value) =>
          setLevelFilter({
            ...levelFilter,
            is_active: value === "true"
          })
          }>

          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="true">启用</SelectItem>
            <SelectItem value="false">停用</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={
                selectedLevels.length === levels.length &&
                levels.length > 0
                }
                onCheckedChange={(checked) => {
                  if (checked) {
                    setSelectedLevels((levels || []).map((l) => l.id));
                  } else {
                    setSelectedLevels([]);
                  }
                }} />

            </TableHead>
            <TableHead>等级编码</TableHead>
            <TableHead>等级名称</TableHead>
            <TableHead>排序</TableHead>
            <TableHead>适用角色</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(levels || []).map((level) =>
          <TableRow key={level.id}>
              <TableCell>
                <Checkbox
                checked={selectedLevels.includes(level.id)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    setSelectedLevels([...selectedLevels, level.id]);
                  } else {
                    setSelectedLevels(
                      (selectedLevels || []).filter((id) => id !== level.id)
                    );
                  }
                }} />

              </TableCell>
              <TableCell>
                <Badge className={getLevelBadgeColor(level.level_code)}>
                  {level.level_code}
                </Badge>
              </TableCell>
              <TableCell className="font-medium">
                {level.level_name}
              </TableCell>
              <TableCell>{level.level_order}</TableCell>
              <TableCell>{level.role_type || "通用"}</TableCell>
              <TableCell>
                {level.is_active ?
              <Badge className="bg-green-100 text-green-800">
                    启用
              </Badge> :

              <Badge className="bg-gray-100 text-gray-800">
                    停用
              </Badge>
              }
              </TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                  navigate(`/qualifications/levels/${level.id}`)
                  }
                  title="查看详情">

                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                  navigate(
                    `/qualifications/levels/${level.id}/edit`
                  )
                  }
                  title="编辑">

                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDeleteLevel(level.id)}>

                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
          </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
