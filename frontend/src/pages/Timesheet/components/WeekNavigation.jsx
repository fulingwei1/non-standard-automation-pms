import { motion } from "framer-motion";
import { Calendar, ChevronLeft, ChevronRight, Plus, Copy, Save, Send } from "lucide-react";
import { Card, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import { fadeIn } from "../../../lib/animations";
import { formatFullDate } from "../utils/dateUtils";

export function WeekNavigation({
    weekDates,
    weekOffset,
    setWeekOffset,
    isCurrentWeek,
    loading,
    saving,
    entries,
    onAddRecord,
    onCopyLastWeek,
    onSaveDraft,
    onSubmit,
}) {
    return (
        <motion.div variants={fadeIn}>
            <Card className="bg-surface-1/50">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setWeekOffset(weekOffset - 1)}
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </Button>
                            <div className="flex items-center gap-2">
                                <Calendar className="w-5 h-5 text-accent" />
                                <span className="font-medium text-white">
                                    {formatFullDate(weekDates[0])} ~ {formatFullDate(weekDates[6])}
                                </span>
                                {isCurrentWeek && (
                                    <Badge variant="secondary" className="ml-2">
                                        本周
                                    </Badge>
                                )}
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setWeekOffset(weekOffset + 1)}
                                disabled={weekOffset >= 0}
                            >
                                <ChevronRight className="w-4 h-4" />
                            </Button>
                        </div>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" onClick={onAddRecord} disabled={loading}>
                                <Plus className="w-4 h-4 mr-1" />
                                添加记录
                            </Button>
                            <Button
                                variant="outline"
                                onClick={onCopyLastWeek}
                                disabled={loading || weekOffset === 0}
                                title="复制上周的工时记录"
                            >
                                <Copy className="w-4 h-4 mr-1" />
                                复制上周
                            </Button>
                            <Button variant="outline" onClick={onSaveDraft} disabled={loading || saving}>
                                <Save className="w-4 h-4 mr-1" />
                                保存草稿
                            </Button>
                            <Button
                                onClick={onSubmit}
                                disabled={loading || saving || entries.filter((e) => e.status === "DRAFT").length === 0}
                                className="bg-blue-600 hover:bg-blue-700"
                            >
                                <Send className="w-4 h-4 mr-1" />
                                {saving ? "提交中..." : "提交审批"}
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
