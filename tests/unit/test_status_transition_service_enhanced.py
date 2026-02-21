# -*- coding: utf-8 -*-
"""
状态联动服务增强单元测试

测试覆盖：
- 服务初始化和处理器注入
- 合同签订事件处理（多场景）
- BOM发布事件处理（多场景）
- 物料缺货/齐套事件处理（多场景）
- FAT/SAT验收事件处理（通过/失败）
- ECN影响交期事件处理
- 阶段自动流转检查（S3→S4, S4→S5, S5→S6, S7→S8, S8→S9）
- 状态变更日志记录
- 边界条件和异常处理
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call

from app.services.status_transition_service import StatusTransitionService


class TestStatusTransitionService(unittest.TestCase):
    """状态联动服务测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        
        # Mock所有处理器类，使用正确的导入路径
        self.patcher_contract = patch('app.services.status_handlers.contract_handler.ContractStatusHandler')
        self.patcher_material = patch('app.services.status_handlers.material_handler.MaterialStatusHandler')
        self.patcher_acceptance = patch('app.services.status_handlers.acceptance_handler.AcceptanceStatusHandler')
        self.patcher_ecn = patch('app.services.status_handlers.ecn_handler.ECNStatusHandler')
        
        self.mock_contract_handler_class = self.patcher_contract.start()
        self.mock_material_handler_class = self.patcher_material.start()
        self.mock_acceptance_handler_class = self.patcher_acceptance.start()
        self.mock_ecn_handler_class = self.patcher_ecn.start()
        
        # Mock处理器实例
        self.mock_contract_handler = MagicMock()
        self.mock_material_handler = MagicMock()
        self.mock_acceptance_handler = MagicMock()
        self.mock_ecn_handler = MagicMock()
        
        self.mock_contract_handler_class.return_value = self.mock_contract_handler
        self.mock_material_handler_class.return_value = self.mock_material_handler
        self.mock_acceptance_handler_class.return_value = self.mock_acceptance_handler
        self.mock_ecn_handler_class.return_value = self.mock_ecn_handler
        
        # 创建服务实例
        self.service = StatusTransitionService(self.db)
    
    def tearDown(self):
        """测试后置清理"""
        self.patcher_contract.stop()
        self.patcher_material.stop()
        self.patcher_acceptance.stop()
        self.patcher_ecn.stop()
        self.db.reset_mock()


class TestInitialization(TestStatusTransitionService):
    """测试初始化"""
    
    def test_init_creates_all_handlers(self):
        """测试初始化时创建所有处理器"""
        # 验证所有处理器都被创建
        self.mock_contract_handler_class.assert_called_once_with(self.db, self.service)
        self.mock_material_handler_class.assert_called_once_with(self.db, self.service)
        self.mock_acceptance_handler_class.assert_called_once_with(self.db, self.service)
        self.mock_ecn_handler_class.assert_called_once_with(self.db, self.service)
    
    def test_init_stores_db_session(self):
        """测试初始化时存储数据库会话"""
        self.assertIs(self.service.db, self.db)
    
    def test_init_assigns_handler_instances(self):
        """测试初始化时分配处理器实例"""
        self.assertIs(self.service.contract_handler, self.mock_contract_handler)
        self.assertIs(self.service.material_handler, self.mock_material_handler)
        self.assertIs(self.service.acceptance_handler, self.mock_acceptance_handler)
        self.assertIs(self.service.ecn_handler, self.mock_ecn_handler)


