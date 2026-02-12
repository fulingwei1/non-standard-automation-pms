/**
 * 知识库 (Refactored)
 * 历史方案、产品知识、工艺知识、竞品情报、模板库 (重构版本)
 */

import React, { useState, useEffect, useCallback as _useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  Search,
  Filter,
  Plus,
  Calendar,
  Eye,
  Download,
  Star,
  StarOff,
  Folder,
  FileText,
  File,
  Image,
  Video,
  MoreHorizontal,
  ChevronRight,
  ChevronDown,
  Clock,
  Users,
  Building2,
  Briefcase,
  Package,
  Upload,
  Edit,
  Trash2,
  Share,
  Copy,
  Settings,
  Grid,
  List,
  TrendingUp } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Tabs,
  Modal,
  Form,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Divider,
  Avatar,
  Typography,
  Alert,
  Badge,
  Dropdown,
  Menu,
  Switch,
  Radio,
  Checkbox,
  Upload as AntUpload,
  message,
  Spin,
  Tree,
  Breadcrumb,
  Pagination,
  Empty,
  Rate } from
"antd";

// 导入拆分后的组件
import {
  KnowledgeBaseOverview,
  DocumentManager,
  CategoryManager,
  SearchAndFilter,
  DocumentViewer } from
'../components/knowledge-base';

import {
  KNOWLEDGE_TYPES,
  FILE_TYPES,
  ACCESS_LEVELS,
  CATEGORIES,
  SORT_OPTIONS,
  SEARCH_FILTERS,
  VIEW_LAYOUTS,
  IMPORTANCE_LEVELS,
  STATUS_OPTIONS,
  TABLE_CONFIG,
  DEFAULT_FILTERS } from
'@/lib/constants/knowledge';

// 导入API服务
import { serviceApi } from '../services/api/service';

const { Title, Text, Paragraph } = Typography;
// TabPane is deprecated - using items prop instead
const { RangePicker } = DatePicker;
const { TextArea } = Input;
const { DirectoryTree } = Tree;

