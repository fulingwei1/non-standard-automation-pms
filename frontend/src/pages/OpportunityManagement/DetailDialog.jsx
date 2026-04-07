

import { cn } from "../../lib/utils";
import { stageConfig } from "./constants";

export default function DetailDialog({
  open,
  onOpenChange,
  selectedOpp,
  detailEditing,
  setDetailEditing,
  detailForm,
  setDetailForm,
  detailSaving,
  detailData,
  buildDetailForm,
  onDetailSave
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>商机详情</DialogTitle>
          <DialogDescription>查看商机详细信息和需求</DialogDescription>
        </DialogHeader>
        {selectedOpp &&
          <div className="space-y-6">
            {/* 基本信息 */}
            <div>
              <h3 className="text-lg font-semibold mb-4">基本信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-400">商机编码</Label>
                  <p className="text-white">{selectedOpp.opp_code}</p>
                </div>
                <div>
                  <Label className="text-slate-400">商机名称</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.opp_name || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, opp_name: e.target.value })
                      } /> :
                    <p className="text-white">{detailData?.opp_name}</p>
                  }
                </div>
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
                  {detailEditing ?
                    <select
                      value={detailForm?.stage || "DISCOVERY"}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, stage: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                      {Object.entries(stageConfig).map(([key, config]) =>
                        <option key={key} value={key || "unknown"}>
                          {config.label}
                        </option>
                      )}
                    </select> :
                    <Badge
                      className={cn(
                        stageConfig[selectedOpp.stage]?.color,
                        "mt-1"
                      )}>

                      {stageConfig[selectedOpp.stage]?.label}
                    </Badge>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">项目类型</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.project_type || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, project_type: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.project_type || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">设备类型</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.equipment_type || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, equipment_type: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.equipment_type || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">预估金额</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.est_amount ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, est_amount: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.est_amount ?
                        parseFloat(detailData.est_amount).toLocaleString() +
                        " 元" :
                        "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">预估毛利率</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.est_margin ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, est_margin: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.est_margin ?
                        detailData.est_margin + "%" :
                        "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">预算范围</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.budget_range || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, budget_range: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.budget_range || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">交付窗口</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.delivery_window || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, delivery_window: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.delivery_window || "-"}
                    </p>
                  }
                </div>
                <div className="col-span-2">
                  <Label className="text-slate-400">决策链</Label>
                  {detailEditing ?
                    <Textarea
                      value={detailForm?.decision_chain || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, decision_chain: e.target.value })
                      }
                      rows={2} /> :
                    <p className="text-white mt-1">
                      {detailData?.decision_chain || "-"}
                    </p>
                  }
                </div>
                <div className="col-span-2">
                  <Label className="text-slate-400">验收依据</Label>
                  {detailEditing ?
                    <Textarea
                      value={detailForm?.acceptance_basis || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, acceptance_basis: e.target.value })
                      }
                      rows={2} /> :
                    <p className="text-white mt-1">
                      {detailData?.acceptance_basis || "-"}
                    </p>
                  }
                </div>
              </div>
            </div>

            {/* 扩展信息 */}
            <div>
              <h3 className="text-lg font-semibold mb-4">扩展信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-400">成交概率 (%)</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.probability ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, probability: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.probability ?? "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">预计成交日期</Label>
                  {detailEditing ?
                    <Input
                      type="date"
                      value={detailForm?.expected_close_date || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, expected_close_date: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.expected_close_date || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">风险等级</Label>
                  {detailEditing ?
                    <select
                      value={detailForm?.risk_level || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, risk_level: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                      <option value="">未设置</option>
                      <option value="LOW">低</option>
                      <option value="MEDIUM">中</option>
                      <option value="HIGH">高</option>
                    </select> :
                    <p className="text-white">
                      {detailData?.risk_level || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">评分</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.score ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, score: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.score ?? "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">优先级得分</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.priority_score ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, priority_score: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.priority_score ?? "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">需求成熟度</Label>
                  {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.requirement_maturity ?? ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, requirement_maturity: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.requirement_maturity ?? "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">技术评估状态</Label>
                  {detailEditing ?
                    <Input
                      value={detailForm?.assessment_status || ""}
                      onChange={(e) =>
                        setDetailForm({ ...detailForm, assessment_status: e.target.value })
                      } /> :
                    <p className="text-white">
                      {detailData?.assessment_status || "-"}
                    </p>
                  }
                </div>
                <div>
                  <Label className="text-slate-400">阶段门状态</Label>
                  <p className="text-white">
                    {selectedOpp.gate_status || "-"}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">阶段门通过时间</Label>
                  <p className="text-white">
                    {selectedOpp.gate_passed_at || "-"}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">最后修改人</Label>
                  <p className="text-white">
                    {selectedOpp.updated_by_name || "-"}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">更新时间</Label>
                  <p className="text-white">
                    {selectedOpp.updated_at || "-"}
                  </p>
                </div>
              </div>
            </div>

            {/* 需求信息 */}
            {(detailEditing || selectedOpp.requirement) &&
              <div>
                <h3 className="text-lg font-semibold mb-4">需求信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">产品对象</Label>
                    {detailEditing ?
                      <Input
                        value={detailForm?.requirement?.product_object || ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              product_object: e.target.value
                            }
                          })
                        } /> :
                      <p className="text-white">
                        {detailData?.requirement?.product_object || "-"}
                      </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">节拍 (秒)</Label>
                    {detailEditing ?
                      <Input
                        type="number"
                        value={detailForm?.requirement?.ct_seconds ?? ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              ct_seconds: e.target.value
                            }
                          })
                        } /> :
                      <p className="text-white">
                        {detailData?.requirement?.ct_seconds || "-"}
                      </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">接口/通信协议</Label>
                    {detailEditing ?
                      <Textarea
                        value={detailForm?.requirement?.interface_desc || ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              interface_desc: e.target.value
                            }
                          })
                        }
                        rows={2} /> :
                      <p className="text-white mt-1">
                        {detailData?.requirement?.interface_desc || "-"}
                      </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">现场约束</Label>
                    {detailEditing ?
                      <Textarea
                        value={detailForm?.requirement?.site_constraints || ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              site_constraints: e.target.value
                            }
                          })
                        }
                        rows={2} /> :
                      <p className="text-white mt-1">
                        {detailData?.requirement?.site_constraints || "-"}
                      </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">验收依据</Label>
                    {detailEditing ?
                      <Textarea
                        value={detailForm?.requirement?.acceptance_criteria || ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              acceptance_criteria: e.target.value
                            }
                          })
                        }
                        rows={2} /> :
                      <p className="text-white mt-1">
                        {detailData?.requirement?.acceptance_criteria || "-"}
                      </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">安全要求</Label>
                    {detailEditing ?
                      <Textarea
                        value={detailForm?.requirement?.safety_requirement || ""}
                        onChange={(e) =>
                          setDetailForm({
                            ...detailForm,
                            requirement: {
                              ...detailForm.requirement,
                              safety_requirement: e.target.value
                            }
                          })
                        }
                        rows={2} /> :
                      <p className="text-white mt-1">
                        {detailData?.requirement?.safety_requirement || "-"}
                      </p>
                    }
                  </div>
                </div>
              </div>
            }
          </div>
        }
        <DialogFooter>
          {detailEditing ? (
            <>
              <Button
                variant="outline"
                onClick={() => {
                  setDetailEditing(false);
                  setDetailForm(buildDetailForm(selectedOpp));
                }}>
                取消
              </Button>
              <Button onClick={onDetailSave} disabled={detailSaving}>
                {detailSaving ? "保存中..." : "保存"}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}>
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
