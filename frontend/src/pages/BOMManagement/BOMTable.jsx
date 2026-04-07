

import { formatCurrency, formatDate } from '../../lib/utils';
import { statusConfigs } from './constants';

/**
 * BOMTable — card containing the BOM list table with actions.
 */
export default function BOMTable({
    loading,
    filteredBoms,
    onViewDetail,
    onExport,
    onCreateNew,
}) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <div>
                    <CardTitle>BOM列表</CardTitle>
                    <CardDescription>共 {filteredBoms.length} 个BOM</CardDescription>
                </div>
                <Button onClick={onCreateNew}>
                    <Plus className="w-4 h-4 mr-2" />
                    新建BOM
                </Button>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="text-center py-8 text-slate-400">加载中...</div>
                ) : filteredBoms.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">暂无BOM数据</div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>BOM编号</TableHead>
                                <TableHead>BOM名称</TableHead>
                                <TableHead>项目</TableHead>
                                <TableHead>机台</TableHead>
                                <TableHead>版本</TableHead>
                                <TableHead>状态</TableHead>
                                <TableHead>物料数量</TableHead>
                                <TableHead>总金额</TableHead>
                                <TableHead>更新时间</TableHead>
                                <TableHead className="text-right">操作</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {(filteredBoms || []).map((bom) => (
                                <TableRow key={bom.id}>
                                    <TableCell className="font-mono text-sm">
                                        {bom.bom_no}
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        {bom.bom_name}
                                    </TableCell>
                                    <TableCell>{bom.project_name || '-'}</TableCell>
                                    <TableCell>{bom.machine_name || '-'}</TableCell>
                                    <TableCell>
                                        <Badge variant="outline">{bom.version}</Badge>
                                        {bom.is_latest && (
                                            <Badge className="ml-2 bg-emerald-500">最新</Badge>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        <Badge
                                            className={
                                                statusConfigs[bom.status]?.color || 'bg-slate-500'
                                            }
                                        >
                                            {statusConfigs[bom.status]?.label || bom.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{bom.total_items || 0}</TableCell>
                                    <TableCell>
                                        {formatCurrency(bom.total_amount || 0)}
                                    </TableCell>
                                    <TableCell className="text-slate-500 text-sm">
                                        {formatDate(bom.updated_at)}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onViewDetail(bom.id)}
                                            >
                                                <Eye className="w-4 h-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onExport(bom.id)}
                                            >
                                                <Download className="w-4 h-4" />
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
