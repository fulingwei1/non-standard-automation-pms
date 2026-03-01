/**
 * 模板配置列表页
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Plus, Edit2, Trash2, Copy, CheckCircle, XCircle } from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui";
import { templateConfigApi } from "../services/api/templateConfig";

export default function TemplateConfigList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [configs, setConfigs] = useState([]);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const loadConfigs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await templateConfigApi.list({ page: 1, page_size: 100 });
      const data = res.data || res;
      setConfigs(data.items || []);
    } catch (error) {
      console.error("加载配置列表失败:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfigs();
  }, [loadConfigs]);

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await templateConfigApi.delete(deletingId);
      loadConfigs();
    } catch (error) {
      alert("删除失败：" + error.message);
    } finally {
      setShowDeleteDialog(false);
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="模板配置管理"
            description="管理和编辑项目模板配置，自定义阶段和节点"
            actions={
              <Button onClick={() => navigate("/template-configs/new")}>
                <Plus className="w-4 h-4 mr-2" />
                新建配置
              </Button>
            }
          />

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-slate-400">加载中...</div>
            </div>
          ) : configs.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-slate-400">
                暂无配置，点击右上角"新建配置"创建
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {configs.map((config) => (
                <Card key={config.id}>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-lg">
                            {config.config_name}
                          </h3>
                          {config.is_default && (
                            <Badge variant="default">默认</Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-400">
                          {config.description || "无描述"}
                        </p>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">编码:</span>
                        <span className="font-mono">{config.config_code}</span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">基础模板:</span>
                        <Badge variant="outline">{config.base_template_code}</Badge>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">状态:</span>
                        {config.is_active ? (
                          <Badge variant="default" className="gap-1">
                            <CheckCircle className="w-3 h-3" />
                            启用
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="gap-1">
                            <XCircle className="w-3 h-3" />
                            停用
                          </Badge>
                        )}
                      </div>
                      
                      <div className="flex gap-2 pt-4 border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => navigate(`/template-configs/edit/${config.id}`)}
                        >
                          <Edit2 className="w-3 h-3 mr-1" />
                          编辑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => {
                            setDeletingId(config.id);
                            setShowDeleteDialog(true);
                          }}
                        >
                          <Trash2 className="w-3 h-3 mr-1" />
                          删除
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* 删除确认对话框 */}
          <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>确认删除</DialogTitle>
              </DialogHeader>
              <p className="text-slate-400">
                确定要删除此配置吗？此操作不可恢复。
              </p>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
                  取消
                </Button>
                <Button variant="destructive" onClick={handleDelete}>
                  删除
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
