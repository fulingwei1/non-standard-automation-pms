/**
 * Organization tree view component
 * Displays the full org hierarchy with a detail panel
 */

import { useState, useEffect } from "react";




import { salesTeamApi } from "../../services/api";

export default function OrganizationTree() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [orgTree, setOrgTree] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadOrg = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await salesTeamApi.getOrg();
        const data = res.formatted || res.data?.data || res.data || {};
        setOrgTree(data.organization_tree || null);
      } catch (err) {
        console.error("加载组织架构失败:", err);
        setError("加载组织架构数据失败，请稍后重试");
        setOrgTree(null);
      } finally {
        setLoading(false);
      }
    };
    loadOrg();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-slate-400">加载组织架构中...</CardContent>
      </Card>
    );
  }

  if (error || !orgTree) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-slate-400">
          {error || "暂无组织架构数据，请先创建销售团队"}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Organization tree */}
      <Card>
        <CardHeader>
          <CardTitle>销售组织架构</CardTitle>
          <CardDescription>点击节点查看详情，4层层级：总经理 → 总监 → 经理 → 销售</CardDescription>
        </CardHeader>
        <CardContent>
          <OrgNode node={orgTree} level={0} onSelect={setSelectedNode} selectedId={selectedNode?.id} />
        </CardContent>
      </Card>

      {/* Selected node detail */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedNode ? (
              <div className="flex items-center gap-2">
                {selectedNode.level === "GM" && <Briefcase className="w-5 h-5 text-purple-500" />}
                {selectedNode.level === "Director" && <Building2 className="w-5 h-5 text-blue-500" />}
                {selectedNode.level === "Manager" && <Users className="w-5 h-5 text-green-500" />}
                {selectedNode.level === "Sales" && <User className="w-5 h-5 text-slate-500" />}
                {selectedNode.name}
              </div>
            ) : (
              "选择节点查看详情"
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedNode ? (
            <div className="space-y-4">
              {selectedNode.person && (
                <div>
                  <div className="text-sm text-slate-400">负责人</div>
                  <div className="font-medium">{selectedNode.person.name} · {selectedNode.person.title}</div>
                </div>
              )}

              {selectedNode.metrics && (
                <>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">业绩完成率</div>
                    <div className="flex items-center gap-3">
                      <span className={`text-3xl font-bold ${(selectedNode.metrics.achievement_rate || selectedNode.metrics.rate) >= 70 ? 'text-green-500' : (selectedNode.metrics.achievement_rate || selectedNode.metrics.rate) >= 60 ? 'text-blue-500' : 'text-orange-500'}`}>
                        {selectedNode.metrics.achievement_rate || selectedNode.metrics.rate}%
                      </span>
                      <Progress value={selectedNode.metrics.achievement_rate || selectedNode.metrics.rate} className="flex-1" />
                    </div>
                  </div>

                  {selectedNode.metrics.achieved_ytd && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-slate-400">已完成</div>
                        <div className="text-lg font-bold">¥{(selectedNode.metrics.achieved_ytd / 1000000).toFixed(1)}M</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400">年度指标</div>
                        <div className="text-lg font-bold">¥{(selectedNode.metrics.quota_annual / 1000000).toFixed(0)}M</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400">团队人数</div>
                        <div className="text-lg font-bold">{selectedNode.metrics.team_size}人</div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {selectedNode.children && selectedNode.children.length > 0 && (
                <div>
                  <div className="text-sm text-slate-400 mb-2">下属团队/成员 ({selectedNode.children.length}个)</div>
                  <div className="space-y-2">
                    {selectedNode.children.map((child) => (
                      <div key={child.id} className="p-2 border rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{child.name}</span>
                          <Badge variant="outline">{child.level}</Badge>
                        </div>
                        {child.metrics && (
                          <div className="text-xs text-slate-400 mt-1">
                            完成率：<span className={(child.metrics.rate || child.metrics.achievement_rate) >= 70 ? 'text-green-500' : (child.metrics.rate || child.metrics.achievement_rate) >= 60 ? 'text-blue-500' : 'text-orange-500'}>{child.metrics.rate || child.metrics.achievement_rate}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-slate-400 py-8">
              <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <div>点击左侧组织节点查看详情</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
