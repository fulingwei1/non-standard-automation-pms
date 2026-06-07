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
} from "../../components/ui";

const defaultFormData = {
    material_type: "drawing",
    material_name: "",
    file_path: "",
    file_size: "",
    version: "",
    is_required: true,
};

export function ReviewMaterialDialog({ open, onOpenChange, reviewId, onSubmit }) {
    const [formData, setFormData] = useState(defaultFormData);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open) {
            setFormData(defaultFormData);
        }
    }, [open]);

    const updateField = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        const fileSize = Number(formData.file_size);
        if (!Number.isFinite(fileSize) || fileSize < 0) {
            alert("请输入有效文件大小");
            return;
        }

        setSubmitting(true);
        try {
            await onSubmit({
                review_id: Number(reviewId),
                material_type: formData.material_type,
                material_name: formData.material_name.trim(),
                file_path: formData.file_path.trim(),
                file_size: fileSize,
                version: formData.version.trim() || null,
                is_required: formData.is_required,
            });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-xl bg-slate-950 border-slate-800">
                <DialogHeader>
                    <DialogTitle>登记评审材料</DialogTitle>
                    <DialogDescription>把图纸、方案、BOM 等评审输入沉淀到技术评审记录。</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>材料类型</span>
                            <select
                                value={formData.material_type}
                                onChange={(event) => updateField("material_type", event.target.value)}
                                className="h-11 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 text-sm text-white"
                            >
                                <option value="drawing">图纸</option>
                                <option value="bom">BOM</option>
                                <option value="report">报告</option>
                                <option value="document">文档</option>
                                <option value="other">其他</option>
                            </select>
                        </label>

                        <label className="space-y-2 text-sm text-slate-300">
                            <span>材料名称</span>
                            <Input
                                required
                                value={formData.material_name}
                                onChange={(event) => updateField("material_name", event.target.value)}
                            />
                        </label>
                    </div>

                    <label className="space-y-2 text-sm text-slate-300">
                        <span>文件路径</span>
                        <Input
                            required
                            value={formData.file_path}
                            onChange={(event) => updateField("file_path", event.target.value)}
                        />
                    </label>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <label className="space-y-2 text-sm text-slate-300">
                            <span>文件大小</span>
                            <Input
                                required
                                type="number"
                                min="0"
                                value={formData.file_size}
                                onChange={(event) => updateField("file_size", event.target.value)}
                            />
                        </label>

                        <label className="space-y-2 text-sm text-slate-300">
                            <span>版本号</span>
                            <Input
                                value={formData.version}
                                onChange={(event) => updateField("version", event.target.value)}
                            />
                        </label>
                    </div>

                    <label className="flex items-center gap-3 text-sm text-slate-300">
                        <input
                            type="checkbox"
                            checked={formData.is_required}
                            onChange={(event) => updateField("is_required", event.target.checked)}
                            className="h-4 w-4 rounded border-white/10 bg-white/[0.03]"
                        />
                        <span>必备材料</span>
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
                            {submitting ? "提交中..." : "登记材料"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
