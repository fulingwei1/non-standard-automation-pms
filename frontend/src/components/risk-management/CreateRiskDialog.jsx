/**
 * 创建风险对话框
 */

import { useState } from "react";



export default function CreateRiskDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    risk_category: "",
    risk_name: "",
    description: "",
    probability: "",
    impact: "",
    owner_id: "",
    trigger_condition: "",
  });

  const handleSubmit = () => {
    if (!formData.risk_name.trim() || !formData.risk_category.trim()) {
      alert("请填写风险名称和类别");
      return;
    }
    onSubmit(formData);
    setFormData({
      risk_category: "",
      risk_name: "",
      description: "",
      probability: "",
      impact: "",
      owner_id: "",
      trigger_condition: "",
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建风险</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  风险类别 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.risk_category}
                  onChange={(e) =>
                    setFormData({ ...formData, risk_category: e.target.value })
                  }
                  placeholder="如：技术风险、进度风险等"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  风险名称 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.risk_name}
                  onChange={(e) =>
                    setFormData({ ...formData, risk_name: e.target.value })
                  }
                  placeholder="请输入风险名称"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                风险描述
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="请详细描述风险情况"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  发生概率
                </label>
                <select
                  value={formData.probability}
                  onChange={(e) =>
                    setFormData({ ...formData, probability: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">请选择</option>
                  <option value="HIGH">高</option>
                  <option value="MEDIUM">中</option>
                  <option value="LOW">低</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  影响程度
                </label>
                <select
                  value={formData.impact}
                  onChange={(e) =>
                    setFormData({ ...formData, impact: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">请选择</option>
                  <option value="HIGH">高</option>
                  <option value="MEDIUM">中</option>
                  <option value="LOW">低</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                触发条件
              </label>
              <Input
                value={formData.trigger_condition}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    trigger_condition: e.target.value,
                  })
                }
                placeholder="描述风险触发条件（可选）"
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
