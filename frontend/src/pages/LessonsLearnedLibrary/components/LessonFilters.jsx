import { Search } from "lucide-react";
import { Card, CardContent, Input } from "../../../components/ui";

export function LessonFilters({
    keyword, setKeyword,
    lessonType, setLessonType,
    category, setCategory,
    status, setStatus,
    priority, setPriority,
    categories
}) {
    return (
        <Card>
            <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                    <Input
                        placeholder="搜索标题或描述..."
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        icon={Search}
                        className="md:col-span-2"
                    />

                    <select
                        value={lessonType || ""}
                        onChange={(e) => setLessonType(e.target.value || null)}
                        className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                        <option value="">全部类型</option>
                        <option value="SUCCESS">成功经验</option>
                        <option value="FAILURE">失败教训</option>
                    </select>
                    <select
                        value={category || ""}
                        onChange={(e) => setCategory(e.target.value || null)}
                        className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                        <option value="">全部分类</option>
                        {categories.map((cat) => (
                            <option key={cat} value={cat}>
                                {cat}
                            </option>
                        ))}
                    </select>
                    <select
                        value={status || ""}
                        onChange={(e) => setStatus(e.target.value || null)}
                        className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                        <option value="">全部状态</option>
                        <option value="OPEN">待处理</option>
                        <option value="IN_PROGRESS">处理中</option>
                        <option value="RESOLVED">已解决</option>
                        <option value="CLOSED">已关闭</option>
                    </select>
                    <select
                        value={priority || ""}
                        onChange={(e) => setPriority(e.target.value || null)}
                        className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                        <option value="">全部优先级</option>
                        <option value="LOW">低</option>
                        <option value="MEDIUM">中</option>
                        <option value="HIGH">高</option>
                    </select>
                </div>
            </CardContent>
        </Card>
    );
}
