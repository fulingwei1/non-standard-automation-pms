import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import { Button, Card, CardContent, SkeletonCard, Badge } from "../../../components/ui";
import { cn, formatDate } from "../../../lib/utils";
import { getLessonTypeBadge, getStatusBadge, getPriorityBadge } from '../constants';

const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05, delayChildren: 0.1 }
    }
};

const staggerChild = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
};

export function LessonList({ loading, lessons, total, page, pageSize, setPage, onViewReview }) {
    if (loading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map((i) => <SkeletonCard key={i} />)}
            </div>
        );
    }

    if (lessons.length === 0) {
        return (
            <Card>
                <CardContent className="p-12 text-center">
                    <p className="text-slate-400">暂无经验教训</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <motion.div variants={staggerContainer} className="space-y-4">
                {lessons.map((lesson) => {
                    const typeBadge = getLessonTypeBadge(lesson.lesson_type);
                    const statusBadge = getStatusBadge(lesson.status);
                    const priorityBadge = getPriorityBadge(lesson.priority);
                    const TypeIcon = typeBadge.icon;

                    return (
                        <motion.div key={lesson.id} variants={staggerChild}>
                            <Card className="hover:border-primary/50 transition-colors">
                                <CardContent className="p-6">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1 space-y-3">
                                            <div className="flex items-center gap-3">
                                                <TypeIcon className={cn("h-5 w-5", typeBadge.color)} />
                                                <h3 className="text-lg font-semibold text-white">
                                                    {lesson.title}
                                                </h3>
                                                <Badge variant={typeBadge.variant}>{typeBadge.label}</Badge>
                                                <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
                                                <Badge variant={priorityBadge.variant}>{priorityBadge.label}</Badge>
                                            </div>
                                            <p className="text-slate-300 line-clamp-2">
                                                {lesson.description}
                                            </p>
                                            <div className="flex items-center gap-4 text-sm text-slate-400">
                                                {lesson.project_code && (
                                                    <span>
                                                        项目: {lesson.project_code} {lesson.project_name}
                                                    </span>
                                                )}
                                                {lesson.category && <span>分类: {lesson.category}</span>}
                                                {lesson.responsible_person && (
                                                    <span>责任人: {lesson.responsible_person}</span>
                                                )}
                                                {lesson.due_date && <span>截止: {formatDate(lesson.due_date)}</span>}
                                                {lesson.resolved_date && (
                                                    <span className="text-emerald-400">
                                                        已解决: {formatDate(lesson.resolved_date)}
                                                    </span>
                                                )}
                                            </div>
                                            {lesson.root_cause && (
                                                <div className="mt-3 p-3 bg-surface-2 rounded-md">
                                                    <p className="text-sm text-slate-300">
                                                        <span className="font-medium">根本原因:</span>{" "}
                                                        {lesson.root_cause}
                                                    </p>
                                                </div>
                                            )}
                                            {lesson.improvement_action && (
                                                <div className="mt-2 p-3 bg-surface-2 rounded-md">
                                                    <p className="text-sm text-slate-300">
                                                        <span className="font-medium">改进措施:</span>{" "}
                                                        {lesson.improvement_action}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                        <div className="ml-4 flex gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onViewReview(lesson.review_id)}
                                            >
                                                <Eye className="h-4 w-4 mr-2" />
                                                查看复盘
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    );
                })}
            </motion.div>

            {total > pageSize && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-400">
                        共 {total} 条记录，第 {page} 页
                    </p>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                        >
                            上一页
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => p + 1)}
                            disabled={page * pageSize >= total}
                        >
                            下一页
                        </Button>
                    </div>
                </div>
            )}
        </>
    );
}
