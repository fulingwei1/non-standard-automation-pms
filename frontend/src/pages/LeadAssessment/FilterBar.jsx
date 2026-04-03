/**
 * FilterBar
 * Search input + source / status / qualification / industry select filters.
 */

import { Card, Row, Col, Input, Select, Space, Tag } from 'antd';
import { Search } from 'lucide-react';
import {
  LEAD_SOURCES,
  LEAD_STATUS,
  QUALIFICATION_LEVELS,
  INDUSTRY_TYPES,
} from '../../lib/constants/leadAssessment';

const FilterBar = ({ searchText, filters, onSearch, onFilterChange }) => (
  <Card className="mb-4">
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12}>
        <Input
          placeholder="搜索公司名称、联系人、电话..."
          prefix={<Search size={16} />}
          value={searchText || ''}
          onChange={(e) => onSearch(e.target.value)}
          allowClear
        />
      </Col>

      <Col xs={24} md={12}>
        <Space wrap>
          {/* 线索来源 */}
          <Select
            placeholder="线索来源"
            value={filters.source}
            onChange={(value) => onFilterChange({ source: value })}
            style={{ width: 120 }}
            allowClear
          >
            {(LEAD_SOURCES || []).map((source) => (
              <Select.Option key={source.value} value={source.value}>
                {source.icon} {source.label}
              </Select.Option>
            ))}
          </Select>

          {/* 状态 */}
          <Select
            placeholder="状态"
            value={filters.status}
            onChange={(value) => onFilterChange({ status: value })}
            style={{ width: 100 }}
            allowClear
          >
            {Object.values(LEAD_STATUS).map((status) => (
              <Select.Option key={status.value} value={status.value}>
                <Tag color={status.color}>{status.label}</Tag>
              </Select.Option>
            ))}
          </Select>

          {/* 资格分级 */}
          <Select
            placeholder="资格分级"
            value={filters.qualification}
            onChange={(value) => onFilterChange({ qualification: value })}
            style={{ width: 120 }}
            allowClear
          >
            {Object.values(QUALIFICATION_LEVELS).map((qual) => (
              <Select.Option key={qual.value} value={qual.value}>
                <Tag color={qual.color}>{qual.label}</Tag>
              </Select.Option>
            ))}
          </Select>

          {/* 行业 */}
          <Select
            placeholder="行业"
            value={filters.industry}
            onChange={(value) => onFilterChange({ industry: value })}
            style={{ width: 100 }}
            allowClear
          >
            {Object.values(INDUSTRY_TYPES).map((industry) => (
              <Select.Option key={industry.value} value={industry.value}>
                {industry.label}
              </Select.Option>
            ))}
          </Select>
        </Space>
      </Col>
    </Row>
  </Card>
);

export default FilterBar;
