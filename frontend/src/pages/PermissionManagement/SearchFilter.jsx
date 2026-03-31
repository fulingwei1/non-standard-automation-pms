import { Search, Filter } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { getModuleLabel } from "../../config/permissionLabels";

export function SearchFilter({ searchKeyword, setSearchKeyword, filterModule, setFilterModule, modules }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索权限编码、名称或描述..."
              value={searchKeyword || "unknown"}
              onChange={(e) => setSearchKeyword(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={filterModule || "unknown"} onValueChange={setFilterModule}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="选择模块" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有模块</SelectItem>
              {(modules || []).map((module) =>
                <SelectItem key={module} value={module || "unknown"}>
                  {getModuleLabel(module)}
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