const KnowledgeBase = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [viewLayout, setViewLayout] = useState('grid');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');
  const [_expandedKeys, _setExpandedKeys] = useState(['0']);
  const [_selectedKeys, _setSelectedKeys] = useState([]);
  const [_showUploadModal, setShowUploadModal] = useState(false);
  const [_showCreateModal, setShowCreateModal] = useState(false);
  const [_editingDocument, setEditingDocument] = useState(null);

  // 默认分类树（静态数据，可后续改为从API获取）
  const defaultCategories = [
  {
    key: '0',
    title: '全部文档',
    children: [
    {
      key: '1',
      title: '工程技术',
      children: [
      { key: '1-1', title: '历史方案' },
      { key: '1-2', title: '产品知识' },
      { key: '1-3', title: '工艺知识' }]

    },
    {
      key: '2',
      title: '销售支持',
      children: [
      { key: '2-1', title: '竞品情报' },
      { key: '2-2', title: '销售模板' }]

    }]

  }];


  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 调用真实API
      const params = {
        page: 1,
        page_size: 100,
        keyword: searchText || undefined,
        category: filters.category || undefined,
        status: filters.status || undefined,
        is_faq: filters.is_faq || undefined
      };

      const response = await serviceApi.knowledgeBase.list(params);
      const apiData = response.data || response;

      // 映射API响应到组件期望的格式
      const mappedDocuments = (apiData.items || []).map((item) => ({
        id: item.id,
        title: item.title,
        type: item.is_faq ? 'faq' : item.file_path ? 'document' : 'article',
        category: item.category || 'engineering',
        status: item.status?.toLowerCase() || 'draft',
        accessLevel: 'internal',
        author: item.author_name || '未知',
        createdAt: item.created_at?.split('T')[0] || '',
        updatedAt: item.updated_at?.split('T')[0] || '',
        viewCount: item.view_count || 0,
        downloadCount: item.download_count || 0,
        likeCount: item.like_count || 0,
        helpfulCount: item.helpful_count || 0,
        adoptCount: item.adopt_count || 0,
        rating: item.rating || 0,
        tags: item.tags || [],
        description: item.content?.substring(0, 200) || '',
        content: item.content,
        fileUrl: item.file_path,
        fileType: item.file_path ? 'document' : 'text',
        fileName: item.file_name,
        fileSize: item.file_size,
        isFeatured: item.is_featured,
        isFaq: item.is_faq,
        allowDownload: item.allow_download
      }));

      setDocuments(mappedDocuments);
      setCategories(defaultCategories);
    } catch (error) {
      console.error('加载知识库数据失败:', error);
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchesSearch = !searchText ||
      (doc.title || "").toLowerCase().includes(searchLower) ||
      (doc.description || "").toLowerCase().includes(searchLower) ||
      (doc.tags || []).some((tag) => (tag || "").toLowerCase().includes(searchLower));

      const matchesType = !filters.type || doc.type === filters.type;
      const matchesCategory = !filters.category || doc.category === filters.category;
      const matchesStatus = !filters.status || doc.status === filters.status;
      const matchesAccessLevel = !filters.accessLevel || doc.accessLevel === filters.accessLevel;

      return matchesSearch && matchesType && matchesCategory && matchesStatus && matchesAccessLevel;
    });
  }, [documents, searchText, filters]);

  // 事件处理
  const _handleUploadDocument = () => {
    setShowUploadModal(true);
  };

  const handleCreateDocument = () => {
    setShowCreateModal(true);
  };

  const handleEditDocument = (doc) => {
    setEditingDocument(doc);
    setShowCreateModal(true);
  };

  const handleDeleteDocument = async (docId) => {
    try {
      setLoading(true);
      // 调用真实删除API
      await serviceApi.knowledgeBase.delete(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
      message.success('删除成功');
    } catch (error) {
      console.error('删除文档失败:', error);
      message.error('删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = (docId) => {
    setDocuments(documents.map((doc) =>
    doc.id === docId ?
    { ...doc, isFavorite: !doc.isFavorite } :
    doc
    ));
    message.success('收藏状态更新成功');
  };

  const handleDocumentView = (doc) => {
    setSelectedDocument(doc);
    // 更新浏览次数
    setDocuments(documents.map((d) =>
    d.id === doc.id ?
    { ...d, viewCount: (d.viewCount || 0) + 1 } :
    d
    ));
  };

  const handleDownload = (doc) => {
    message.success(`正在下载: ${doc.title}`);
    // 更新下载次数
    setDocuments(documents.map((d) =>
    d.id === doc.id ?
    { ...d, downloadCount: (d.downloadCount || 0) + 1 } :
    d
    ));
  };

  // 表格列配置
  const documentColumns = [
  {
    title: '文档标题',
    dataIndex: 'title',
    key: 'title',
    render: (text, record) =>
    <div>
          <div style={{ fontWeight: 'bold', cursor: 'pointer' }} onClick={() => handleDocumentView(record)}>
            {FILE_TYPES[record.fileType?.toUpperCase()]?.icon || '📄'} {text}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            <Tag size="small">{KNOWLEDGE_TYPES[record.type?.toUpperCase()]?.label}</Tag>
            <Tag size="small">{CATEGORIES[record.category?.toUpperCase()]?.label}</Tag>
            {record.isFavorite && <Star size={12} style={{ color: '#faad14' }} />}
          </div>
    </div>

  },
  {
    title: '作者',
    dataIndex: 'author',
    key: 'author',
    render: (author) =>
    <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar size="small" icon={<Users />} />
          <span style={{ marginLeft: 8 }}>{author}</span>
    </div>

  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status) => {
      const config = STATUS_OPTIONS[status?.toUpperCase()];
      return <Tag color={config?.color}>{config?.label}</Tag>;
    }
  },
  {
    title: '访问级别',
    dataIndex: 'accessLevel',
    key: 'accessLevel',
    render: (level) => {
      const config = ACCESS_LEVELS[level?.toUpperCase()];
      return <Tag color={config?.color}>{config?.label}</Tag>;
    }
  },
  {
    title: '统计',
    key: 'stats',
    render: (_, record) =>
    <div>
          <div style={{ fontSize: 12 }}>
            <Eye size={12} /> {record.viewCount || 0} 
            <Download size={12} style={{ marginLeft: 8 }} /> {record.downloadCount || 0}
          </div>
          {record.rating &&
      <Rate disabled value={record.rating} style={{ fontSize: 12 }} />
      }
    </div>

  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    render: (date) => <span style={{ fontSize: 12 }}>{date}</span>
  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) =>
    <Space>
          <Button
        type="link"
        icon={<Eye size={16} />}
        onClick={() => handleDocumentView(record)}>

            查看
          </Button>
          <Button
        type="link"
        icon={<Download size={16} />}
        onClick={() => handleDownload(record)}>

            下载
          </Button>
          <Button
        type="link"
        icon={record.isFavorite ? <Star size={16} /> : <StarOff size={16} />}
        onClick={() => handleToggleFavorite(record.id)}>

            {record.isFavorite ? '已收藏' : '收藏'}
          </Button>
          <Button
        type="link"
        icon={<Edit size={16} />}
        onClick={() => handleEditDocument(record)}>

            编辑
          </Button>
          <Button
        type="link"
        danger
        icon={<Trash2 size={16} />}
        onClick={() => handleDeleteDocument(record.id)}>

            删除
          </Button>
    </Space>

  }];


  // 渲染文档网格
  const renderDocumentGrid = () =>
  <Row gutter={[16, 16]}>
      {filteredDocuments.map((doc) => {
      const typeConfig = KNOWLEDGE_TYPES[doc.type?.toUpperCase()];
      const fileConfig = FILE_TYPES[doc.fileType?.toUpperCase()];

      return (
        <Col xs={24} sm={12} lg={8} xl={6} key={doc.id}>
            <Card
            hoverable
            className="document-card"
            cover={
            <div style={{
              height: 120,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: typeConfig?.color || '#f0f0f0'
            }}>
                  <span style={{ fontSize: 48 }}>{fileConfig?.icon || '📄'}</span>
            </div>
            }
            actions={[
            <Eye key="view" onClick={() => handleDocumentView(doc)} />,
            <Download key="download" onClick={() => handleDownload(doc)} />,
            doc.isFavorite ?
            <Star key="favorite" onClick={() => handleToggleFavorite(doc.id)} /> :
            <StarOff key="favorite" onClick={() => handleToggleFavorite(doc.id)} />]
            }>

              <Card.Meta
              title={
              <div style={{ fontSize: 14, height: 40, overflow: 'hidden' }}>
                    {doc.title}
              </div>
              }
              description={
              <div>
                    <div style={{ fontSize: 12, color: '#666', height: 40, overflow: 'hidden' }}>
                      {doc.description}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Tag size="small">{typeConfig?.label}</Tag>
                      <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                        <Users size={10} /> {doc.author} · <Clock size={10} /> {doc.createdAt}
                      </div>
                    </div>
              </div>
              } />

            </Card>
        </Col>);

    })}
  </Row>;


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="knowledge-base-container"
      style={{ padding: '24px', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <BookOpen className="inline-block mr-2" />
              知识库
            </Title>
            <Text type="secondary">
              历史方案、产品知识、工艺知识、竞品情报、模板库
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}
              onClick={handleCreateDocument}>

              创建文档
            </Button>
            <Button
              icon={<Upload size={16} />}
              onClick={() => setShowUploadModal(true)}>

              上传文档
            </Button>
            <Radio.Group
              value={viewLayout}
              onChange={(e) => setViewLayout(e.target.value)}
              buttonStyle="solid">

              <Radio.Button value="grid"><Grid size={16} /></Radio.Button>
              <Radio.Button value="list"><List size={16} /></Radio.Button>
            </Radio.Group>
          </Space>
        </div>
      </div>

      {/* 搜索和过滤器 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              placeholder="搜索文档标题、内容、标签..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="文档类型"
                value={filters.type}
                onChange={(value) => setFilters({ ...filters, type: value })}
                style={{ width: 150 }}
                allowClear>

                {Object.values(KNOWLEDGE_TYPES).map((type) =>
                <Select.Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="分类"
                value={filters.category}
                onChange={(value) => setFilters({ ...filters, category: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(CATEGORIES).map((cat) =>
                <Select.Option key={cat.value} value={cat.value}>
                    {cat.label}
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(STATUS_OPTIONS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                </Select.Option>
                )}
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主要内容区域 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        style={{ marginBottom: '24px' }}
        items={[
        {
          key: 'overview',
          label:
          <span>
                <TrendingUp size={16} />
                概览分析
          </span>,

          children:
          <KnowledgeBaseOverview
            data={{ documents: filteredDocuments, categories }}
            loading={loading}
            onNavigate={(type, value) => {
              setActiveTab('documents');
              if (type === 'type') {setFilters({ ...filters, type: value });}
            }} />


        },
        {
          key: 'documents',
          label:
          <span>
                <FileText size={16} />
                文档管理 ({filteredDocuments.length})
          </span>,

          children: loading ?
          <Spin size="large" style={{ display: 'block', textAlign: 'center', padding: '100px 0' }} /> :
          viewLayout === 'grid' ?
          renderDocumentGrid() :

          <Table
            columns={documentColumns}
            dataSource={filteredDocuments}
            rowKey="id"
            pagination={TABLE_CONFIG.pagination}
            scroll={TABLE_CONFIG.scroll} />


        },
        {
          key: 'categories',
          label:
          <span>
                <Folder size={16} />
                分类管理
          </span>,

          children:
          <CategoryManager
            categories={categories}
            loading={loading}
            onRefresh={loadData} />


        },
        {
          key: 'search',
          label:
          <span>
                <Filter size={16} />
                高级搜索
          </span>,

          children:
          <SearchAndFilter
            filters={filters}
            onFiltersChange={setFilters}
            documents={filteredDocuments}
            loading={loading} />


        }]
        } />


      {/* 文档查看器模态框 */}
      <Modal
        title={selectedDocument?.title}
        open={!!selectedDocument}
        onCancel={() => setSelectedDocument(null)}
        footer={null}
        width={1000}>

        {selectedDocument &&
        <DocumentViewer
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)} />

        }
      </Modal>
    </motion.div>);

};

export default KnowledgeBase;