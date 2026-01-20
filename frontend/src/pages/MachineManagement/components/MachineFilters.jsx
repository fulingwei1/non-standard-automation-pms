import { Search } from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { Input } from '../../../components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../../components/ui/select';
import { statusConfigs, healthConfigs } from '../constants';

/**
 * 机台过滤器组件
 */
export function MachineFilters({ filters, onFiltersChange }) {
    const handleChange = (key, value) => {
        onFiltersChange({ ...filters, [key]: value });
    };

    return (
        <Card>
            <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                        <Input
                            placeholder="搜索机台编码、名称..."
                            value={filters.searchKeyword}
                            onChange={(e) => handleChange('searchKeyword', e.target.value)}
                            className="pl-10"
                        />
                    </div>
                    <Select
                        value={filters.filterStatus}
                        onValueChange={(val) => handleChange('filterStatus', val)}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部状态</SelectItem>
                            {Object.entries(statusConfigs).map(([key, config]) => (
                                <SelectItem key={key} value={key}>
                                    {config.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <Select
                        value={filters.filterHealth}
                        onValueChange={(val) => handleChange('filterHealth', val)}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="选择健康度" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部健康度</SelectItem>
                            {Object.entries(healthConfigs).map(([key, config]) => (
                                <SelectItem key={key} value={key}>
                                    {config.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </CardContent>
        </Card>
    );
}
