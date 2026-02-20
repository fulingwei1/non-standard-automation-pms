# -*- coding: utf-8 -*-
"""
ECN审批适配器增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter


@pytest.fixture
def db_mock():
    """数据库mock"""
    return MagicMock()


@pytest.fixture
def ecn_adapter(db_mock):
    """ECN适配器实例"""
    return EcnApprovalAdapter(db_mock)


@pytest.fixture
def sample_ecn():
    """示例ECN对象"""
    ecn = MagicMock()
    ecn.id = 1
    ecn.ecn_no = "ECN-2024-001"
    ecn.ecn_title = "设计变更-电机调整"
    ecn.ecn_type = "DESIGN"
    ecn.status = "DRAFT"
    ecn.project_id = 10
    ecn.applicant_id = 100
    ecn.applicant_name = "张三"
    ecn.applicant_dept = "工程部"
    ecn.priority = "HIGH"
    ecn.urgency = "URGENT"
    ecn.cost_impact = 15000.50
    ecn.schedule_impact_days = 5
    ecn.quality_impact = "中"
    ecn.source_type = "DESIGN_CHANGE"
    ecn.source_no = "DC-001"
    ecn.machine_id = 20
    ecn.root_cause = "设计优化"
    ecn.root_cause_category = "DESIGN"
    ecn.current_step = None
    ecn.approval_result = None
    ecn.approval_instance_id = None
    ecn.approval_status = None
    ecn.approval_date = None
    ecn.approval_note = None
    ecn.final_approver_id = None
    ecn.impact_analysis = "需要调整电机参数"
    
    # Mock关联对象
    ecn.project = MagicMock()
    ecn.project.project_code = "PRJ-001"
    ecn.project.project_name = "测试项目"
    
    ecn.applicant = MagicMock()
    ecn.applicant.name = "张三"
    
    return ecn


@pytest.fixture
def sample_instance():
    """示例审批实例"""
    instance = MagicMock()
    instance.id = 50
    instance.status = "APPROVED"
    instance.completed_at = datetime.now()
    instance.final_approver_id = 200
    instance.final_comment = "同意变更"
    return instance


class TestGetEntityData:
    """测试get_entity_data方法 - 覆盖数据获取逻辑"""
    
    def test_get_entity_data_with_evaluations(self, ecn_adapter, db_mock, sample_ecn):
        """测试包含评估数据的实体数据获取"""
        # 准备评估数据
        eval1 = MagicMock()
        eval1.status = "COMPLETED"
        eval1.eval_dept = "工程部"
        eval1.cost_estimate = 5000.0
        eval1.schedule_estimate = 2
        
        eval2 = MagicMock()
        eval2.status = "PENDING"
        eval2.eval_dept = "采购部"
        eval2.cost_estimate = 3000.0
        eval2.schedule_estimate = 1
        
        # Mock查询链
        query_mock = MagicMock()
        filter_mock = MagicMock()
        
        # 第一次query返回ECN
        first_call = MagicMock()
        first_call.filter.return_value.first.return_value = sample_ecn
        
        # 第二次query返回评估列表
        second_call = MagicMock()
        second_call.filter.return_value.all.return_value = [eval1, eval2]
        
        db_mock.query.side_effect = [first_call, second_call]
        
        result = ecn_adapter.get_entity_data(1)
        
        # 验证基本字段
        assert result["ecn_no"] == "ECN-2024-001"
        assert result["ecn_type"] == "DESIGN"
        assert result["cost_impact"] == 15000.50
        assert result["schedule_impact_days"] == 5
        assert result["priority"] == "HIGH"
        
        # 验证评估汇总
        eval_summary = result["evaluation_summary"]
        assert eval_summary["total_evaluations"] == 2
        assert eval_summary["completed_evaluations"] == 1
        assert eval_summary["pending_evaluations"] == 1
        assert eval_summary["total_cost_estimate"] == 8000.0
        assert eval_summary["total_schedule_estimate"] == 3
        assert "工程部" in eval_summary["departments"]
        assert "采购部" in eval_summary["departments"]
    
    def test_get_entity_data_without_project(self, ecn_adapter, db_mock, sample_ecn):
        """测试无关联项目的情况"""
        sample_ecn.project = None
        sample_ecn.project_id = None
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_ecn
        query_mock.filter.return_value.all.return_value = []
        db_mock.query.return_value = query_mock
        
        result = ecn_adapter.get_entity_data(1)
        
        assert result["project_code"] is None
        assert result["project_name"] is None


class TestOnCallbacks:
    """测试生命周期回调方法"""
    
    def test_on_submit_updates_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试提交时更新状态"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        ecn_adapter.on_submit(1, sample_instance)
        
        assert sample_ecn.status == "EVALUATING"
        assert sample_ecn.current_step == "EVALUATION"
        db_mock.flush.assert_called_once()
    
    def test_on_approved_updates_status_and_result(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试通过时更新状态和结果"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        ecn_adapter.on_approved(1, sample_instance)
        
        assert sample_ecn.status == "APPROVED"
        assert sample_ecn.approval_result == "APPROVED"
        assert sample_ecn.current_step == "EXECUTION"
        db_mock.flush.assert_called_once()
    
    def test_on_rejected_updates_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试驳回时更新状态"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        ecn_adapter.on_rejected(1, sample_instance)
        
        assert sample_ecn.status == "REJECTED"
        assert sample_ecn.approval_result == "REJECTED"
        db_mock.flush.assert_called_once()
    
    def test_on_withdrawn_resets_to_draft(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试撤回时重置为草稿"""
        sample_ecn.status = "PENDING_APPROVAL"
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        ecn_adapter.on_withdrawn(1, sample_instance)
        
        assert sample_ecn.status == "DRAFT"
        assert sample_ecn.current_step is None
        db_mock.flush.assert_called_once()


