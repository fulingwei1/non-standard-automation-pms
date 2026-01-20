/**
 * Knowledge Base Overview Component
 * 知识库概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Avatar, Button, Flex } from 'antd';
import {
  BookOpen,
  FileText,
  Users,
  Download,
  Eye,
  Star,
  TrendingUp,
  FolderOpen,
  Clock } from
'lucide-react';
import {
  KNOWLEDGE_TYPES,
  FILE_TYPES,
  CATEGORIES,
  ACCESS_LEVELS } from
'./knowledgeBaseConstants';

const KnowledgeBaseOverview = ({ data, loading, onNavigate }) => {
  const [_selectedType, _setSelectedType] = useState(null);

  const overviewStats = useMemo(() => {
    if (!data?.documents) {return {};}

    const totalDocs = data.documents.length;
    const publishedDocs = data.documents.filter((d) => d.status === 'published').length;
    const totalViews = data.documents.reduce((acc, d) => acc + (d.viewCount || 0), 0);
    const totalDownloads = data.documents.reduce((acc, d) => acc + (d.downloadCount || 0), 0);

    return {
      totalDocs,
      publishedDocs,
      totalViews,
      totalDownloads,
      publishRate: totalDocs > 0 ? (publishedDocs / totalDocs * 100).toFixed(1) : 0
    };
  }, [data]);

  const typeDistribution = useMemo(() => {
    if (!data?.documents) {return {};}

    const distribution = {};
    Object.keys(KNOWLEDGE_TYPES).forEach((key) => {
      distribution[key] = 0;
    });

    data.documents.forEach((doc) => {
      if (doc.type && KNOWLEDGE_TYPES[doc.type.toUpperCase()]) {
        distribution[doc.type.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const recentDocuments = useMemo(() => {
    if (!data?.documents) {return [];}

    return data.documents.
    sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).
    slice(0, 10);
  }, [data]);

  const popularDocuments = useMemo(() => {
    if (!data?.documents) {return [];}

    return data.documents.
    sort((a, b) => (b.viewCount || 0) - (a.viewCount || 0)).
    slice(0, 8);
  }, [data]);

  const renderTypeCard = (typeKey, count) => {
    const config = KNOWLEDGE_TYPES[typeKey];
    const total = data?.documents?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card
        key={typeKey}
        size="small"
        className="type-card"
        hoverable
        onClick={() => onNavigate && onNavigate('type', config.value)}
        style={{ cursor: 'pointer', textAlign: 'center' }}>

        <div style={{ fontSize: 24, marginBottom: 8 }}>{config.icon}</div>
        <div style={{ color: config.color, fontWeight: 'bold', fontSize: 16 }}>
          {count}
        </div>
        <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
          {config.label}
        </div>
        <Progress
          percent={percentage}
          strokeColor={config.color}
          showInfo={false}
          size="small"
          style={{ marginTop: 8 }} />

      </Card>);

  };

  const renderRecentDocument = (doc) => {
    const typeConfig = KNOWLEDGE_TYPES[doc.type?.toUpperCase()];
    const fileConfig = FILE_TYPES[doc.fileType?.toUpperCase()];

    return (
      <Flex
        key={doc.id}
        align="center"
        justify="space-between"
        style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}
      >
        <Flex align="center" gap={12} style={{ flex: 1, minWidth: 0 }}>
          <Avatar
            icon={fileConfig?.icon || '📄'}
            style={{ backgroundColor: typeConfig?.color || '#1890ff', flexShrink: 0 }}
          />
          <div style={{ minWidth: 0, flex: 1 }}>
            <div>
              <span style={{ cursor: 'pointer' }}>{doc.title}</span>
              <Tag size="small" style={{ marginLeft: 8 }}>
                {typeConfig?.label}
              </Tag>
            </div>
            <div style={{ color: '#666', fontSize: 13, marginTop: 4 }}>{doc.description}</div>
            <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
              <Clock size={12} style={{ verticalAlign: 'middle' }} /> {doc.createdAt} · <Users size={12} style={{ verticalAlign: 'middle' }} /> {doc.author}
            </div>
          </div>
        </Flex>
        <Flex gap={4} style={{ flexShrink: 0 }}>
          <Button type="link" icon={<Eye size={14} />} size="small">查看</Button>
          <Button type="link" icon={<Download size={14} />} size="small">下载</Button>
        </Flex>
      </Flex>
    );
  };

  return (
    <div className="knowledge-base-overview">
      {/* 统计概览 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="文档总数"
              value={overviewStats.totalDocs}
              prefix={<BookOpen />}
              suffix={`(${overviewStats.publishedDocs} 已发布)`}
              styles={{ content: { color: '#1890ff' } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="总浏览量"
              value={overviewStats.totalViews}
              prefix={<Eye />}
              styles={{ content: { color: '#52c41a' } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="总下载量"
              value={overviewStats.totalDownloads}
              prefix={<Download />}
              styles={{ content: { color: '#722ed1' } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="发布率"
              value={overviewStats.publishRate}
              suffix="%"
              prefix={<TrendingUp />}
              styles={{ content: { color: '#faad14' } }} />

          </Card>
        </Col>
      </Row>

      {/* 文档类型分布 */}
      <Card title="文档类型分布" className="mb-4" loading={loading}>
        <Row gutter={[16, 16]}>
          {Object.entries(typeDistribution).map(([type, count]) =>
          renderTypeCard(type, count)
          )}
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        {/* 最近文档 */}
        <Col xs={24} lg={12}>
          <Card
            title="最近文档"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('recent')}>
                查看更多
            </Button>
            }>

            <div style={{ maxHeight: 400, overflowY: 'auto' }}>
              {recentDocuments.length > 0 ? (
                recentDocuments.map(renderRecentDocument)
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>暂无文档</div>
              )}
            </div>

          </Card>
        </Col>

        {/* 热门文档 */}
        <Col xs={24} lg={12}>
          <Card
            title="热门文档"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('popular')}>
                查看更多
            </Button>
            }>

            <div style={{ maxHeight: 400, overflowY: 'auto' }}>
              {popularDocuments.length > 0 ? (
                popularDocuments.map(renderRecentDocument)
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>暂无文档</div>
              )}
            </div>

          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card title="快速操作" className="mt-4" loading={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Button
              type="primary"
              block
              icon={<BookOpen />}
              onClick={() => onNavigate && onNavigate('create')}>

              创建文档
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<FolderOpen />}
              onClick={() => onNavigate && onNavigate('categories')}>

              分类管理
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<Download />}
              onClick={() => onNavigate && onNavigate('export')}>

              批量导出
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<Star />}
              onClick={() => onNavigate && onNavigate('favorites')}>

              我的收藏
            </Button>
          </Col>
        </Row>
      </Card>
    </div>);

};

export default KnowledgeBaseOverview;