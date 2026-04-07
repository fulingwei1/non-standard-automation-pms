


export default function ContractTab({
  contractTemplates,
  loading,
  onShowDialog,
  onPublish,
  onReload,
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">合同条款模板</h3>
          <p className="text-sm text-muted-foreground">
            快速复用标准条款、审批流与附件清单，保障 G4 交付质量。
          </p>
        </div>
        <Button onClick={onShowDialog}>新增合同模板</Button>
      </div>
      {contractTemplates.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          尚未配置合同模板。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {(contractTemplates || []).map((template) => (
          <Card key={template.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span>{template.template_name}</span>
                <Badge variant="outline">{template.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between text-muted-foreground">
                <span>类型: {template.contract_type || "-"}</span>
                <span>范围: {template.visibility_scope}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                最新版本: {template.current_version_id || "未发布"}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onPublish(template)}
                >
                  <UploadCloud className="w-4 h-4 mr-1" /> 发布
                </Button>
                <Button size="sm" onClick={onReload}>
                  <FileText className="w-4 h-4 mr-1" /> 同步条款
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
                        {version.release_notes || "暂无说明"}
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
