/**
 * Assembly Attributes Table - 物料装配属性配置表格
 */
import { Package } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
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
import { Switch } from "../../components/ui/switch";
import { cn } from "../../lib/utils";
import { stageOptions, importanceOptions, getStageOption } from "./constants";

export function AssemblyAttrsTable({
  selectedBom,
  loading,
  assemblyAttrs,
  filteredAttrs,
  editedAttrs,
  searchText,
  handleAttrChange,
}) {
  if (!selectedBom) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center text-slate-400">
            <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>请先选择项目和BOM</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>物料装配属性配置</CardTitle>
        <CardDescription>
          共 {filteredAttrs.length} 条记录
          {searchText && ` (搜索: ${searchText})`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredAttrs.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">物料编码</TableHead>
                <TableHead>物料名称</TableHead>
                <TableHead className="w-[80px]">需求数量</TableHead>
                <TableHead className="w-[150px]">装配阶段</TableHead>
                <TableHead className="w-[120px]">重要程度</TableHead>
                <TableHead className="w-[80px]">阻塞性</TableHead>
                <TableHead className="w-[80px]">可后补</TableHead>
                <TableHead className="w-[80px]">有替代</TableHead>
                <TableHead className="w-[80px]">安装顺序</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(filteredAttrs || []).map((attr) => {
                const edited = editedAttrs[attr.bom_item_id] || attr;
                const stageOpt = getStageOption(edited.assembly_stage);

                return (
                  <TableRow key={attr.id || attr.bom_item_id}>
                    <TableCell className="font-mono text-sm">
                      {attr.material_code}
                    </TableCell>
                    <TableCell>{attr.material_name}</TableCell>
                    <TableCell>{attr.required_qty}</TableCell>
                    <TableCell>
                      <Select
                        value={edited.assembly_stage || "MECH"}
                        onValueChange={(v) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "assembly_stage",
                            v
                          )
                        }
                      >
                        <SelectTrigger className="h-8">
                          <SelectValue>
                            <div className="flex items-center gap-1">
                              <div
                                className={cn(
                                  "w-3 h-3 rounded-full",
                                  stageOpt.color
                                )}
                              />
                              <span className="text-sm">
                                {stageOpt.label}
                              </span>
                            </div>
                          </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          {(stageOptions || []).map((stage) => (
                            <SelectItem
                              key={stage.value}
                              value={stage.value}
                            >
                              <div className="flex items-center gap-2">
                                <div
                                  className={cn(
                                    "w-3 h-3 rounded-full",
                                    stage.color
                                  )}
                                />
                                {stage.label}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Select
                        value={edited.importance_level || "NORMAL"}
                        onValueChange={(v) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "importance_level",
                            v
                          )
                        }
                      >
                        <SelectTrigger className="h-8">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(importanceOptions || []).map((imp) => (
                            <SelectItem key={imp.value} value={imp.value}>
                              <Badge className={imp.color}>
                                {imp.label}
                              </Badge>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={edited.is_blocking ?? true}
                        onCheckedChange={(v) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "is_blocking",
                            v
                          )
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={edited.can_postpone ?? false}
                        onCheckedChange={(v) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "can_postpone",
                            v
                          )
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={edited.has_substitute ?? false}
                        onCheckedChange={(v) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "has_substitute",
                            v
                          )
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        className="h-8 w-16"
                        value={edited.stage_order || 0}
                        onChange={(e) =>
                          handleAttrChange(
                            attr.bom_item_id,
                            "stage_order",
                            parseInt(e.target.value) || 0
                          )
                        }
                        min={0}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 text-slate-400">
            {assemblyAttrs.length === 0
              ? '暂无装配属性配置，请使用"自动分配"或"套用模板"初始化'
              : "没有匹配的记录"}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
