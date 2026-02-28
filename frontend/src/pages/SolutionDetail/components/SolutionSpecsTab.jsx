import { Badge } from "../../../components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";

export function SolutionSpecsTab({ solution }) {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">产品信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                    {Object.entries(solution.techSpecs.productInfo).map(
                        ([key, value]) => (
                            <div key={key} className="flex justify-between">
                                <span className="text-slate-500">
                                    {key === "name"
                                        ? "产品名称"
                                        : key === "model"
                                            ? "型号规格"
                                            : key === "size"
                                                ? "外形尺寸"
                                                : key === "weight"
                                                    ? "重量"
                                                    : "材质"}
                                </span>
                                <span className="text-white">{value}</span>
                            </div>
                        ),
                    )}
                </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">产能参数</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                    <div className="flex justify-between">
                        <span className="text-slate-500">UPH</span>
                        <span className="text-white">
                            {solution.techSpecs.capacity.uph} pcs/h
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">节拍</span>
                        <span className="text-white">
                            {solution.techSpecs.capacity.cycleTime} 秒/件
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">日产能</span>
                        <span className="text-white">
                            {solution.techSpecs.capacity.dailyOutput} pcs
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">测试通道</span>
                        <span className="text-white">
                            {solution.techSpecs.capacity.channels} 通道
                        </span>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">测试项目</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-2">
                        {solution.techSpecs.testItems.map((item, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                                {item}
                            </Badge>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">执行标准</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-2">
                        {solution.techSpecs.testStandards.map((standard, index) => (
                            <Badge key={index} className="text-xs bg-blue-500">
                                {standard}
                            </Badge>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <Card className="lg:col-span-2 bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg">环境要求</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {Object.entries(solution.techSpecs.environment).map(
                            ([key, value]) => (
                                <div
                                    key={key}
                                    className="text-center p-3 bg-surface-50 rounded-lg"
                                >
                                    <p className="text-xs text-slate-500 mb-1">
                                        {key === "temperature"
                                            ? "温度范围"
                                            : key === "humidity"
                                                ? "湿度范围"
                                                : key === "power"
                                                    ? "电源"
                                                    : key === "airPressure"
                                                        ? "气压"
                                                        : "占地面积"}
                                    </p>
                                    <p className="text-sm font-medium text-white">{value}</p>
                                </div>
                            ),
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
