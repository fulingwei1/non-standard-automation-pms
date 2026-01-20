/**
 * Contract Editor Component
 * 合同编辑组件（占位实现，保证页面可运行）
 */

import React, { useEffect } from 'react';
import { Card, Form, Row, Col, Input, Select, InputNumber, Space, Button, message } from 'antd';
import {
  CONTRACT_TYPES,
  PAYMENT_TERMS,
  RISK_LEVELS,
  CONTRACT_TEMPLATES,
  APPROVAL_LEVELS
} from './contractManagementConstants';

const ContractEditor = ({ contract, onSave, onCancel }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (!contract) {
      form.resetFields();
      return;
    }

    form.setFieldsValue({
      title: contract.title,
      type: contract.type,
      clientName: contract.clientName,
      value: contract.value,
      signingDate: contract.signingDate,
      expiryDate: contract.expiryDate,
      paymentTerms: contract.paymentTerms,
      riskLevel: contract.riskLevel,
      template: contract.template,
      approvalLevel: contract.approvalLevel
    });
  }, [contract, form]);

  const handleFinish = async (values) => {
    message.success(contract ? '已保存合同（模拟）' : '已创建合同（模拟）');
    onSave?.(values);
  };

  return (
    <Card>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        initialValues={{
          type: 'sales',
          riskLevel: 'medium',
          paymentTerms: 'progress'
        }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Form.Item
              label="合同名称"
              name="title"
              rules={[{ required: true, message: '请输入合同名称' }]}
            >
              <Input placeholder="例如：光伏电站建设合同" allowClear />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item label="客户名称" name="clientName">
              <Input placeholder="例如：绿色能源科技有限公司" allowClear />
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="合同类型" name="type">
              <Select allowClear placeholder="选择合同类型">
                {Object.values(CONTRACT_TYPES).map((t) => (
                  <Select.Option key={t.value} value={t.value}>
                    {t.icon} {t.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="合同金额" name="value">
              <InputNumber
                style={{ width: '100%' }}
                min={0}
                step={1000}
                placeholder="金额（元）"
              />
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="风险等级" name="riskLevel">
              <Select allowClear placeholder="选择风险等级">
                {Object.values(RISK_LEVELS).map((r) => (
                  <Select.Option key={r.value} value={r.value}>
                    <span style={{ color: r.color }}>{r.label}</span>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item label="签署日期" name="signingDate">
              <Input placeholder="YYYY-MM-DD" allowClear />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item label="到期日期" name="expiryDate">
              <Input placeholder="YYYY-MM-DD" allowClear />
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="付款条款" name="paymentTerms">
              <Select allowClear placeholder="选择付款条款">
                {Object.values(PAYMENT_TERMS).map((p) => (
                  <Select.Option key={p.value} value={p.value}>
                    {p.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="合同模板" name="template">
              <Select allowClear placeholder="选择模板">
                {Object.values(CONTRACT_TEMPLATES).map((t) => (
                  <Select.Option key={t.value} value={t.value}>
                    {t.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item label="审批级别" name="approvalLevel">
              <Select allowClear placeholder="选择审批级别">
                {Object.values(APPROVAL_LEVELS).map((a) => (
                  <Select.Option key={a.value} value={a.value}>
                    {a.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Space style={{ marginTop: 8 }}>
          <Button type="primary" htmlType="submit">
            保存
          </Button>
          <Button onClick={() => onCancel?.()}>取消</Button>
        </Space>
      </Form>
    </Card>
  );
};

export default ContractEditor;

