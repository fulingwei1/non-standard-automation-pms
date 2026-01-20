import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter, Button } from "../../../components/ui";

export function TechnicalReviewDeleteDialog({ open, review, onClose, onConfirm }) {
    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="bg-slate-900 border-slate-800">
                <DialogHeader>
                    <DialogTitle className="text-slate-100">确认删除</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <p className="text-slate-400">
                        确定要删除评审 "{review?.review_name}" 吗？此操作不可恢复。
                    </p>
                </DialogBody>
                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={onClose}
                        className="border-slate-700"
                    >
                        取消
                    </Button>
                    <Button
                        onClick={onConfirm}
                        className="bg-red-600 hover:bg-red-700"
                    >
                        删除
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
