import { Card, CardContent, Progress } from '../../../components/ui';

export function ProjectClosureQuality({ closure }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
                <CardContent className="p-5">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        质量评分
                    </h3>
                    {closure.quality_score !== null &&
                        closure.quality_score !== undefined ? (
                        <div className="flex items-center gap-4">
                            <div className="text-4xl font-bold text-primary">
                                {closure.quality_score}
                            </div>
                            <div className="flex-1">
                                <Progress value={closure.quality_score} />
                            </div>
                        </div>
                    ) : (
                        <p className="text-slate-500">未评分</p>
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-5">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        客户满意度
                    </h3>
                    {closure.customer_satisfaction !== null &&
                        closure.customer_satisfaction !== undefined ? (
                        <div className="flex items-center gap-4">
                            <div className="text-4xl font-bold text-emerald-400">
                                {closure.customer_satisfaction}
                            </div>
                            <div className="flex-1">
                                <Progress value={closure.customer_satisfaction} />
                            </div>
                        </div>
                    ) : (
                        <p className="text-slate-500">未评分</p>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
