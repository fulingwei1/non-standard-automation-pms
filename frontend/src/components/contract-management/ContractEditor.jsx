/**
 * Contract Editor Component
 * 合同编辑组件（已接入真实 API）
 */

import { useEffect, useState } from 'react';
import {
  Card,
  Form,
  Row,
  Col,
  Input,
  Select,
  InputNumber,
  Space,
  Button,
  message,
  Spin,
} from 'antd';
import {
  CONTRACT_TYPES,
  RISK_LEVELS,
} from '@/lib/constants/contractManagement';
import { contractApi, customerApi, opportunityApi } from '@/services/api';

const ContractEditor = ({ contract, onSave, onCancel }) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [opportunities, setOpportunities] = useState([]);

  useEffect(() => {
    const loadOptions = async () => {
      try {
        setLoadingOptions(true);
        const [customerRes, oppRes] = await Promise.all([
          customerApi.list({ page: 1, page_size: 1000 }),
          opportunityApi.list({ page: 1, page_size: 1000 }),
        ]);

        const customerItems =
          customerRes?.data?.items || customerRes?.data || customerRes || [];
        const oppItems = oppRes?.data?.items || oppRes?.data || oppRes || [];

        setCustomers(Array.isArray(customerItems) ? customerItems : []);
        setOpportunities(Array.isArray(oppItems) ? oppItems : []);
      } catch (_err) {
        message.warning('客户/商机选项加载失败，可手动填写后重试');
        setCustomers([]);
        setOpportunities([]);
      } finally {
        setLoadingOptions(false);
      }
    };

    loadOptions();
  }, []);

  useEffect(() => {
    if (!contract) {
      form.resetFields();
      form.setFieldsValue({
        status: 'draft',
        contract_type: 'sales',
      });
      return;
    }

    form.setFieldsValue({
      contract_code: contract.contract_code || contract.contractCode,
      customer_contract_no:
        contract.customer_contract_no || contract.customerContractNo,
      opportunity_id: contract.opportunity_id || contract.opportunityId,
      customer_id: contract.customer_id || contract.customerId,
      quote_version_id: contract.quote_version_id || contract.quote_id,
      contract_amount:
        contract.contract_amount || contract.total_amount || contract.value,
      signed_date: (contract.signed_date || contract.signing_date || '')
        ?.toString()
        ?.slice(0, 10),
      status: contract.status || 'draft',
      payment_terms_summary:
        contract.payment_terms_summary || contract.payment_terms || '',
      acceptance_summary:
        contract.acceptance_summary || contract.contract_subject || '',
      owner_id: contract.owner_id || contract.sales_owner_id,
      contract_type: contract.contract_type || 'sales',
      risk_level: contract.riskLevel || contract.risk_level,
    });
  }, [contract, form]);

  const handleFinish = async (values) => {
    if (!values.opportunity_id || !values.customer_id) {
      message.error('商机和客户为必填项');
      return;
    }

    const payload = {
      contract_code: values.contract_code || undefined,
      customer_contract_no: values.customer_contract_no || undefined,
      opportunity_id: values.opportunity_id,
      quote_version_id: values.quote_version_id || undefined,
      customer_id: values.customer_id,
      contract_amount: values.contract_amount,
      signed_date: values.signed_date || undefined,
      status: values.status || 'draft',
      payment_terms_summary: values.payment_terms_summary || undefined,
      acceptance_summary: values.acceptance_summary || undefined,
      owner_id: values.owner_id || undefined,
    };

    try {
      setSubmitting(true);
      const response = contract?.id
        ? await contractApi.update(contract.id, payload)
        : await contractApi.create(payload);

      message.success(contract ? '合同更新成功' : '合同创建成功');
      onSave?.(response?.data || response || payload);
    } catch (error) {
      const detail =
        error?.response?.data?.detail || error?.response?.data?.message || error?.message;
      message.error(`保存失败：${detail || '未知错误'}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <Spin spinning={loadingOptions}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFinish}
          initialValues={{
            status: 'draft',
            contract_type: 'sales',
          }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Form.Item label="合同编码" name="contract_code">
                <Input placeholder="为空自动生成" allowClear />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="客户合同编号" name="customer_contract_no">
                <Input placeholder="客户侧合同编号" allowClear />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="状态" name="status">
                <Select allowClear placeholder="选择状态">
                  <Select.Option value="draft">草稿</Select.Option>
                  <Select.Option value="pending_approval">待审批</Select.Option>
                  <Select.Option value="approved">已审批</Select.Option>
                  <Select.Option value="signed">已签署</Select.Option>
                  <Select.Option value="executing">执行中</Select.Option>
                  <Select.Option value="completed">已完成</Select.Option>
                  <Select.Option value="voided">已作废</Select.Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="关联商机"
                name="opportunity_id"
                rules={[{ required: true, message: '请选择商机' }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="选择商机"
                  options={(opportunities || []).map((opp) => ({
                    value: opp.id,
                    label: `${opp.opp_code || opp.id} - ${opp.opp_name || opp.name || '未命名商机'}`,
                  }))}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                label="客户"
                name="customer_id"
                rules={[{ required: true, message: '请选择客户' }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="选择客户"
                  options={(customers || []).map((customer) => ({
                    value: customer.id,
                    label:
                      customer.customer_name || customer.name || `客户#${customer.id}`,
                  }))}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="合同金额" name="contract_amount">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  step={1000}
                  placeholder="金额（元）"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="签订日期" name="signed_date">
                <Input placeholder="YYYY-MM-DD" allowClear />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="报价版本ID" name="quote_version_id">
                <InputNumber
                  style={{ width: '100%' }}
                  min={1}
                  placeholder="可选"
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="负责人ID" name="owner_id">
                <InputNumber style={{ width: '100%' }} min={1} placeholder="可选" />
              </Form.Item>
            </Col>

            <Col xs={24} md={8}>
              <Form.Item label="合同类型(展示字段)" name="contract_type">
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
              <Form.Item label="风险等级(展示字段)" name="risk_level">
                <Select allowClear placeholder="选择风险等级">
                  {Object.values(RISK_LEVELS).map((r) => (
                    <Select.Option key={r.value} value={r.value}>
                      <span style={{ color: r.color }}>{r.label}</span>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Form.Item label="付款条款摘要" name="payment_terms_summary">
                <Input.TextArea rows={3} placeholder="例如：30%预付款，60%发货前，10%验收后" />
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Form.Item label="验收/合同摘要" name="acceptance_summary">
                <Input.TextArea rows={3} placeholder="填写合同标的、验收关键点等" />
              </Form.Item>
            </Col>
          </Row>

          <Space style={{ marginTop: 8 }}>
            <Button type="primary" htmlType="submit" loading={submitting}>
              保存
            </Button>
            <Button onClick={() => onCancel?.()} disabled={submitting}>
              取消
            </Button>
          </Space>
        </Form>
      </Spin>
    </Card>
  );
};

export default ContractEditor;
