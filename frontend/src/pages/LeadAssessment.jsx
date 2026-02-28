/**
 * Lead Assessment Page (Refactored)
 * Sales lead evaluation and qualification (重构版本)
 */

import { useState, useMemo, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Filter,
  Plus,
  LayoutGrid,
  List as ListIcon,
  Calendar,
  Building2,
  User,
  Phone,
  Mail,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Star,
  TrendingUp,
  TrendingDown,
  Eye,
  Edit,
  FileText,
  Target,
  PhoneCall,
  MessageSquare,
  Users,
  Award,
  BarChart3,
  Settings,
  RefreshCw,
  Download,
  Upload } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Modal,
  Form,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Divider,
  List,
  Avatar,
  Typography,
  Alert,
  Badge,
  Dropdown,
  Menu,
  Switch,
  Radio,
  Checkbox,
  message,
  Spin,
  Tabs,
  Progress,
  Timeline,
  Rate,
  InputNumber,
  Slider,
  Steps } from
"antd";

// 导入拆分后的组件
import {
  LeadOverview,
  LeadList,
  AssessmentForm,
  ScoringEngine,
  FollowUpManager } from
'../components/lead-assessment';

import { leadApi } from '../services/api/sales';

import {
  LEAD_SOURCES,
  LEAD_STATUS,
  QUALIFICATION_LEVELS,
  INDUSTRY_TYPES,
  COMPANY_SIZES,
  BUDGET_RANGES,
  DECISION_MAKER_ROLES,
  ASSESSMENT_CRITERIA,
  FOLLOW_UP_STATUS,
  TASK_TYPES,
  SCORE_COLORS,
  TABLE_CONFIG,
  DEFAULT_FILTERS } from
'@/lib/constants/leadAssessment';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;
const { Step } = Steps;

