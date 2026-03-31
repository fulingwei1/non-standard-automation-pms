import { ClipboardCheck, CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent } from '../../components/ui/card';
import { Progress } from '../../components/ui/progress';

/**
 * Four summary stat cards shown at the top of the AcceptanceExecution page:
 * total items, passed, failed, and pass-rate.
 */
export function ExecutionSummaryCards({ totalItems, passedCount, failedCount, totalChecked }) {
    const passRate = totalChecked > 0 ? (passedCount / totalChecked) * 100 : 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-slate-500 mb-1">总项数</div>
                            <div className="text-2xl font-bold">{totalItems}</div>
                        </div>
                        <ClipboardCheck className="w-8 h-8 text-blue-500" />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-slate-500 mb-1">通过</div>
                            <div className="text-2xl font-bold text-emerald-600">{passedCount}</div>
                        </div>
                        <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-slate-500 mb-1">不通过</div>
                            <div className="text-2xl font-bold text-red-600">{failedCount}</div>
                        </div>
                        <XCircle className="w-8 h-8 text-red-500" />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-slate-500 mb-1">通过率</div>
                            <div className="text-2xl font-bold">
                                {passRate.toFixed(1)}%
                            </div>
                        </div>
                        <Progress value={passRate} className="w-16 h-16" />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
