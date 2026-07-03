import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogBody,
    DialogFooter,
} from '../../components/ui/dialog';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../components/ui/select';
import { resultStatusConfigs } from './constants';

/**
 * Dialog for recording / updating the result of a single check item.
 */
export function UpdateItemDialog({
    open,
    onOpenChange,
    selectedItem,
    itemResult,
    setItemResult,
    onSave,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>
                        {selectedItem?.item_name} - 检查结果
                    </DialogTitle>
                    <DialogDescription className="sr-only">
                        记录检查项结果、实际值、偏差和备注。
                    </DialogDescription>
                </DialogHeader>

                <DialogBody>
                    {selectedItem && (
                        <div className="space-y-4">
                            <div>
                                <div className="text-sm text-slate-500 mb-1">验收标准</div>
                                <div>{selectedItem.acceptance_criteria || '-'}</div>
                            </div>

                            {selectedItem.standard_value && (
                                <div>
                                    <div className="text-sm text-slate-500 mb-1">标准值</div>
                                    <div>
                                        {selectedItem.standard_value}{' '}
                                        {selectedItem.unit || ''}
                                    </div>
                                </div>
                            )}

                            <div>
                                <label className="text-sm font-medium mb-2 block">
                                    检查结果 *
                                </label>
                                <Select
                                    value={itemResult.result_status}
                                    onValueChange={(val) =>
                                        setItemResult({ ...itemResult, result_status: val })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(resultStatusConfigs).map(([key, config]) => (
                                            <SelectItem key={key} value={key || 'unknown'}>
                                                {config.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {selectedItem.standard_value && (
                                <div>
                                    <label className="text-sm font-medium mb-2 block">
                                        实际值
                                    </label>
                                    <Input
                                        value={itemResult.actual_value}
                                        onChange={(e) =>
                                            setItemResult({
                                                ...itemResult,
                                                actual_value: e.target.value,
                                            })
                                        }
                                        placeholder="填写实际测量值"
                                    />
                                </div>
                            )}

                            <div>
                                <label className="text-sm font-medium mb-2 block">偏差</label>
                                <Input
                                    value={itemResult.deviation}
                                    onChange={(e) =>
                                        setItemResult({
                                            ...itemResult,
                                            deviation: e.target.value,
                                        })
                                    }
                                    placeholder="偏差说明"
                                />
                            </div>

                            <div>
                                <label className="text-sm font-medium mb-2 block">备注</label>
                                <Input
                                    value={itemResult.remark}
                                    onChange={(e) =>
                                        setItemResult({ ...itemResult, remark: e.target.value })
                                    }
                                    placeholder="备注说明"
                                />
                            </div>
                        </div>
                    )}
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSave}>保存</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
