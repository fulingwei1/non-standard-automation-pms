import { cn } from "../../lib/utils";
import { getLevelColor, getStatusBadgeClass, getStatusLabel } from "./utils";

export default function SupplierTable({
  suppliers,
  loading,
  total,
  page,
  pageSize,
  onPageChange,
  onViewDetail,
  onEdit,
  onRating,
}) {
  if (loading) {
    return (
      <div className="p-4 text-center text-slate-400">加载中...</div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border">
          <thead>
            <tr className="bg-slate-900/50 border-b border-slate-700">
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                供应商编码
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                供应商名称
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                类型
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                联系人
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                综合评分
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                等级
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                状态
              </th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-slate-400">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {(suppliers || []).map((supplier) => (
              <tr key={supplier.id} className="hover:bg-slate-800/30">
                <td className="px-4 py-2 text-sm text-slate-200 font-mono">
                  {supplier.supplier_code}
                </td>
                <td className="px-4 py-2 text-sm text-slate-200">
                  {supplier.supplier_name}
                </td>
                <td className="px-4 py-2 text-sm text-slate-400">
                  {supplier.supplier_type || "-"}
                </td>
                <td className="px-4 py-2 text-sm text-slate-300">
                  <div>{supplier.contact_person || "-"}</div>
                  {supplier.contact_phone && (
                    <div className="text-xs text-slate-500">
                      {supplier.contact_phone}
                    </div>
                  )}
                </td>
                <td className="px-4 py-2 text-sm">
                  {supplier.overall_rating ? (
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      <span className="text-slate-200">
                        {parseFloat(supplier.overall_rating).toFixed(1)}
                      </span>
                    </div>
                  ) : (
                    <span className="text-slate-500">-</span>
                  )}
                </td>
                <td className="px-4 py-2 text-sm">
                  {supplier.supplier_level && (
                    <Badge
                      className={cn(
                        "text-white",
                        getLevelColor(supplier.supplier_level)
                      )}
                    >
                      {supplier.supplier_level}级
                    </Badge>
                  )}
                </td>
                <td className="px-4 py-2 text-sm">
                  <Badge className={getStatusBadgeClass(supplier.status)}>
                    {getStatusLabel(supplier.status)}
                  </Badge>
                </td>
                <td className="px-4 py-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDetail(supplier.id)}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(supplier.id)}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      <Edit3 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRating(supplier.id)}
                      title="评级"
                      className="text-slate-400 hover:text-slate-200"
                    >
                      <Award className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {suppliers.length === 0 && (
        <p className="p-4 text-center text-slate-400">
          没有找到符合条件的供应商。
        </p>
      )}
      {total > pageSize && (
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-slate-400">
            共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                onPageChange(Math.min(Math.ceil(total / pageSize), page + 1))
              }
              disabled={page >= Math.ceil(total / pageSize)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
