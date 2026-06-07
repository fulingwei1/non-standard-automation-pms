import { useEffect, useState } from "react";
import {
    Button,
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    Input,
    Textarea,
} from "../../components/ui";

const defaultFormData = {
    category: "",
    check_item: "",
    result: "PASS",
    issue_level: "B",
    issue_desc: "",
    checker_id: "",
    remark: "",
};

export function ReviewChecklistDialog({ open, onOpenChange, reviewId, users, onSubmit }) {
    const [formData, setFormData] = useState(defaultFormData);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open) {
            setFormData((prev) => ({
                ...defaultFormData,
                checker_id: prev.checker_id || users?.[0]?.id?.toString() || "",
            }));
        }
    }, [open, users]);

    const updateField = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!formData.checker_id) {
            alert("请选择检查人");
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit({
                review_id: Number(reviewId),
                checklist_item_id: null,
                category: formData.category.trim(),
                check_item: formData.check_item.trim(),
                result: formData.result,
                issue_level: formData.result === "FAIL" ? formData.issue_level : null,
                issue_desc: formData.result === "FAIL" ? formData.issue_desc.trim() : null,
                checker_id: Number(formData.checker_id),
                remark: formData.remark.trim() || null,
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl bg-slate-950 border-slate-800">
                <DialogHeader>
                    <DialogTitle>添加检查项</DialogTitle>
                    <DialogDescription>记录评审结论，失败项会同步形成整改问题。</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>检查类别</span>
                            <Input
                                required
                                value={formData.category}
                                onChange={(event) => updateField("category", event.target.value)}
                            />
                        </label>

                        <label className="space-y-2 text-sm text-slate-300">
                            <span>检查结果</span>
                            <select
                                value={formData.result}
                                onChange={(event) => updateField("result", event.target.value)}
                                className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white"
                            >
                                <option value="PASS">通过</option>
                                <option value="FAIL">不通过</option>
                                <option value="NA">不适用</option>
                            </select>
                        </label>
                    </div>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>检查项内容</span>
                        <Textarea
                            required
                            value={formData.check_item}
                            onChange={(event) => updateField("check_item", event.target.value)}
                        />
                    </label>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>问题等级</span>
                            <select
                                value={formData.issue_level}
                                onChange={(event) => updateField("issue_level", event.target.value)}
                                disabled={formData.result !== "FAIL"}
                                className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white disabled:opacity-50"
                            >
                                <option value="A">A</option>
                                <option value="B">B</option>
                                <option value="C">C</option>
                                <option value="D">D</option>
                            </select>
                        </label>

                        <label className="space-y-2 text-sm text-slate-300">
                            <span>检查人</span>
                            <select
                                required
                                value={formData.checker_id}
                                onChange={(event) => updateField("checker_id", event.target.value)}
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
                    </div>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>问题描述</span>
                        <Textarea
                            value={formData.issue_desc}
                            onChange={(event) => updateField("issue_desc", event.target.value)}
                            disabled={formData.result !== "FAIL"}
                        />
                    </label>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>备注</span>
                        <Textarea
                            value={formData.remark}
                            onChange={(event) => updateField("remark", event.target.value)}
                        />
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
                            {submitting ? "提交中..." : "添加检查项"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
