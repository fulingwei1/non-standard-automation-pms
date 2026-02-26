/**
 * 报表生成页面
 */
import React, { useState, useEffect } from 'react';
import { FileText, Download } from 'lucide-react';
import { reportCenterApi } from '../services/api';

export default function ReportGeneration() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [period, setPeriod] = useState('');
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTemplates();
    // 默认设置为上月
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1);
    setPeriod(`${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`);
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await reportCenterApi.getTemplates({ enabled: true });
      const data = response.data;
      setTemplates(data?.items || data || []);
    } catch (error) {
      console.error('获取模板列表失败:', error);
    }
  };

  const handlePreview = async () => {
    if (!selectedTemplate || !period) {
      alert('请选择模板和周期');
      return;
    }

    setLoading(true);
    try {
      const response = await reportCenterApi.previewByTemplate({
        template_id: selectedTemplate,
        period,
        limit: 50
      });
      const data = response.data;
      setPreview(data);
    } catch (error) {
      console.error('预览失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedTemplate || !period) {
      alert('请选择模板和周期');
      return;
    }

    setLoading(true);
    try {
      await reportCenterApi.generate({
        template_id: parseInt(selectedTemplate),
        period
      });
      alert('报表生成成功！');
    } catch (error) {
      console.error('生成失败:', error);
      alert('生成失败: ' + (error.response?.data?.detail || '请稍后重试'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">生成工时报表</h1>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">选择模板</label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">请选择</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">报表周期</label>
            <input
              type="month"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <div className="flex items-end space-x-2">
            <button
              onClick={handlePreview}
              disabled={loading}
              className="btn btn-secondary"
            >
              <FileText className="w-4 h-4 mr-2" />
              预览数据
            </button>
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="btn btn-primary"
            >
              <Download className="w-4 h-4 mr-2" />
              生成报表
            </button>
          </div>
        </div>

        {loading && <div className="text-center py-4">处理中...</div>}

        {preview && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">数据预览</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {preview.summary[0] && Object.keys(preview.summary[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {preview.summary.map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((val, i) => (
                        <td key={i} className="px-4 py-2 text-sm">{val}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 text-sm text-gray-500">
              显示前 {preview.summary.length} 条 / 总计 {preview.total_summary_rows} 条
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
