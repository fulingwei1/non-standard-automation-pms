/**
 * Individual template card component
 */





import { formatCurrency } from "../../lib/utils";
import { TEMPLATE_TYPE_LABEL_MAP } from "./constants";

export default function TemplateCard({
  template,
  onPreview,
  onEdit,
  onDelete,
}) {
  return (
    <Card className="hover:border-slate-600 transition-colors">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">
              {template.template_name}
            </CardTitle>
            <CardDescription className="mt-1">
              {template.template_code}
            </CardDescription>
          </div>
          <Badge
            className={template.is_active ? "bg-green-500" : "bg-slate-500"}
          >
            {template.is_active ? "启用" : "禁用"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            <span>
              类型:{" "}
              {TEMPLATE_TYPE_LABEL_MAP[template.template_type] || template.template_type}
            </span>
          </div>
          {template.equipment_type && (
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span>设备: {template.equipment_type}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            <span>总成本: {formatCurrency(template.total_cost || 0)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span>使用次数: {template.usage_count || 0}</span>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPreview(template)}
            className="flex-1"
          >
            <Eye className="h-4 w-4 mr-1" />
            预览
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(template)}
            className="flex-1"
          >
            <Edit className="h-4 w-4 mr-1" />
            编辑
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onDelete(template)}
            className="text-red-400 hover:text-red-300"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
