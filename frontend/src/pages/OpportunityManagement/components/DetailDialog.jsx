/**
 * 商机详情对话框（含编辑模式）
 */

import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
  Button, Input, Label, Textarea, Badge,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { stageConfig, buildDetailForm } from "../constants";

// 只读/编辑切换的字段渲染
function EditableField({ label, editing, value, onChange, type = "text", children }) {
  if (editing) {
    if (type === "textarea") {
      return (
        <div>
          <Label className="text-slate-400">{label}</Label>
          <Textarea value={value || ""} onChange={onChange} rows={2} />
        </div>
      );
    }
    return (
      <div>
        <Label className="text-slate-400">{label}</Label>
        <Input type={type} value={value ?? ""} onChange={onChange} />
      </div>
    );
  }
  return (
    <div>
      <Label className="text-slate-400">{label}</Label>
      {children || <p className="text-white">{value || "-"}</p>}
    </div>
  );
}

export function DetailDialog({
  open, onOpenChange,
  selectedOpp,
  detailEditing, setDetailEditing,
  detailSaving,
  detailForm, setDetailForm,
  detailData,
  onSave,
}) {
  if (!selectedOpp) return null;

  // 更新 detailForm 的便捷方法
  const updateField = (field) => (e) =>
    setDetailForm({ ...detailForm, [field]: e.target.value });
  const updateRequirement = (field) => (e) =>
    setDetailForm({
      ...detailForm,
      requirement: { ...detailForm?.requirement, [field]: e.target.value },
    });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>商机详情</DialogTitle>
          <DialogDescription>查看商机详细信息和需求</DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          {/* 基本信息 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">基本信息</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-400">商机编码</Label>
                <p className="text-white">{selectedOpp.opp_code}</p>
              </div>
              <EditableField
                label="商机名称"
                editing={detailEditing}
                value={detailEditing ? detailForm?.opp_name : detailData?.opp_name}
                onChange={updateField("opp_name")}
              />
              <div>
                <Label className="text-slate-400">客户</Label>
                <p className="text-white">{selectedOpp.customer_name}</p>
              </div>
              <div>
                <Label className="text-slate-400">负责人</Label>
                <p className="text-white">{selectedOpp.owner_name || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">阶段</Label>
                {detailEditing ? (
                  <select
                    value={detailForm?.stage || "DISCOVERY"}
                    onChange={updateField("stage")}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    {Object.entries(stageConfig).map(([key, config]) => (
                      <option key={key} value={key || "unknown"}>
                        {config.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <Badge className={cn(stageConfig[selectedOpp.stage]?.color, "mt-1")}>
                    {stageConfig[selectedOpp.stage]?.label}
                  </Badge>
                )}
              </div>
              <EditableField
                label="项目类型" editing={detailEditing}
                value={detailEditing ? detailForm?.project_type : detailData?.project_type}
                onChange={updateField("project_type")}
              />
              <EditableField
                label="设备类型" editing={detailEditing}
                value={detailEditing ? detailForm?.equipment_type : detailData?.equipment_type}
                onChange={updateField("equipment_type")}
              />
              <EditableField
                label="预估金额" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.est_amount : detailData?.est_amount}
                onChange={updateField("est_amount")}
              >
                <p className="text-white">
                  {detailData?.est_amount
                    ? parseFloat(detailData.est_amount).toLocaleString() + " 元"
                    : "-"}
                </p>
              </EditableField>
              <EditableField
                label="预估毛利率" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.est_margin : detailData?.est_margin}
                onChange={updateField("est_margin")}
              >
                <p className="text-white">
                  {detailData?.est_margin ? detailData.est_margin + "%" : "-"}
                </p>
              </EditableField>
              <EditableField
                label="预算范围" editing={detailEditing}
                value={detailEditing ? detailForm?.budget_range : detailData?.budget_range}
                onChange={updateField("budget_range")}
              />
              <EditableField
                label="交付窗口" editing={detailEditing}
                value={detailEditing ? detailForm?.delivery_window : detailData?.delivery_window}
                onChange={updateField("delivery_window")}
              />
              <div className="col-span-2">
                <EditableField
                  label="决策链" editing={detailEditing} type="textarea"
                  value={detailEditing ? detailForm?.decision_chain : detailData?.decision_chain}
                  onChange={updateField("decision_chain")}
                >
                  <p className="text-white mt-1">{detailData?.decision_chain || "-"}</p>
                </EditableField>
              </div>
              <div className="col-span-2">
                <EditableField
                  label="验收依据" editing={detailEditing} type="textarea"
                  value={detailEditing ? detailForm?.acceptance_basis : detailData?.acceptance_basis}
                  onChange={updateField("acceptance_basis")}
                >
                  <p className="text-white mt-1">{detailData?.acceptance_basis || "-"}</p>
                </EditableField>
              </div>
            </div>
          </div>

          {/* 扩展信息 */}
          <div>
            <h3 className="text-lg font-semibold mb-4">扩展信息</h3>
            <div className="grid grid-cols-2 gap-4">
              <EditableField
                label="成交概率 (%)" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.probability : detailData?.probability}
                onChange={updateField("probability")}
              />
              <EditableField
                label="预计成交日期" editing={detailEditing} type="date"
                value={detailEditing ? detailForm?.expected_close_date : detailData?.expected_close_date}
                onChange={updateField("expected_close_date")}
              />
              <div>
                <Label className="text-slate-400">风险等级</Label>
                {detailEditing ? (
                  <select
                    value={detailForm?.risk_level || ""}
                    onChange={updateField("risk_level")}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    <option value="">未设置</option>
                    <option value="LOW">低</option>
                    <option value="MEDIUM">中</option>
                    <option value="HIGH">高</option>
                  </select>
                ) : (
                  <p className="text-white">{detailData?.risk_level || "-"}</p>
                )}
              </div>
              <EditableField
                label="评分" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.score : detailData?.score}
                onChange={updateField("score")}
              />
              <EditableField
                label="优先级得分" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.priority_score : detailData?.priority_score}
                onChange={updateField("priority_score")}
              />
              <EditableField
                label="需求成熟度" editing={detailEditing} type="number"
                value={detailEditing ? detailForm?.requirement_maturity : detailData?.requirement_maturity}
                onChange={updateField("requirement_maturity")}
              />
              <EditableField
                label="技术评估状态" editing={detailEditing}
                value={detailEditing ? detailForm?.assessment_status : detailData?.assessment_status}
                onChange={updateField("assessment_status")}
              />
              <div>
                <Label className="text-slate-400">阶段门状态</Label>
                <p className="text-white">{selectedOpp.gate_status || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">阶段门通过时间</Label>
                <p className="text-white">{selectedOpp.gate_passed_at || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">最后修改人</Label>
                <p className="text-white">{selectedOpp.updated_by_name || "-"}</p>
              </div>
              <div>
                <Label className="text-slate-400">更新时间</Label>
                <p className="text-white">{selectedOpp.updated_at || "-"}</p>
              </div>
            </div>
          </div>

          {/* 需求信息 */}
          {(detailEditing || selectedOpp.requirement) && (
            <div>
              <h3 className="text-lg font-semibold mb-4">需求信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <EditableField
                  label="产品对象" editing={detailEditing}
                  value={detailEditing ? detailForm?.requirement?.product_object : detailData?.requirement?.product_object}
                  onChange={updateRequirement("product_object")}
                />
                <EditableField
                  label="节拍 (秒)" editing={detailEditing} type="number"
                  value={detailEditing ? detailForm?.requirement?.ct_seconds : detailData?.requirement?.ct_seconds}
                  onChange={updateRequirement("ct_seconds")}
                />
                <div className="col-span-2">
                  <EditableField
                    label="接口/通信协议" editing={detailEditing} type="textarea"
                    value={detailEditing ? detailForm?.requirement?.interface_desc : detailData?.requirement?.interface_desc}
                    onChange={updateRequirement("interface_desc")}
                  >
                    <p className="text-white mt-1">{detailData?.requirement?.interface_desc || "-"}</p>
                  </EditableField>
                </div>
                <div className="col-span-2">
                  <EditableField
                    label="现场约束" editing={detailEditing} type="textarea"
                    value={detailEditing ? detailForm?.requirement?.site_constraints : detailData?.requirement?.site_constraints}
                    onChange={updateRequirement("site_constraints")}
                  >
                    <p className="text-white mt-1">{detailData?.requirement?.site_constraints || "-"}</p>
                  </EditableField>
                </div>
                <div className="col-span-2">
                  <EditableField
                    label="验收依据" editing={detailEditing} type="textarea"
                    value={detailEditing ? detailForm?.requirement?.acceptance_criteria : detailData?.requirement?.acceptance_criteria}
                    onChange={updateRequirement("acceptance_criteria")}
                  >
                    <p className="text-white mt-1">{detailData?.requirement?.acceptance_criteria || "-"}</p>
                  </EditableField>
                </div>
                <div className="col-span-2">
                  <EditableField
                    label="安全要求" editing={detailEditing} type="textarea"
                    value={detailEditing ? detailForm?.requirement?.safety_requirement : detailData?.requirement?.safety_requirement}
                    onChange={updateRequirement("safety_requirement")}
                  >
                    <p className="text-white mt-1">{detailData?.requirement?.safety_requirement || "-"}</p>
                  </EditableField>
                </div>
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          {detailEditing ? (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setDetailEditing(false);
                  setDetailForm(buildDetailForm(selectedOpp));
                }}
              >
                取消
              </Button>
              <Button onClick={onSave} disabled={detailSaving}>
                {detailSaving ? "保存中..." : "保存"}
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                关闭
              </Button>
              <Button onClick={() => setDetailEditing(true)}>编辑</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
