import { Upload, Download, Eye, CheckCircle2 } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogBody,
    DialogFooter,
} from '../../components/ui/dialog';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from '../../components/ui/tabs';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../../components/ui/table';
import { formatCurrency, formatDate } from '../../lib/utils';
import { statusConfigs } from './constants';

/**
 * BOMDetailDialog — tabbed dialog showing BOM items, version history, and basic info.
 */
export default function BOMDetailDialog({
    open,
    onOpenChange,
    selectedBom,
    bomItems,
    versions,
    onImport,
    onExport,
    onRelease,
    onViewVersion,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>
                        {selectedBom?.bom_name} - {selectedBom?.bom_no}
                    </DialogTitle>
                </DialogHeader>

                <DialogBody>
                    {selectedBom && (
                        <Tabs defaultValue="items" className="w-full">
                            <TabsList>
                                <TabsTrigger value="items">BOM明细</TabsTrigger>
                                <TabsTrigger value="versions">版本历史</TabsTrigger>
                                <TabsTrigger value="info">基本信息</TabsTrigger>
                            </TabsList>

                            {/* ── Items tab ─────────────────────────────────── */}
                            <TabsContent value="items" className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div className="text-sm text-slate-500">
                                        共 {bomItems.length} 项物料
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={onImport}
                                        >
                                            <Upload className="w-4 h-4 mr-2" />
                                            导入
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onExport(selectedBom.id)}
                                        >
                                            <Download className="w-4 h-4 mr-2" />
                                            导出
                                        </Button>
                                        {selectedBom.status === 'APPROVED' && (
                                            <Button size="sm" onClick={onRelease}>
                                                <CheckCircle2 className="w-4 h-4 mr-2" />
                                                发布
                                            </Button>
                                        )}
                                    </div>
                                </div>

                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>序号</TableHead>
                                            <TableHead>物料编码</TableHead>
                                            <TableHead>物料名称</TableHead>
                                            <TableHead>规格</TableHead>
                                            <TableHead>单位</TableHead>
                                            <TableHead>数量</TableHead>
                                            <TableHead>单价</TableHead>
                                            <TableHead>金额</TableHead>
                                            <TableHead>来源</TableHead>
                                            <TableHead>需求日期</TableHead>
                                            <TableHead>关键件</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {(bomItems || []).map((item, index) => (
                                            <TableRow key={item.id}>
                                                <TableCell>{item.item_no || index + 1}</TableCell>
                                                <TableCell className="font-mono text-sm">
                                                    {item.material_code}
                                                </TableCell>
                                                <TableCell>{item.material_name}</TableCell>
                                                <TableCell className="text-slate-500">
                                                    {item.specification || '-'}
                                                </TableCell>
                                                <TableCell>{item.unit}</TableCell>
                                                <TableCell>{item.quantity}</TableCell>
                                                <TableCell>
                                                    {formatCurrency(item.unit_price || 0)}
                                                </TableCell>
                                                <TableCell className="font-medium">
                                                    {formatCurrency(item.amount || 0)}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline">{item.source_type}</Badge>
                                                </TableCell>
                                                <TableCell className="text-slate-500 text-sm">
                                                    {item.required_date
                                                        ? formatDate(item.required_date)
                                                        : '-'}
                                                </TableCell>
                                                <TableCell>
                                                    {item.is_key_item && (
                                                        <Badge className="bg-amber-500">关键</Badge>
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TabsContent>

                            {/* ── Versions tab ──────────────────────────────── */}
                            <TabsContent value="versions" className="space-y-4">
                                <div className="text-sm text-slate-500 mb-4">
                                    共 {versions.length} 个版本
                                </div>
                                <div className="space-y-2">
                                    {(versions || []).map((version) => (
                                        <Card key={version.id}>
                                            <CardContent className="pt-4">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <Badge>{version.version}</Badge>
                                                        {version.is_latest && (
                                                            <Badge className="bg-emerald-500">最新</Badge>
                                                        )}
                                                        <Badge
                                                            className={statusConfigs[version.status]?.color}
                                                        >
                                                            {statusConfigs[version.status]?.label}
                                                        </Badge>
                                                        <span className="text-sm text-slate-500">
                                                            {formatDate(version.created_at)}
                                                        </span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() => onViewVersion(version)}
                                                        >
                                                            <Eye className="w-4 h-4 mr-2" />
                                                            查看
                                                        </Button>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </TabsContent>

                            {/* ── Info tab ──────────────────────────────────── */}
                            <TabsContent value="info" className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">BOM编号</div>
                                        <div className="font-mono">{selectedBom.bom_no}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">BOM名称</div>
                                        <div>{selectedBom.bom_name}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">项目</div>
                                        <div>{selectedBom.project_name || '-'}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">机台</div>
                                        <div>{selectedBom.machine_name || '-'}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">版本</div>
                                        <div>{selectedBom.version}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">状态</div>
                                        <Badge
                                            className={statusConfigs[selectedBom.status]?.color}
                                        >
                                            {statusConfigs[selectedBom.status]?.label}
                                        </Badge>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">物料数量</div>
                                        <div>{selectedBom.total_items || 0}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">总金额</div>
                                        <div className="font-medium">
                                            {formatCurrency(selectedBom.total_amount || 0)}
                                        </div>
                                    </div>
                                </div>
                            </TabsContent>
                        </Tabs>
                    )}
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        关闭
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
