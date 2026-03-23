/**
 * 新建商机对话框
 */

import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
  Button, Input, Label, Textarea,
} from "../../../components/ui";
import { stageConfig } from "../constants";

export function CreateDialog({
  open, onOpenChange,
  formData, setFormData,
  customers,
  onCreate,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建商机</DialogTitle>
          <DialogDescription>创建新的销售商机</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>客户 *</Label>
              <select
                value={formData.customer_id}
                onChange={(e) =>
                  setFormData({ ...formData, customer_id: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="">请选择客户</option>
                {(customers || []).map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.customer_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>商机名称 *</Label>
              <Input
                value={formData.opp_name}
                onChange={(e) =>
                  setFormData({ ...formData, opp_name: e.target.value })
                }
                placeholder="请输入商机名称"
              />
            </div>
            <div>
              <Label>项目类型</Label>
              <Input
                value={formData.project_type}
                onChange={(e) =>
                  setFormData({ ...formData, project_type: e.target.value })
                }
                placeholder="单机/线体/改造"
              />
            </div>
            <div>
              <Label>设备类型</Label>
              <Input
                value={formData.equipment_type}
                onChange={(e) =>
                  setFormData({ ...formData, equipment_type: e.target.value })
                }
                placeholder="ICT/FCT/EOL"
              />
            </div>
            <div>
              <Label>阶段</Label>
              <select
                value={formData.stage}
                onChange={(e) =>
                  setFormData({ ...formData, stage: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                {Object.entries(stageConfig).map(([key, config]) => (
                  <option key={key} value={key || "unknown"}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>预估金额</Label>
              <Input
                type="number"
                value={formData.est_amount}
                onChange={(e) =>
                  setFormData({ ...formData, est_amount: e.target.value })
                }
                placeholder="请输入预估金额"
              />
            </div>
            <div>
              <Label>预估毛利率 (%)</Label>
              <Input
                type="number"
                value={formData.est_margin}
                onChange={(e) =>
                  setFormData({ ...formData, est_margin: e.target.value })
                }
                placeholder="请输入预估毛利率"
              />
            </div>
            <div>
              <Label>预算范围</Label>
              <Input
                value={formData.budget_range}
                onChange={(e) =>
                  setFormData({ ...formData, budget_range: e.target.value })
                }
                placeholder="如: 80-120万"
              />
            </div>
          </div>
          <div>
            <Label>决策链</Label>
            <Textarea
              value={formData.decision_chain}
              onChange={(e) =>
                setFormData({ ...formData, decision_chain: e.target.value })
              }
              placeholder="请输入决策链信息"
              rows={2}
            />
          </div>
          <div>
            <Label>交付窗口</Label>
            <Input
              value={formData.delivery_window}
              onChange={(e) =>
                setFormData({ ...formData, delivery_window: e.target.value })
              }
              placeholder="如: 2026年Q2"
            />
          </div>
          <div>
            <Label>验收依据</Label>
            <Textarea
              value={formData.acceptance_basis}
              onChange={(e) =>
                setFormData({ ...formData, acceptance_basis: e.target.value })
              }
              placeholder="请输入验收依据"
              rows={2}
            />
          </div>
          {/* 需求信息 */}
          <div className="border-t border-slate-700 pt-4">
            <h4 className="text-sm font-semibold mb-2">需求信息</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>产品对象</Label>
                <Input
                  value={formData.requirement.product_object}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: { ...formData.requirement, product_object: e.target.value },
                    })
                  }
                  placeholder="如: PCB板"
                />
              </div>
              <div>
                <Label>节拍 (秒)</Label>
                <Input
                  type="number"
                  value={formData.requirement.ct_seconds}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: { ...formData.requirement, ct_seconds: e.target.value },
                    })
                  }
                  placeholder="如: 1"
                />
              </div>
              <div className="col-span-2">
                <Label>接口/通信协议</Label>
                <Textarea
                  value={formData.requirement.interface_desc}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: { ...formData.requirement, interface_desc: e.target.value },
                    })
                  }
                  placeholder="如: RS232/以太网"
                  rows={2}
                />
              </div>
              <div className="col-span-2">
                <Label>现场约束</Label>
                <Textarea
                  value={formData.requirement.site_constraints}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: { ...formData.requirement, site_constraints: e.target.value },
                    })
                  }
                  placeholder="请输入现场约束条件"
                  rows={2}
                />
              </div>
              <div className="col-span-2">
                <Label>验收依据</Label>
                <Textarea
                  value={formData.requirement.acceptance_criteria}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: { ...formData.requirement, acceptance_criteria: e.target.value },
                    })
                  }
                  placeholder="如: 节拍≤1秒，良率≥99.5%"
                  rows={2}
                />
              </div>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onCreate}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
