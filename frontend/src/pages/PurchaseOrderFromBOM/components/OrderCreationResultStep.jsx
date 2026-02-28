import React from 'react';
import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { fadeIn } from "../../../lib/animations";
import { useNavigate } from "react-router-dom";

export function OrderCreationResultStep({ createdOrders, onReset }) {
    const navigate = useNavigate();
    if (!createdOrders) return null;

    return (
        <motion.div variants={fadeIn} className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                    <CardTitle className="text-slate-200 flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        创建成功
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                        已成功创建 {createdOrders.length} 个采购订单
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        {(createdOrders || []).map((order, index) => (
                            <div
                                key={index}
                                className="p-3 border border-slate-700 rounded-lg bg-slate-900/30 flex items-center justify-between"
                            >
                                <div>
                                    <p className="text-slate-200 font-mono">{order.order_no}</p>
                                    <p className="text-slate-400 text-sm">
                                        {order.supplier_name}
                                    </p>
                                </div>
                                <div className="text-right">
                                    <p className="text-slate-200 font-bold">
                                        ¥{order.total_amount?.toFixed(2)}
                                    </p>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => navigate(`/purchases/${order.order_id}`)}
                                    >
                                        查看
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="flex gap-2 pt-4">
                        <Button
                            variant="outline"
                            onClick={onReset}
                            className="flex-1"
                        >
                            继续创建
                        </Button>
                        <Button
                            onClick={() => navigate("/purchases")}
                            className="flex-1 bg-blue-600 hover:bg-blue-700"
                        >
                            查看订单列表
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
