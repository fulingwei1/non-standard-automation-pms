import React from 'react';
import DeleteConfirmDialog from "../../../components/common/DeleteConfirmDialog";

export function TechnicalReviewDeleteDialog({ open, review, onClose, onConfirm }) {
    return (
        <DeleteConfirmDialog
            open={open}
            onOpenChange={(next) => {
                if (!next) {onClose?.();}
            }}
            title="确认删除"
            description={`确定要删除评审 "${review?.review_name}" 吗？此操作不可恢复。`}
            confirmText="删除"
            onConfirm={onConfirm}
            contentClassName="bg-slate-900 border-slate-800"
            titleClassName="text-slate-100"
            descriptionClassName="text-slate-400"
            cancelButtonClassName="border-slate-700"
            confirmButtonClassName="bg-red-600 hover:bg-red-700"
        />
    );
}
