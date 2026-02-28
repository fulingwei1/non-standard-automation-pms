import { Eye, Box } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../../../components/ui/table';
import { formatDate } from '../../../lib/utils';
import { statusConfigs, healthConfigs } from '../constants';

/**
 * 机台列表表格组件
 */
export function MachineTable({ machines, loading, onViewDetail }) {
    const navigate = useNavigate();

    return (
        <Card>
            <CardHeader>
                <CardTitle>机台列表</CardTitle>
                <CardDescription>共 {machines.length} 个机台</CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="text-center py-8 text-slate-400">加载中...</div>
                ) : machines.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">暂无机台数据</div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>机台编码</TableHead>
                                <TableHead>机台名称</TableHead>
                                <TableHead>类型</TableHead>
                                <TableHead>状态</TableHead>
                                <TableHead>健康度</TableHead>
                                <TableHead>进度</TableHead>
                                <TableHead>更新时间</TableHead>
                                <TableHead className="text-right">操作</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {(machines || []).map((machine) => (
                                <TableRow key={machine.id}>
                                    <TableCell className="font-mono text-sm">
                                        {machine.machine_code}
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        {machine.machine_name}
                                    </TableCell>
                                    <TableCell>{machine.machine_type || '-'}</TableCell>
                                    <TableCell>
                                        <Badge className={statusConfigs[machine.status]?.color || 'bg-slate-500'}>
                                            {statusConfigs[machine.status]?.label || machine.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={healthConfigs[machine.health]?.color || 'bg-slate-500'}>
                                            {healthConfigs[machine.health]?.label || machine.health}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between text-xs">
                                                <span>{machine.progress || 0}%</span>
                                            </div>
                                            <Progress value={machine.progress || 0} className="h-1.5" />
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-slate-500 text-sm">
                                        {formatDate(machine.updated_at)}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onViewDetail(machine.id)}
                                            >
                                                <Eye className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => navigate(`/bom?machine_id=${machine.id}`)}
                                            >
                                                <Box className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </CardContent>
        </Card>
    );
}
