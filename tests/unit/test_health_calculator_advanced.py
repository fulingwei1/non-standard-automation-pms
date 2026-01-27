# -*- coding: utf-8 -*-
"""
健康度计算器高级测试

包含边缘案例、批量处理、缺失数据处理等
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.enums import AlertLevelEnum, IssueStatusEnum, ProjectHealthEnum
from app.models.alert import AlertRecord, AlertRule
from app.models.issue import Issue, IssueTypeEnum
from app.models.progress import Task
from app.models.project import Project, ProjectMilestone, ProjectStatusLog
from app.services.health_calculator import HealthCalculator


@pytest.mark.unit
@pytest.mark.integration
class TestHealthCalculatorEdgeCases:
    """健康度计算器边缘场景测试"""

    def test_missing_planned_end_date(self, db_session: Session):
        """项目缺少计划结束日期时不应出错"""
        # 创建项目（无计划结束日期）
        project = Project(
        project_code="PJ-EDGE-001",
        project_name="边缘测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        actual_start_date=date.today(),
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H1（正常）
        assert health == ProjectHealthEnum.H1.value

    def test_missing_actual_start_date(self, db_session: Session):
        """项目缺少实际开始日期"""
        # 创建项目（无实际开始日期）
        project = Project(
        project_code="PJ-EDGE-002",
        project_name="边缘测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("50.00"),
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H1（由于进度偏差检查需要实际开始日期）
        assert health == ProjectHealthEnum.H1.value

    def test_multiple_risk_factors(self, db_session: Session):
        """多个风险因素同时存在（阻塞应优先）"""
        # 创建项目
        project = Project(
        project_code="PJ-EDGE-003",
        project_name="边缘测试项目",
        stage="S6",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("30.00"),  # 进度落后
        created_by=1,
        )
        db_session.add(project)

        # 创建阻塞任务
        blocked_task = Task(
        project_id=project.id,
        task_code="TASK-001",
        title="阻塞任务",
        status="BLOCKED",
        )
        db_session.add(blocked_task)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H3（阻塞优先级高于风险）
        assert health == ProjectHealthEnum.H3.value

    def test_blocked_plus_risks(self, db_session: Session):
        """阻塞状态下的其他风险不应影响结果"""
        # 创建项目
        project = Project(
        project_code="PJ-EDGE-004",
        project_name="边缘测试项目",
        stage="S6",
        status="ST14",  # 缺料阻塞状态
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("10.00"),  # 严重进度落后
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H3（阻塞状态）
        assert health == ProjectHealthEnum.H3.value

    def test_closed_status_high_priority(self, db_session: Session):
        """已完结状态优先级最高（忽略其他风险）"""
        # 创建已完结项目
        project = Project(
        project_code="PJ-EDGE-005",
        project_name="边缘测试项目",
        stage="S9",
        status="ST30",  # 已结项
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("10.00"),  # 进度落后
        created_by=1,
        )
        db_session.add(project)

        # 创建逾期里程碑
        milestone = ProjectMilestone(
        project_id=project.id,
        milestone_name="测试里程碑",
        planned_date=date.today() - timedelta(days=1),
        status="IN_PROGRESS",
        is_key=True,
        )
        db_session.add(milestone)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H4（已完结优先）
        assert health == ProjectHealthEnum.H4.value

    def test_schedule_variance_exact_threshold(self, db_session: Session):
        """进度偏差正好等于阈值时的边界处理"""
        # 创建项目（进度正好落后阈值10%）
        project = Project(
        project_code="PJ-EDGE-006",
        project_name="边缘测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("30.00"),  # 30%完成，应达到50%（落后10%）
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 阈值是>10%，所以10%不算风险
        assert health == ProjectHealthEnum.H1.value

    def test_schedule_variance_above_threshold(self, db_session: Session):
        """进度偏差超过阈值"""
        # 创建项目（进度落后11%）
        project = Project(
        project_code="PJ-EDGE-007",
        project_name="边缘测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("29.00"),  # 29%完成，应达到50%（落后11%）
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H2（风险）
        assert health == ProjectHealthEnum.H2.value

    def test_all_risk_factors_h2(self, db_session: Session):
        """所有H2风险因素都存在"""
        # 创建项目
        project = Project(
        project_code="PJ-EDGE-008",
        project_name="边缘测试项目",
        stage="S6",
        status="ST22",  # FAT整改中（风险状态）
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=6),  # 6天后到期（临近）
        progress_pct=Decimal("25.00"),  # 进度落后
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H2（有风险）
        assert health == ProjectHealthEnum.H2.value

    def test_blocking_issue_only(self, db_session: Session):
        """只有阻塞问题（没有阻塞状态）"""
        # 创建项目
        project = Project(
        project_code="PJ-EDGE-009",
        project_name="边缘测试项目",
        stage="S6",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        # 创建阻塞问题
        blocking_issue = Issue(
        project_id=project.id,
        issue_type=IssueTypeEnum.BLOCKER,
        priority="HIGH",
        title="阻塞问题",
        description="阻塞了项目进度",
        status=IssueStatusEnum.OPEN.value,
        )
        db_session.add(blocking_issue)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H3（阻塞问题导致阻塞）
        assert health == ProjectHealthEnum.H3.value


@pytest.mark.unit
@pytest.mark.integration
class TestHealthCalculatorBatchProcessing:
    """健康度批量计算测试"""

    def test_batch_calculate_empty_project_list(self, db_session: Session):
        """批量计算空项目列表"""
        calculator = HealthCalculator(db_session)
        result = calculator.batch_calculate(project_ids=[], batch_size=100)

        # 应返回空结果
        assert result["total"] == 0
        assert result["updated"] == 0
        assert result["unchanged"] == 0
        assert len(result["details"]) == 0

    def test_batch_calculate_single_project(self, db_session: Session):
        """批量计算单个项目"""
        # 创建项目
        project = Project(
        project_code="PJ-BATCH-001",
        project_name="批量测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 批量计算
        calculator = HealthCalculator(db_session)
        result = calculator.batch_calculate(project_ids=[project.id], batch_size=100)

        # 验证结果
        assert result["total"] == 1
        # 由于健康度未变，应记为未改变
        assert result["unchanged"] == 1

    def test_batch_calculate_multiple_projects(self, db_session: Session):
        """批量计算多个项目"""
        # 创建3个项目（其中一个健康度会变化）
        projects = []
        for i in range(3):
            project = Project(
            project_code=f"PJ-BATCH-{i + 2:03d}",
            project_name=f"批量测试项目{i}",
            stage="S2" if i != 1 else "S6",
            status="ST01" if i != 1 else "ST14",  # 第2个是阻塞状态
            health="H1",
            created_by=1,
            )
            db_session.add(project)
            projects.append(project)

            db_session.commit()

            # 获取项目ID列表
            project_ids = [p.id for p in projects]

            # 批量计算
            calculator = HealthCalculator(db_session)
            result = calculator.batch_calculate(project_ids=project_ids, batch_size=100)

            # 验证结果
            assert result["total"] == 3
            # 第2个项目（阻塞状态）应更新
            assert result["updated"] == 1
            # 其他2个项目应未改变
            assert result["unchanged"] == 2
            # 验证更新的项目ID是第2个
            updated_project_id = result["details"][1]["project_id"]
            assert updated_project_id == projects[1].id
            assert result["details"][1]["new_health"] == ProjectHealthEnum.H3.value

    def test_batch_calculate_with_batch_size(self, db_session: Session):
        """测试批量大小参数"""
        # 创建10个项目
        projects = []
        for i in range(10):
            project = Project(
            project_code=f"PJ-BATCH-{i + 10:03d}",
            project_name=f"批量测试项目{i}",
            stage="S2",
            status="ST01",
            health="H1",
            created_by=1,
            )
            db_session.add(project)
            projects.append(project)

            db_session.commit()

            # 批量计算（批量大小=3）
            calculator = HealthCalculator(db_session)
            project_ids = [p.id for p in projects]
            result = calculator.batch_calculate(project_ids=project_ids, batch_size=3)

            # 验证结果
            assert result["total"] == 10

    def test_batch_calculate_auto_save_true(self, db_session: Session):
        """批量计算时自动保存到数据库"""
        # 创建项目（会从H1变为H2）
        project = Project(
        project_code="PJ-BATCH-SAVE",
        project_name="批量保存测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("25.00"),  # 进度落后，会变成H2
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 批量计算（自动保存）
        calculator = HealthCalculator(db_session)
        result = calculator.batch_calculate(project_ids=[project.id], batch_size=100)

        # 验证数据库已更新
        db_session.refresh(project)
        assert project.health == ProjectHealthEnum.H2.value

        # 验证返回结果
        assert result["updated"] == 1

    def test_batch_calculate_with_transaction_error(self, db_session: Session):
        """批量计算时的数据库错误处理"""
        # 创建项目
        project = Project(
        project_code="PJ-BATCH-ERR",
        project_name="批量错误测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # Mock一个会出错的项目（通过设置一个不存在的project_id）
        calculator = HealthCalculator(db_session)
        result = calculator.batch_calculate(project_ids=[99999], batch_size=100)

        # 应返回空结果（项目不存在）
        assert result["total"] == 0


@pytest.mark.unit
@pytest.mark.integration
class TestHealthCalculatorStatusLog:
    """健康度状态变更日志测试"""

    def test_health_change_creates_status_log(self, db_session: Session):
        """健康度变化时创建状态日志"""
        # 创建项目（会从H1变为H2）
        project = Project(
        project_code="PJ-LOG-001",
        project_name="状态日志测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("20.00"),  # 进度落后
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        old_health = project.health

        # 计算并更新（自动保存）
        calculator = HealthCalculator(db_session)
        result = calculator.calculate_and_update(project, auto_save=True)

        # 验证返回结果
        assert result["old_health"] == old_health
        assert result["new_health"] != old_health
        assert result["changed"] is True

        # 验证数据库中的状态日志
        status_logs = (
        db_session.query(ProjectStatusLog)
        .filter(
        ProjectStatusLog.project_id == project.id,
        ProjectStatusLog.change_type == "HEALTH_AUTO_CALCULATED",
        )
        .all()
        )

        assert len(status_logs) > 0
        # 验证日志内容
        log = status_logs[0]
        assert log.old_health == old_health
        assert log.new_health == result["new_health"]
        assert log.changed_by is None  # 系统自动计算
        assert "系统自动计算健康度" in log.change_note

    def test_health_no_change_no_status_log(self, db_session: Session):
        """健康度无变化时不创建状态日志"""
        # 创建项目
        project = Project(
        project_code="PJ-LOG-002",
        project_name="状态日志测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        old_health = project.health

        # 计算并更新（自动保存）
        calculator = HealthCalculator(db_session)
        result = calculator.calculate_and_update(project, auto_save=True)

        # 验证返回结果（无变化）
        assert result["old_health"] == old_health
        assert result["new_health"] == old_health
        assert result["changed"] is False

        # 验证数据库中没有新的状态日志
        status_logs = (
        db_session.query(ProjectStatusLog)
        .filter(
        ProjectStatusLog.project_id == project.id,
        ProjectStatusLog.change_type == "HEALTH_AUTO_CALCULATED",
        )
        .all()
        )

        assert len(status_logs) == 0

    def test_multiple_health_changes_multiple_logs(self, db_session: Session):
        """多次健康度变化创建多条日志"""
        # 创建项目
        project = Project(
        project_code="PJ-LOG-003",
        project_name="状态日志测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        calculator = HealthCalculator(db_session)

        # 第1次变化（H1 -> H2）
        project.progress_pct = Decimal("30.00")
        project.planned_start_date = date.today() - timedelta(days=30)
        project.planned_end_date = date.today() + timedelta(days=30)
        db_session.add(project)
        db_session.commit()

        result1 = calculator.calculate_and_update(project, auto_save=True)
        assert result1["changed"] is True

        # 第2次变化（H2 -> H3）
        project.status = "ST14"  # 设置为阻塞状态
        db_session.add(project)
        db_session.commit()

        result2 = calculator.calculate_and_update(project, auto_save=True)
        assert result2["changed"] is True

        # 验证有2条状态日志
        status_logs = (
        db_session.query(ProjectStatusLog)
        .filter(
        ProjectStatusLog.project_id == project.id,
        ProjectStatusLog.change_type == "HEALTH_AUTO_CALCULATED",
        )
        .all()
        )

        assert len(status_logs) == 2

    def test_auto_save_false_no_database_update(self, db_session: Session):
        """auto_save=False时不更新数据库"""
        # 创建项目
        project = Project(
        project_code="PJ-SAVE-001",
        project_name="保存测试项目",
        stage="S2",
        status="ST01",
        health="H1",
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        progress_pct=Decimal("20.00"),
        created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        old_health = project.health

        # 计算但不自动保存
        calculator = HealthCalculator(db_session)
        result = calculator.calculate_and_update(project, auto_save=False)

        # 验证返回结果（有变化）
        assert result["changed"] is True

        # 验证数据库中的健康度未改变
        db_session.refresh(project)
        assert project.health == old_health


@pytest.mark.unit
@pytest.mark.integration
class TestHealthCalculatorAlertIntegration:
    """健康度与预警集成测试"""

    def test_critical_shortage_alert_triggers_h3(self, db_session: Session):
        """严重缺料预警触发H3"""
        # 创建预警规则
        alert_rule = AlertRule(
        rule_code="MAT-SHORT-CRIT",
        rule_name="严重缺料预警",
        rule_type="MATERIAL_SHORTAGE",
        alert_level=AlertLevelEnum.CRITICAL.value,
        is_active=True,
        )
        db_session.add(alert_rule)
        db_session.commit()

        # 创建项目
        project = Project(
        project_code="PJ-ALERT-001",
        project_name="预警测试项目",
        stage="S3",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        # 创建严重缺料预警
        alert = AlertRecord(
        project_id=project.id,
        rule_id=alert_rule.id,
        alert_level=AlertLevelEnum.CRITICAL.value,
        status="PENDING",  # 未处理
        alert_title="严重缺料",
        alert_content="关键物料短缺",
        )
        db_session.add(alert)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H3（严重预警导致阻塞）
        assert health == ProjectHealthEnum.H3.value

    def test_warning_shortage_alert_triggers_h2(self, db_session: Session):
        """警告级缺料预警触发H2"""
        # 创建预警规则
        alert_rule = AlertRule(
        rule_code="MAT-SHORT-WARN",
        rule_name="缺料预警",
        rule_type="MATERIAL_SHORTAGE",
        alert_level=AlertLevelEnum.WARNING.value,
        is_active=True,
        )
        db_session.add(alert_rule)
        db_session.commit()

        # 创建项目
        project = Project(
        project_code="PJ-ALERT-002",
        project_name="预警测试项目",
        stage="S3",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        # 创建警告级缺料预警
        alert = AlertRecord(
        project_id=project.id,
        rule_id=alert_rule.id,
        alert_level=AlertLevelEnum.WARNING.value,
        status="PENDING",
        alert_title="缺料",
        alert_content="物料短缺",
        )
        db_session.add(alert)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H2（警告导致风险）
        assert health == ProjectHealthEnum.H2.value

    def test_resolved_alert_does_not_affect_health(self, db_session: Session):
        """已解决的预警不影响健康度"""
        # 创建预警规则
        alert_rule = AlertRule(
        rule_code="MAT-SHORT-RES",
        rule_name="缺料预警",
        rule_type="MATERIAL_SHORTAGE",
        alert_level=AlertLevelEnum.CRITICAL.value,
        is_active=True,
        )
        db_session.add(alert_rule)
        db_session.commit()

        # 创建项目
        project = Project(
        project_code="PJ-ALERT-003",
        project_name="预警测试项目",
        stage="S3",
        status="ST01",
        health="H1",
        created_by=1,
        )
        db_session.add(project)

        # 创建已解决的严重预警
        alert = AlertRecord(
        project_id=project.id,
        rule_id=alert_rule.id,
        alert_level=AlertLevelEnum.CRITICAL.value,
        status="RESOLVED",  # 已解决
        alert_title="缺料",
        alert_content="已解决",
        )
        db_session.add(alert)
        db_session.commit()

        # 计算健康度
        calculator = HealthCalculator(db_session)
        health = calculator.calculate_health(project)

        # 应返回H1（预警已解决）
        assert health == ProjectHealthEnum.H1.value
