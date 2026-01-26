import React from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import { Label } from "../../../components/ui/label";

export function CustomerDetailDialog({ open, onOpenChange, data }) {
    if (!data) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>客户详情</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4 text-sm">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label className="text-muted-foreground">客户编码</Label>
                            <p className="font-medium font-mono">{data.customer_code}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">客户名称</Label>
                            <p className="font-medium">{data.customer_name}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">简称</Label>
                            <p className="font-medium">{data.customer_short_name || "-"}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">行业</Label>
                            <p className="font-medium">{data.industry || "-"}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">联系人</Label>
                            <p className="font-medium">{data.contact_person || "-"}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">联系电话</Label>
                            <p className="font-medium">{data.contact_phone || "-"}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">邮箱</Label>
                            <p className="font-medium">{data.contact_email || "-"}</p>
                        </div>
                        <div>
                            <Label className="text-muted-foreground">状态</Label>
                            <p className="font-medium">
                                <Badge variant={data.is_active ? "default" : "secondary"}>
                                    {data.is_active ? "启用" : "禁用"}
                                </Badge>
                            </p>
                        </div>
                        <div className="col-span-2">
                            <Label className="text-muted-foreground">地址</Label>
                            <p className="font-medium">{data.address || "-"}</p>
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button onClick={() => onOpenChange(false)}>关闭</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
