/**
 * Meeting Management (Refactored)
 * 会议管理页面 (重构版本)
 */

import { useState, useEffect, useMemo as _useMemo } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Users,
  Clock,
  MapPin,
  Video,
  Phone,
  Plus,
  Search,
  Edit,
  Eye,
  RefreshCw,
  Download } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  Spin,
  Tabs,
  Badge,
  message } from
"antd";

import {
  MEETING_TYPES,
  MEETING_STATUS } from
'../components/meeting-management/meetingManagementConstants';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const MeetingManagement = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [activeTab, setActiveTab] = useState('upcoming');
  const [_searchText, _setSearchText] = useState('');


  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getMeetings();
      setMeetings(data);
      setLoading(false);
    } catch (_error) {
      message.error('加载会议数据失败');
      setLoading(false);
    }
  };

  const tabItems = [
  {
    key: 'upcoming',
    tab:
    <span>
          <Calendar size={16} />
          即将召开 ({meetings.filter((m) => m.status === 'scheduled').length})
    </span>,

    content:
    <div>
          <Table
        dataSource={meetings.filter((m) => m.status === 'scheduled')}
        columns={[
        {
          title: '会议信息',
          key: 'info',
          render: (_, record) =>
          <div>
                    <div style={{ fontWeight: 'bold' }}>{record.title}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>
                      <Users size={12} /> {record.participants.length}人
                    </div>
          </div>

        }]
        }
        loading={loading} />

    </div>

  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="meeting-management-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <Calendar className="inline-block mr-2" />
              会议管理
            </Title>
            <Text type="secondary">
              会议安排、日程管理、会议室预定
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}>

              创建会议
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={loadData}>

              刷新
            </Button>
          </Space>
        </div>
      </div>

      {/* 主要内容区域 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="large">

          {tabItems.map((item) =>
          <TabPane key={item.key} tab={item.tab}>
              {item.content}
          </TabPane>
          )}
        </Tabs>
      </Card>
    </motion.div>);

};

export default MeetingManagement;
