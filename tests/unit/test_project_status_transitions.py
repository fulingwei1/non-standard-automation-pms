# -*- coding: utf-8 -*-
"""
项目状态转换单元测试

测试内容：
- 项目状态转换
- 状态跳过验证
- 状态历史记录
"""

import pytest
from sqlalchemy.orm import Session

from app.models import Project, ProjectStatusLog
from datetime import datetime


@pytest.mark.unit
class TestProjectStatusTransitions:
    """项目状态转换测试"""

    def test_status_s1_to_s2_transition(self, db_session: Session):
        """测试阶段 S1 -> S2 转换"""
        project = Project(
            project_code="PJ250119003",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 执行阶段转换
        project.stage = "S2"
        db_session.commit()
        db_session.refresh(project)

        # 验证阶段
        assert project.stage == "S2"

        # 创建历史记录
        history = ProjectStatusLog(
            project_id=project.id,
            old_status="S1",
            new_status="S2",
            change_type="STAGE_CHANGE",
            changed_at=datetime.now(),
            change_reason="正常阶段推进",
        )
        db_session.add(history)
        db_session.commit()

        # 验证历史记录
        assert history.old_status == "S1"
        assert history.new_status == "S2"
        assert history.changed_at is not None

        # 清理
        db_session.delete(history)
        db_session.delete(project)
        db_session.commit()

    def test_invalid_status_transition(self, db_session: Session):
        """测试无效状态转换 - 验证状态可以直接设置（无业务验证）"""
        project = Project(
            project_code="PJ250119004",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 数据库层面允许直接设置状态（业务验证应在服务层）
        project.status = "ST05"
        db_session.commit()
        db_session.refresh(project)

        # 验证状态已更改
        assert project.status == "ST05"

        # 清理
        db_session.delete(project)
        db_session.commit()

    def test_health_status_assignment(self, db_session: Session):
        """测试健康度状态分配"""
        project = Project(
            project_code="PJ250119005",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # H1: 正常
        project.health = "H1"
        db_session.commit()
        assert project.health == "H1"

        # H2: 有风险
        project.health = "H2"
        db_session.commit()
        assert project.health == "H2"

        # H3: 阻塞
        project.health = "H3"
        db_session.commit()
        assert project.health == "H3"

        # H4: 已完结
        project.health = "H4"
        db_session.commit()
        assert project.health == "H4"

        # 清理
        db_session.delete(project)
        db_session.commit()

    def test_project_status_creation(self, db_session: Session):
        """测试创建项目和状态"""
        project = Project(
            project_code="PJ250119006",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 验证项目已创建
        assert project.id is not None
        assert project.stage == "S1"
        assert project.status == "ST01"

        # 清理
        db_session.delete(project)
        db_session.commit()


@pytest.mark.unit
@pytest.mark.slow
class TestProjectStatusHistory:
    """项目状态历史测试"""

    def test_status_history_creation(self, db_session: Session):
        """测试创建状态历史记录"""
        project = Project(
            project_code="PJ250119007",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 创建状态变更历史
        history = ProjectStatusLog(
            project_id=project.id,
            old_status="ST01",
            new_status="ST02",
            change_type="STATUS_CHANGE",
            changed_at=datetime.now(),
            change_reason="首次状态转换",
        )
        db_session.add(history)
        db_session.commit()

        # 验证历史记录已创建
        histories = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == project.id)
            .all()
        )

        assert len(histories) >= 1
        assert histories[0].old_status == "ST01"
        assert histories[0].new_status == "ST02"

        # 清理
        for h in histories:
            db_session.delete(h)
        db_session.delete(project)
        db_session.commit()

    def test_status_history_ordering(self, db_session: Session):
        """测试状态历史按时间排序"""
        import time

        project = Project(
            project_code="PJ250119008",
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 添加多条历史记录
        statuses = ["ST01", "ST02", "ST03", "ST04", "ST05"]
        for i in range(len(statuses) - 1):
            history = ProjectStatusLog(
                project_id=project.id,
                old_status=statuses[i],
                new_status=statuses[i + 1],
                change_type="STATUS_CHANGE",
                changed_at=datetime.now(),
                change_reason=f"状态转换 {i + 1}",
            )
            db_session.add(history)
            db_session.commit()
            time.sleep(0.01)  # 确保时间戳不同

        # 验证排序
        histories = (
            db_session.query(ProjectStatusLog)
            .filter(ProjectStatusLog.project_id == project.id)
            .order_by(ProjectStatusLog.changed_at)
            .all()
        )

        assert len(histories) == 4
        for i in range(len(histories) - 1):
            assert histories[i].changed_at <= histories[i + 1].changed_at

        # 清理
        for h in histories:
            db_session.delete(h)
        db_session.delete(project)
        db_session.commit()
