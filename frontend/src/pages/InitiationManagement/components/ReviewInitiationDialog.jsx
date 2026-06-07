import { useEffect, useState } from "react";
import {
    Button,
    Dialog,
    DialogBody,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    Input,
} from "../../../components/ui";

const defaultForm = {
    review_result: "",
    approved_pm_id: "",
    approved_level: "",
};

export function ReviewInitiationDialog({
    open,
    mode,
    projectManagers,
    loading,
    onOpenChange,
    onSubmit,
}) {
    const [formData, setFormData] = useState(defaultForm);
    const isApprove = mode === "approve";

    useEffect(() => {
        if (open) {
            setFormData({
                ...defaultForm,
                review_result: isApprove ? "同意立项" : "",
                approved_pm_id:
                    isApprove && projectManagers?.length ? String(projectManagers[0].id) : "",
            });
        }
    }, [isApprove, open, projectManagers]);

    const handleSubmit = async () => {
        if (!formData.review_result.trim()) {
            alert(isApprove ? "请填写评审结论" : "请填写驳回原因");
            return;
        }

        const payload = {
            review_result: formData.review_result.trim(),
        };
        if (isApprove) {
            if (formData.approved_pm_id) {
                payload.approved_pm_id = Number(formData.approved_pm_id);
            }
            if (formData.approved_level) {
                payload.approved_level = formData.approved_level;
            }
        }

        const ok = await onSubmit(payload);
        if (ok) {
            setFormData(defaultForm);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>{isApprove ? "审批通过" : "驳回立项"}</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        {isApprove && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    项目经理
                                </label>
                                <select
                                    value={formData.approved_pm_id}
                                    onChange={(event) =>
                                        setFormData({
                                            ...formData,
                                            approved_pm_id: event.target.value,
                                        })
                                    }
                                    className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                >
                                    <option value="">暂不指定</option>
                                    {(projectManagers || []).map((user) => (
                                        <option key={user.id} value={user.id}>
                                            {user.real_name || user.username || `用户 ${user.id}`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {isApprove && (
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    项目级别
                                </label>
                                <Input
                                    value={formData.approved_level}
                                    onChange={(event) =>
                                        setFormData({
                                            ...formData,
                                            approved_level: event.target.value,
                                        })
                                    }
                                    placeholder="A/B/C"
                                />
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                {isApprove ? "评审结论" : "驳回原因"}
                            </label>
                            <textarea
                                value={formData.review_result}
                                onChange={(event) =>
                                    setFormData({
                                        ...formData,
                                        review_result: event.target.value,
                                    })
                                }
                                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                                rows={3}
                            />
                        </div>
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {isApprove ? "审批通过" : "确认驳回"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
