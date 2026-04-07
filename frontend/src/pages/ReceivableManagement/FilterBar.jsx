

import { paymentStatusConfig } from "./constants";

/**
 * FilterBar — search input, status dropdown filter, and overdue-only toggle.
 *
 * @param {{
 *   searchTerm: string,
 *   onSearchChange: (v: string) => void,
 *   statusFilter: string,
 *   onStatusChange: (v: string) => void,
 *   overdueOnly: boolean,
 *   onOverdueChange: (v: boolean) => void,
 * }} props
 */
export function FilterBar({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusChange,
  overdueOnly,
  onOverdueChange,
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索发票编码..."
              value={searchTerm || ""}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Status filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Filter className="mr-2 h-4 w-4" />
                状态:{" "}
                {statusFilter === "all"
                  ? "全部"
                  : paymentStatusConfig[statusFilter]?.label}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => onStatusChange("all")}>
                全部
              </DropdownMenuItem>
              {Object.entries(paymentStatusConfig).map(([key, config]) => (
                <DropdownMenuItem key={key} onClick={() => onStatusChange(key)}>
                  {config.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Overdue toggle */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={overdueOnly}
              onChange={(e) => onOverdueChange(e.target.checked)}
              className="w-4 h-4"
            />
            <Label>仅显示逾期</Label>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
