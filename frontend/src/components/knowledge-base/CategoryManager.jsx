/**
 * Category Manager Component
 * 分类管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Tree, Empty, Button, Space } from 'antd';

const { DirectoryTree } = Tree;

const CategoryManager = ({ categories = [], loading = false, onRefresh }) => {
  const treeData = useMemo(() => categories || [], [categories]);

  return (
    <Card
      title="分类管理"
      loading={loading}
      extra={
        <Space>
          <Button onClick={() => onRefresh?.()} disabled={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      {treeData.length === 0 ? (
        <Empty description="暂无分类数据" />
      ) : (
        <DirectoryTree
          multiple={false}
          defaultExpandAll
          treeData={treeData}
          style={{ background: '#fff' }}
        />
      )}
    </Card>
  );
};

export default CategoryManager;

