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

/**
 * ReleaseBOMDialog — confirmation dialog for releasing an approved BOM.
 */
export default function ReleaseBOMDialog({
    open,
    onOpenChange,
    releaseNote,
    setReleaseNote,
    onSubmit,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>发布BOM</DialogTitle>
                </DialogHeader>

                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                变更说明
                            </label>
                            <Input
                                value={releaseNote || 'unknown'}
                                onChange={(e) => setReleaseNote(e.target.value)}
                                placeholder="请输入变更说明"
                            />
                        </div>
                    </div>
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSubmit}>发布</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
