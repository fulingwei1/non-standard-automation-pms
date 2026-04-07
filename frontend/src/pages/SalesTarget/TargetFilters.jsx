

import { fadeIn } from "../../lib/animations";

export default function TargetFilters({ searchTerm, setSearchTerm, filters, setFilters }) {
  return (
    <motion.div variants={fadeIn}>
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="flex-1 relative">
              <Input
                placeholder="搜索目标..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
            <Select
              value={filters.target_scope}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, target_scope: value || "" }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="目标范围" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部范围</SelectItem>
                <SelectItem value="PERSONAL">个人目标</SelectItem>
                <SelectItem value="TEAM">团队目标</SelectItem>
                <SelectItem value="DEPARTMENT">部门目标</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.target_type}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, target_type: value || "" }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="目标类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="LEAD_COUNT">线索数量</SelectItem>
                <SelectItem value="OPPORTUNITY_COUNT">商机数量</SelectItem>
                <SelectItem value="CONTRACT_AMOUNT">合同金额</SelectItem>
                <SelectItem value="COLLECTION_AMOUNT">回款金额</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.target_period}
              onValueChange={(value) =>
                setFilters((prev) => ({
                  ...prev,
                  target_period: value || "",
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="目标周期" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部周期</SelectItem>
                <SelectItem value="MONTHLY">月度</SelectItem>
                <SelectItem value="QUARTERLY">季度</SelectItem>
                <SelectItem value="YEARLY">年度</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.status}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, status: value || "" }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="ACTIVE">进行中</SelectItem>
                <SelectItem value="COMPLETED">已完成</SelectItem>
                <SelectItem value="CANCELLED">已取消</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
