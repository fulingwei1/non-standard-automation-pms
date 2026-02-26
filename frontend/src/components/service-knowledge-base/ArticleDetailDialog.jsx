/**
 * 知识库文章详情对话框
 */

import { useState, useEffect } from "react";




import { cn } from "../../lib/utils";
import { categoryConfig, statusConfig } from "./knowledgeConfig";
import { Badge, Button, Dialog, DialogBody, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, Input, Textarea } from "../ui";
import { Edit, Eye, HelpCircle, Save, Star, ThumbsUp, Trash2 } from "lucide-react";

export default function ArticleDetailDialog({ article, onClose, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(article);

  useEffect(() => {
    setFormData(article);
  }, [article]);

  const handleSave = () => {
    onUpdate(article.id, formData);
    setIsEditing(false);
  };

  const category = categoryConfig[article.category] || categoryConfig["其他"];
  const status = statusConfig[article.status] || statusConfig["草稿"];

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {article.is_featured && (
              <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
            )}
            <span>{article.title}</span>
            <Badge className={cn(category.bg, category.color, "text-xs")}>
              {category.label}
            </Badge>
            {article.is_faq && (
              <Badge
                variant="outline"
                className="text-xs text-blue-400 border-blue-500/30"
              >
                FAQ
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>知识库文章详情</DialogDescription>
        </DialogHeader>
        <DialogBody>
          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">
                  文章标题
                </label>
                <Input
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm text-slate-400 block">
                    文章内容
                  </label>
                  <Badge variant="outline" className="text-xs">
                    Markdown
                  </Badge>
                </div>
                <Textarea
                  value={formData.content}
                  onChange={(e) =>
                    setFormData({ ...formData, content: e.target.value })
                  }
                  rows={15}
                  className="bg-slate-800/50 border-slate-700 font-mono text-sm"
                  placeholder="支持 Markdown 格式..."
                />
                {formData.content && (
                  <div className="mt-2 text-xs text-slate-500">
                    {formData.content.length} 字符
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <p className="text-sm text-slate-400 mb-1">文章编号</p>
                <p className="font-mono text-white">{article.article_no}</p>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-1">文章内容</p>
                <div className="text-white bg-slate-800/50 p-4 rounded-lg whitespace-pre-wrap">
                  {article.content}
                </div>
              </div>

              {article.tags && article.tags.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">标签</p>
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map((tag, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="text-xs"
                      >
                        <Tag className="w-3 h-3 mr-1" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">作者</p>
                  <p className="text-white">{article.author}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">状态</p>
                  <Badge className={cn(status.color, "text-xs")}>
                    {status.label}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">创建时间</p>
                  <p className="text-white">{article.created_at}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">更新时间</p>
                  <p className="text-white">{article.updated_at}</p>
                </div>
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">浏览量:</span>
                  <span className="text-white">{article.view_count}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">点赞:</span>
                  <span className="text-white">{article.like_count}</span>
                </div>
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">有用:</span>
                  <span className="text-white">{article.helpful_count}</span>
                </div>
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                取消
              </Button>
              <Button onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                保存
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => onDelete(article.id)}>
                <Trash2 className="w-4 h-4 mr-2" />
                删除
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit className="w-4 h-4 mr-2" />
                编辑
              </Button>
              <Button variant="outline" onClick={onClose}>
                关闭
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
