import { Search, Download, Plus, ChevronDown } from "lucide-react";
import { Card, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "../../../components/ui/select";
import { cn } from "../../../lib/utils";
import { ORDER_STATUS_CONFIGS } from "../../../components/purchase-orders";

export function OrdersControls({
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    onExport,
    onCreate
}) {
    return (
        <Card className="bg-surface-1 border-border mb-6">
            <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row gap-4 items-center">
                    {/* Search */}
                    <div className="flex-1">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
                            <Input
                                placeholder="搜索订单编号、供应商..."
                                value={searchQuery || "unknown"}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 bg-surface-2 border-border"
                            />
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="flex gap-2">
                        <Select value={statusFilter || "unknown"} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-40 bg-surface-2 border-border">
                                <SelectValue placeholder="订单状态" />
                            </SelectTrigger>
                            <SelectContent className="bg-surface-2 border-border">
                                <SelectItem value="all">全部状态</SelectItem>
                                {Object.entries(ORDER_STATUS_CONFIGS).map(([key, config]) => (
                                    <SelectItem key={key} value={key || "unknown"}>
                                        {config.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        <Select value={sortBy || "unknown"} onValueChange={setSortBy}>
                            <SelectTrigger className="w-32 bg-surface-2 border-border">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-surface-2 border-border">
                                <SelectItem value="expected_date">到货日期</SelectItem>
                                <SelectItem value="totalAmount">订单金额</SelectItem>
                                <SelectItem value="createdDate">创建日期</SelectItem>
                            </SelectContent>
                        </Select>

                        <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                            className="bg-surface-2 border-border"
                        >
                            <ChevronDown className={cn("h-4 w-4 transition-transform", sortOrder === "asc" && "rotate-180")} />
                        </Button>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={onExport} className="bg-surface-2 border-border">
                            <Download className="h-4 w-4 mr-2" />
                            导出
                        </Button>
                        <Button onClick={onCreate} className="bg-accent hover:bg-accent/90">
                            <Plus className="h-4 w-4 mr-2" />
                            新建订单
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
