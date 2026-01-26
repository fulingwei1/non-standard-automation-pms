import React, { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "../../../components/ui/select";

export function EditCustomerDialog({ open, onOpenChange, data, onSubmit }) {
    const [formData, setFormData] = useState(null);

    useEffect(() => {
        if (data) {
            setFormData({ ...data });
        }
    }, [data]);

    if (!formData) return null;

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = () => {
        onSubmit(formData.id, formData);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>编辑客户</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-customer-name" className="text-right">
                            客户名称
                        </Label>
                        <Input
                            id="edit-customer-name"
                            name="customer_name"
                            value={formData.customer_name || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-short-name" className="text-right">
                            简称
                        </Label>
                        <Input
                            id="edit-short-name"
                            name="customer_short_name"
                            value={formData.customer_short_name || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-industry" className="text-right">
                            行业
                        </Label>
                        <Input
                            id="edit-industry"
                            name="industry"
                            value={formData.industry || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-contact-person" className="text-right">
                            联系人
                        </Label>
                        <Input
                            id="edit-contact-person"
                            name="contact_person"
                            value={formData.contact_person || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-contact-phone" className="text-right">
                            联系电话
                        </Label>
                        <Input
                            id="edit-contact-phone"
                            name="contact_phone"
                            value={formData.contact_phone || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-contact-email" className="text-right">
                            邮箱
                        </Label>
                        <Input
                            id="edit-contact-email"
                            name="contact_email"
                            type="email"
                            value={formData.contact_email || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-address" className="text-right">
                            地址
                        </Label>
                        <Input
                            id="edit-address"
                            name="address"
                            value={formData.address || ""}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-is-active" className="text-right">
                            状态
                        </Label>
                        <Select
                            value={formData.is_active ? "active" : "inactive"}
                            onValueChange={(value) =>
                                setFormData((prev) => ({
                                    ...prev,
                                    is_active: value === "active"
                                }))
                            }
                        >
                            <SelectTrigger className="col-span-3">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="active">启用</SelectItem>
                                <SelectItem value="inactive">禁用</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={handleSubmit}>保存</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
