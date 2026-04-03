import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Button,
    Badge,
} from "../../components/ui";
import { Plus } from "lucide-react";
import { CHECKLIST_RESULT_COLORS } from "./constants";

const RESULT_LABELS = {
    PASS: "通过",
    FAIL: "不通过",
    NA: "不适用",
};

/**
 * Renders the "检查项" (Checklist) tab content.
 */
export function ChecklistTab({ isNew, checklistRecords, onAddChecklist }) {
    return (
        <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>检查项记录</CardTitle>
                    {!isNew && (
                        <Button
                            size="sm"
                            onClick={onAddChecklist}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            添加检查项
                        </Button>
                    )}
                </CardHeader>
                <CardContent>
                    {checklistRecords.length === 0 ? (
                        <p className="text-center text-slate-400 py-8">暂无检查项记录</p>
                    ) : (
                        <div className="space-y-2">
                            {(checklistRecords || []).map((c) => (
                                <div
                                    key={c.id}
                                    className="p-3 bg-slate-800/50 rounded-lg space-y-2"
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="text-slate-200">{c.check_item}</p>
                                            <p className="text-sm text-slate-400">{c.category}</p>
                                        </div>
                                        <Badge
                                            className={
                                                CHECKLIST_RESULT_COLORS[c.result] ||
                                                CHECKLIST_RESULT_COLORS.NA
                                            }
                                        >
                                            {RESULT_LABELS[c.result] ?? c.result}
                                        </Badge>
                                    </div>
                                    {c.issue_desc && (
                                        <p className="text-sm text-amber-400">
                                            问题: {c.issue_desc} (等级: {c.issue_level})
                                        </p>
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
