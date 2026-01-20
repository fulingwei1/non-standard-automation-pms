import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogBody,
    DialogFooter,
} from '../../../components/ui/dialog';
import { statusConfigs, healthConfigs } from '../constants';

/**
 * 机台详情对话框组件
 */
export function MachineDetailDialog({ open, onOpenChange, machine, onEdit }) {
    if (!machine) return null;

    const statusConfig = statusConfigs[machine.status] || { label: '未知', className: '' };
    const healthConfig = healthConfigs[machine.health] || { label: '未知', className: '' };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>机台详情</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-6">
                        {/* 基本信息 */}
                        <div>
                            <h3 className="text-lg font-semibold mb-3">基本信息</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-muted-foreground">机台编码</label>
                                    <p className="font-medium">{machine.machine_code}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">机台名称</label>
                                    <p className="font-medium">{machine.machine_name}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">机台类型</label>
                                    <p className="font-medium">{machine.machine_type || '-'}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">所属项目</label>
                                    <p className="font-medium">{machine.project_name || '-'}</p>
                                </div>
                            </div>
                        </div>

                        {/* 状态信息 */}
                        <div>
                            <h3 className="text-lg font-semibold mb-3">状态信息</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-muted-foreground">当前状态</label>
                                    <div className="mt-1">
                                        <Badge className={statusConfig.className}>
                                            {statusConfig.label}
                                        </Badge>
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">健康度</label>
                                    <div className="mt-1">
                                        <Badge className={healthConfig.className}>
                                            {healthConfig.label}
                                        </Badge>
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">当前阶段</label>
                                    <p className="font-medium">{machine.current_stage || '-'}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">进度</label>
                                    <p className="font-medium">{machine.progress || 0}%</p>
                                </div>
                            </div>
                        </div>

                        {/* 时间信息 */}
                        <div>
                            <h3 className="text-lg font-semibold mb-3">时间信息</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-muted-foreground">计划开始</label>
                                    <p className="font-medium">{machine.plan_start || '-'}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">计划结束</label>
                                    <p className="font-medium">{machine.plan_end || '-'}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">实际开始</label>
                                    <p className="font-medium">{machine.actual_start || '-'}</p>
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground">实际结束</label>
                                    <p className="font-medium">{machine.actual_end || '-'}</p>
                                </div>
                            </div>
                        </div>

                        {/* 描述 */}
                        {machine.description && (
                            <div>
                                <h3 className="text-lg font-semibold mb-3">描述</h3>
                                <p className="text-sm text-muted-foreground">{machine.description}</p>
                            </div>
                        )}
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        关闭
                    </Button>
                    {onEdit && (
                        <Button onClick={() => onEdit(machine)}>
                            编辑
                        </Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