const LeadAssessment = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [leads, setLeads] = useState([]);
  const [_selectedLead, setSelectedLead] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [viewLayout, setViewLayout] = useState('grid');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [overdueFollowUps, setOverdueFollowUps] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState({ growth: 0, newLeads: 0, convertedLeads: 0 });

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 获取线索列表
      const leadsRes = await leadApi.list({
        source: filters.source || undefined,
        status: filters.status || undefined,
        qualification: filters.qualification || undefined,
        industry: filters.industry || undefined,
      });
      const leadsData = leadsRes.data?.items || leadsRes.data?.items || leadsRes.data || [];
      // 将后端字段映射到前端字段
      const mappedLeads = leadsData.map((lead) => ({
        id: lead.id,
        companyName: lead.company_name || lead.companyName || '',
        contactPerson: lead.contact_person || lead.contactPerson || '',
        position: lead.position || '',
        phone: lead.phone || '',
        email: lead.email || '',
        industry: lead.industry || '',
        companySize: lead.company_size || lead.companySize || '',
        source: lead.source || '',
        status: lead.status?.toLowerCase() || '',
        qualification: lead.qualification?.toLowerCase() || '',
        score: lead.score || 0,
        budget: lead.budget || '',
        authority: lead.authority || '',
        need: lead.need || '',
        timeline: lead.timeline || '',
        address: lead.address || '',
        createdAt: lead.created_at || lead.createdAt || '',
        lastContact: lead.last_contact || lead.lastContact || '',
        description: lead.description || '',
      }));
      setLeads(mappedLeads);

      // 获取所有线索的跟进记录
      const allFollowUps = [];
      for (const lead of mappedLeads.slice(0, 20)) { // 限制请求数
        try {
          const fuRes = await leadApi.getFollowUps(lead.id);
          const fuData = fuRes.data?.items || fuRes.data?.items || fuRes.data || [];
          fuData.forEach((fu) => {
            allFollowUps.push({
              id: fu.id,
              leadId: lead.id,
              leadCompany: lead.companyName,
              type: fu.type || fu.follow_up_type || 'call',
              description: fu.description || fu.content || '',
              dueDate: fu.due_date || fu.dueDate || '',
              status: fu.status?.toLowerCase() || 'pending',
            });
          });
        } catch (_e) { /* skip individual failures */ }
      }
      const now = new Date();
      setFollowUps(allFollowUps.filter((fu) => fu.status !== 'overdue'));
      setOverdueFollowUps(allFollowUps.filter((fu) => {
        if (fu.status === 'overdue') return true;
        return fu.dueDate && new Date(fu.dueDate) < now && fu.status === 'pending';
      }));

      // 计算月度统计（前端聚合）
      const thisMonth = new Date();
      const lastMonth = new Date(thisMonth);
      lastMonth.setMonth(lastMonth.getMonth() - 1);
      const thisMonthStr = `${thisMonth.getFullYear()}-${String(thisMonth.getMonth() + 1).padStart(2, '0')}`;
      const lastMonthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
      const thisMonthLeads = mappedLeads.filter((l) => (l.createdAt || '').startsWith(thisMonthStr));
      const lastMonthLeads = mappedLeads.filter((l) => (l.createdAt || '').startsWith(lastMonthStr));
      const convertedLeads = mappedLeads.filter((l) => l.status === 'converted' || l.qualification === 'converted');
      const growth = lastMonthLeads.length > 0
        ? ((thisMonthLeads.length - lastMonthLeads.length) / lastMonthLeads.length * 100)
        : 0;
      setMonthlyStats({
        growth: parseFloat(growth.toFixed(1)),
        newLeads: thisMonthLeads.length,
        convertedLeads: convertedLeads.length,
      });
    } catch (_error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const searchLower = searchText.toLowerCase();
      const matchesSearch = !searchText ||
      (lead.companyName || "").toLowerCase().includes(searchLower) ||
      (lead.contactPerson || "").toLowerCase().includes(searchLower) ||
      (lead.phone || "").includes(searchText);

      const matchesSource = !filters.source || lead.source === filters.source;
      const matchesStatus = !filters.status || lead.status === filters.status;
      const matchesQualification = !filters.qualification || lead.qualification === filters.qualification;
      const matchesIndustry = !filters.industry || lead.industry === filters.industry;

      return matchesSearch && matchesSource && matchesStatus && matchesQualification && matchesIndustry;
    });
  }, [leads, searchText, filters]);

  // 事件处理
  const handleCreateLead = () => {
    setEditingLead(null);
    setShowAssessmentModal(true);
  };

  const handleEditLead = (lead) => {
    setEditingLead(lead);
    setShowAssessmentModal(true);
  };

  const handleDeleteLead = async (leadId) => {
    try {
      setLoading(true);
      await leadApi.update(leadId, { status: 'INVALID' });
      setLeads(leads.filter((l) => l.id !== leadId));
      message.success('删除成功');
    } catch (_error) {
      message.error('删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAssessLead = (lead) => {
    setEditingLead(lead);
    setActiveTab('assessment');
  };

  const handleConvertLead = (lead) => {
    message.success(`正在转化线索: ${lead.companyName}`);
  };

  const handleExportLeads = (format) => {
    message.success(`正在导出${format}格式线索数据...`);
  };

  // 评分计算
  const calculateLeadScore = (lead) => {
    let totalScore = 0;

    // 预算评分
    const budgetScore =
    (BUDGET_RANGES.find((b) => b.value === lead.budget)?.weight || 0) * 5;
    totalScore += budgetScore * ASSESSMENT_CRITERIA.BUDGET.weight;

    // 权限评分
    const authorityScore = DECISION_MAKER_ROLES[lead.authority?.toUpperCase()]?.weight || 0;
    totalScore += authorityScore * ASSESSMENT_CRITERIA.AUTHORITY.weight;

    // 需求评分
    const needScore = lead.need === 'urgent' ? 5 : lead.need === 'moderate' ? 3 : 1;
    totalScore += needScore * ASSESSMENT_CRITERIA.NEED.weight;

    // 时间评分
    const timeScore = lead.timeline === 'immediate' ? 5 : lead.timeline === 'quarter' ? 3 : 1;
    totalScore += timeScore * ASSESSMENT_CRITERIA.TIMELINE.weight;

    // 竞争评分（简化）
    const competitionScore = 3; // 假设中等竞争
    totalScore += competitionScore * ASSESSMENT_CRITERIA.COMPETITION.weight;

    return Math.round(totalScore);
  };

  // 表格列配置
  const _leadColumns = [
  {
    title: '公司信息',
    key: 'company',
    render: (_, record) =>
    <div>
          <div style={{ fontWeight: 'bold', cursor: 'pointer' }}>
            <Building2 size={16} /> {record.companyName}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            <Users size={12} /> {record.contactPerson} · {record.position}
          </div>
          <div style={{ fontSize: 11, color: '#999' }}>
            {INDUSTRY_TYPES[record.industry?.toUpperCase()]?.label} · 
            {COMPANY_SIZES[record.companySize?.toUpperCase()]?.label}
          </div>
    </div>

  },
  {
    title: '联系方式',
    key: 'contact',
    render: (_, record) =>
    <div>
          <div style={{ fontSize: 12 }}>
            <Phone size={12} /> {record.phone}
          </div>
          <div style={{ fontSize: 12 }}>
            <Mail size={12} /> {record.email}
          </div>
    </div>

  },
  {
    title: '状态',
    key: 'status',
    render: (_, record) =>
    <div>
          <Tag color={LEAD_STATUS[record.status?.toUpperCase()]?.color}>
            {LEAD_STATUS[record.status?.toUpperCase()]?.label}
          </Tag>
          <div style={{ marginTop: 4 }}>
            <Tag
          size="small"
          color={QUALIFICATION_LEVELS[record.qualification?.toUpperCase()]?.color}>

              {QUALIFICATION_LEVELS[record.qualification?.toUpperCase()]?.label}
            </Tag>
          </div>
    </div>

  },
  {
    title: '评分',
    dataIndex: 'score',
    key: 'score',
    render: (score) => {
      const color = Object.values(SCORE_COLORS).find((c) => score >= c.min);
      return (
        <div>
            <div style={{
            color: color?.color,
            fontWeight: 'bold',
            fontSize: 16
          }}>
              {score}
            </div>
            <Progress
            percent={score}
            strokeColor={color?.color}
            showInfo={false}
            size="small"
            style={{ marginTop: 4 }} />

        </div>);

    }
  },
  {
    title: '来源',
    dataIndex: 'source',
    key: 'source',
    render: (source) => {
      const config = LEAD_SOURCES.find((item) => item.value === source);
      return (
        <Tag color={config?.color}>
            {config?.icon} {config?.label || source}
        </Tag>);

    }
  },
  {
    title: '最后联系',
    dataIndex: 'lastContact',
    key: 'lastContact',
    render: (date) =>
    <div style={{ fontSize: 12 }}>
          <Calendar size={12} /> {date}
    </div>

  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) =>
    <Space>
          <Button
        type="link"
        icon={<Eye size={16} />}
        onClick={() => setSelectedLead(record)}>

            查看
          </Button>
          <Button
        type="link"
        icon={<Edit size={16} />}
        onClick={() => handleEditLead(record)}>

            编辑
          </Button>
          <Button
        type="link"
        icon={<Target size={16} />}
        onClick={() => handleAssessLead(record)}>

            评估
          </Button>
          {record.qualification === 'hot' &&
      <Button
        type="link"
        icon={<CheckCircle2 size={16} />}
        onClick={() => handleConvertLead(record)}>

              转化
      </Button>
      }
          <Dropdown
        overlay={
        <Menu>
                <Menu.Item onClick={() => handleExportLeads('Excel')}>
                  <FileText size={14} /> 导出Excel
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
            danger
            onClick={() => handleDeleteLead(record.id)}>

                  <XCircle size={14} /> 删除线索
                </Menu.Item>
        </Menu>
        }>

            <Button type="link" icon={<Settings size={16} />}>
              更多
            </Button>
          </Dropdown>
    </Space>

  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="lead-assessment-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <Target className="inline-block mr-2" />
              线索评估
            </Title>
            <Text type="secondary">
              销售线索评估、资格分级和转化管理
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}
              onClick={handleCreateLead}>

              新建线索
            </Button>
            <Button
              icon={<Upload size={16} />}>

              批量导入
            </Button>
            <Button
              icon={<Download size={16} />}>

              导出数据
            </Button>
            <Radio.Group
              value={viewLayout}
              onChange={(e) => setViewLayout(e.target.value)}
              buttonStyle="solid">

              <Radio.Button value="grid"><LayoutGrid size={16} /></Radio.Button>
              <Radio.Button value="list"><ListIcon size={16} /></Radio.Button>
            </Radio.Group>
          </Space>
        </div>
      </div>

      {/* 搜索和过滤器 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              placeholder="搜索公司名称、联系人、电话..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="线索来源"
                value={filters.source}
                onChange={(value) => setFilters({ ...filters, source: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(LEAD_SOURCES).map((source) =>
                <Select.Option key={source.value} value={source.value}>
                    {source.icon} {source.label}
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 100 }}
                allowClear>

                {Object.values(LEAD_STATUS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="资格分级"
                value={filters.qualification}
                onChange={(value) => setFilters({ ...filters, qualification: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(QUALIFICATION_LEVELS).map((qual) =>
                <Select.Option key={qual.value} value={qual.value}>
                    <Tag color={qual.color}>{qual.label}</Tag>
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="行业"
                value={filters.industry}
                onChange={(value) => setFilters({ ...filters, industry: value })}
                style={{ width: 100 }}
                allowClear>

                {Object.values(INDUSTRY_TYPES).map((industry) =>
                <Select.Option key={industry.value} value={industry.value}>
                    {industry.label}
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
            label: (
              <span>
                <BarChart3 size={16} />
                概览分析
              </span>
            ),
            children: (
              <LeadOverview
                data={{ leads, followUps, overdueFollowUps, monthlyStats }}
                loading={loading}
                onNavigate={(type, _value) => {
                  if (type === 'hot-leads') {
                    setFilters({ ...filters, qualification: 'hot' });
                    setActiveTab('leads');
                  } else if (type === 'follow-ups') {
                    setActiveTab('followups');
                  } else if (type === 'overdue') {
                    setFilters({ ...filters, status: 'overdue' });
                    setActiveTab('leads');
                  }
                }}
              />
            ),
          },
          {
            key: 'leads',
            label: (
              <span>
                <Users size={16} />
                线索列表 ({filteredLeads.length})
              </span>
            ),
            children: (
              <LeadList
                leads={filteredLeads}
                loading={loading}
                onEdit={handleEditLead}
                onDelete={handleDeleteLead}
                onAssess={handleAssessLead}
                onConvert={handleConvertLead}
              />
            ),
          },
          {
            key: 'assessment',
            label: (
              <span>
                <Award size={16} />
                评估表单
              </span>
            ),
            children: (
              <AssessmentForm
                lead={editingLead}
                onSave={(lead) => {
                  if (lead.id) {
                    setLeads(leads.map((l) => l.id === lead.id ? { ...lead, score: calculateLeadScore(lead) } : l));
                  } else {
                    const newLead = { ...lead, id: Date.now(), score: calculateLeadScore(lead), createdAt: new Date().toISOString().split('T')[0] };
                    setLeads([...leads, newLead]);
                  }
                  setShowAssessmentModal(false);
                  setEditingLead(null);
                  loadData();
                }}
                onCancel={() => {
                  setShowAssessmentModal(false);
                  setEditingLead(null);
                }}
              />
            ),
          },
          {
            key: 'scoring',
            label: (
              <span>
                <Target size={16} />
                评分引擎
              </span>
            ),
            children: (
              <ScoringEngine
                leads={leads}
                criteria={ASSESSMENT_CRITERIA}
                onReScore={(updatedLeads) => {
                  setLeads(updatedLeads);
                  message.success('重新评分完成');
                }}
              />
            ),
          },
          {
            key: 'followups',
            label: (
              <span>
                <MessageSquare size={16} />
                跟进管理
              </span>
            ),
            children: (
              <FollowUpManager
                followUps={[...followUps, ...overdueFollowUps]}
                leads={leads}
                loading={loading}
                onRefresh={loadData}
              />
            ),
          },
        ]}
      />

      {/* 线索评估模态框 */}
      <Modal
        title={editingLead ? '编辑线索' : '新建线索'}
        open={showAssessmentModal}
        onCancel={() => {
          setShowAssessmentModal(false);
          setEditingLead(null);
        }}
        footer={null}
        width={1000}>

        <AssessmentForm
          lead={editingLead}
          onSave={(lead) => {
            if (lead.id) {
              setLeads(leads.map((l) => l.id === lead.id ? { ...lead, score: calculateLeadScore(lead) } : l));
            } else {
              const newLead = { ...lead, id: Date.now(), score: calculateLeadScore(lead), createdAt: new Date().toISOString().split('T')[0] };
              setLeads([...leads, newLead]);
            }
            setShowAssessmentModal(false);
            setEditingLead(null);
            loadData();
          }}
          onCancel={() => {
            setShowAssessmentModal(false);
            setEditingLead(null);
          }} />

      </Modal>
    </motion.div>);

};

export default LeadAssessment;