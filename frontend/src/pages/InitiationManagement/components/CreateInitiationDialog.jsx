import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter, Button, Input } from "../../../components/ui";

export function CreateInitiationDialog({ open, onOpenChange, onSubmit }) {
    const [formData, setFormData] = useState({
        project_name: "",
        project_type: "NEW",
        project_level: "",
        customer_name: "",
        contract_no: "",
        contract_amount: "",
        required_start_date: "",
        required_end_date: "",
        requirement_summary: "",
        technical_difficulty: "",
        estimated_hours: "",
        resource_requirements: "",
        risk_assessment: ""
    });

    const handleSubmit = () => {
        if (!formData.project_name || !formData.customer_name) {
            alert("请填写项目名称和客户名称");
            return;
        }
        onSubmit(formData);
        setFormData({
            project_name: "",
            project_type: "NEW",
            project_level: "",
            customer_name: "",
            contract_no: "",
            contract_amount: "",
            required_start_date: "",
            required_end_date: "",
            requirement_summary: "",
            technical_difficulty: "",
            estimated_hours: "",
            resource_requirements: "",
            risk_assessment: ""
        });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>新建立项申请</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    项目名称 <span className="text-red-400">*</span>
                                </label>
                                <Input
                                    value={formData.project_name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, project_name: e.target.value })
                                    }
                                    placeholder="请输入项目名称"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    客户名称 <span className="text-red-400">*</span>
                                </label>
                                <Input
                                    value={formData.customer_name}
                                    onChange={(e) =>
                                        setFormData({ ...formData, customer_name: e.target.value })
                                    }
                                    placeholder="请输入客户名称"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    合同编号
                                </label>
                                <Input
                                    value={formData.contract_no}
                                    onChange={(e) =>
                                        setFormData({ ...formData, contract_no: e.target.value })
                                    }
                                    placeholder="请输入合同编号"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    合同金额
                                </label>
                                <Input
                                    type="number"
                                    value={formData.contract_amount}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            contract_amount: e.target.value
                                        })
                                    }
                                    placeholder="请输入合同金额"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    要求开始日期
                                </label>
                                <Input
                                    type="date"
                                    value={formData.required_start_date}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            required_start_date: e.target.value
                                        })
                                    }
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-white mb-2">
                                    要求交付日期
                                </label>
                                <Input
                                    type="date"
                                    value={formData.required_end_date}
                                    onChange={(e) =>
                                        setFormData({
                                            ...formData,
                                            required_end_date: e.target.value
                                        })
                                    }
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                需求概述
                            </label>
                            <textarea
                                value={formData.requirement_summary}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        requirement_summary: e.target.value
                                    })
                                }
                                placeholder="请输入需求概述"
                                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                                rows={3}
                            />
                        </div>
                    </div>
                </DialogBody>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={handleSubmit}>创建</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
