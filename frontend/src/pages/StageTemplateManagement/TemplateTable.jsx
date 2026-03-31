import { motion, AnimatePresence } from "framer-motion";
import {
  Layers,
  Edit3,
  Trash2,
  Copy,
  Star,
  Eye,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
import { Switch } from "../../components/ui/switch";
import { cn } from "../../lib/utils";
import { PROJECT_TYPES } from "./constants";

export default function TemplateTable({
  loading,
  filteredTemplates,
  onView,
  onEdit,
  onCopy,
  onDelete,
  onToggleActive,
}) {
  return (
    <Card className="bg-surface-100 border-white/5">
      <CardHeader className="border-b border-white/5">
        <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
          <Layers className="h-5 w-5 text-violet-400" />
          模板列表
          <Badge variant="secondary" className="ml-2">
            {filteredTemplates.length} 项
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className="text-slate-400">模板编码</TableHead>
                <TableHead className="text-slate-400">模板名称</TableHead>
                <TableHead className="text-slate-400">项目类型</TableHead>
                <TableHead className="text-slate-400">描述</TableHead>
                <TableHead className="text-slate-400 text-center">阶段/节点</TableHead>
                <TableHead className="text-slate-400 text-center">默认</TableHead>
                <TableHead className="text-slate-400 text-center">状态</TableHead>
                <TableHead className="text-slate-400 text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <AnimatePresence>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-10">
                      <div className="flex items-center justify-center gap-2 text-slate-400">
                        <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-violet-500" />
                        加载中...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : filteredTemplates.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-10 text-slate-400">
                      暂无数据
                    </TableCell>
                  </TableRow>
                ) : (
                  (filteredTemplates || []).map((template, index) => (
                    <motion.tr
                      key={template.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: index * 0.03 }}
                      className="border-white/5 hover:bg-white/[0.02]"
                    >
                      <TableCell>
                        <code className="text-sm font-mono text-slate-300 bg-white/5 px-2 py-0.5 rounded">
                          {template.template_code}
                        </code>
                      </TableCell>
                      <TableCell>
                        <span className="text-white font-medium">{template.template_name}</span>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "border",
                            PROJECT_TYPES[template.project_type]?.color ||
                              PROJECT_TYPES.STANDARD.color
                          )}
                        >
                          {PROJECT_TYPES[template.project_type]?.label || "未知"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-slate-400 text-sm line-clamp-1 max-w-[250px]">
                          {template.description || "-"}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-3">
                          <span className="text-blue-400 font-medium">{template.stage_count || 0}</span>
                          <span className="text-slate-600">/</span>
                          <span className="text-purple-400 font-medium">{template.node_count || 0}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {template.is_default ? (
                          <div className="flex items-center justify-center">
                            <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
                          </div>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <Switch
                          checked={template.is_active}
                          onCheckedChange={() => onToggleActive(template)}
                          className="data-[state=checked]:bg-emerald-500"
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => onView(template)}
                            title="查看详情"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => onEdit(template)}
                            title="编辑"
                          >
                            <Edit3 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => onCopy(template)}
                            title="复制"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => onDelete(template)}
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </motion.tr>
                  ))
                )}
              </AnimatePresence>
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
