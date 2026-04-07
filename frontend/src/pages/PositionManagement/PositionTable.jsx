





import { fadeIn } from "../../lib/animations";
import { POSITION_CATEGORIES, getCategoryConfig } from "./categoryConstants";

export default function PositionTable({
  positions,
  loading,
  searchKeyword,
  setSearchKeyword,
  filterCategory,
  setFilterCategory,
  total,
  page,
  setPage,
  pageSize,
  onView,
  onEdit,
  onRoleMapping,
  onDelete,
}) {
  return (
    <motion.div variants={fadeIn}>
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>岗位列表</CardTitle>
          <div className="flex items-center space-x-2">
            <Input
              placeholder="搜索岗位名称/编码..."
              value={searchKeyword || "unknown"}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="max-w-sm"
            />
            <Select value={filterCategory || "unknown"} onValueChange={setFilterCategory}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="筛选类别" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有类别</SelectItem>
                {POSITION_CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">加载中...</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                  <thead>
                    <tr className="bg-muted/50">
                      <th className="px-4 py-2 text-left text-sm font-semibold">岗位编码</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">岗位名称</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">类别</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">所属组织</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">默认角色</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">状态</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {(positions || []).map((position) => {
                      const catConfig = getCategoryConfig(position.position_category);
                      return (
                        <tr key={position.id}>
                          <td className="px-4 py-2 text-sm font-mono">{position.position_code}</td>
                          <td className="px-4 py-2 text-sm font-medium">{position.position_name}</td>
                          <td className="px-4 py-2 text-sm">
                            <Badge variant="outline" className={catConfig.color}>
                              {catConfig.label}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {position.org_unit_name || "-"}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex flex-wrap gap-1">
                              {position.roles?.length > 0 ? (
                                position.roles.slice(0, 3).map((role, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs">
                                    {role.role_name || role}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-muted-foreground">未配置</span>
                              )}
                              {position.roles?.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{position.roles?.length - 3}
                                </Badge>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <Badge variant={position.is_active ? "default" : "secondary"}>
                              {position.is_active ? "启用" : "禁用"}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-1">
                              <Button variant="ghost" size="sm" onClick={() => onView(position)}>
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => onEdit(position)}>
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onRoleMapping(position)}
                                title="配置角色映射"
                                className="text-blue-600 hover:text-blue-700"
                              >
                                <Link2 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive"
                                onClick={() => onDelete(position)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {positions.length === 0 && (
                <div className="p-8 text-center text-muted-foreground">
                  <Briefcase className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>暂无岗位数据</p>
                  <p className="text-sm mt-2">点击"新增岗位"开始创建岗位</p>
                </div>
              )}
              {total > pageSize && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                      disabled={page >= Math.ceil(total / pageSize)}
                    >
                      下一页
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
