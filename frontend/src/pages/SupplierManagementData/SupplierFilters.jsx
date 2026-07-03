import { Search } from "lucide-react";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";

export default function SupplierFilters({
  searchKeyword,
  filterType,
  filterStatus,
  filterLevel,
  onSearchChange,
  onFilterTypeChange,
  onFilterStatusChange,
  onFilterLevelChange,
}) {
  return (
    <div className="flex items-center space-x-2">
      <Input
        placeholder="搜索供应商名称/编码..."
        value={searchKeyword}
        onChange={(e) => onSearchChange(e.target.value)}
        className="max-w-sm bg-slate-900/50 border-slate-700 text-slate-200"
        icon={Search}
      />

      <Select value={filterType || "all"} onValueChange={onFilterTypeChange}>
        <SelectTrigger className="w-[150px] bg-slate-900/50 border-slate-700">
          <SelectValue placeholder="供应商类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">所有类型</SelectItem>
          <SelectItem value="MATERIAL">物料供应商</SelectItem>
          <SelectItem value="OUTSOURCE">外协供应商</SelectItem>
          <SelectItem value="BOTH">两者兼有</SelectItem>
        </SelectContent>
      </Select>
      <Select value={filterStatus || "all"} onValueChange={onFilterStatusChange}>
        <SelectTrigger className="w-[150px] bg-slate-900/50 border-slate-700">
          <SelectValue placeholder="状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">所有状态</SelectItem>
          <SelectItem value="ACTIVE">合作中</SelectItem>
          <SelectItem value="SUSPENDED">暂停</SelectItem>
          <SelectItem value="BLACKLIST">黑名单</SelectItem>
        </SelectContent>
      </Select>
      <Select value={filterLevel || "all"} onValueChange={onFilterLevelChange}>
        <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
          <SelectValue placeholder="等级" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">所有等级</SelectItem>
          <SelectItem value="A">A级</SelectItem>
          <SelectItem value="B">B级</SelectItem>
          <SelectItem value="C">C级</SelectItem>
          <SelectItem value="D">D级</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
