import { motion } from "framer-motion";
import { Package } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Label } from "../../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../components/ui/select";
import { EmptyState } from "../../../components/common";
import { fadeIn } from "../../../lib/animations";

export function BOMSelectionStep({
    boms,
    suppliers,
    selectedBomId,
    setSelectedBomId,
    defaultSupplierId,
    setDefaultSupplierId,
    loading,
    onGenerate
}) {
    return (
        <motion.div variants={fadeIn} className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                    <CardTitle className="text-slate-200">选择BOM</CardTitle>
                    <CardDescription className="text-slate-400">
                        选择要生成采购订单的BOM，系统将按供应商自动分组物料
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {boms.length === 0 ? (
                        <EmptyState
                            icon={Package}
                            title="暂无已发布的BOM"
                            description="请先在BOM管理中发布BOM，然后才能生成采购订单"
                        />
                    ) : (
                        <>
                            <div>
                                <Label className="text-slate-400">BOM *</Label>
                                <Select
                                    value={selectedBomId?.toString() || ""}
                                    onValueChange={setSelectedBomId}
                                >
                                    <SelectTrigger className="bg-slate-900/50 border-slate-700">
                                        <SelectValue placeholder="选择BOM" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {boms.map((bom) => (
                                            <SelectItem key={bom.id} value={bom.id.toString()}>
                                                {bom.bom_no} - {bom.project_name || bom.machine_name || ""}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <Label className="text-slate-400">默认供应商（可选）</Label>
                                <Select
                                    value={defaultSupplierId?.toString() || ""}
                                    onValueChange={(val) =>
                                        setDefaultSupplierId(val ? parseInt(val) : null)
                                    }
                                >
                                    <SelectTrigger className="bg-slate-900/50 border-slate-700">
                                        <SelectValue placeholder="选择默认供应商（可选）" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="none">无</SelectItem>
                                        {suppliers.map((supplier) => (
                                            <SelectItem key={supplier.id} value={supplier.id.toString()}>
                                                {supplier.supplier_name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-slate-500 mt-1">
                                    如果BOM物料没有指定供应商，将使用此默认供应商
                                </p>
                            </div>
                            <div className="flex gap-2 pt-4">
                                <Button
                                    onClick={onGenerate}
                                    disabled={!selectedBomId || loading}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                                >
                                    {loading ? "生成中..." : "生成预览"}
                                </Button>
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>
        </motion.div>
    );
}
