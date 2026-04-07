
export default function AllClearState() {
  return (
    <Card className="mb-6">
      <CardContent className="py-12 text-center">
        <CheckCircle2 className="w-16 h-16 mx-auto mb-4 text-emerald-500" />
        <div className="text-xl font-semibold text-slate-900 mb-2">
          恭喜！没有发现依赖问题
        </div>
        <div className="text-slate-600">
          项目的依赖关系配置良好，可以正常执行。
        </div>
      </CardContent>
    </Card>
  );
}
