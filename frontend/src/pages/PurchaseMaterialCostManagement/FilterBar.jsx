/**
 * Filter Bar Component
 */

import { Search } from "lucide-react";
import {
  Card,
  CardContent,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { STANDARD_FILTER_OPTIONS, ACTIVE_FILTER_OPTIONS } from "./constants";

export default function FilterBar({
  searchTerm,
  setSearchTerm,
  typeFilter,
  setTypeFilter,
  standardFilter,
  setStandardFilter,
  activeFilter,
  setActiveFilter,
  materialTypes,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索物料名称、编码或规格..."
                value={searchTerm || "unknown"}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Select value={typeFilter || "unknown"} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="物料类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              {(materialTypes || []).map((type) => (
                <SelectItem key={type} value={type || "unknown"}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={standardFilter || "unknown"}
            onValueChange={setStandardFilter}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="标准件" />
            </SelectTrigger>
            <SelectContent>
              {STANDARD_FILTER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={activeFilter || "unknown"}
            onValueChange={setActiveFilter}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="启用状态" />
            </SelectTrigger>
            <SelectContent>
              {ACTIVE_FILTER_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
