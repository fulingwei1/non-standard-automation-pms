/**
 * PageHeader
 * Top section of the LeadAssessment page:
 * title, subtitle, action buttons, and view-layout toggle.
 */

import { Typography, Space, Button, Radio } from 'antd';
import { Plus, Upload, Download, LayoutGrid, List as ListIcon, Target } from 'lucide-react';

const { Title, Text } = Typography;

const PageHeader = ({
  viewLayout,
  onViewLayoutChange,
  onCreateLead,
}) => (
  <div className="page-header" style={{ marginBottom: '24px' }}>
    <div
      className="header-content"
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <div>
        <Title level={2} style={{ margin: 0 }}>
          <Target className="inline-block mr-2" />
          线索评估
        </Title>
        <Text type="secondary">销售线索评估、资格分级和转化管理</Text>
      </div>

      <Space>
        <Button
          type="primary"
          icon={<Plus size={16} />}
          onClick={onCreateLead}
        >
          新建线索
        </Button>
        <Button icon={<Upload size={16} />}>批量导入</Button>
        <Button icon={<Download size={16} />}>导出数据</Button>
        <Radio.Group
          value={viewLayout || 'grid'}
          onChange={(e) => onViewLayoutChange(e.target.value)}
          buttonStyle="solid"
        >
          <Radio.Button value="grid">
            <LayoutGrid size={16} />
          </Radio.Button>
          <Radio.Button value="list">
            <ListIcon size={16} />
          </Radio.Button>
        </Radio.Group>
      </Space>
    </div>
  </div>
);

export default PageHeader;
