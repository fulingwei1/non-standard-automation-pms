/**
 * LeadColumns
 * Ant Design table column definitions for the lead list table.
 * Exported as a hook-like factory so callers pass event handlers and get
 * back the columns array — no component state required.
 */

import { Button, Space, Tag, Dropdown, Menu, Progress } from 'antd';
import {
  Building2,
  Users,
  Phone,
  Mail,
  Calendar,
  Eye,
  Edit,
  Target,
  CheckCircle2,
  FileText,
  XCircle,
  Settings,
} from 'lucide-react';
import {
  LEAD_STATUS,
  QUALIFICATION_LEVELS,
  LEAD_SOURCES,
  INDUSTRY_TYPES,
  COMPANY_SIZES,
  SCORE_COLORS,
} from '../../lib/constants/leadAssessment';

/**
 * Build the columns array for the leads table.
 *
 * @param {Object} handlers
 * @param {Function} handlers.onView
 * @param {Function} handlers.onEdit
 * @param {Function} handlers.onAssess
 * @param {Function} handlers.onConvert
 * @param {Function} handlers.onDelete
 * @param {Function} handlers.onExport
 */
export const buildLeadColumns = ({
  onView,
  onEdit,
  onAssess,
  onConvert,
  onDelete,
  onExport,
}) => [
  {
    title: '公司信息',
    key: 'company',
    render: (_, record) => (
      <div>
        <div style={{ fontWeight: 'bold', cursor: 'pointer' }}>
          <Building2 size={16} /> {record.companyName}
        </div>
        <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
          <Users size={12} /> {record.contactPerson} · {record.position}
        </div>
        <div style={{ fontSize: 11, color: '#999' }}>
          {INDUSTRY_TYPES[record.industry?.toUpperCase()]?.label} ·{' '}
          {COMPANY_SIZES[record.companySize?.toUpperCase()]?.label}
        </div>
      </div>
    ),
  },
  {
    title: '联系方式',
    key: 'contact',
    render: (_, record) => (
      <div>
        <div style={{ fontSize: 12 }}>
          <Phone size={12} /> {record.phone}
        </div>
        <div style={{ fontSize: 12 }}>
          <Mail size={12} /> {record.email}
        </div>
      </div>
    ),
  },
  {
    title: '状态',
    key: 'status',
    render: (_, record) => (
      <div>
        <Tag color={LEAD_STATUS[record.status?.toUpperCase()]?.color}>
          {LEAD_STATUS[record.status?.toUpperCase()]?.label}
        </Tag>
        <div style={{ marginTop: 4 }}>
          <Tag
            size="small"
            color={
              QUALIFICATION_LEVELS[record.qualification?.toUpperCase()]?.color
            }
          >
            {QUALIFICATION_LEVELS[record.qualification?.toUpperCase()]?.label}
          </Tag>
        </div>
      </div>
    ),
  },
  {
    title: '评分',
    dataIndex: 'score',
    key: 'score',
    render: (score) => {
      const color = Object.values(SCORE_COLORS).find((c) => score >= c.min);
      return (
        <div>
          <div
            style={{ color: color?.color, fontWeight: 'bold', fontSize: 16 }}
          >
            {score}
          </div>
          <Progress
            percent={score}
            strokeColor={color?.color}
            showInfo={false}
            size="small"
            style={{ marginTop: 4 }}
          />
        </div>
      );
    },
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
        </Tag>
      );
    },
  },
  {
    title: '最后联系',
    dataIndex: 'lastContact',
    key: 'lastContact',
    render: (date) => (
      <div style={{ fontSize: 12 }}>
        <Calendar size={12} /> {date}
      </div>
    ),
  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) => (
      <Space>
        <Button
          type="link"
          icon={<Eye size={16} />}
          onClick={() => onView && onView(record)}
        >
          查看
        </Button>
        <Button
          type="link"
          icon={<Edit size={16} />}
          onClick={() => onEdit(record)}
        >
          编辑
        </Button>
        <Button
          type="link"
          icon={<Target size={16} />}
          onClick={() => onAssess(record)}
        >
          评估
        </Button>
        {record.qualification === 'hot' && (
          <Button
            type="link"
            icon={<CheckCircle2 size={16} />}
            onClick={() => onConvert(record)}
          >
            转化
          </Button>
        )}
        <Dropdown
          overlay={
            <Menu>
              <Menu.Item onClick={() => onExport && onExport('Excel')}>
                <FileText size={14} /> 导出Excel
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item danger onClick={() => onDelete(record.id)}>
                <XCircle size={14} /> 删除线索
              </Menu.Item>
            </Menu>
          }
        >
          <Button type="link" icon={<Settings size={16} />}>
            更多
          </Button>
        </Dropdown>
      </Space>
    ),
  },
];
