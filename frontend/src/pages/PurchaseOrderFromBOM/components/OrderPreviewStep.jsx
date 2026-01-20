import React from 'react';
import { motion } from "framer-motion";
import { Edit } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Label } from "../../../components/ui/label";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "../../../components/ui/table";
import { fadeIn } from "../../../lib/animations";

export function OrderPreviewStep({
    preview,
    loading,
    onEditOrder,
    onReset,
    onCreate
}) {
    if (!preview) return null;

    return (
        <motion.div variants={fadeIn} className="space-y-6">
            {/* Summary */}
            <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                    <CardTitle className="text-slate-200">预览汇总</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <Label className="text-slate-400">BOM编号</Label>
                            <p className="text-slate-200 font-mono">{preview.bom_no}</p>
                        </div>
                        <div>
                            <Label className="text-slate-400">订单数量</Label>
                            <p className="text-slate-200 text-2xl font-bold">
                                {preview.summary?.total_orders || 0}
                            </p>
                        </div>
                        <div>
                            <Label className="text-slate-400">物料数量</Label>
                            <p className="text-slate-200 text-2xl font-bold">
                                {preview.summary?.total_items || 0}
                            </p>
                        </div>
                        <div>
                            <Label className="text-slate-400">总金额（含税）</Label>
                            <p className="text-slate-200 text-2xl font-bold text-emerald-400">
                                ¥{preview.summary?.total_amount_with_tax?.toFixed(2) || "0.00"}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Orders Preview */}
            <div className="space-y-4">
                {preview.preview?.map((order, index) => (
                    <Card key={index} className="bg-slate-800/50 border-slate-700/50">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle className="text-slate-200">
                                        订单 {index + 1}: {order.supplier_name}
                                    </CardTitle>
                                    <CardDescription className="text-slate-400">
                                        {order.order_title}
                                    </CardDescription>
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => onEditOrder(index)}
                                    >
                                        <Edit className="w-4 h-4 mr-1" />
                                        编辑
                                    </Button>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <Label className="text-slate-400">供应商</Label>
                                        <p className="text-slate-200">{order.supplier_name}</p>
                                    </div>
                                    <div>
                                        <Label className="text-slate-400">项目</Label>
                                        <p className="text-slate-200">{order.project_name || "-"}</p>
                                    </div>
                                    <div>
                                        <Label className="text-slate-400">物料数量</Label>
                                        <p className="text-slate-200">{order.item_count}</p>
                                    </div>
                                    <div>
                                        <Label className="text-slate-400">总金额</Label>
                                        <p className="text-slate-200">
                                            ¥{order.total_amount?.toFixed(2)}
                                        </p>
                                    </div>
                                    <div>
                                        <Label className="text-slate-400">税额</Label>
                                        <p className="text-slate-200">
                                            ¥{order.tax_amount?.toFixed(2)}
                                        </p>
                                    </div>
                                    <div>
                                        <Label className="text-slate-400">含税金额</Label>
                                        <p className="text-slate-200 text-emerald-400 font-bold">
                                            ¥{order.amount_with_tax?.toFixed(2)}
                                        </p>
                                    </div>
                                </div>

                                {/* Items Table */}
                                <div className="overflow-x-auto">
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-slate-700">
                                                <TableHead className="text-slate-400">序号</TableHead>
                                                <TableHead className="text-slate-400">物料编码</TableHead>
                                                <TableHead className="text-slate-400">物料名称</TableHead>
                                                <TableHead className="text-slate-400">规格</TableHead>
                                                <TableHead className="text-slate-400">单位</TableHead>
                                                <TableHead className="text-slate-400 text-right">数量</TableHead>
                                                <TableHead className="text-slate-400 text-right">单价</TableHead>
                                                <TableHead className="text-slate-400 text-right">金额</TableHead>
                                                <TableHead className="text-slate-400 text-right">税额</TableHead>
                                                <TableHead className="text-slate-400 text-right">含税金额</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {order.items?.map((item, itemIndex) => (
                                                <TableRow key={itemIndex} className="border-slate-700">
                                                    <TableCell className="text-slate-300">
                                                        {item.item_no}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300 font-mono text-xs">
                                                        {item.material_code}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300">
                                                        {item.material_name}
                                                    </TableCell>
                                                    <TableCell className="text-slate-400 text-sm">
                                                        {item.specification || "-"}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300">
                                                        {item.unit}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300 text-right">
                                                        {item.quantity}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300 text-right">
                                                        ¥{item.unit_price?.toFixed(2)}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300 text-right">
                                                        ¥{item.amount?.toFixed(2)}
                                                    </TableCell>
                                                    <TableCell className="text-slate-300 text-right">
                                                        ¥{item.tax_amount?.toFixed(2)}
                                                    </TableCell>
                                                    <TableCell className="text-slate-200 text-right font-medium">
                                                        ¥{item.amount_with_tax?.toFixed(2)}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Actions */}
            <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={onReset}>
                    重新选择
                </Button>
                <Button
                    onClick={onCreate}
                    disabled={loading}
                    className="bg-emerald-600 hover:bg-emerald-700"
                >
                    {loading
                        ? "创建中..."
                        : `创建 ${preview.preview?.length || 0} 个采购订单`}
                </Button>
            </div>
        </motion.div>
    );
}
