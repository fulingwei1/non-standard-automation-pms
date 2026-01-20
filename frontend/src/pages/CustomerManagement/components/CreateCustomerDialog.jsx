import React, { useState } from "react";
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

const INITIAL_STATE = {
    customer_code: "",
    customer_name: "",
    customer_short_name: "",
    industry: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    address: "",
    remark: ""
};

export function CreateCustomerDialog({ open, onOpenChange, onSubmit }) {
    const [formData, setFormData] = useState(INITIAL_STATE);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = () => {
        if (!formData.customer_code || !formData.customer_name) {
            alert("请填写必填项");
            return;
        }
        onSubmit(formData);
        setFormData(INITIAL_STATE);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>新增客户</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-customer-code" className="text-right">
                            客户编码 *
                        </Label>
                        <Input
                            id="create-customer-code"
                            name="customer_code"
                            value={formData.customer_code}
                            onChange={handleChange}
                            className="col-span-3"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-customer-name" className="text-right">
                            客户名称 *
                        </Label>
                        <Input
                            id="create-customer-name"
                            name="customer_name"
                            value={formData.customer_name}
                            onChange={handleChange}
                            className="col-span-3"
                            required
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-short-name" className="text-right">
                            简称
                        </Label>
                        <Input
                            id="create-short-name"
                            name="customer_short_name"
                            value={formData.customer_short_name}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-industry" className="text-right">
                            行业
                        </Label>
                        <Input
                            id="create-industry"
                            name="industry"
                            value={formData.industry}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-contact-person" className="text-right">
                            联系人
                        </Label>
                        <Input
                            id="create-contact-person"
                            name="contact_person"
                            value={formData.contact_person}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-contact-phone" className="text-right">
                            联系电话
                        </Label>
                        <Input
                            id="create-contact-phone"
                            name="contact_phone"
                            value={formData.contact_phone}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-contact-email" className="text-right">
                            邮箱
                        </Label>
                        <Input
                            id="create-contact-email"
                            name="contact_email"
                            type="email"
                            value={formData.contact_email}
                            onChange={handleChange}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-address" className="text-right">
                            地址
                        </Label>
                        <Input
                            id="create-address"
                            name="address"
                            value={formData.address}
                            onChange={handleChange}
                            className="col-span-3"
                        />
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
