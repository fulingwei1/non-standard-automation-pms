

import { getStatusBadge } from "./constants";

/**
 * Renders the "参与人" (Participants) tab content.
 */
export function ParticipantsTab({ isNew, participants, users, onAddParticipant }) {
    return (
        <div className="space-y-4">
            <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>评审参与人</CardTitle>
                    {!isNew && (
                        <Button
                            size="sm"
                            onClick={onAddParticipant}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Plus className="w-4 h-4 mr-2" />
                            添加参与人
                        </Button>
                    )}
                </CardHeader>
                <CardContent>
                    {participants.length === 0 ? (
                        <p className="text-center text-slate-400 py-8">暂无参与人</p>
                    ) : (
                        <div className="space-y-2">
                            {(participants || []).map((p) => {
                                const user = (users || []).find((u) => u.id === p.user_id);
                                const displayName =
                                    user?.real_name || user?.username || `用户${p.user_id}`;
                                return (
                                    <div
                                        key={p.id}
                                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                                    >
                                        <div className="flex items-center gap-3">
                                            <User className="w-5 h-5 text-slate-400" />
                                            <div>
                                                <p className="text-slate-200">{displayName}</p>
                                                <p className="text-sm text-slate-400">
                                                    {p.role} {p.is_required ? "(必需)" : "(可选)"}
                                                </p>
                                            </div>
                                        </div>
                                        <Badge
                                            className={
                                                getStatusBadge(p.attendance || "PENDING").color
                                            }
                                        >
                                            {p.attendance === "CONFIRMED" && "已确认"}
                                            {p.attendance === "ABSENT" && "缺席"}
                                            {p.attendance === "DELEGATED" && "已委派"}
                                            {!p.attendance && "待确认"}
                                        </Badge>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