class TestGetTitleAndSummary:
    """测试标题和摘要生成"""
    
    def test_get_title_with_ecn(self, ecn_adapter, db_mock, sample_ecn):
        """测试生成包含ECN信息的标题"""
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        title = ecn_adapter.get_title(1)
        
        assert "ECN审批" in title
        assert "ECN-2024-001" in title
        assert "设计变更-电机调整" in title
    
    def test_get_title_without_ecn(self, ecn_adapter, db_mock):
        """测试ECN不存在时的标题"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        title = ecn_adapter.get_title(999)
        
        assert "ECN审批 - #999" == title
    
    def test_get_summary_comprehensive(self, ecn_adapter, db_mock, sample_ecn):
        """测试生成完整摘要"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_ecn
        query_mock.filter.return_value.all.return_value = []
        db_mock.query.return_value = query_mock
        
        summary = ecn_adapter.get_summary(1)
        
        assert "类型: DESIGN" in summary
        assert "项目: 测试项目" in summary
        assert "成本影响: ¥15,000.50" in summary
        assert "工期影响: 5天" in summary
        assert "优先级: HIGH" in summary
    
    def test_get_summary_empty_when_not_found(self, ecn_adapter, db_mock):
        """测试ECN不存在时返回空摘要"""
        db_mock.query.return_value.filter.return_value.first.return_value = None
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        summary = ecn_adapter.get_summary(999)
        
        assert summary == ""


