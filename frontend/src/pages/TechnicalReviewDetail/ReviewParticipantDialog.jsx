import { useEffect, useState } from "react";
import {
    Button,
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "../../components/ui";

const defaultFormData = {
    user_id: "",
    role: "expert",
    is_required: true,
};

export function ReviewParticipantDialog({ open, onOpenChange, reviewId, users, onSubmit }) {
    const [formData, setFormData] = useState(defaultFormData);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open) {
            setFormData((prev) => ({
                ...defaultFormData,
                user_id: prev.user_id || users?.[0]?.id?.toString() || "",
            }));
        }
    }, [open, users]);

    const updateField = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!formData.user_id) {
            alert("请选择参与人");
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit({
                review_id: Number(reviewId),
                user_id: Number(formData.user_id),
                role: formData.role,
                is_required: formData.is_required,
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg bg-slate-950 border-slate-800">
                <DialogHeader>
                    <DialogTitle>添加评审参与人</DialogTitle>
                    <DialogDescription>把售前、设计、项目等关键人员纳入同一场技术评审。</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <label className="space-y-2 text-sm text-slate-300">
                        <span>参与人</span>
                        <select
                            required
                            value={formData.user_id}
                            onChange={(event) => updateField("user_id", event.target.value)}
                            className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white"
                        >
                            <option value="">请选择</option>
                            {(users || []).map((user) => (
                                <option key={user.id} value={user.id}>
                                    {user.real_name || user.username || `用户${user.id}`}
                                </option>
                            ))}
                        </select>
                    </label>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>评审角色</span>
                        <select
                            value={formData.role}
                            onChange={(event) => updateField("role", event.target.value)}
                            className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white"
                        >
                            <option value="host">主持人</option>
                            <option value="expert">专家</option>
                            <option value="presenter">汇报人</option>
                            <option value="recorder">记录人</option>
                            <option value="observer">观察人</option>
                        </select>
                    </label>

                    <label className="flex items-center gap-3 text-sm text-slate-300">
                        <input
                            type="checkbox"
                            checked={formData.is_required}
                            onChange={(event) => updateField("is_required", event.target.checked)}
                            className="h-4 w-4 rounded border-white/10 bg-white/[0.03]"
                        />
                        <span>必须参与</span>
                    </label>

                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={submitting}
                        >
                            取消
                        </Button>
                        <Button type="submit" disabled={submitting}>
                            {submitting ? "提交中..." : "添加参与人"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
