import { Card, CardContent } from '../../../components/ui';

export function ProjectClosureReview({ closure }) {
    if (closure.status !== "REVIEWED") return null;

    return (
        <Card>
            <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">
                    评审信息
                </h3>
                <div className="space-y-3">
                    <div>
                        <span className="text-sm text-slate-400">评审结果</span>
                        <p className="text-white mt-1">{closure.review_result}</p>
                    </div>
                    {closure.review_notes && (
                        <div>
                            <span className="text-sm text-slate-400">评审记录</span>
                            <p className="text-white mt-1 whitespace-pre-wrap">
                                {closure.review_notes}
                            </p>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
