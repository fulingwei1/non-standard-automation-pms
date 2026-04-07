


export default function SearchFilterBar({
  searchKeyword,
  setSearchKeyword,
  filterType,
  setFilterType,
  filterActive,
  setFilterActive,
}) {
  return (
    <Card className="bg-surface-100 border-white/5">
      <CardContent className="p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索模板名称或编码..."
              value={searchKeyword || "unknown"}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10 bg-white/5 border-white/10"
            />
          </div>
          <Select value={filterType || "unknown"} onValueChange={setFilterType}>
            <SelectTrigger className="w-[180px] bg-white/5 border-white/10">
              <SelectValue placeholder="项目类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="STANDARD">标准项目</SelectItem>
              <SelectItem value="CUSTOM">定制项目</SelectItem>
              <SelectItem value="R&D">研发项目</SelectItem>
              <SelectItem value="MAINTENANCE">维保项目</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterActive || "unknown"} onValueChange={setFilterActive}>
            <SelectTrigger className="w-[120px] bg-white/5 border-white/10">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="active">已启用</SelectItem>
              <SelectItem value="inactive">已禁用</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
