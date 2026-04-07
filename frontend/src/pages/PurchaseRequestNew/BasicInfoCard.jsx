




export default function BasicInfoCard({
  formData,
  setFormData,
  projects,
  machines,
  suppliers,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardHeader>
        <CardTitle className="text-slate-200">基本信息</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-slate-400">所属项目</Label>
            <Select
              value={formData.project_id?.toString() || ""}
              onValueChange={(val) =>
                setFormData({
                  ...formData,
                  project_id: val ? parseInt(val) : null,
                  machine_id: null,
                })
              }
            >
              <SelectTrigger className="bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="选择项目（可选）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">无</SelectItem>
                {(projects || []).map((project) => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    {project.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-slate-400">设备</Label>
            <Select
              value={formData.machine_id?.toString() || ""}
              onValueChange={(val) =>
                setFormData({
                  ...formData,
                  machine_id: val ? parseInt(val) : null,
                })
              }
              disabled={!formData.project_id}
            >
              <SelectTrigger
                className="bg-slate-900/50 border-slate-700"
                disabled={!formData.project_id}
              >
                <SelectValue placeholder="选择设备（可选）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">无</SelectItem>
                {(machines || []).map((machine) => (
                  <SelectItem key={machine.id} value={machine.id.toString()}>
                    {machine.machine_code} - {machine.machine_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-2">
            <Label className="text-slate-400">指定供应商 *</Label>
            <Select
              value={formData.supplier_id?.toString() || ""}
              onValueChange={(val) => {
                if (val === "none") {
                  setFormData({ ...formData, supplier_id: null });
                } else {
                  setFormData({
                    ...formData,
                    supplier_id: parseInt(val),
                  });
                }
              }}
            >
              <SelectTrigger className="bg-slate-900/50 border-slate-700">
                <SelectValue placeholder="选择供应商" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">未指定</SelectItem>
                {(suppliers || []).map((supplier) => (
                  <SelectItem key={supplier.id} value={supplier.id.toString()}>
                    {supplier.supplier_name || supplier.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-slate-400">申请类型</Label>
            <Select
              value={formData.request_type}
              onValueChange={(val) =>
                setFormData({ ...formData, request_type: val })
              }
            >
              <SelectTrigger className="bg-slate-900/50 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NORMAL">普通</SelectItem>
                <SelectItem value="URGENT">紧急</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-slate-400">需求日期</Label>
            <Input
              type="date"
              value={formData.required_date}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  required_date: e.target.value,
                })
              }
              className="bg-slate-900/50 border-slate-700"
            />
          </div>
        </div>
        <div>
          <Label className="text-slate-400">申请原因</Label>
          <Textarea
            value={formData.request_reason}
            onChange={(e) =>
              setFormData({
                ...formData,
                request_reason: e.target.value,
              })
            }
            placeholder="填写申请原因..."
            className="bg-slate-900/50 border-slate-700 text-slate-200"
            rows={3}
          />
        </div>
        <div>
          <Label className="text-slate-400">备注</Label>
          <Textarea
            value={formData.remark}
            onChange={(e) =>
              setFormData({ ...formData, remark: e.target.value })
            }
            placeholder="备注信息（可选）..."
            className="bg-slate-900/50 border-slate-700 text-slate-200"
            rows={2}
          />
        </div>
      </CardContent>
    </Card>
  );
}
