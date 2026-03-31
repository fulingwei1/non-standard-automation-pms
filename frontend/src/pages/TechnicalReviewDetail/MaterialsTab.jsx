import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Button,
} from "../../components/ui";
import { Upload, FileText, Trash2 } from "lucide-react";
import { technicalReviewApi } from "../../services/api";
import { confirmAction } from "@/lib/confirmAction";

/**
 * Renders the "材料" (Materials) tab content.
 */
export function MaterialsTab({ isNew, materials, onUpload, onRefresh }) {
    const handleDelete = async (materialId) => {
        if (await confirmAction("确定删除此材料吗？")) {
            try {
                await technicalReviewApi.deleteMaterial(materialId);
                await onRefresh();
            } catch (_error) {
                alert("删除失败");
            }
        }
    };

    return (
        <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>评审材料</CardTitle>
                    {!isNew && (
                        <Button
                            size="sm"
                            onClick={onUpload}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Upload className="w-4 h-4 mr-2" />
                            上传材料
                        </Button>
                    )}
                </CardHeader>
                <CardContent>
                    {(materials?.length ?? 0) === 0 ? (
                        <p className="text-center text-slate-400 py-8">暂无材料</p>
                    ) : (
                        <div className="space-y-2">
                            {(materials || []).map((m) => (
                                <div
                                    key={m.id}
                                    className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                                >
                                    <div className="flex items-center gap-3">
                                        <FileText className="w-5 h-5 text-slate-400" />
                                        <div>
                                            <p className="text-slate-200">{m.material_name}</p>
                                            <p className="text-sm text-slate-400">
                                                {m.material_type} |{" "}
                                                {(m.file_size / 1024 / 1024).toFixed(2)}MB{" "}
                                                {m.is_required && "(必需)"}
                                            </p>
                                        </div>
                                    </div>
                                    {!isNew && (
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => handleDelete(m.id)}
                                            className="text-red-400 hover:text-red-300"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