class TestSubmitForApproval:
    """测试提交审批流程"""
    
    @patch('app.services.approval_engine.adapters.ecn.WorkflowEngine')
    def test_submit_for_approval_success(self, mock_workflow_engine, ecn_adapter, db_mock, sample_ecn):
        """测试成功提交审批"""
        # Mock审批实例
        instance = MagicMock()
        instance.id = 100
        instance.status = "PENDING"
        
        # Mock WorkflowEngine
        engine_instance = MagicMock()
        engine_instance.create_instance.return_value = instance
        mock_workflow_engine.return_value = engine_instance
        
        # Mock评估列表
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        result = ecn_adapter.submit_for_approval(
            ecn=sample_ecn,
            initiator_id=100,
            title="测试ECN审批",
            summary="测试摘要",
            urgency="URGENT"
        )
        
        assert result.id == 100
        assert sample_ecn.approval_instance_id == 100
        assert sample_ecn.approval_status == "PENDING"
        db_mock.add.assert_called_with(sample_ecn)
        db_mock.commit.assert_called_once()
    
    @patch('app.services.approval_engine.adapters.ecn.WorkflowEngine')
    def test_submit_for_approval_with_evaluations(self, mock_workflow_engine, ecn_adapter, db_mock, sample_ecn):
        """测试包含评估数据的提交"""
        # Mock评估数据
        eval1 = MagicMock()
        eval1.eval_dept = "工程部"
        eval1.evaluator_id = 1
        eval1.evaluator_name = "李四"
        eval1.impact_analysis = "影响分析"
        eval1.cost_estimate = 5000.0
        eval1.schedule_estimate = 2
        eval1.resource_requirement = "资源需求"
        eval1.risk_assessment = "风险评估"
        eval1.eval_result = "APPROVE"
        eval1.eval_opinion = "同意"
        eval1.status = "COMPLETED"
        
        instance = MagicMock()
        instance.id = 100
        
        engine_instance = MagicMock()
        engine_instance.create_instance.return_value = instance
        mock_workflow_engine.return_value = engine_instance
        
        db_mock.query.return_value.filter.return_value.all.return_value = [eval1]
        
        result = ecn_adapter.submit_for_approval(
            ecn=sample_ecn,
            initiator_id=100
        )
        
        # 验证create_instance被调用时包含评估数据
        call_args = engine_instance.create_instance.call_args
        config = call_args[1]['config']
        assert 'ecn' in config
        assert 'evaluations' in config['ecn']
        assert len(config['ecn']['evaluations']) == 1
    
    def test_submit_for_approval_already_submitted(self, ecn_adapter, db_mock, sample_ecn):
        """测试重复提交处理"""
        sample_ecn.approval_instance_id = 50
        existing_instance = MagicMock()
        existing_instance.id = 50
        
        db_mock.query.return_value.filter.return_value.first.return_value = existing_instance
        
        result = ecn_adapter.submit_for_approval(
            ecn=sample_ecn,
            initiator_id=100
        )
        
        assert result.id == 50  # 返回现有实例


