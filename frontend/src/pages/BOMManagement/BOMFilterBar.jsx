import { Search } from 'lucide-react';
import { Card, CardContent } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../components/ui/select';
import { statusConfigs } from './constants';

/**
 * BOMFilterBar — search input + project / machine / status selects.
 */
export default function BOMFilterBar({
    searchKeyword,
    setSearchKeyword,
    filterProject,
    filterMachine,
    setFilterMachine,
    filterStatus,
    setFilterStatus,
    projects,
    machines,
    onProjectChange,
}) {
    return (
        <Card>
            <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Keyword search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                        <Input
                            placeholder="搜索BOM编号、名称..."
                            value={searchKeyword || 'unknown'}
                            onChange={(e) => setSearchKeyword(e.target.value)}
                            className="pl-10"
                        />
                    </div>

                    {/* Project filter */}
                    <Select
                        value={filterProject || 'unknown'}
                        onValueChange={onProjectChange}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="选择项目" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部项目</SelectItem>
                            {(projects || []).map((proj) => (
                                <SelectItem key={proj.id} value={proj.id.toString()}>
                                    {proj.project_name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>

                    {/* Machine filter */}
                    <Select
                        value={filterMachine || 'unknown'}
                        onValueChange={setFilterMachine}
                        disabled={!filterProject}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="选择机台" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部机台</SelectItem>
                            {(machines || []).map((machine) => (
                                <SelectItem key={machine.id} value={machine.id.toString()}>
                                    {machine.machine_name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>

                    {/* Status filter */}
                    <Select
                        value={filterStatus || 'unknown'}
                        onValueChange={setFilterStatus}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">全部状态</SelectItem>
                            {Object.entries(statusConfigs).map(([key, config]) => (
                                <SelectItem key={key} value={key || 'unknown'}>
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
