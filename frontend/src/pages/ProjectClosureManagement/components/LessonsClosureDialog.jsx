import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogBody, DialogFooter, Button } from "../../../components/ui";

export function LessonsClosureDialog({ open, onOpenChange, onSubmit, closure }) {
    const [formData, setFormData] = useState({
        lessons_learned: closure?.lessons_learned || "",
        improvement_suggestions: closure?.improvement_suggestions || ""
    });

    useEffect(() => {
        if (closure) {
            setFormData({
                lessons_learned: closure.lessons_learned || "",
                improvement_suggestions: closure.improvement_suggestions || ""
            });
        }
    }, [closure]);

    const handleSubmit = () => {
        onSubmit(formData);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>编辑经验教训</DialogTitle>
                </DialogHeader>
                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                经验教训
                            </label>
                            <textarea
                                value={formData.lessons_learned}
                                onChange={(e) =>
                                    setFormData({ ...formData, lessons_learned: e.target.value })
                                }
                                placeholder="请总结项目经验教训"
                                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                                rows={5}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                改进建议
                            </label>
                            <textarea
                                value={formData.improvement_suggestions}
                                onChange={(e) =>
                                    setFormData({
                                        ...formData,
                                        improvement_suggestions: e.target.value
                                    })
                                }
                                placeholder="请提出改进建议"
                                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                                rows={4}
                            />
                        </div>
                    </div>
                </DialogBody>
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
