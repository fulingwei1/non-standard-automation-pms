import { Calculator } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Progress } from "../../../components/ui/progress";

export function SolutionCostTab({ costEstimate }) {
    if (!costEstimate) {
        return (
            <div className="col-span-full text-center py-16 text-slate-400">
                <Calculator className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                <p className="text-lg font-medium">暂无成本估算</p>
                <p className="text-sm">请先进行成本核算</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2 bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">成本明细</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {[
                            {
                                name: "硬件成本",
                                value: costEstimate.hardware_cost || 0,
                                color: "bg-blue-500",
                            },
                            {
                                name: "软件成本",
                                value: costEstimate.software_cost || 0,
                                color: "bg-violet-500",
                            },
                            {
                                name: "治具成本",
                                value: costEstimate.fixture_cost || 0,
                                color: "bg-amber-500",
                            },
                            {
                                name: "安装调试",
                                value: costEstimate.installation_cost || 0,
                                color: "bg-emerald-500",
                            },
                            {
                                name: "培训费用",
                                value: costEstimate.training_cost || 0,
                                color: "bg-pink-500",
                            },
                            {
                                name: "运输费用",
                                value: costEstimate.shipping_cost || 0,
                                color: "bg-slate-500",
                            },
                        ].map((item, index) => {
                            const total = costEstimate.total_cost || 1;
                            return (
                                <div key={index} className="flex items-center gap-4">
                                    <div className="w-24 text-sm text-slate-400">
                                        {item.name}
                                    </div>
                                    <div className="flex-1">
                                        <Progress
                                            value={(item.value / total) * 100}
                                            className="h-2"
                                        />
                                    </div>
                                    <div className="w-28 text-right text-sm text-white">
                                        ¥{item.value.toLocaleString()}
                                    </div>
                                </div>
                            );
                        })}
                        <div className="flex items-center gap-4 pt-4 border-t border-white/5">
                            <div className="w-24 text-sm font-medium text-white">总成本</div>
                            <div className="flex-1" />
                            <div className="w-28 text-right text-lg font-bold text-white">
                                ¥{(costEstimate.total_cost || 0).toLocaleString()}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20">
                <CardHeader>
                    <CardTitle className="text-lg text-emerald-400">利润分析</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="text-center p-4 bg-surface-50/50 rounded-lg">
                        <p className="text-sm text-slate-400 mb-1">报价金额</p>
                        <p className="text-3xl font-bold text-white">
                            ¥{(costEstimate.suggested_price || 0).toLocaleString()}
                        </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                            <p className="text-xs text-slate-400 mb-1">毛利率</p>
                            <p className="text-xl font-bold text-emerald-400">
                                {(costEstimate.gross_margin || 0).toFixed(0)}%
                            </p>
                        </div>
                        <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                            <p className="text-xs text-slate-400 mb-1">预计利润</p>
                            <p className="text-xl font-bold text-emerald-400">
                                ¥
                                {(
                                    (costEstimate.suggested_price || 0) -
                                    (costEstimate.total_cost || 0)
                                ).toLocaleString()}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
