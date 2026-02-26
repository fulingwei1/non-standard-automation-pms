/**
 * Meeting Management (Refactored)
 * 会议管理页面 - 接入后端 PMO 会议 API
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Users,
  Plus,
  RefreshCw,
} from "lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Modal,
  Form,
  DatePicker,
  Typography,
  Tabs,
  message,
} from "antd";

import {
  MEETING_TYPES,
  MEETING_STATUS,
} from "@/lib/constants/meetingManagement";
import { pmoApi } from "../services/api";

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

const MeetingManagement = () => {
  const [loading, setLoading] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [activeTab, setActiveTab] = useState("upcoming");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState(undefined);
  const [filterStatus, setFilterStatus] = useState(undefined);

  // 弹窗状态
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  // 数据加载
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchKeyword || undefined,
        meeting_type: filterType,
        status: filterStatus,
      };
      const res = await pmoApi.meetings.list(params);
      const data = res.data;
      setMeetings(data?.items || data || []);
      setTotal(data?.total || 0);
    } catch (_error) {
      message.error("加载会议数据失败");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchKeyword, filterType, filterStatus]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 创建会议
  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      setSubmitting(true);
      if (values.meeting_date) {
        values.meeting_date = values.meeting_date.format("YYYY-MM-DD HH:mm");
      }
      await pmoApi.meetings.create(values);
      message.success("会议创建成功");
      setCreateModalOpen(false);
      createForm.resetFields();
      loadData();
    } catch (err) {
      if (err.errorFields) return; // form validation
      message.error("创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  // 查看详情
  const handleViewDetail = async (record) => {
    try {
      const res = await pmoApi.meetings.get(record.id);
      setSelectedMeeting(res.data);
      setDetailModalOpen(true);
    } catch (_err) {
      message.error("加载会议详情失败");
    }
  };

  // 编辑会议
  const handleEdit = (record) => {
    setSelectedMeeting(record);
    editForm.setFieldsValue(record);
    setEditModalOpen(true);
  };

  const handleUpdate = async () => {
    try {
      const values = await editForm.validateFields();
      setSubmitting(true);
      if (values.meeting_date?.format) {
        values.meeting_date = values.meeting_date.format("YYYY-MM-DD HH:mm");
      }
      await pmoApi.meetings.update(selectedMeeting.id, values);
      message.success("会议更新成功");
      setEditModalOpen(false);
      editForm.resetFields();
      loadData();
    } catch (err) {
      if (err.errorFields) return;
      message.error("更新失败");
    } finally {
      setSubmitting(false);
    }
  };

  // 表格列
  const columns = [
    {
      title: "会议名称",
      dataIndex: "meeting_name",
      key: "meeting_name",
      render: (text, record) => (
        <a onClick={() => handleViewDetail(record)}>{text || record.title}</a>
      ),
    },
    {
      title: "类型",
      dataIndex: "meeting_type",
      key: "meeting_type",
      render: (type) => {
        const found = MEETING_TYPES?.find((t) => t.value === type);
        return <Tag>{found?.label || type || "-"}</Tag>;
      },
    },
    {
      title: "时间",
      dataIndex: "meeting_date",
      key: "meeting_date",
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status) => {
        const found = MEETING_STATUS?.find((s) => s.value === status);
        return <Tag color={found?.color || "default"}>{found?.label || status || "-"}</Tag>;
      },
    },
    {
      title: "参与人数",
      key: "participants",
      render: (_, record) => (
        <span>
          <Users size={14} className="inline mr-1" />
          {record.participants?.length || record.participant_count || 0}人
        </span>
      ),
    },
    {
      title: "操作",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleViewDetail(record)}>
            详情
          </Button>
          <Button size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  // 会议表单字段
  const MeetingFormFields = () => (
    <>
      <Form.Item
        name="meeting_name"
        label="会议名称"
        rules={[{ required: true, message: "请输入会议名称" }]}
      >
        <Input placeholder="请输入会议名称" />
      </Form.Item>
      <Form.Item name="meeting_type" label="会议类型">
        <Select
          placeholder="请选择会议类型"
          options={MEETING_TYPES?.map((t) => ({ label: t.label, value: t.value }))}
        />
      </Form.Item>
      <Form.Item name="meeting_date" label="会议时间">
        <DatePicker showTime format="YYYY-MM-DD HH:mm" style={{ width: "100%" }} />
      </Form.Item>
      <Form.Item name="location" label="会议地点">
        <Input placeholder="请输入会议地点" />
      </Form.Item>
      <Form.Item name="description" label="会议描述">
        <TextArea rows={3} placeholder="请输入会议描述" />
      </Form.Item>
    </>
  );

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="meeting-management-container"
      style={{ padding: "24px", background: "#f5f5f5", minHeight: "100vh" }}
    >
      {/* 页面头部 */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <Calendar className="inline-block mr-2" />
              会议管理
            </Title>
            <Text type="secondary">会议安排、日程管理、会议室预定</Text>
          </div>
          <Space>
            <Button type="primary" icon={<Plus size={16} />} onClick={() => setCreateModalOpen(true)}>
              创建会议
            </Button>
            <Button icon={<RefreshCw size={16} />} onClick={loadData}>
              刷新
            </Button>
          </Space>
        </div>
      </div>

      {/* 筛选区域 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索会议名称"
            allowClear
            style={{ width: 240 }}
            onSearch={(val) => { setSearchKeyword(val); setPage(1); }}
          />
          <Select
            placeholder="会议类型"
            allowClear
            style={{ width: 160 }}
            options={MEETING_TYPES?.map((t) => ({ label: t.label, value: t.value }))}
            onChange={(val) => { setFilterType(val); setPage(1); }}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            options={MEETING_STATUS?.map((s) => ({ label: s.label, value: s.value }))}
            onChange={(val) => { setFilterStatus(val); setPage(1); }}
          />
        </Space>
      </Card>

      {/* 会议列表 */}
      <Card>
        <Table
          dataSource={meetings}
          columns={columns}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p) => setPage(p),
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>

      {/* 创建会议弹窗 */}
      <Modal
        title="创建会议"
        open={createModalOpen}
        onOk={handleCreate}
        onCancel={() => { setCreateModalOpen(false); createForm.resetFields(); }}
        confirmLoading={submitting}
      >
        <Form form={createForm} layout="vertical">
          <MeetingFormFields />
        </Form>
      </Modal>

      {/* 编辑会议弹窗 */}
      <Modal
        title="编辑会议"
        open={editModalOpen}
        onOk={handleUpdate}
        onCancel={() => { setEditModalOpen(false); editForm.resetFields(); }}
        confirmLoading={submitting}
      >
        <Form form={editForm} layout="vertical">
          <MeetingFormFields />
        </Form>
      </Modal>

      {/* 会议详情弹窗 */}
      <Modal
        title="会议详情"
        open={detailModalOpen}
        onCancel={() => setDetailModalOpen(false)}
        footer={null}
        width={640}
      >
        {selectedMeeting && (
          <div>
            <p><strong>会议名称：</strong>{selectedMeeting.meeting_name || selectedMeeting.title}</p>
            <p><strong>会议类型：</strong>{selectedMeeting.meeting_type}</p>
            <p><strong>会议时间：</strong>{selectedMeeting.meeting_date}</p>
            <p><strong>会议地点：</strong>{selectedMeeting.location || "-"}</p>
            <p><strong>状态：</strong>{selectedMeeting.status}</p>
            <p><strong>描述：</strong>{selectedMeeting.description || "-"}</p>
            <p><strong>会议纪要：</strong>{selectedMeeting.minutes || "-"}</p>
          </div>
        )}
      </Modal>
    </motion.div>
  );
};

export default MeetingManagement;
