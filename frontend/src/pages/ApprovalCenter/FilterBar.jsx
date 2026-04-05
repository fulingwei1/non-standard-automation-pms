import { Search, RefreshCw } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { cn } from "../../lib/utils";

const FilterBar = ({ searchText, setSearchText, filters, updateFilters, refresh, loading }) => (
  <Card className="bg-slate-800/50 border-slate-700 mb-6">
    <CardContent className="p-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="搜索标题、编号..."
            value={searchText || "unknown"}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                updateFilters({ keyword: searchText });
              }
            }}
            className="pl-10 bg-slate-900/50 border-slate-700"
          />
        </div>

        <Select
          value={filters.urgency}
          onValueChange={(value) => updateFilters({ urgency: value })}
        >
          <SelectTrigger className="w-[130px] bg-slate-900/50 border-slate-700">
            <SelectValue placeholder="紧急程度" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部紧急度</SelectItem>
            <SelectItem value="NORMAL">普通</SelectItem>
            <SelectItem value="URGENT">紧急</SelectItem>
            <SelectItem value="CRITICAL">特急</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          className="border-slate-600"
          onClick={refresh}
          disabled={loading}
        >
          <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
          刷新
        </Button>
      </div>
    </CardContent>
  </Card>
);

export default FilterBar;
