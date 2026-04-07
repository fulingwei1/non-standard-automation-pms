
export function DemoAccountBanner() {
  return (
    <Card className="border-amber-500/50 bg-amber-500/10">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Shield className="h-8 w-8 text-amber-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-amber-400 mb-2">
              演示账号限制
            </h3>
            <p className="text-slate-300 mb-4">
              权限管理功能需要连接真实的后端服务，演示账号无法访问此功能。
              如需使用权限管理功能，请使用真实账号登录。
            </p>
            <div className="flex gap-3">
              <Button
                onClick={() => {
                  localStorage.removeItem("token");
                  localStorage.removeItem("user");
                  window.location.href = "/";
                }}
                className="bg-amber-500 hover:bg-amber-600 text-white"
              >
                切换到真实账号登录
              </Button>
              <Button
                variant="outline"
                onClick={() => window.history.back()}
                className="border-slate-600 text-slate-300 hover:bg-slate-800"
              >
                返回上一页
              </Button>
            </div>
            <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
              <p className="text-xs text-slate-400 mb-1">提示：</p>
              <p className="text-xs text-slate-400">
                真实账号需要后端服务支持。请使用数据库中的真实用户账号登录（如：admin/admin）。
                如果后端服务未启动或数据库中没有用户，请联系系统管理员。
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
