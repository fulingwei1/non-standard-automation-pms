import { useState, useEffect } from "react";
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

// 非标自动化常见客户所属行业
const INDUSTRIES = [
    "家电制造", "消费电子/3C", "汽车零部件", "新能源汽车", "动力电池", "光伏",
    "半导体/集成电路", "通信设备", "医疗器械", "精密五金", "智能装备", "其他"
];

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

// 自动生成客户编码：KH-YYYYMMDD-XXXX
function genCustomerCode() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
    return `KH-${stamp}-${String(Date.now()).slice(-4)}`;
}

export function CreateCustomerDialog({ open, onOpenChange, onSubmit }) {
    const [formData, setFormData] = useState(INITIAL_STATE);
    const [errors, setErrors] = useState({});

    // 打开时自动生成编码
    useEffect(() => {
        if (open) {
            setFormData({ ...INITIAL_STATE, customer_code: genCustomerCode() });
            setErrors({});
        }
    }, [open]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
        if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }));
    };

    const handleSubmit = () => {
        const nextErrors = {};
        if (!formData.customer_name || !formData.customer_name.trim()) {
            nextErrors.customer_name = "请填写客户名称";
        }
        if (formData.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
            nextErrors.contact_email = "邮箱格式不正确";
        }
        if (Object.keys(nextErrors).length > 0) {
            setErrors(nextErrors);
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
                            客户编码
                        </Label>
                        <div className="col-span-3">
                            <Input
                                id="create-customer-code"
                                name="customer_code"
                                value={formData.customer_code}
                                readOnly
                                className="bg-muted/50 text-muted-foreground"
                            />
                            <p className="text-xs text-muted-foreground mt-1">系统自动生成，无需填写</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="create-customer-name" className="text-right">
                            客户名称 <span className="text-red-500">*</span>
                        </Label>
                        <div className="col-span-3">
                            <Input
                                id="create-customer-name"
                                name="customer_name"
                                value={formData.customer_name}
                                onChange={handleChange}
                                className={errors.customer_name ? "border-red-500" : ""}
                            />
                            {errors.customer_name && (
                                <p className="text-xs text-red-500 mt-1">{errors.customer_name}</p>
                            )}
                        </div>
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
                        <Select
                            value={formData.industry}
                            onValueChange={(value) =>
                                setFormData((prev) => ({ ...prev, industry: value }))
                            }
                        >
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="请选择行业" />
                            </SelectTrigger>
                            <SelectContent>
                                {INDUSTRIES.map((ind) => (
                                    <SelectItem key={ind} value={ind}>
                                        {ind}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
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
                        <div className="col-span-3">
                            <Input
                                id="create-contact-email"
                                name="contact_email"
                                type="email"
                                value={formData.contact_email}
                                onChange={handleChange}
                                className={errors.contact_email ? "border-red-500" : ""}
                            />
                            {errors.contact_email && (
                                <p className="text-xs text-red-500 mt-1">{errors.contact_email}</p>
                            )}
                        </div>
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
