/**
 * 报表归档查询页面
 */
import React, { useState, useEffect } from 'react';
import { Download, Search, Eye } from 'lucide-react';
import { reportCenterApi } from '../services/api';

export default function ReportArchives() {
  const [archives, setArchives] = useState([]);
  const [filters, setFilters] = useState({
    report_type: '',
    period: '',
    status: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchArchives();
  }, []);

  const fetchArchives = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.report_type) params.report_type = filters.report_type;
      if (filters.period) params.period = filters.period;
      if (filters.status) params.status = filters.status;

      const response = await reportCenterApi.getArchives(params);
      const data = response.data;
      setArchives(data?.items || data || []);
    } catch (error) {
      console.error('获取归档列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (archiveId) => {
    try {
      const response = await reportCenterApi.downloadArchive(archiveId);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${archiveId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">报表归档查询</h1>

      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">报表类型</label>
            <select
              value={filters.report_type}
              onChange={(e) => setFilters({...filters, report_type: e.target.value})}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">全部</option>
              <option value="USER_MONTHLY">人员月度报表</option>
              <option value="DEPT_MONTHLY">部门月度报表</option>
              <option value="PROJECT_MONTHLY">项目月度报表</option>
              <option value="COMPANY_MONTHLY">公司整体报表</option>
              <option value="OVERTIME_MONTHLY">加班统计报表</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">报表周期</label>
            <input
              type="month"
              value={filters.period}
              onChange={(e) => setFilters({...filters, period: e.target.value})}
              className="w-full border border-gray-300 rounded px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">状态</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">全部</option>
              <option value="SUCCESS">成功</option>
              <option value="FAILED">失败</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchArchives}
              className="btn btn-primary w-full"
            >
              <Search className="w-4 h-4 mr-2" />
              查询
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div>加载中...</div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">报表类型</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">周期</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">文件大小</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">数据行数</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">生成时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">下载次数</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(archives || []).map((archive) => (
                <tr key={archive.id}>
                  <td className="px-6 py-4">{archive.report_type}</td>
                  <td className="px-6 py-4">{archive.period}</td>
                  <td className="px-6 py-4">{formatFileSize(archive.file_size)}</td>
                  <td className="px-6 py-4">{archive.row_count}</td>
                  <td className="px-6 py-4">{new Date(archive.generated_at).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded ${archive.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {archive.status === 'SUCCESS' ? '成功' : '失败'}
                    </span>
                  </td>
                  <td className="px-6 py-4">{archive.download_count}</td>
                  <td className="px-6 py-4 space-x-2">
                    {archive.status === 'SUCCESS' && (
                      <button
                        onClick={() => handleDownload(archive.id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    )}
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
