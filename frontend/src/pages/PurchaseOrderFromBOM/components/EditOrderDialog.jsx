import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter } from "../../../components/ui/dialog";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { Textarea } from "../../../components/ui/textarea";

export function EditOrderDialog({ editingOrder, setEditingOrder, onSave }) {
    if (!editingOrder) return null;

    return (
        <Dialog open={!!editingOrder} onOpenChange={() => setEditingOrder(null)}>
            <DialogContent className="max-w-2xl bg-slate-900 border-slate-700">
                <DialogHeader>
                    <DialogTitle className="text-slate-200">编辑订单信息</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <Label className="text-slate-400">订单标题</Label>
                            <Input
                                value={editingOrder.order_title}
                                onChange={(e) =>
                                    setEditingOrder({
                                        ...editingOrder,
                                        order_title: e.target.value
                                    })
                                }
                                className="bg-slate-800 border-slate-700 text-slate-200"
                            />
                        </div>
                        <div>
                            <Label className="text-slate-400">备注</Label>
                            <Textarea
                                value={editingOrder.remark || ""}
                                onChange={(e) =>
                                    setEditingOrder({
                                        ...editingOrder,
                                        remark: e.target.value
                                    })
                                }
                                className="bg-slate-800 border-slate-700 text-slate-200"
                                rows={3}
                            />
                        </div>
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button variant="outline" onClick={() => setEditingOrder(null)}>
                        取消
                    </Button>
                    <Button onClick={onSave}>保存</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
