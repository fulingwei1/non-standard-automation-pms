/**
 * 报表模板管理页面
 */
import React, { useState, useEffect } from 'react';
import {  Plus, Edit2, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';

export default function ReportTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [_showDialog, setShowDialog] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/reports/templates');
      const result = await response.json();
      if (result.code === 0) {
        setTemplates(result.data.items);
      }
    } catch (error) {
      console.error('获取模板列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (templateId) => {
    try {
      const response = await fetch(`/api/v1/reports/templates/${templateId}/toggle`, {
        method: 'POST'
      });
      const result = await response.json();
      if (result.code === 0) {
        fetchTemplates();
      }
    } catch (error) {
      console.error('切换模板状态失败:', error);
    }
  };

  const handleDelete = async (templateId) => {
    if (!confirm('确定要删除此模板吗？')) return;
    
    try {
      const response = await fetch(`/api/v1/reports/templates/${templateId}`, {
        method: 'DELETE'
      });
      const result = await response.json();
      if (result.code === 0) {
        fetchTemplates();
      }
    } catch (error) {
      console.error('删除模板失败:', error);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">报表模板管理</h1>
        <button
          onClick={() => setShowDialog(true)}
          className="btn btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          新建模板
        </button>
      </div>

      {loading ? (
        <div>加载中...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模板名称</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">报表类型</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">输出格式</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">生成频率</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {templates.map((template) => (
                <tr key={template.id}>
                  <td className="px-6 py-4">{template.name}</td>
                  <td className="px-6 py-4">{template.report_type}</td>
                  <td className="px-6 py-4">{template.output_format}</td>
                  <td className="px-6 py-4">{template.frequency}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded ${template.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {template.enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 space-x-2">
                    <button onClick={() => handleToggle(template.id)} className="text-blue-600 hover:text-blue-800">
                      {template.enabled ? <ToggleRight /> : <ToggleLeft />}
                    </button>
                    <button className="text-blue-600 hover:text-blue-800">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(template.id)} className="text-red-600 hover:text-red-800">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
