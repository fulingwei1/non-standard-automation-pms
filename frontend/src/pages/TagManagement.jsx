// -*- coding: utf-8 -*-
/**
 * 标签字典管理页面
 * 管理员工能力评估标签，包括技能、领域、态度等维度
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Plus, Search, Edit3, Trash2, Tag, Target, Users, Heart, Star, Zap,
  ChevronRight, Save, RefreshCw
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { cn } from '../lib/utils';
import { staffMatchingApi } from '../services/api';

// 标签类型配置
const TAG_TYPES = [
  { key: 'SKILL', label: '技能标签', icon: Target, color: 'blue' },
  { key: 'DOMAIN', label: '领域经验', icon: Users, color: 'green' },
  { key: 'ATTITUDE', label: '工作态度', icon: Heart, color: 'orange' },
  { key: 'CHARACTER', label: '性格特质', icon: Star, color: 'purple' },
  { key: 'SPECIAL', label: '特殊能力', icon: Zap, color: 'red' },
];

// 模拟数据
const mockTags = {
  SKILL: [
    { id: 1, tag_code: 'SKILL_001', tag_name: '机械设计', description: '机械结构设计能力', weight: 1.0, is_active: true },
    { id: 2, tag_code: 'SKILL_002', tag_name: 'SolidWorks', description: '3D建模软件', weight: 1.0, is_active: true },
    { id: 3, tag_code: 'SKILL_003', tag_name: 'AutoCAD', description: '2D制图软件', weight: 0.8, is_active: true },
    { id: 4, tag_code: 'SKILL_004', tag_name: 'PLC编程', description: '可编程逻辑控制器编程', weight: 1.0, is_active: true },
    { id: 5, tag_code: 'SKILL_005', tag_name: '电气设计', description: '电气原理图设计', weight: 1.0, is_active: true },
    { id: 6, tag_code: 'SKILL_006', tag_name: 'C#开发', description: '上位机软件开发', weight: 1.0, is_active: true },
  ],
  DOMAIN: [
    { id: 7, tag_code: 'DOMAIN_001', tag_name: '汽车行业', description: '汽车零部件制造经验', weight: 1.0, is_active: true },
    { id: 8, tag_code: 'DOMAIN_002', tag_name: '3C电子', description: '消费电子制造经验', weight: 1.0, is_active: true },
    { id: 9, tag_code: 'DOMAIN_003', tag_name: '医疗器械', description: '医疗设备制造经验', weight: 1.2, is_active: true },
  ],
  ATTITUDE: [
    { id: 10, tag_code: 'ATT_001', tag_name: '责任心强', description: '对工作认真负责', weight: 1.0, is_active: true },
    { id: 11, tag_code: 'ATT_002', tag_name: '团队协作', description: '善于团队合作', weight: 1.0, is_active: true },
    { id: 12, tag_code: 'ATT_003', tag_name: '主动性高', description: '工作主动积极', weight: 1.0, is_active: true },
  ],
  CHARACTER: [
    { id: 13, tag_code: 'CHAR_001', tag_name: '沟通能力强', description: '善于沟通表达', weight: 1.0, is_active: true },
    { id: 14, tag_code: 'CHAR_002', tag_name: '抗压能力强', description: '能承受工作压力', weight: 1.0, is_active: true },
  ],
  SPECIAL: [
    { id: 15, tag_code: 'SPEC_001', tag_name: '项目管理', description: '具备项目管理能力', weight: 1.2, is_active: true },
    { id: 16, tag_code: 'SPEC_002', tag_name: '客户沟通', description: '善于与客户沟通', weight: 1.0, is_active: true },
  ],
};

export default function TagManagement() {
  const [activeType, setActiveType] = useState('SKILL');
  const [tags, setTags] = useState(mockTags);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [editingTag, setEditingTag] = useState(null);
  const [formData, setFormData] = useState({
    tag_code: '',
    tag_name: '',
    tag_type: 'SKILL',
    description: '',
    weight: 1.0,
  });

  // 加载标签数据
  const loadTags = useCallback(async () => {
    setLoading(true);
    try {
      const response = await staffMatchingApi.getTags({ page_size: 500 });
      if (response.data?.items) {
        const grouped = {};
        TAG_TYPES.forEach(t => grouped[t.key] = []);
        response.data.items.forEach(tag => {
          if (grouped[tag.tag_type]) {
            grouped[tag.tag_type].push(tag);
          }
        });
        setTags(grouped);
      }
    } catch (error) {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTags();
  }, [loadTags]);

  // 过滤标签
  const filteredTags = (tags[activeType] || []).filter(tag =>
    tag.tag_name.includes(searchKeyword) || tag.tag_code.includes(searchKeyword)
  );

  // 打开新建对话框
  const handleCreate = () => {
    setEditingTag(null);
    setFormData({
      tag_code: '',
      tag_name: '',
      tag_type: activeType,
      description: '',
      weight: 1.0,
    });
    setShowDialog(true);
  };

  // 打开编辑对话框
  const handleEdit = (tag) => {
    setEditingTag(tag);
    setFormData({
      tag_code: tag.tag_code,
      tag_name: tag.tag_name,
      tag_type: tag.tag_type,
      description: tag.description || '',
      weight: tag.weight || 1.0,
    });
    setShowDialog(true);
  };

  // 保存标签
  const handleSave = async () => {
    try {
      if (editingTag) {
        await staffMatchingApi.updateTag(editingTag.id, formData);
      } else {
        await staffMatchingApi.createTag(formData);
      }
      setShowDialog(false);
      loadTags();
    } catch (error) {
      const newTag = editingTag
        ? { ...editingTag, ...formData }
        : { id: Date.now(), ...formData, is_active: true };

      setTags(prev => ({
        ...prev,
        [activeType]: editingTag
          ? prev[activeType].map(t => t.id === editingTag.id ? newTag : t)
          : [...prev[activeType], newTag]
      }));
      setShowDialog(false);
    }
  };

  // 删除标签
  const handleDelete = async (tag) => {
    if (!window.confirm(`确定要删除标签"${tag.tag_name}"吗？`)) return;

    try {
      await staffMatchingApi.deleteTag(tag.id);
      loadTags();
    } catch (error) {
      setTags(prev => ({
        ...prev,
        [activeType]: prev[activeType].filter(t => t.id !== tag.id)
      }));
    }
  };

  const activeTypeConfig = TAG_TYPES.find(t => t.key === activeType);
  const TypeIcon = activeTypeConfig?.icon || Tag;

  return (
    <div className="space-y-6">
      <PageHeader
        title="标签字典管理"
        description="管理员工能力评估标签，包括技能、领域、态度等维度"
      />

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧：标签类型列表 */}
        <div className="col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">标签类型</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-white/5">
                {TAG_TYPES.map(type => {
                  const Icon = type.icon;
                  const count = (tags[type.key] || []).length;
                  const isActive = activeType === type.key;

                  return (
                    <button
                      key={type.key}
                      onClick={() => setActiveType(type.key)}
                      className={cn(
                        'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                        isActive
                          ? 'bg-primary/10 text-primary'
                          : 'hover:bg-white/5 text-slate-400'
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="flex-1">{type.label}</span>
                      <Badge variant="secondary" className="text-xs">
                        {count}
                      </Badge>
                      {isActive && <ChevronRight className="h-4 w-4" />}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 统计信息 */}
          <Card className="mt-4">
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-white">
                  {Object.values(tags).flat().length}
                </div>
                <div className="text-sm text-slate-400 mt-1">总标签数</div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右侧：标签列表 */}
        <div className="col-span-9">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <TypeIcon className="h-5 w-5 text-primary" />
                <CardTitle>{activeTypeConfig?.label}</CardTitle>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="搜索标签..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="pl-9 w-64"
                  />
                </div>
                <Button variant="outline" size="icon" onClick={loadTags}>
                  <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                </Button>
                <Button onClick={handleCreate}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建标签
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-12 text-slate-400">加载中...</div>
              ) : filteredTags.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  {searchKeyword ? '没有找到匹配的标签' : '暂无标签，点击上方按钮创建'}
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {filteredTags.map(tag => (
                    <motion.div
                      key={tag.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        'p-4 rounded-lg border transition-colors',
                        tag.is_active
                          ? 'border-white/10 bg-white/5 hover:bg-white/10'
                          : 'border-white/5 bg-white/[0.02] opacity-50'
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white">{tag.tag_name}</span>
                            {tag.weight !== 1.0 && (
                              <Badge variant="outline" className="text-xs">
                                权重 {tag.weight}
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs text-slate-500 mt-1">{tag.tag_code}</div>
                          {tag.description && (
                            <div className="text-sm text-slate-400 mt-2">{tag.description}</div>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => handleEdit(tag)}
                          >
                            <Edit3 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-400 hover:text-red-300"
                            onClick={() => handleDelete(tag)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* 新建/编辑对话框 */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTag ? '编辑标签' : '新建标签'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>标签编码</Label>
                <Input
                  value={formData.tag_code}
                  onChange={(e) => setFormData({ ...formData, tag_code: e.target.value })}
                  placeholder="如: SKILL_001"
                />
              </div>
              <div className="space-y-2">
                <Label>标签名称</Label>
                <Input
                  value={formData.tag_name}
                  onChange={(e) => setFormData({ ...formData, tag_name: e.target.value })}
                  placeholder="如: 机械设计"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>描述</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="标签描述..."
              />
            </div>
            <div className="space-y-2">
              <Label>权重系数</Label>
              <Input
                type="number"
                step="0.1"
                min="0.1"
                max="2.0"
                value={formData.weight}
                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) })}
              />
              <p className="text-xs text-slate-500">
                权重影响匹配算法中该标签的重要性，范围 0.1-2.0，默认 1.0
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
