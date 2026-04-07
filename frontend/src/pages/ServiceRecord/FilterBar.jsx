import { fadeIn } from "../../lib/animations";
import { SERVICE_STATUS, SERVICE_TYPES } from "../../components/service-record";

export default function FilterBar({
  searchQuery,
  setSearchQuery,
  typeFilter,
  setTypeFilter,
  statusFilter,
  setStatusFilter,
  dateFilter,
  setDateFilter,
}) {
  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible">
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索记录号、项目名称、客户名称、服务地点..."
                  value={searchQuery || "unknown"}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={typeFilter || "unknown"}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
              >
                <option value="ALL">全部类型</option>
                {Object.values(SERVICE_TYPES).map((type) => (
                  <option key={type.label} value={type.label}>
                    {type.label}
                  </option>
                ))}
              </select>
              <select
                value={statusFilter || "unknown"}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
              >
                <option value="ALL">全部状态</option>
                {Object.values(SERVICE_STATUS).map((status) => (
                  <option key={status.label} value={status.label}>
                    {status.label}
                  </option>
                ))}
              </select>
              <Input
                type="date"
                value={dateFilter.start}
                onChange={(e) =>
                  setDateFilter((prev) => ({ ...prev, start: e.target.value }))
                }
                className="w-40"
              />
              <Input
                type="date"
                value={dateFilter.end}
                onChange={(e) =>
                  setDateFilter((prev) => ({ ...prev, end: e.target.value }))
                }
                className="w-40"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
