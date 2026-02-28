import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui";

export function LeaveBalanceTable({ balanceRows }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>假期余额</CardTitle>
            </CardHeader>
            <CardContent>
                {balanceRows.length === 0 ? (
                    <div className="text-slate-400 text-sm py-6 text-center">
                        暂无已批准请假记录，无法计算余额使用情况
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-slate-700">
                                    <th className="text-left py-2 pr-2 text-slate-400 font-medium">员工</th>
                                    <th className="text-left py-2 pr-2 text-slate-400 font-medium">部门</th>
                                    <th className="text-right py-2 pl-2 text-slate-400 font-medium">已休(天)</th>
                                    <th className="text-right py-2 pl-2 text-slate-400 font-medium">次数</th>
                                </tr>
                            </thead>
                            <tbody>
                                {balanceRows.map((row) => (
                                    <tr key={row.employee} className="border-b border-slate-800/60">
                                        <td className="py-2 pr-2 text-white">{row.employee}</td>
                                        <td className="py-2 pr-2 text-slate-300">{row.department}</td>
                                        <td className="py-2 pl-2 text-right text-white font-medium">
                                            {row.usedDays.toFixed(1)}
                                        </td>
                                        <td className="py-2 pl-2 text-right text-slate-300">
                                            {row.approvedCount}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