class TestSyncFromApprovalInstance:
    """测试审批实例状态同步"""
    
    def test_sync_approved_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试同步审批通过状态"""
        sample_instance.status = "APPROVED"
        sample_instance.final_approver_id = 200
        sample_instance.completed_at = datetime(2024, 2, 20, 10, 0, 0)
        sample_instance.final_comment = "同意变更"
        
        ecn_adapter.sync_from_approval_instance(sample_instance, sample_ecn)
        
        assert sample_ecn.approval_status == "APPROVED"
        assert sample_ecn.status == "APPROVED"
        assert sample_ecn.approval_result == "APPROVED"
        assert sample_ecn.approval_date == datetime(2024, 2, 20, 10, 0, 0)
        assert sample_ecn.final_approver_id == 200
        assert sample_ecn.approval_note == "同意变更"
        db_mock.add.assert_called_with(sample_ecn)
        db_mock.commit.assert_called_once()
    
    def test_sync_rejected_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试同步驳回状态"""
        sample_instance.status = "REJECTED"
        sample_instance.completed_at = datetime.now()
        
        ecn_adapter.sync_from_approval_instance(sample_instance, sample_ecn)
        
        assert sample_ecn.status == "REJECTED"
        assert sample_ecn.approval_result == "REJECTED"
    
    def test_sync_cancelled_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试同步取消状态"""
        sample_instance.status = "CANCELLED"
        
        ecn_adapter.sync_from_approval_instance(sample_instance, sample_ecn)
        
        assert sample_ecn.status == "CANCELLED"
        assert sample_ecn.approval_result == "CANCELLED"
    
    def test_sync_terminated_status(self, ecn_adapter, db_mock, sample_ecn, sample_instance):
        """测试同步终止状态"""
        sample_instance.status = "TERMINATED"
        
        ecn_adapter.sync_from_approval_instance(sample_instance, sample_ecn)
        
        assert sample_ecn.status == "TERMINATED"
        assert sample_ecn.approval_result == "TERMINATED"


class TestGetRequiredEvaluators:
    """测试获取必需评估人"""
    
    def test_required_evaluators_for_design_ecn(self, ecn_adapter, db_mock, sample_ecn):
        """测试设计类ECN的评估部门"""
        sample_ecn.ecn_type = "DESIGN"
        sample_ecn.cost_impact = 5000.0
        
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        evaluators = ecn_adapter.get_required_evaluators(1)
        
        dept_names = [e["dept"] for e in evaluators]
        assert "工程部" in dept_names  # 基础部门
        assert "质量部" in dept_names  # DESIGN类型需要质量部
    
    def test_required_evaluators_for_material_ecn(self, ecn_adapter, db_mock, sample_ecn):
        """测试物料类ECN的评估部门"""
        sample_ecn.ecn_type = "MATERIAL"
        sample_ecn.cost_impact = 3000.0
        
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        evaluators = ecn_adapter.get_required_evaluators(1)
        
        dept_names = [e["dept"] for e in evaluators]
        assert "工程部" in dept_names
        assert "采购部" in dept_names
        assert "生产部" in dept_names
    
    def test_required_evaluators_high_cost_impact(self, ecn_adapter, db_mock, sample_ecn):
        """测试高成本影响需要财务评估"""
        sample_ecn.ecn_type = "DESIGN"
        sample_ecn.cost_impact = 15000.0  # 超过10000
        
        db_mock.query.return_value.filter.return_value.first.return_value = sample_ecn
        
        evaluators = ecn_adapter.get_required_evaluators(1)
        
        dept_names = [e["dept"] for e in evaluators]
        assert "财务部" in dept_names


class TestCreateEvaluationTasks:
    """测试创建评估任务"""
    
    def test_create_evaluation_tasks(self, ecn_adapter, db_mock, sample_instance):
        """测试创建评估任务"""
        # Mock get_required_evaluators
        with patch.object(ecn_adapter, 'get_required_evaluators') as mock_get_eval:
            mock_get_eval.return_value = [
                {"dept": "工程部", "required": True},
                {"dept": "采购部", "required": True}
            ]
            
            evaluations = ecn_adapter.create_evaluation_tasks(1, sample_instance)
            
            assert len(evaluations) == 2
            assert evaluations[0].ecn_id == 1
            assert evaluations[0].status == "PENDING"
            db_mock.flush.assert_called_once()


class TestCheckEvaluationComplete:
    """测试检查评估完成状态"""
    
    def test_check_evaluation_all_completed(self, ecn_adapter, db_mock):
        """测试所有评估已完成"""
        eval1 = MagicMock()
        eval1.status = "COMPLETED"
        eval1.eval_dept = "工程部"
        eval1.cost_estimate = 3000.0
        eval1.schedule_estimate = 2
        eval1.eval_result = "APPROVE"
        
        eval2 = MagicMock()
        eval2.status = "COMPLETED"
        eval2.eval_dept = "采购部"
        eval2.cost_estimate = 2000.0
        eval2.schedule_estimate = 1
        eval2.eval_result = "APPROVE"
        
        db_mock.query.return_value.filter.return_value.all.return_value = [eval1, eval2]
        
        is_complete, summary = ecn_adapter.check_evaluation_complete(1)
        
        assert is_complete is True
        assert summary["total"] == 2
        assert summary["pending"] == 0
        assert summary["completed"] == 2
        assert summary["total_cost"] == 5000.0
        assert summary["total_days"] == 3
        assert summary["all_approved"] is True
    
    def test_check_evaluation_has_pending(self, ecn_adapter, db_mock):
        """测试还有待评估项"""
        eval1 = MagicMock()
        eval1.status = "COMPLETED"
        eval1.eval_dept = "工程部"
        eval1.cost_estimate = 3000.0
        eval1.schedule_estimate = 2
        eval1.eval_result = "APPROVE"
        
        eval2 = MagicMock()
        eval2.status = "PENDING"
        eval2.eval_dept = "采购部"
        
        db_mock.query.return_value.filter.return_value.all.return_value = [eval1, eval2]
        
        is_complete, summary = ecn_adapter.check_evaluation_complete(1)
        
        assert is_complete is False
        assert summary["pending"] == 1
        assert "采购部" in summary["pending_depts"]
    
    def test_check_evaluation_no_evaluations(self, ecn_adapter, db_mock):
        """测试没有评估记录"""
        db_mock.query.return_value.filter.return_value.all.return_value = []
        
        is_complete, summary = ecn_adapter.check_evaluation_complete(1)
        
        assert is_complete is False
        assert summary == {}
