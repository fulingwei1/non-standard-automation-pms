import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Badge,
    Input,
    Select,
} from "../../components/ui";
import { formatDate } from "../../lib/utils";
import { getStatusBadge } from "./constants";

/**
 * Renders the "基本信息" (Basic Info) tab content.
 * Includes the review form fields and, when viewing an existing record,
 * the read-only conclusion panel.
 */
export function BasicInfoTab({ isNew, review, formData, updateField, projects, users }) {
    return (
        <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                    <CardTitle>评审信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                评审类型 *
                            </label>
                            <Select
                                value={formData.review_type}
                                onValueChange={(value) => updateField("review_type", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="PDR">方案设计评审 (PDR)</option>
                                <option value="DDR">详细设计评审 (DDR)</option>
                                <option value="PRR">生产准备评审 (PRR)</option>
                                <option value="FRR">出厂评审 (FRR)</option>
                                <option value="ARR">现场评审 (ARR)</option>
                            </Select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                评审名称 *
                            </label>
                            <Input
                                value={formData.review_name}
                                onChange={(e) => updateField("review_name", e.target.value)}
                                placeholder="请输入评审名称"
                                className="bg-slate-800/50 border-slate-700"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                关联项目 *
                            </label>
                            <Select
                                value={formData.project_id}
                                onValueChange={(value) => updateField("project_id", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="">请选择项目</option>
                                {(projects || []).map((p) => (
                                    <option key={p.id} value={p.id}>
                                        {p.project_code} - {p.project_name}
                                    </option>
                                ))}
                            </Select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                计划评审时间 *
                            </label>
                            <Input
                                type="datetime-local"
                                value={formData.scheduled_date}
                                onChange={(e) => updateField("scheduled_date", e.target.value)}
                                className="bg-slate-800/50 border-slate-700"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                评审地点
                            </label>
                            <Input
                                value={formData.location}
                                onChange={(e) => updateField("location", e.target.value)}
                                placeholder="请输入评审地点"
                                className="bg-slate-800/50 border-slate-700"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                会议形式 *
                            </label>
                            <Select
                                value={formData.meeting_type}
                                onValueChange={(value) => updateField("meeting_type", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="ONSITE">现场</option>
                                <option value="ONLINE">线上</option>
                                <option value="HYBRID">混合</option>
                            </Select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                主持人 *
                            </label>
                            <Select
                                value={formData.host_id}
                                onValueChange={(value) => updateField("host_id", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="">请选择主持人</option>
                                {(users || []).map((u) => (
                                    <option key={u.id} value={u.id}>
                                        {u.real_name || u.username}
                                    </option>
                                ))}
                            </Select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                汇报人 *
                            </label>
                            <Select
                                value={formData.presenter_id}
                                onValueChange={(value) => updateField("presenter_id", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="">请选择汇报人</option>
                                {(users || []).map((u) => (
                                    <option key={u.id} value={u.id}>
                                        {u.real_name || u.username}
                                    </option>
                                ))}
                            </Select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                记录人 *
                            </label>
                            <Select
                                value={formData.recorder_id}
                                onValueChange={(value) => updateField("recorder_id", value)}
                                className="bg-slate-800/50 border-slate-700"
                            >
                                <option value="">请选择记录人</option>
                                {(users || []).map((u) => (
                                    <option key={u.id} value={u.id}>
                                        {u.real_name || u.username}
                                    </option>
                                ))}
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 评审结论（仅查看模式） */}
            {!isNew && review?.conclusion && (
                <Card className="bg-slate-900/50 border-slate-800">
                    <CardHeader>
                        <CardTitle>评审结论</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-slate-400">结论:</span>
                                <Badge className={getStatusBadge(review.conclusion).color}>
                                    {review.conclusion === "PASS" && "通过"}
                                    {review.conclusion === "PASS_WITH_CONDITION" && "有条件通过"}
                                    {review.conclusion === "REJECT" && "不通过"}
                                    {review.conclusion === "ABORT" && "中止"}
                                </Badge>
                            </div>
                            {review.conclusion_summary && (
                                <p className="text-sm text-slate-300">{review.conclusion_summary}</p>
                            )}
                            {review.condition_deadline && (
                                <p className="text-sm text-slate-400">
                                    整改期限: {formatDate(review.condition_deadline, "YYYY-MM-DD")}
                                </p>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
