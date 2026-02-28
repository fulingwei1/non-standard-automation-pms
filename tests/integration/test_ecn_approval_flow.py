# -*- coding: utf-8 -*-
"""
ECN审批流程集成测试

测试范围：
1. ECN提交到统一审批流程
2. ECN审批操作（通过/驳回/撤回）
3. 状态同步
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ecn import (
    Ecn,
    EcnEvaluation,
    EcnApprovalMatrix,
)
from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
from app.services.approval_engine.workflow_engine import WorkflowEngine


class TestEcnApprovalFlow:
    """ECN审批流程集成测试"""

    @pytest.fixture
    def ecn_sample(self, db_session: Session):
        """创建测试用的ECN数据"""
        # 创建ECN
        ecn = Ecn(
            ecn_no=f"ECN{datetime.now().strftime('%Y%m%d%H%M%S')}01",
            ecn_title="测试ECN-物料变更",
            ecn_type="物料变更",
            source_type="生产反馈",
            applicant_id=1,  # 假设有用户ID=1
            applicant_name="测试用户",
            project_id=1,
            status="DRAFT",
        )
        db_session.add(ecn)

        # 创建审批矩阵
        for level in [1, 2, 3]:
            matrix = EcnApprovalMatrix(
                ecn_type="物料变更",
                approval_level=level,
                approval_role=f"LEVEL{level}",
                is_active=True,
            )
            db_session.add(matrix)

        db_session.commit()

        return ecn

    def test_submit_ecn_for_approval(self, db_session: Session, ecn_sample: Ecn):
        """测试提交ECN到审批流程"""
        adapter = EcnApprovalAdapter(db_session)

        # 提交审批
        instance = adapter.submit_for_approval(
            ecn=ecn_sample,
            initiator_id=ecn_sample.applicant_id,
            title="ECN物料变更审批",
            summary="需要审批：测试ECN涉及物料变更，成本估算约1000元",
        )

        # 验证结果
        assert instance is not None
        assert instance.instance_no.startswith("AP")
        assert instance.entity_type == "ECN"
        assert instance.status in ["PENDING", "IN_PROGRESS"]

        # 验证ECN记录已更新
        ecn = db_session.query(Ecn).filter(Ecn.id == ecn_sample.id).first()
        assert ecn.approval_instance_id == instance.id
        assert ecn.approval_status == instance.status

    def test_get_ecn_approval_status(self, db_session: Session, ecn_sample: Ecn):
        """测试查询ECN审批状态"""
        adapter = EcnApprovalAdapter(db_session)

        status = adapter.get_approval_status(ecn_sample)

        # 验证基础信息
        assert status["status"] in [
            "NOT_SUBMITTED",
            "PENDING",
            "IN_PROGRESS",
            "APPROVED",
            "REJECTED",
            "CANCELLED",
            "TERMINATED",
        ]

        # 验证实例ID
        assert status["instance_id"] == ecn_sample.approval_instance_id

        # 验证状态文本
        if status["status"] == "PENDING":
            assert "未提交" in status["status_text"]
        elif status["status"] == "APPROVED":
            assert "已通过" in status["status_text"]
        elif status["status"] == "REJECTED":
            assert "已驳回" in status["status_text"]

        # 验证进度
        assert status["progress"] >= 0
        assert status["progress"] <= 100

    def test_get_ecn_approver_matrix(self, db_session: Session, ecn_sample: Ecn):
        """测试获取ECN审批人"""
        adapter = EcnApprovalAdapter(db_session)

        approvers = adapter.get_ecn_approvers(ecn_sample, level=1)
        assert isinstance(approvers, list)
        # 即使初始环境没用户，也应返回空列表或找到某些用户
        # 这里验证不报错即合格

    def test_create_ecn_approval_records(self, db_session: Session, ecn_sample: Ecn):
        """测试创建ECN审批记录"""
        adapter = EcnApprovalAdapter(db_session)

        # 先提交审批
        instance = adapter.submit_for_approval(
            ecn=ecn_sample,
            initiator_id=ecn_sample.applicant_id,
            title="ECN物料变更审批",
            summary="需要审批：测试ECN涉及物料变更",
        )

        # 创建审批记录
        approval_records = adapter.create_ecn_approval_records(
            instance=instance,
            ecn=ecn_sample,
        )

        # 验证结果
        assert len(approval_records) == 3  # 应该创建3个级别的审批记录
        for record in approval_records:
            assert record.ecn_id == ecn_sample.id
            assert record.status == "PENDING"
            assert record.approval_level in [1, 2, 3]

    def test_sync_from_approval_instance_approved(
        self, db_session: Session, ecn_sample: Ecn
    ):
        """测试审批通过后的同步"""
        adapter = EcnApprovalAdapter(db_session)

        # 模拟审批通过
        instance = adapter.submit_for_approval(
            ecn=ecn_sample,
            initiator_id=ecn_sample.applicant_id,
            title="ECN物料变更审批",
            summary="需要审批：测试ECN涉及物料变更，成本估算约1000元",
        )

        # 通过审批
        workflow_engine = WorkflowEngine(db_session)
        workflow_engine.submit_approval(
            instance=instance,
            approver_id=ecn_sample.applicant_id,
            decision="APPROVE",
            comment="同意物料变更，成本在合理范围内",
        )

        # 同步状态
        adapter.sync_from_approval_instance(instance, ecn_sample)

        # 验证ECN状态已更新
        assert ecn_sample.status == "APPROVED"
        assert ecn_sample.approval_result == "APPROVED"

    def test_sync_from_approval_instance_rejected(
        self, db_session: Session, ecn_sample: Ecn
    ):
        """测试审批驳回后的同步"""
        adapter = EcnApprovalAdapter(db_session)

        instance = adapter.submit_for_approval(
            ecn=ecn_sample,
            initiator_id=ecn_sample.applicant_id,
            title="ECN物料变更审批",
            summary="需要审批：测试ECN涉及物料变更，成本估算约1000元",
        )

        # 驳回审批
        workflow_engine = WorkflowEngine(db_session)
        workflow_engine.submit_approval(
            instance=instance,
            approver_id=ecn_sample.applicant_id,
            decision="REJECT",
            comment="成本过高，超出预算，建议重新评估",
        )

        # 同步状态
        adapter.sync_from_approval_instance(instance, ecn_sample)

        # 验证ECN状态已更新
        assert ecn_sample.status == "REJECTED"
        assert ecn_sample.approval_result == "REJECTED"

    def test_ecn_with_evaluation(self, db_session: Session):
        """测试带评估的ECN审批"""
        # 创建带评估的ECN
        ecn = Ecn(
            ecn_no=f"ECN{datetime.now().strftime('%Y%m%d%H%M%S')}02",
            ecn_title="测试ECN工艺变更",
            ecn_type="工艺变更",
            source_type="生产反馈",
            applicant_id=1,
            applicant_name="测试用户",
            project_id=1,
            status="DRAFT",
        )
        db_session.add(ecn)
        db_session.flush()  # 获得ID

        # 添加评估
        evaluation = EcnEvaluation(
            ecn_id=ecn.id,
            eval_dept="技术部",
            evaluator_id=1,
            evaluator_name="技术部主管",
            impact_analysis="需要修改工艺文件，影响评估：轻微",
            cost_estimate=5000,
            schedule_estimate=5,
            resource_requirent="无需额外资源",
            risk_assessment="低风险",
            eval_result="PASSED",
            status="COMPLETED",
            conditions="需在周五前完成修改",
        )
        db_session.add(evaluation)

        # 提交审批
        adapter = EcnApprovalAdapter(db_session)
        instance = adapter.submit_for_approval(
            ecn=ecn,
            initiator_id=ecn.applicant_id,
            title="ECN工艺变更审批（带评估）",
            summary="需要审批：技术部已完成评估，确认可以执行",
        )

        assert instance is not None
        assert instance.status in ["PENDING", "IN_PROGRESS"]


if __name__ == "__main__":
    pytest.main([__file__])
