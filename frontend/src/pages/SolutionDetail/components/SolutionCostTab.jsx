import { Calculator } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Progress } from "../../../components/ui/progress";

const toNumber = (value) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
};

const formatCurrency = (value) => `¥${toNumber(value).toLocaleString()}`;

const formatQuantity = (quantity, unit) => {
    const number = toNumber(quantity);
    if (!number) {
        return "";
    }

    return `${Number.isInteger(number) ? number : number.toFixed(2)}${unit || ""}`;
};

const categoryColors = {
    硬件: "bg-blue-500",
    软件: "bg-violet-500",
    治具: "bg-amber-500",
    安装调试: "bg-emerald-500",
    培训: "bg-pink-500",
    运输: "bg-slate-500",
};

const legacyCostRows = (costEstimate) => [
    {
        name: "硬件成本",
        category: "硬件",
        value: costEstimate.hardware_cost || 0,
        color: categoryColors["硬件"],
    },
    {
        name: "软件成本",
        category: "软件",
        value: costEstimate.software_cost || 0,
        color: categoryColors["软件"],
    },
    {
        name: "治具成本",
        category: "治具",
        value: costEstimate.fixture_cost || 0,
        color: categoryColors["治具"],
    },
    {
        name: "安装调试",
        category: "安装调试",
        value: costEstimate.installation_cost || 0,
        color: categoryColors["安装调试"],
    },
    {
        name: "培训费用",
        category: "培训",
        value: costEstimate.training_cost || 0,
        color: categoryColors["培训"],
    },
    {
        name: "运输费用",
        category: "运输",
        value: costEstimate.shipping_cost || 0,
        color: categoryColors["运输"],
    },
];

const getCostRows = (costEstimate) => {
    if (Array.isArray(costEstimate.breakdown) && costEstimate.breakdown.length > 0) {
        return costEstimate.breakdown.map((item) => {
            const quantity = toNumber(item.quantity);
            const unitPrice = toNumber(item.unit_price);
            const amount = toNumber(item.amount) || quantity * unitPrice;
            const category = item.category || "成本项";

            return {
                name: item.item_name || item.name || category,
                category,
                quantity: formatQuantity(quantity, item.unit),
                specification: item.specification || "",
                value: amount,
                color: categoryColors[category] || "bg-slate-500",
            };
        });
    }

    return legacyCostRows(costEstimate);
};

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

    const rows = getCostRows(costEstimate);
    const totalCost =
        toNumber(costEstimate.total_cost) ||
        rows.reduce((sum, item) => sum + toNumber(item.value), 0);
    const suggestedPrice = toNumber(costEstimate.suggested_price);
    const profit = suggestedPrice - totalCost;
    const grossMargin =
        costEstimate.gross_margin != null
            ? toNumber(costEstimate.gross_margin)
            : suggestedPrice > 0
                ? (profit / suggestedPrice) * 100
                : 0;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2 bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">成本明细</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {rows.map((item, index) => {
                            const total = totalCost || 1;
                            return (
                                <div key={index} className="flex items-center gap-4">
                                    <div className="w-36 text-sm">
                                        <div className="text-white">{item.name}</div>
                                        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                                            <span>{item.category}</span>
                                            {item.quantity && <span>{item.quantity}</span>}
                                            {item.specification && <span>{item.specification}</span>}
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <Progress
                                            value={(item.value / total) * 100}
                                            className="h-2"
                                        />
                                    </div>
                                    <div className="w-28 text-right text-sm text-white">
                                        {formatCurrency(item.value)}
                                    </div>
                                </div>
                            );
                        })}
                        <div className="flex items-center gap-4 pt-4 border-t border-white/5">
                            <div className="w-24 text-sm font-medium text-white">总成本</div>
                            <div className="flex-1" />
                            <div className="w-28 text-right text-lg font-bold text-white">
                                {formatCurrency(totalCost)}
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
                            {formatCurrency(suggestedPrice)}
                        </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                            <p className="text-xs text-slate-400 mb-1">毛利率</p>
                            <p className="text-xl font-bold text-emerald-400">
                                {grossMargin.toFixed(0)}%
                            </p>
                        </div>
                        <div className="text-center p-3 bg-surface-50/50 rounded-lg">
                            <p className="text-xs text-slate-400 mb-1">预计利润</p>
                            <p className="text-xl font-bold text-emerald-400">
                                {formatCurrency(profit)}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
