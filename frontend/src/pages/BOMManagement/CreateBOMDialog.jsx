




/**
 * CreateBOMDialog — form to create a new BOM.
 */
export default function CreateBOMDialog({
    open,
    onOpenChange,
    newBom,
    setNewBom,
    projects,
    machines,
    onProjectChange,
    onSubmit,
}) {
    const selectedProjectId =
        newBom.machine_id
            ? projects
                  .find(
                      (p) =>
                          (machines || []).find((m) => m.id === newBom.machine_id)
                              ?.project_id === p.id
                  )
                  ?.id?.toString() || ''
            : '';

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>新建BOM</DialogTitle>
                </DialogHeader>

                <DialogBody>
                    <div className="space-y-4">
                        {/* Project */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">项目</label>
                            <Select
                                value={selectedProjectId}
                                onValueChange={onProjectChange}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="选择项目" />
                                </SelectTrigger>
                                <SelectContent>
                                    {(projects || []).map((proj) => (
                                        <SelectItem key={proj.id} value={proj.id.toString()}>
                                            {proj.project_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Machine */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">机台</label>
                            <Select
                                value={newBom.machine_id?.toString() || ''}
                                onValueChange={(val) =>
                                    setNewBom({ ...newBom, machine_id: parseInt(val) })
                                }
                                disabled={!newBom.machine_id && machines.length === 0}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="选择机台" />
                                </SelectTrigger>
                                <SelectContent>
                                    {(machines || []).map((machine) => (
                                        <SelectItem
                                            key={machine.id}
                                            value={machine.id.toString()}
                                        >
                                            {machine.machine_name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* BOM name */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">BOM名称</label>
                            <Input
                                value={newBom.bom_name}
                                onChange={(e) =>
                                    setNewBom({ ...newBom, bom_name: e.target.value })
                                }
                                placeholder="请输入BOM名称"
                            />
                        </div>

                        {/* Version */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">版本</label>
                            <Input
                                value={newBom.version}
                                onChange={(e) =>
                                    setNewBom({ ...newBom, version: e.target.value })
                                }
                                placeholder="1.0"
                            />
                        </div>

                        {/* Remark */}
                        <div>
                            <label className="text-sm font-medium mb-2 block">备注</label>
                            <Input
                                value={newBom.remark}
                                onChange={(e) =>
                                    setNewBom({ ...newBom, remark: e.target.value })
                                }
                                placeholder="备注信息"
                            />
                        </div>
                    </div>
                </DialogBody>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={onSubmit}>创建</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
