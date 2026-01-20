import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogBody,
    DialogFooter,
} from '../../../components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../../components/ui/select';
import { statusConfigs, healthConfigs } from '../constants';

/**
 * 创建机台对话框组件
 */
export function CreateMachineDialog({ open, onOpenChange, formData, onFormChange, onSubmit }) {
    const handleChange = (key, value) => {
        onFormChange({ ...formData, [key]: value });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>新建机台</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">机台编码 *</label>
                            <Input
                                value={formData.machine_code}
                                onChange={(e) => handleChange('machine_code', e.target.value)}
                                placeholder="请输入机台编码"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">机台名称 *</label>
                            <Input
                                value={formData.machine_name}
                                onChange={(e) => handleChange('machine_name', e.target.value)}
                                placeholder="请输入机台名称"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">机台类型</label>
                            <Input
                                value={formData.machine_type}
                                onChange={(e) => handleChange('machine_type', e.target.value)}
                                placeholder="机台类型"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">状态</label>
                            <Select
                                value={formData.status}
                                onValueChange={(val) => handleChange('status', val)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(statusConfigs).map(([key, config]) => (
                                        <SelectItem key={key} value={key}>
                                            {config.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">健康度</label>
                            <Select
                                value={formData.health}
                                onValueChange={(val) => handleChange('health', val)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(healthConfigs).map(([key, config]) => (
                                        <SelectItem key={key} value={key}>
                                            {config.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">描述</label>
                            <Input
                                value={formData.description}
                                onChange={(e) => handleChange('description', e.target.value)}
                                placeholder="机台描述"
                            />
                        </div>
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSubmit}>创建</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