class TestContractSignedHandler(TestStatusTransitionService):
    """测试合同签订处理"""
    
    def test_handle_contract_signed_success(self):
        """测试成功处理合同签订"""
        mock_project = MagicMock()
        mock_project.id = 1
        self.mock_contract_handler.handle_contract_signed.return_value = mock_project
        
        result = self.service.handle_contract_signed(contract_id=100, auto_create_project=True)
        
        self.assertEqual(result, mock_project)
        self.mock_contract_handler.handle_contract_signed.assert_called_once_with(
            contract_id=100,
            auto_create_project=True,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_contract_signed_no_auto_create(self):
        """测试不自动创建项目"""
        self.mock_contract_handler.handle_contract_signed.return_value = None
        
        result = self.service.handle_contract_signed(contract_id=100, auto_create_project=False)
        
        self.assertIsNone(result)
        self.mock_contract_handler.handle_contract_signed.assert_called_once_with(
            contract_id=100,
            auto_create_project=False,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_contract_signed_returns_existing_project(self):
        """测试返回已存在的项目"""
        mock_existing_project = MagicMock()
        mock_existing_project.id = 999
        self.mock_contract_handler.handle_contract_signed.return_value = mock_existing_project
        
        result = self.service.handle_contract_signed(contract_id=100)
        
        self.assertEqual(result.id, 999)


class TestBOMPublishedHandler(TestStatusTransitionService):
    """测试BOM发布处理"""
    
    def test_handle_bom_published_success(self):
        """测试成功处理BOM发布"""
        self.mock_material_handler.handle_bom_published.return_value = True
        
        result = self.service.handle_bom_published(project_id=1, machine_id=10)
        
        self.assertTrue(result)
        self.mock_material_handler.handle_bom_published.assert_called_once_with(
            project_id=1,
            machine_id=10,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_bom_published_without_machine(self):
        """测试无设备ID的BOM发布"""
        self.mock_material_handler.handle_bom_published.return_value = True
        
        result = self.service.handle_bom_published(project_id=1, machine_id=None)
        
        self.assertTrue(result)
        self.mock_material_handler.handle_bom_published.assert_called_once_with(
            project_id=1,
            machine_id=None,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_bom_published_failure(self):
        """测试BOM发布失败"""
        self.mock_material_handler.handle_bom_published.return_value = False
        
        result = self.service.handle_bom_published(project_id=999)
        
        self.assertFalse(result)


class TestMaterialShortageHandler(TestStatusTransitionService):
    """测试物料缺货处理"""
    
    def test_handle_material_shortage_critical(self):
        """测试关键物料缺货"""
        self.mock_material_handler.handle_material_shortage.return_value = True
        
        result = self.service.handle_material_shortage(project_id=1, is_critical=True)
        
        self.assertTrue(result)
        self.mock_material_handler.handle_material_shortage.assert_called_once_with(
            project_id=1,
            is_critical=True,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_material_shortage_non_critical(self):
        """测试非关键物料缺货"""
        self.mock_material_handler.handle_material_shortage.return_value = True
        
        result = self.service.handle_material_shortage(project_id=1, is_critical=False)
        
        self.assertTrue(result)
        self.mock_material_handler.handle_material_shortage.assert_called_once_with(
            project_id=1,
            is_critical=False,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_material_shortage_default_critical(self):
        """测试默认为关键物料"""
        self.mock_material_handler.handle_material_shortage.return_value = True
        
        result = self.service.handle_material_shortage(project_id=1)
        
        self.assertTrue(result)
        # 验证默认is_critical=True
        call_args = self.mock_material_handler.handle_material_shortage.call_args
        self.assertEqual(call_args[1]['is_critical'], True)


class TestMaterialReadyHandler(TestStatusTransitionService):
    """测试物料齐套处理"""
    
    def test_handle_material_ready_success(self):
        """测试成功处理物料齐套"""
        self.mock_material_handler.handle_material_ready.return_value = True
        
        result = self.service.handle_material_ready(project_id=1)
        
        self.assertTrue(result)
        self.mock_material_handler.handle_material_ready.assert_called_once_with(
            project_id=1,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_material_ready_failure(self):
        """测试物料齐套处理失败"""
        self.mock_material_handler.handle_material_ready.return_value = False
        
        result = self.service.handle_material_ready(project_id=999)
        
        self.assertFalse(result)


class TestFATHandler(TestStatusTransitionService):
    """测试FAT验收处理"""
    
    def test_handle_fat_passed_with_machine(self):
        """测试FAT验收通过（带设备ID）"""
        self.mock_acceptance_handler.handle_fat_passed.return_value = True
        
        result = self.service.handle_fat_passed(project_id=1, machine_id=10)
        
        self.assertTrue(result)
        self.mock_acceptance_handler.handle_fat_passed.assert_called_once_with(
            project_id=1,
            machine_id=10,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_fat_passed_without_machine(self):
        """测试FAT验收通过（无设备ID）"""
        self.mock_acceptance_handler.handle_fat_passed.return_value = True
        
        result = self.service.handle_fat_passed(project_id=1, machine_id=None)
        
        self.assertTrue(result)
    
    def test_handle_fat_failed_with_issues(self):
        """测试FAT验收失败（带问题列表）"""
        issues = ["电气问题", "机械故障"]
        self.mock_acceptance_handler.handle_fat_failed.return_value = True
        
        result = self.service.handle_fat_failed(project_id=1, machine_id=10, issues=issues)
        
        self.assertTrue(result)
        self.mock_acceptance_handler.handle_fat_failed.assert_called_once_with(
            project_id=1,
            machine_id=10,
            issues=issues,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_fat_failed_without_issues(self):
        """测试FAT验收失败（无问题列表）"""
        self.mock_acceptance_handler.handle_fat_failed.return_value = True
        
        result = self.service.handle_fat_failed(project_id=1, machine_id=None, issues=None)
        
        self.assertTrue(result)


class TestSATHandler(TestStatusTransitionService):
    """测试SAT验收处理"""
    
    def test_handle_sat_passed_with_machine(self):
        """测试SAT验收通过（带设备ID）"""
        self.mock_acceptance_handler.handle_sat_passed.return_value = True
        
        result = self.service.handle_sat_passed(project_id=1, machine_id=10)
        
        self.assertTrue(result)
        self.mock_acceptance_handler.handle_sat_passed.assert_called_once_with(
            project_id=1,
            machine_id=10,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_sat_passed_without_machine(self):
        """测试SAT验收通过（无设备ID）"""
        self.mock_acceptance_handler.handle_sat_passed.return_value = True
        
        result = self.service.handle_sat_passed(project_id=1, machine_id=None)
        
        self.assertTrue(result)
    
    def test_handle_sat_failed_with_issues(self):
        """测试SAT验收失败（带问题列表）"""
        issues = ["客户环境问题", "性能不达标"]
        self.mock_acceptance_handler.handle_sat_failed.return_value = True
        
        result = self.service.handle_sat_failed(project_id=1, machine_id=10, issues=issues)
        
        self.assertTrue(result)
        self.mock_acceptance_handler.handle_sat_failed.assert_called_once_with(
            project_id=1,
            machine_id=10,
            issues=issues,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_sat_failed_without_issues(self):
        """测试SAT验收失败（无问题列表）"""
        self.mock_acceptance_handler.handle_sat_failed.return_value = True
        
        result = self.service.handle_sat_failed(project_id=1, machine_id=None, issues=None)
        
        self.assertTrue(result)


class TestFinalAcceptanceHandler(TestStatusTransitionService):
    """测试终验收处理"""
    
    def test_handle_final_acceptance_passed_success(self):
        """测试终验收通过成功"""
        self.mock_acceptance_handler.handle_final_acceptance_passed.return_value = True
        
        result = self.service.handle_final_acceptance_passed(project_id=1)
        
        self.assertTrue(result)
        self.mock_acceptance_handler.handle_final_acceptance_passed.assert_called_once_with(
            project_id=1,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_final_acceptance_passed_failure(self):
        """测试终验收处理失败"""
        self.mock_acceptance_handler.handle_final_acceptance_passed.return_value = False
        
        result = self.service.handle_final_acceptance_passed(project_id=999)
        
        self.assertFalse(result)


class TestECNHandler(TestStatusTransitionService):
    """测试ECN影响处理"""
    
    def test_handle_ecn_schedule_impact_positive_days(self):
        """测试ECN延期影响（正数天数）"""
        self.mock_ecn_handler.handle_ecn_schedule_impact.return_value = True
        
        result = self.service.handle_ecn_schedule_impact(
            project_id=1,
            ecn_id=100,
            impact_days=10
        )
        
        self.assertTrue(result)
        self.mock_ecn_handler.handle_ecn_schedule_impact.assert_called_once_with(
            project_id=1,
            ecn_id=100,
            impact_days=10,
            log_status_change=self.service._log_status_change
        )
    
    def test_handle_ecn_schedule_impact_negative_days(self):
        """测试ECN提前影响（负数天数）"""
        self.mock_ecn_handler.handle_ecn_schedule_impact.return_value = True
        
        result = self.service.handle_ecn_schedule_impact(
            project_id=1,
            ecn_id=100,
            impact_days=-5
        )
        
        self.assertTrue(result)
    
    def test_handle_ecn_schedule_impact_zero_days(self):
        """测试ECN无影响（零天数）"""
        self.mock_ecn_handler.handle_ecn_schedule_impact.return_value = True
        
        result = self.service.handle_ecn_schedule_impact(
            project_id=1,
            ecn_id=100,
            impact_days=0
        )
        
        self.assertTrue(result)


class TestAutoStageTransition(TestStatusTransitionService):
    """测试阶段自动流转"""
    
    @patch('app.services.stage_transition_checks.check_s3_to_s4_transition')
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_s3_to_s4_can_advance(self, mock_project_model, mock_check):
        """测试S3→S4阶段流转（可推进）"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S3'
        mock_project.status = 'ST08'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        # Mock检查函数返回值
        mock_check.return_value = (True, 'S4', [])
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=False)
        
        self.assertTrue(result['can_advance'])
        self.assertEqual(result['current_stage'], 'S3')
        self.assertEqual(result['target_stage'], 'S4')
        self.assertEqual(result['missing_items'], [])
        self.assertFalse(result['auto_advanced'])
    
    @patch('app.services.stage_transition_checks.check_s4_to_s5_transition')
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_s4_to_s5_with_missing(self, mock_project_model, mock_check):
        """测试S4→S5阶段流转（有缺失项）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S4'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        mock_check.return_value = (False, None, ['BOM未发布'])
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=False)
        
        self.assertFalse(result['can_advance'])
        self.assertIsNone(result['target_stage'])
        self.assertEqual(result['missing_items'], ['BOM未发布'])
    
    @patch('app.services.stage_transition_checks.execute_stage_transition')
    @patch('app.services.stage_transition_checks.check_s5_to_s6_transition')
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_s5_to_s6_auto_advance(self, mock_project_model, mock_check, mock_execute):
        """测试S5→S6阶段流转（自动推进）"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S5'
        mock_project.status = 'ST16'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        mock_check.return_value = (True, 'S6', [])
        mock_execute.return_value = (True, {
            'success': True,
            'current_stage': 'S5',
            'new_stage': 'S6'
        })
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=True)
        
        self.assertTrue(result['success'])
        mock_execute.assert_called_once()
        self.db.commit.assert_called_once()
    
    @patch('app.services.stage_transition_checks.check_s7_to_s8_transition')
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_s7_to_s8(self, mock_project_model, mock_check):
        """测试S7→S8阶段流转"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S7'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        mock_check.return_value = (True, 'S8', [])
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=False)
        
        self.assertTrue(result['can_advance'])
        self.assertEqual(result['target_stage'], 'S8')
    
    @patch('app.services.stage_transition_checks.check_s8_to_s9_transition')
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_s8_to_s9(self, mock_project_model, mock_check):
        """测试S8→S9阶段流转"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S8'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        mock_check.return_value = (True, 'S9', [])
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=False)
        
        self.assertTrue(result['can_advance'])
        self.assertEqual(result['target_stage'], 'S9')
    
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_project_not_found(self, mock_project_model):
        """测试项目不存在时的处理"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        result = self.service.check_auto_stage_transition(project_id=999, auto_advance=False)
        
        self.assertFalse(result['can_advance'])
        self.assertEqual(result['message'], '项目不存在')
        self.assertIsNone(result['current_stage'])
        self.assertIsNone(result['target_stage'])
    
    @patch('app.services.status_transition_service.Project')
    def test_check_auto_stage_transition_unsupported_stage(self, mock_project_model):
        """测试不支持的阶段"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.stage = 'S10'  # 不支持的阶段
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_project
        self.db.query.return_value = mock_query
        
        result = self.service.check_auto_stage_transition(project_id=1, auto_advance=False)
        
        self.assertFalse(result['can_advance'])


class TestLogStatusChange(TestStatusTransitionService):
    """测试状态变更日志"""
    
    @patch('app.services.status_transition_service.ProjectStatusLog')
    @patch('app.services.status_transition_service.datetime')
    def test_log_status_change_full_params(self, mock_datetime, mock_log_class):
        """测试完整参数的状态变更日志"""
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_log = MagicMock()
        mock_log_class.return_value = mock_log
        
        self.service._log_status_change(
            project_id=1,
            old_stage='S3',
            new_stage='S4',
            old_status='ST08',
            new_status='ST09',
            old_health='H1',
            new_health='H2',
            change_type='MANUAL_TRANSITION',
            change_reason='管理员手动推进',
            changed_by=100
        )
        
        # 验证创建了日志对象
        mock_log_class.assert_called_once_with(
            project_id=1,
            old_stage='S3',
            new_stage='S4',
            old_status='ST08',
            new_status='ST09',
            old_health='H1',
            new_health='H2',
            change_type='MANUAL_TRANSITION',
            change_reason='管理员手动推进',
            changed_by=100,
            changed_at=mock_now
        )
        
        # 验证添加到数据库
        self.db.add.assert_called_once_with(mock_log)
    
    @patch('app.services.status_transition_service.ProjectStatusLog')
    @patch('app.services.status_transition_service.datetime')
    def test_log_status_change_minimal_params(self, mock_datetime, mock_log_class):
        """测试最少参数的状态变更日志"""
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_log = MagicMock()
        mock_log_class.return_value = mock_log
        
        self.service._log_status_change(
            project_id=1,
            change_type='AUTO_TRANSITION'
        )
        
        # 验证使用了默认值
        call_kwargs = mock_log_class.call_args[1]
        self.assertEqual(call_kwargs['project_id'], 1)
        self.assertEqual(call_kwargs['change_type'], 'AUTO_TRANSITION')
        self.assertIsNone(call_kwargs['old_stage'])
        self.assertIsNone(call_kwargs['new_stage'])
        self.assertIsNone(call_kwargs['change_reason'])
        self.assertIsNone(call_kwargs['changed_by'])
    
    @patch('app.services.status_transition_service.ProjectStatusLog')
    @patch('app.services.status_transition_service.datetime')
    def test_log_status_change_stage_only(self, mock_datetime, mock_log_class):
        """测试仅阶段变更的日志"""
        mock_now = datetime(2024, 1, 15, 10, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_log = MagicMock()
        mock_log_class.return_value = mock_log
        
        self.service._log_status_change(
            project_id=1,
            old_stage='S4',
            new_stage='S5',
            change_type='AUTO_STAGE_TRANSITION',
            change_reason='BOM已发布，自动推进至采购制造阶段'
        )
        
        call_kwargs = mock_log_class.call_args[1]
        self.assertEqual(call_kwargs['old_stage'], 'S4')
        self.assertEqual(call_kwargs['new_stage'], 'S5')
        self.assertIsNone(call_kwargs['old_status'])
        self.assertIsNone(call_kwargs['new_status'])


class TestEdgeCases(TestStatusTransitionService):
    """测试边界情况"""
    
    def test_handle_bom_published_with_zero_project_id(self):
        """测试项目ID为0的情况"""
        self.mock_material_handler.handle_bom_published.return_value = False
        
        result = self.service.handle_bom_published(project_id=0)
        
        self.assertFalse(result)
    
    def test_handle_material_shortage_multiple_calls(self):
        """测试多次调用物料缺货"""
        self.mock_material_handler.handle_material_shortage.return_value = True
        
        # 第一次调用
        result1 = self.service.handle_material_shortage(project_id=1, is_critical=True)
        # 第二次调用
        result2 = self.service.handle_material_shortage(project_id=1, is_critical=False)
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        # 验证被调用了两次
        self.assertEqual(self.mock_material_handler.handle_material_shortage.call_count, 2)
    
    def test_handle_fat_failed_with_empty_issues_list(self):
        """测试空问题列表的FAT失败"""
        self.mock_acceptance_handler.handle_fat_failed.return_value = True
        
        result = self.service.handle_fat_failed(project_id=1, machine_id=10, issues=[])
        
        self.assertTrue(result)
        call_args = self.mock_acceptance_handler.handle_fat_failed.call_args
        self.assertEqual(call_args[1]['issues'], [])
    
    def test_handle_ecn_schedule_impact_large_impact(self):
        """测试ECN大延期影响"""
        self.mock_ecn_handler.handle_ecn_schedule_impact.return_value = True
        
        result = self.service.handle_ecn_schedule_impact(
            project_id=1,
            ecn_id=100,
            impact_days=365  # 延期一年
        )
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
