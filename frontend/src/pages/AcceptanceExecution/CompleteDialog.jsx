



import { overallResultConfigs } from './constants';

/**
 * Dialog for finalising an acceptance order with an overall result,
 * conclusion text, and optional conditions (when result is CONDITIONAL).
 */
export function CompleteDialog({
    open,
    onOpenChange,
    completeData,
    setCompleteData,
    onComplete,
}) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>完成验收</DialogTitle>
                </DialogHeader>

                <DialogBody>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                总体结果 *
                            </label>
                            <Select
                                value={completeData.overall_result}
                                onValueChange={(val) =>
                                    setCompleteData({ ...completeData, overall_result: val })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(overallResultConfigs).map(([key, config]) => (
                                        <SelectItem key={key} value={key || 'unknown'}>
                                            {config.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        <div>
                            <label className="text-sm font-medium mb-2 block">
                                验收结论
                            </label>
                            <textarea
                                className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={completeData.conclusion}
                                onChange={(e) =>
                                    setCompleteData({
                                        ...completeData,
                                        conclusion: e.target.value,
                                    })
                                }
                                placeholder="验收结论..."
                            />
                        </div>

                        {completeData.overall_result === 'CONDITIONAL' && (
                            <div>
                                <label className="text-sm font-medium mb-2 block">
                                    通过条件
                                </label>
                                <textarea
                                    className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    value={completeData.conditions}
                                    onChange={(e) =>
                                        setCompleteData({
                                            ...completeData,
                                            conditions: e.target.value,
                                        })
                                    }
                                    placeholder="通过条件..."
                                />
                            </div>
                        )}
                    </div>
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onComplete}>完成验收</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
