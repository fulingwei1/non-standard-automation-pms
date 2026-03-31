import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter,
} from '../../components/ui/dialog';
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../../components/ui/select';
import { DATA_SCOPE_MAP } from './constants';

export default function CreateRoleDialog({
    open, onOpenChange, form, onChange, onSubmit, roles,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>新建角色</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">角色编码 *</label>
                            <Input
                                value={form.role_code}
                                onChange={(e) => onChange('role_code', e.target.value)}
                                placeholder="如: SALES_MANAGER"
                            />
                            <p className="text-xs text-slate-500 mt-1">唯一标识，建议使用大写字母和下划线</p>
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">角色名称 *</label>
                            <Input
                                value={form.role_name}
                                onChange={(e) => onChange('role_name', e.target.value)}
                                placeholder="如: 销售经理"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">继承自</label>
                            <Select
                                value={form.parent_id?.toString() || ''}
                                onValueChange={(v) => onChange('parent_id', v ? parseInt(v) : null)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="选择父角色（可选）" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="__none__">无（顶级角色）</SelectItem>
                                    {(roles || []).filter(r => r.is_active).map((role) => (
                                        <SelectItem key={role.id} value={role.id.toString()}>
                                            {role.role_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-slate-500 mt-1">子角色会自动继承父角色的所有权限</p>
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">数据权限范围</label>
                            <Select
                                value={form.data_scope}
                                onValueChange={(v) => onChange('data_scope', v)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(DATA_SCOPE_MAP).map(([key, config]) => (
                                        <SelectItem key={key} value={key || "unknown"}>
                                            {config.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-sm font-medium mb-2 block">描述</label>
                            <Input
                                value={form.description}
                                onChange={(e) => onChange('description', e.target.value)}
                                placeholder="角色描述"
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
