# -*- coding: utf-8 -*-
"""
审批发起功能单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库、适配器）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from app.services.approval_engine.engine.submit import ApprovalSubmitMixin
from app.models.approval import ApprovalInstance, ApprovalTemplate, ApprovalFlowDefinition
from app.models.user import User


class TestSubmitCore(unittest.TestCase):
    """测试核心提交方法"""

    def setUp(self):
        """每个测试前的准备"""
        # 创建提交器实例并mock数据库
        self.db_mock = MagicMock()
        self.submitter = ApprovalSubmitMixin(db=self.db_mock)
        
        # Mock核心组件
        self.submitter.router = MagicMock()
        self.submitter.executor = MagicMock()
        
        # Mock辅助方法（在父类中定义）
        self.submitter._generate_instance_no = MagicMock(return_value="QUOTE-2024-001")
        self.submitter._get_first_node = MagicMock()
        self.submitter._create_node_tasks = MagicMock()
        self.submitter._log_action = MagicMock()
        
        # 准备mock数据
        self.mock_template = ApprovalTemplate(
            id=1,
            template_code="QUOTE_APPROVAL",
            template_name="报价审批",
            is_active=True
        )
        
        self.mock_user = User(
            id=100,
            username="zhangsan",
            real_name="张三"
        )
        
        self.mock_flow = ApprovalFlowDefinition(
            id=10,
            flow_name="默认流程",
            template_id=1
        )

    # ========== submit() 主流程测试 ==========
    
    def test_submit_basic_success(self):
        """测试基本提交流程（无适配器）"""
        # 准备数据库查询结果
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,  # 第一次查询返回模板
            self.mock_user,      # 第二次查询返回用户
        ]
        
        # Mock路由器返回流程
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock get_adapter抛出异常（模拟无适配器）
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            # 执行提交
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 5000, "days": 3},
                initiator_id=100,
                title="测试报价审批",
                summary="金额5000元"
            )
        
        # 验证结果
        self.assertIsInstance(result, ApprovalInstance)
        self.assertEqual(result.instance_no, "QUOTE-2024-001")
        self.assertEqual(result.template_id, 1)
        self.assertEqual(result.flow_id, 10)
        self.assertEqual(result.entity_type, "QUOTE")
        self.assertEqual(result.entity_id, 1001)
        self.assertEqual(result.initiator_id, 100)
        self.assertEqual(result.status, "PENDING")
        self.assertEqual(result.title, "测试报价审批")
        self.assertEqual(result.summary, "金额5000元")
        
        # 验证数据库操作
        self.db_mock.add.assert_called_once()
        self.db_mock.flush.assert_called_once()
        self.db_mock.commit.assert_called_once()
        
        # 验证日志记录
        self.submitter._log_action.assert_called_once_with(
            instance_id=result.id,
            operator_id=100,
            operator_name="张三",
            action="SUBMIT",
            comment=None
        )

    def test_submit_with_adapter_validation(self):
        """测试带适配器验证的提交"""
        # 准备数据库查询结果
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        
        # Mock路由器
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock适配器
        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {"quote_no": "Q2024001", "customer": "测试客户"}
        mock_adapter.generate_title.return_value = "报价单Q2024001审批"
        mock_adapter.generate_summary.return_value = "客户：测试客户"
        
        with patch('app.services.approval_engine.engine.submit.get_adapter', return_value=mock_adapter):
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 5000},
                initiator_id=100
            )
        
        # 验证适配器调用
        mock_adapter.validate_submit.assert_called_once_with(1001)
        mock_adapter.get_entity_data.assert_called_once_with(1001)
        mock_adapter.generate_title.assert_called_once_with(1001)
        mock_adapter.generate_summary.assert_called_once_with(1001)
        mock_adapter.on_submit.assert_called_once_with(1001, result)
        
        # 验证标题和摘要使用适配器生成的
        self.assertEqual(result.title, "报价单Q2024001审批")
        self.assertEqual(result.summary, "客户：测试客户")

    def test_submit_adapter_validation_failed(self):
        """测试适配器验证失败"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        
        # Mock适配器验证失败
        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (False, "报价单状态不正确")
        
        with patch('app.services.approval_engine.engine.submit.get_adapter', return_value=mock_adapter):
            with self.assertRaisesRegex(ValueError, "报价单状态不正确"):
                self.submitter.submit(
                    template_code="QUOTE_APPROVAL",
                    entity_type="QUOTE",
                    entity_id=1001,
                    form_data={"amount": 5000},
                    initiator_id=100
                )

    def test_submit_template_not_found(self):
        """测试模板不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaisesRegex(ValueError, "审批模板不存在"):
            self.submitter.submit(
                template_code="INVALID_CODE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100
            )

    def test_submit_initiator_not_found(self):
        """测试发起人不存在"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            None,  # 用户不存在
        ]
        
        with self.assertRaisesRegex(ValueError, "发起人不存在"):
            self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=999
            )

    def test_submit_no_flow_found(self):
        """测试未找到适用流程"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        
        # Mock路由器返回None
        self.submitter.router.select_flow.return_value = None
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            with self.assertRaisesRegex(ValueError, "未找到适用的审批流程"):
                self.submitter.submit(
                    template_code="QUOTE_APPROVAL",
                    entity_type="QUOTE",
                    entity_id=1001,
                    form_data={},
                    initiator_id=100
                )

    def test_submit_with_first_node(self):
        """测试创建第一个节点任务"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock第一个节点
        mock_node = MagicMock()
        mock_node.id = 101
        self.submitter._get_first_node.return_value = mock_node
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 5000},
                initiator_id=100
            )
        
        # 验证节点任务创建
        self.assertEqual(result.current_node_id, 101)
        self.submitter._get_first_node.assert_called_once_with(10)
        self.submitter._create_node_tasks.assert_called_once()

    def test_submit_with_cc_users(self):
        """测试提交时添加抄送"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"amount": 5000},
                initiator_id=100,
                cc_user_ids=[200, 201, 202]
            )
        
        # 验证抄送记录创建
        self.submitter.executor.create_cc_records.assert_called_once_with(
            instance=result,
            node_id=None,
            cc_user_ids=[200, 201, 202],
            cc_source="INITIATOR",
            added_by=100
        )

    def test_submit_with_urgency(self):
        """测试不同紧急程度"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            # 测试紧急
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                urgency="URGENT"
            )
        
        self.assertEqual(result.urgency, "URGENT")

    def test_submit_default_title(self):
        """测试默认标题生成"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100
                # 不提供title，应生成默认标题
            )
        
        # 默认标题格式：模板名 - 发起人姓名
        self.assertEqual(result.title, "报价审批 - 张三")

    def test_submit_user_without_real_name(self):
        """测试用户无真实姓名时使用用户名"""
        # 创建无真实姓名的用户
        user_no_name = User(
            id=100,
            username="testuser",
            real_name=None
        )
        
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            user_no_name,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100
            )
        
        # 应使用用户名
        self.assertEqual(result.initiator_name, "testuser")
        self.assertEqual(result.title, "报价审批 - testuser")

    def test_submit_context_building(self):
        """测试上下文构建逻辑"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock适配器
        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {
            "quote_no": "Q2024001",
            "amount": 5000
        }
        
        with patch('app.services.approval_engine.engine.submit.get_adapter', return_value=mock_adapter):
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={"days": 3, "reason": "测试"},
                initiator_id=100
            )
        
        # 验证路由器接收到正确的上下文
        call_args = self.submitter.router.select_flow.call_args
        self.assertEqual(call_args[0][0], 1)  # template_id
        
        context = call_args[0][1]
        # 验证上下文结构
        self.assertIn("form_data", context)
        self.assertIn("initiator", context)
        self.assertIn("entity", context)
        self.assertIn("entity_data", context)
        
        # 验证form_data合并了entity数据
        self.assertEqual(context["form_data"]["days"], 3)
        self.assertEqual(context["form_data"]["entity"]["quote_no"], "Q2024001")

    # ========== save_draft() 测试 ==========
    
    def test_save_draft_success(self):
        """测试保存草稿成功"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        
        result = self.submitter.save_draft(
            template_code="QUOTE_APPROVAL",
            entity_type="QUOTE",
            entity_id=1001,
            form_data={"amount": 5000, "days": 3},
            initiator_id=100,
            title="草稿标题"
        )
        
        # 验证结果
        self.assertIsInstance(result, ApprovalInstance)
        self.assertEqual(result.status, "DRAFT")
        self.assertEqual(result.title, "草稿标题")
        self.assertIsNone(result.flow_id)  # 草稿没有流程
        
        # 验证数据库操作
        self.db_mock.add.assert_called_once()
        self.db_mock.commit.assert_called_once()

    def test_save_draft_template_not_found(self):
        """测试草稿模板不存在"""
        self.db_mock.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaisesRegex(ValueError, "审批模板不存在"):
            self.submitter.save_draft(
                template_code="INVALID_CODE",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100
            )

    def test_save_draft_without_title(self):
        """测试保存草稿无标题"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        
        result = self.submitter.save_draft(
            template_code="QUOTE_APPROVAL",
            entity_type="QUOTE",
            entity_id=1001,
            form_data={},
            initiator_id=100
            # 不提供title
        )
        
        self.assertIsNone(result.title)

    def test_save_draft_user_not_found(self):
        """测试草稿发起人不存在"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            None,  # 用户不存在
        ]
        
        result = self.submitter.save_draft(
            template_code="QUOTE_APPROVAL",
            entity_type="QUOTE",
            entity_id=1001,
            form_data={},
            initiator_id=999
        )
        
        # 用户不存在时，initiator_name应为None
        self.assertIsNone(result.initiator_name)

    # ========== 边界情况测试 ==========
    
    def test_submit_empty_form_data(self):
        """测试空表单数据"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},  # 空表单
                initiator_id=100
            )
        
        self.assertEqual(result.form_data, {})

    def test_submit_no_first_node(self):
        """测试流程无第一个节点"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock没有第一个节点
        self.submitter._get_first_node.return_value = None
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100
            )
        
        # 应该成功创建，但不创建任务
        self.assertIsNone(result.current_node_id)
        self.submitter._create_node_tasks.assert_not_called()

    def test_submit_adapter_no_title_method(self):
        """测试适配器无generate_title方法"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        # Mock适配器没有generate_title方法
        mock_adapter = MagicMock()
        mock_adapter.validate_submit.return_value = (True, None)
        mock_adapter.get_entity_data.return_value = {}
        del mock_adapter.generate_title
        del mock_adapter.generate_summary
        
        with patch('app.services.approval_engine.engine.submit.get_adapter', return_value=mock_adapter):
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                title="手动标题"
            )
        
        # 应使用手动提供的标题
        self.assertEqual(result.title, "手动标题")

    def test_submit_no_cc_users(self):
        """测试不添加抄送"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                cc_user_ids=None  # 不添加抄送
            )
        
        # 不应调用create_cc_records
        self.submitter.executor.create_cc_records.assert_not_called()

    def test_submit_empty_cc_list(self):
        """测试空抄送列表"""
        self.db_mock.query.return_value.filter.return_value.first.side_effect = [
            self.mock_template,
            self.mock_user,
        ]
        self.submitter.router.select_flow.return_value = self.mock_flow
        
        with patch('app.services.approval_engine.engine.submit.get_adapter') as mock_get_adapter:
            mock_get_adapter.side_effect = ValueError("不支持的业务类型")
            
            result = self.submitter.submit(
                template_code="QUOTE_APPROVAL",
                entity_type="QUOTE",
                entity_id=1001,
                form_data={},
                initiator_id=100,
                cc_user_ids=[]  # 空列表
            )
        
        # 空列表被视为falsy，不应调用
        self.submitter.executor.create_cc_records.assert_not_called()


class TestSubmitMixinInit(unittest.TestCase):
    """测试初始化"""
    
    def test_init_with_db(self):
        """测试带数据库初始化"""
        mock_db = MagicMock()
        submitter = ApprovalSubmitMixin(db=mock_db)
        self.assertEqual(submitter.db, mock_db)
    
    def test_init_without_db(self):
        """测试不带数据库初始化"""
        submitter = ApprovalSubmitMixin()
        # 应该不报错，但db未设置


if __name__ == "__main__":
    unittest.main()
