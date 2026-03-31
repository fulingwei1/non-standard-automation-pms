/**
 * ModelsTab - 能力模型管理标签页
 */
import { useNavigate } from "react-router-dom";
import { Eye, Edit, Search, Download } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Input } from "../../components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { formatDate } from "../../lib/utils";

export function ModelsTab({
  models,
  modelFilter,
  setModelFilter,
  modelSearch,
  setModelSearch,
  setPagination,
  loadModels,
  onExportModels,
}) {
  const navigate = useNavigate();

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="搜索岗位类型、子类型..."
            value={modelSearch || "unknown"}
            onChange={(e) => setModelSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPagination((prev) => ({ ...prev, page: 1 }));
                loadModels();
              }
            }}
            className="pl-10" />

        </div>
        <Button
          variant="outline"
          onClick={() => {
            setModelSearch("");
            setPagination((prev) => ({ ...prev, page: 1 }));
            loadModels();
          }}>

          <Search className="h-4 w-4 mr-2" />
          搜索
        </Button>
        <Button variant="outline" onClick={onExportModels}>
          <Download className="h-4 w-4 mr-2" />
          导出
        </Button>
      </div>
      <div className="flex gap-2">
        <Select
          value={modelFilter.position_type}
          onValueChange={(value) =>
          setModelFilter({ ...modelFilter, position_type: value })
          }>

          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="筛选岗位类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="ENGINEER">工程师</SelectItem>
            <SelectItem value="SALES">销售</SelectItem>
            <SelectItem value="CUSTOMER_SERVICE">客服</SelectItem>
            <SelectItem value="WORKER">生产工人</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>岗位类型</TableHead>
            <TableHead>子类型</TableHead>
            <TableHead>等级</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(models || []).map((model) =>
          <TableRow key={model.id}>
              <TableCell>{model.position_type}</TableCell>
              <TableCell>{model.position_subtype || "-"}</TableCell>
              <TableCell>
                <Badge>
                  {model.level?.level_name || model.level_id}
                </Badge>
              </TableCell>
              <TableCell>
                {model.created_at ? formatDate(model.created_at) : "-"}
              </TableCell>
              <TableCell>
                {model.is_active ?
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
                  navigate(`/qualifications/models/${model.id}`)
                  }
                  title="查看详情">

                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                  navigate(
                    `/qualifications/models/${model.id}/edit`
                  )
                  }
                  title="编辑">

                    <Edit className="h-4 w-4" />
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
