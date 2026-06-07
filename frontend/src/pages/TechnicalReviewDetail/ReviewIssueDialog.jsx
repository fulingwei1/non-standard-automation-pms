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
    issue_level: "B",
    category: "",
    description: "",
    suggestion: "",
    assignee_id: "",
    deadline: "",
};

export function ReviewIssueDialog({ open, onOpenChange, reviewId, users, onSubmit }) {
    const [formData, setFormData] = useState(defaultFormData);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open) {
            setFormData((prev) => ({
                ...defaultFormData,
                assignee_id: prev.assignee_id || users?.[0]?.id?.toString() || "",
            }));
        }
    }, [open, users]);

    const updateField = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!formData.assignee_id) {
            alert("请选择责任人");
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit({
                review_id: Number(reviewId),
                issue_level: formData.issue_level,
                category: formData.category.trim(),
                description: formData.description.trim(),
                suggestion: formData.suggestion.trim() || null,
                assignee_id: Number(formData.assignee_id),
                deadline: formData.deadline,
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-xl bg-slate-950 border-slate-800">
                <DialogHeader>
                    <DialogTitle>创建评审问题</DialogTitle>
                    <DialogDescription>记录技术评审中的整改项和责任人。</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>问题等级</span>
                            <select
                                value={formData.issue_level}
                                onChange={(event) => updateField("issue_level", event.target.value)}
                                className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white"
                            >
                                <option value="A">A</option>
                                <option value="B">B</option>
                                <option value="C">C</option>
                                <option value="D">D</option>
                            </select>
                        </label>

                        <label className="space-y-2 text-sm text-slate-300">
                            <span>问题类别</span>
                            <Input
                                required
                                value={formData.category}
                                onChange={(event) => updateField("category", event.target.value)}
                            />
                        </label>
                    </div>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>问题描述</span>
                        <Textarea
                            required
                            value={formData.description}
                            onChange={(event) => updateField("description", event.target.value)}
                        />
                    </label>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>改进建议</span>
                        <Textarea
                            value={formData.suggestion}
                            onChange={(event) => updateField("suggestion", event.target.value)}
                        />
                    </label>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>责任人</span>
                            <select
                                required
                                value={formData.assignee_id}
                                onChange={(event) => updateField("assignee_id", event.target.value)}
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
                            <span>整改期限</span>
                            <Input
                                required
                                type="date"
                                value={formData.deadline}
                                onChange={(event) => updateField("deadline", event.target.value)}
                            />
                        </label>
                    </div>

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
                            {submitting ? "提交中..." : "提交问题"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
