/**
 * 通用数据表格组件
 * 统一处理表格展示、筛选、分页、排序
 */

import React from 'react';
import { Table, TableProps, Pagination, Space, Button, Input } from 'antd';
import { Search, ReloadOutlined } from '@ant-design/icons';
import { usePaginatedData } from '../../hooks/usePaginatedData';
import { FilterPanel } from '../FilterPanel/FilterPanel';
import type { ColumnType } from 'antd/es/table';

export interface DataTableProps<T> extends Omit<TableProps<T>, 'dataSource' | 'loading' | 'pagination'> {
  /** 查询Key（用于React Query缓存） */
  queryKey: (string | number)[];
  /** 查询函数 */
  queryFn: (params: {
    page: number;
    pageSize: number;
    filters?: Record<string, any>;
    keyword?: string;
    orderBy?: string;
    orderDirection?: 'asc' | 'desc';
  }) => Promise<{
    items: T[];
    total: number;
    page: number;
    pageSize: number;
    pages: number;
  }>;
  /** 表格列配置 */
  columns: ColumnType<T>[];
  /** 筛选配置 */
  filters?: Array<{
    key: string;
    label: string;
    type: 'select' | 'input' | 'date' | 'dateRange' | 'number' | 'numberRange';
    options?: Array<{ label: string; value: any }>;
    placeholder?: string;
  }>;
  /** 关键词搜索字段 */
  keywordFields?: string[];
  /** 初始筛选条件 */
  initialFilters?: Record<string, any>;
  /** 初始关键词 */
  initialKeyword?: string;
  /** 每页默认数量 */
  defaultPageSize?: number;
  /** 是否显示筛选面板 */
  showFilters?: boolean;
  /** 是否显示搜索框 */
  showSearch?: boolean;
  /** 是否显示刷新按钮 */
  showRefresh?: boolean;
  /** 自定义操作栏 */
  extra?: React.ReactNode;
}

/**
 * 通用数据表格组件
 * 
 * @example
 * ```tsx
 * <DataTable
 *   queryKey={['projects']}
 *   queryFn={(params) => projectApi.listProjects(params)}
 *   columns={columns}
 *   filters={[
 *     { key: 'status', label: '状态', type: 'select', options: statusOptions },
 *     { key: 'customer_id', label: '客户', type: 'select', options: customerOptions }
 *   ]}
 *   keywordFields={['code', 'name']}
 * />
 * ```
 */
export function DataTable<T extends Record<string, any>>({
  queryKey,
  queryFn,
  columns,
  filters = [],
  keywordFields = [],
  initialFilters = {},
  initialKeyword = '',
  defaultPageSize = 20,
  showFilters = true,
  showSearch = true,
  showRefresh = true,
  extra,
  ...tableProps
}: DataTableProps<T>) {
  const {
    data,
    total,
    pagination,
    filters: activeFilters,
    keyword,
    isLoading,
    handlePageChange,
    handleFilterChange,
    setKeyword,
    refetch,
  } = usePaginatedData(queryKey, queryFn, {
    initialPage: 1,
    initialPageSize: defaultPageSize,
    initialFilters,
    initialKeyword,
  });

  return (
    <div className="data-table">
      {/* 操作栏 */}
      {(showFilters || showSearch || showRefresh || extra) && (
        <div className="data-table-toolbar" style={{ marginBottom: 16 }}>
          <Space>
            {/* 筛选面板 */}
            {showFilters && filters.length > 0 && (
              <FilterPanel
                filters={filters}
                values={activeFilters}
                onChange={handleFilterChange}
              />
            )}

            {/* 搜索框 */}
            {showSearch && keywordFields.length > 0 && (
              <Input.Search
                placeholder="关键词搜索"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onSearch={() => refetch()}
                style={{ width: 300 }}
                allowClear
              />
            )}

            {/* 刷新按钮 */}
            {showRefresh && (
              <Button
                icon={<ReloadOutlined />}
                onClick={() => refetch()}
                loading={isLoading}
              >
                刷新
              </Button>
            )}

            {/* 自定义操作 */}
            {extra}
          </Space>
        </div>
      )}

      {/* 表格 */}
      <Table<T>
        {...tableProps}
        columns={columns}
        dataSource={data}
        loading={isLoading}
        rowKey={(record, index) => record.id ?? index}
        pagination={false}
      />

      {/* 分页 */}
      {total > 0 && (
        <div style={{ marginTop: 16, textAlign: 'right' }}>
          <Pagination
            current={pagination.page}
            pageSize={pagination.pageSize}
            total={total}
            showSizeChanger
            showQuickJumper
            showTotal={(total) => `共 ${total} 条`}
            onChange={(page, pageSize) => handlePageChange(page, pageSize)}
            onShowSizeChange={(current, size) => handlePageChange(current, size)}
          />
        </div>
      )}
    </div>
  );
}
