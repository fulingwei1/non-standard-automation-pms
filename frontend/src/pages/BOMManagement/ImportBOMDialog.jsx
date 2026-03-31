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
 * ImportBOMDialog — file upload dialog for importing BOM items.
 */
export default function ImportBOMDialog({
    open,
    onOpenChange,
    importFile,
    setImportFile,
    onSubmit,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>导入BOM</DialogTitle>
                </DialogHeader>

                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                选择文件
                            </label>
                            <Input
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={(e) =>
                                    setImportFile(e.target.files?.[0] || null)
                                }
                            />
                        </div>
                    </div>
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSubmit} disabled={!importFile}>
                        导入
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
