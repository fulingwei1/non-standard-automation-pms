import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
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

/**
 * Dialog for reporting a new issue against the current acceptance order.
 * `items` is passed in so the user can optionally link the issue to a check item.
 */
export function CreateIssueDialog({
    open,
    onOpenChange,
    items,
    newIssue,
    setNewIssue,
    onSubmit,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>上报问题</DialogTitle>
                </DialogHeader>

                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                关联检查项
                            </label>
                            <Select
                                value={newIssue.item_id?.toString() || ''}
                                onValueChange={(val) =>
                                    setNewIssue({
                                        ...newIssue,
                                        item_id: val && val !== 'none' ? parseInt(val) : null,
                                    })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="选择检查项" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">无</SelectItem>
                                    {(items || []).map((item) => (
                                        <SelectItem key={item.id} value={item.id.toString()}>
                                            {item.item_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                问题分类
                            </label>
                            <Input
                                value={newIssue.category}
                                onChange={(e) =>
                                    setNewIssue({ ...newIssue, category: e.target.value })
                                }
                                placeholder="问题分类"
                            />
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                严重程度
                            </label>
                            <Select
                                value={newIssue.severity}
                                onValueChange={(val) =>
                                    setNewIssue({ ...newIssue, severity: val })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="CRITICAL">严重</SelectItem>
                                    <SelectItem value="MAJOR">重要</SelectItem>
                                    <SelectItem value="MINOR">一般</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                问题描述 *
                            </label>
                            <textarea
                                className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={newIssue.description}
                                onChange={(e) =>
                                    setNewIssue({ ...newIssue, description: e.target.value })
                                }
                                placeholder="详细描述问题..."
                            />
                        </div>
                    </div>
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSubmit}>提交</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
