import React from 'react';
import { Package, Settings, Cpu, Wrench, Box } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";

export function SolutionEquipmentTab({ solution }) {
    return (
        <div className="space-y-6">
            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Package className="w-5 h-5 text-primary" />
                        主要设备
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="text-xs text-slate-400 border-b border-white/5">
                                <tr>
                                    <th className="text-left py-2">设备名称</th>
                                    <th className="text-left py-2">型号规格</th>
                                    <th className="text-right py-2">数量</th>
                                    <th className="text-right py-2">单价</th>
                                    <th className="text-right py-2">总价</th>
                                </tr>
                            </thead>
                            <tbody>
                                {solution.equipment.main.map((item, index) => (
                                    <tr key={index} className="border-b border-white/5">
                                        <td className="py-3 text-white">{item.name}</td>
                                        <td className="py-3 text-slate-400">{item.model}</td>
                                        <td className="py-3 text-right text-white">{item.qty}</td>
                                        <td className="py-3 text-right text-slate-400">
                                            ¥{item.unitPrice.toLocaleString()}
                                        </td>
                                        <td className="py-3 text-right text-emerald-400">
                                            ¥{item.totalPrice.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Settings className="w-5 h-5 text-primary" />
                        配套设备
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="text-xs text-slate-400 border-b border-white/5">
                                <tr>
                                    <th className="text-left py-2">设备名称</th>
                                    <th className="text-left py-2">型号规格</th>
                                    <th className="text-right py-2">数量</th>
                                    <th className="text-right py-2">单价</th>
                                    <th className="text-right py-2">总价</th>
                                </tr>
                            </thead>
                            <tbody>
                                {solution.equipment.auxiliary.map((item, index) => (
                                    <tr key={index} className="border-b border-white/5">
                                        <td className="py-3 text-white">{item.name}</td>
                                        <td className="py-3 text-slate-400">{item.model}</td>
                                        <td className="py-3 text-right text-white">{item.qty}</td>
                                        <td className="py-3 text-right text-slate-400">
                                            ¥{item.unitPrice.toLocaleString()}
                                        </td>
                                        <td className="py-3 text-right text-emerald-400">
                                            ¥{item.totalPrice.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Cpu className="w-5 h-5 text-primary" />
                            软件系统
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {solution.equipment.software.map((item, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                            >
                                <div>
                                    <p className="text-sm font-medium text-white">{item.name}</p>
                                    <p className="text-xs text-slate-500">{item.version}</p>
                                </div>
                                <span className="text-sm text-emerald-400">
                                    ¥{item.price.toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Wrench className="w-5 h-5 text-primary" />
                            治具夹具
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {solution.equipment.fixtures.map((item, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                            >
                                <div>
                                    <p className="text-sm font-medium text-white">{item.name}</p>
                                    <p className="text-xs text-slate-500">
                                        {item.model} × {item.qty}
                                    </p>
                                </div>
                                <span className="text-sm text-emerald-400">
                                    ¥{item.totalPrice.toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
