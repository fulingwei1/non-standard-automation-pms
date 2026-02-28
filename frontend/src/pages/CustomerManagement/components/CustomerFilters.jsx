import { Search } from "lucide-react";
import { Input } from "../../../components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "../../../components/ui/select";
import { CardHeader, CardTitle } from "../../../components/ui/card";

export function CustomerFilters({
    searchKeyword,
    setSearchKeyword,
    filterIndustry,
    setFilterIndustry,
    filterStatus,
    setFilterStatus,
    industries
}) {
    return (
        <CardHeader className="flex-row items-center justify-between">
            <CardTitle>客户列表</CardTitle>
            <div className="flex items-center space-x-2">
                <Input
                    placeholder="搜索客户名称/编码..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="max-w-sm"
                    icon={Search}
                />

                <Select value={filterIndustry} onValueChange={setFilterIndustry}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="筛选行业" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">所有行业</SelectItem>
                        {industries.map((industry) => (
                            <SelectItem key={industry} value={industry}>
                                {industry}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="筛选状态" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">所有状态</SelectItem>
                        <SelectItem value="active">启用</SelectItem>
                        <SelectItem value="inactive">禁用</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </CardHeader>
    );
}
