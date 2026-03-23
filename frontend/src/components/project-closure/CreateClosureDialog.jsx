/**
 * 创建结项申请对话框
 */

import { useState } from "react";



export default function CreateClosureDialog({ open, onOpenChange, onSubmit }) {
  const [formData, setFormData] = useState({
    acceptance_date: "",
    acceptance_result: "",
    acceptance_notes: "",
    project_summary: "",
    achievement: "",
    lessons_learned: "",
    improvement_suggestions: "",
    quality_score: "",
    customer_satisfaction: ""
  });

  const handleSubmit = () => {
    onSubmit(formData);
    setFormData({
      acceptance_date: "",
      acceptance_result: "",
      acceptance_notes: "",
      project_summary: "",
      achievement: "",
      lessons_learned: "",
      improvement_suggestions: "",
      quality_score: "",
      customer_satisfaction: ""
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建结项申请</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Acceptance */}
            <div>
              <h4 className="text-sm font-medium text-white mb-3">验收信息</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    验收日期
                  </label>
                  <Input
                    type="date"
                    value={formData.acceptance_date}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        acceptance_date: e.target.value
                      })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    验收结果
                  </label>
                  <Input
                    value={formData.acceptance_result}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        acceptance_result: e.target.value
                      })
                    }
                    placeholder="如：通过、有条件通过等"
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-white mb-2">
                  验收说明
                </label>
                <textarea
                  value={formData.acceptance_notes}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      acceptance_notes: e.target.value
                    })
                  }
                  placeholder="请输入验收说明"
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows={3}
                />
              </div>
            </div>

            {/* Summary */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                项目总结
              </label>
              <textarea
                value={formData.project_summary}
                onChange={(e) =>
                  setFormData({ ...formData, project_summary: e.target.value })
                }
                placeholder="请总结项目整体情况"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>

            {/* Achievement */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                项目成果
              </label>
              <textarea
                value={formData.achievement}
                onChange={(e) =>
                  setFormData({ ...formData, achievement: e.target.value })
                }
                placeholder="请描述项目取得的成果"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>

            {/* Lessons */}
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
                rows={4}
              />
            </div>

            {/* Improvement */}
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
                rows={3}
              />
            </div>

            {/* Scores */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  质量评分 (0-100)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.quality_score}
                  onChange={(e) =>
                    setFormData({ ...formData, quality_score: e.target.value })
                  }
                  placeholder="请输入质量评分"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  客户满意度 (0-100)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.customer_satisfaction}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      customer_satisfaction: e.target.value
                    })
                  }
                  placeholder="请输入客户满意度"
                />
              </div>
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
