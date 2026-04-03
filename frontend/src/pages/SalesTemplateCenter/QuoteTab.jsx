import { CheckCircle2, PenTool } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";

export default function QuoteTab({
  quoteTemplates,
  loading,
  onShowDialog,
  onPublish,
  onPreview,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">标准报价模板库</h3>
          <p className="text-sm text-muted-foreground">
            可复用的报价骨架与 CPQ 规则，支持多版本、审批与预测。
          </p>
        </div>
        <Button onClick={onShowDialog}>新增模板</Button>
      </div>
      {quoteTemplates.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          暂无模板，点击「新增模板」开始配置。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {(quoteTemplates || []).map((template) => (
          <Card key={template.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base">
                {template.template_name}
              </CardTitle>
              <Badge variant="outline">{template.status}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center text-sm text-muted-foreground justify-between">
                <span>编码: {template.template_code}</span>
                <span>可见范围: {template.visibility_scope}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                当前版本: {template.current_version_id || "未发布"}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onPublish(template)}
                >
                  <CheckCircle2 className="w-4 h-4 mr-1" /> 发布最新
                </Button>
                <Button
                  size="sm"
                  onClick={() => onPreview(template)}
                >
                  <PenTool className="w-4 h-4 mr-1" /> 应用/预测
                </Button>
              </div>
              <div className="space-y-2">
                {(template.versions || []).slice(0, 3).map((version) => (
                  <div
                    key={version.id}
                    className="border rounded-md p-2 text-xs flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium">{version.version_no}</div>
                      <div className="text-muted-foreground">
                        {version.release_notes || "未填写说明"}
                      </div>
                    </div>
                    <Badge variant="secondary">{version.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
