/**
 * Organization hierarchy definition card
 */



import { ORG_HIERARCHY } from "./constants";

export default function OrgHierarchyCard() {
  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>销售组织层级定义</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-4 gap-4">
          {ORG_HIERARCHY.map((item) => (
            <Card key={item.level}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline">{item.level}</Badge>
                  <span className="font-medium">{item.name}</span>
                </div>
                <div className="text-sm text-slate-400 space-y-1">
                  <div>范围：{item.scope}</div>
                  <div>汇报：{item.report}</div>
                  <div>管理：{item.manage}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
