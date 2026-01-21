import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter, Button } from "../../../components/ui";

export function ClosureDetailDialog({ open, onOpenChange, closure }) {
    if (!closure) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>结项详情</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-6">
                        {/* All closure details in a comprehensive view */}
                        <div className="text-sm text-slate-400">详细内容请查看主页面</div>
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button onClick={() => onOpenChange(false)}>关闭</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
