/**
 * 创建知识库文章对话框
 */

import { useState } from "react";




import { toast } from "../ui/toast";
import { Badge, Button, Dialog, DialogBody, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, Input, Textarea } from "../ui";
import { Plus, Save, XCircle } from "lucide-react";

export default function CreateArticleDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    title: "",
    category: "故障处理",
    content: "",
    tags: [],
    is_faq: false,
    is_featured: false,
    status: "草稿"
  });

  const [tagInput, setTagInput] = useState("");

  const handleSubmit = () => {
    if (!formData.title || !formData.content) {
      toast.error("请填写文章标题和内容");
      return;
    }
    onSubmit(formData);
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput("");
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建知识库文章</DialogTitle>
          <DialogDescription>
            填写文章信息，系统将自动生成文章编号
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  文章标题 *
                </label>
                <Input
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  placeholder="输入文章标题"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  分类 *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) =>
                    setFormData({ ...formData, category: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="故障处理">故障处理</option>
                  <option value="操作指南">操作指南</option>
                  <option value="技术文档">技术文档</option>
                  <option value="FAQ">FAQ</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm text-slate-400 block">
                  文章内容 *
                </label>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>支持 Markdown 格式</span>
                  <Badge variant="outline" className="text-xs">
                    Markdown
                  </Badge>
                </div>
              </div>
              <div className="relative">
                <Textarea
                  value={formData.content}
                  onChange={(e) =>
                    setFormData({ ...formData, content: e.target.value })
                  }
                  placeholder="输入文章详细内容...&#10;&#10;支持 Markdown 格式：&#10;- 使用 **粗体** 和 *斜体*&#10;- 使用 # 标题&#10;- 使用 - 或 * 创建列表&#10;- 使用 ```代码块```"
                  rows={12}
                  className="bg-slate-800/50 border-slate-700 font-mono text-sm"
                />
                <div className="absolute bottom-2 right-2 text-xs text-slate-500">
                  {formData.content.length} 字符
                </div>
              </div>
              {/* Markdown Preview Toggle */}
              {formData.content && (
                <div className="mt-2">
                  <details className="group">
                    <summary className="cursor-pointer text-xs text-slate-400 hover:text-slate-300">
                      预览 Markdown 渲染效果
                    </summary>
                    <div className="mt-2 p-3 bg-slate-900/50 border border-slate-700 rounded-lg prose prose-invert prose-sm max-w-none">
                      <div
                        className="text-slate-200 whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{
                          __html: formData.content
                            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                            .replace(/\*(.*?)\*/g, "<em>$1</em>")
                            .replace(/^### (.*$)/gim, "<h3>$1</h3>")
                            .replace(/^## (.*$)/gim, "<h2>$1</h2>")
                            .replace(/^# (.*$)/gim, "<h1>$1</h1>")
                            .replace(/^- (.*$)/gim, "<li>$1</li>")
                            .replace(/\n/g, "<br/>")
                        }}
                      />
                    </div>
                  </details>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1 block">标签</label>
              <div className="flex gap-2">
                <Input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleAddTag()}
                  placeholder="输入标签后按回车"
                  className="bg-slate-800/50 border-slate-700"
                />
                <Button variant="outline" size="sm" onClick={handleAddTag}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {tag}
                      <XCircle
                        className="w-3 h-3 ml-1 cursor-pointer"
                        onClick={() => handleRemoveTag(tag)}
                      />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_faq}
                  onChange={(e) =>
                    setFormData({ ...formData, is_faq: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label className="text-sm text-slate-400">标记为FAQ</label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) =>
                    setFormData({ ...formData, is_featured: e.target.checked })
                  }
                  className="w-4 h-4"
                />
                <label className="text-sm text-slate-400">设为精选</label>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  状态
                </label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="草稿">草稿</option>
                  <option value="已发布">已发布</option>
                </select>
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit}>
            <Save className="w-4 h-4 mr-2" />
            创建文章
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
