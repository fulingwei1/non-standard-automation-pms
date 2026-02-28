import React from "react";
import { BarChart3, Eye, Edit3, Trash2 } from "lucide-react";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";

export function CustomerTable({
    customers,
    loading,
    total,
    page,
    pageSize,
    setPage,
    onViewDetail,
    onView360,
    onEdit,
    onDelete
}) {
    return (
        <div className="p-6 pt-0">
            {loading ? (
                <div className="p-4 text-center text-muted-foreground">Loading...</div>
            ) : (
                <>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-border">
                            <thead>
                                <tr className="bg-muted/50">
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        客户编码
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        客户名称
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        简称
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        行业
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        联系人
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        状态
                                    </th>
                                    <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                                        操作
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {(customers || []).map((customer) => (
                                    <tr key={customer.id}>
                                        <td className="px-4 py-2 text-sm text-foreground font-mono">
                                            {customer.customer_code}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-foreground">
                                            {customer.customer_name}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-muted-foreground">
                                            {customer.customer_short_name || "-"}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-muted-foreground">
                                            {customer.industry || "-"}
                                        </td>
                                        <td className="px-4 py-2 text-sm text-muted-foreground">
                                            <div>{customer.contact_person || "-"}</div>
                                            {customer.contact_phone && (
                                                <div className="text-xs text-muted-foreground">
                                                    {customer.contact_phone}
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-4 py-2 text-sm">
                                            <Badge
                                                variant={customer.is_active ? "default" : "secondary"}
                                            >
                                                {customer.is_active ? "启用" : "禁用"}
                                            </Badge>
                                        </td>
                                        <td className="px-4 py-2 text-sm">
                                            <div className="flex items-center space-x-2">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => onView360(customer.id)}
                                                    title="客户360视图"
                                                >
                                                    <BarChart3 className="h-4 w-4 text-blue-600" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => onViewDetail(customer.id)}
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => onEdit(customer.id)}
                                                >
                                                    <Edit3 className="h-4 w-4" />
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => onDelete(customer.id)}
                                                >
                                                    <Trash2 className="h-4 w-4 text-red-500" />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {customers.length === 0 && (
                        <p className="p-4 text-center text-muted-foreground">
                            没有找到符合条件的客户。
                        </p>
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
                                    onClick={() =>
                                        setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
                                    }
                                    disabled={page >= Math.ceil(total / pageSize)}
                                >
                                    下一页
                                </Button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
