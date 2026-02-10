"""
进度聚合算法单元测试
测试核心痛点2：实时进度聚合

运行测试：
    pytest tests/unit/test_progress_aggregation.py -v
    pytest tests/unit/test_progress_aggregation.py -v -m aggregation
"""


import pytest
from sqlalchemy.orm import Session

from app.models import Project
from app.models.task_center import TaskUnified
from app.services.progress_aggregation_service import (
    _check_and_update_health,
    aggregate_task_progress,
)


@pytest.mark.unit
@pytest.mark.aggregation
class TestProgressAggregation:
    """测试进度聚合算法（痛点2核心功能）"""

    def test_simple_average_calculation(self, db_session: Session):
        """测试简单平均聚合算法"""
        # 创建项目
        project = Project(
            id=1,
            project_code="TEST-001",
            project_name="测试项目",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建3个任务
        tasks_data = [
            {"progress": 0, "status": "ACCEPTED"},      # 任务1: 0%
            {"progress": 50, "status": "IN_PROGRESS"},  # 任务2: 50%
            {"progress": 100, "status": "COMPLETED"},   # 任务3: 100%
        ]

        created_tasks = []
        for i, task_data in enumerate(tasks_data, 1):
            task = TaskUnified(
                id=i,
                task_code=f"TASK-TEST-{i:03d}",
                project_id=project.id,
                title=f"测试任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                priority="MEDIUM",
                status=task_data["status"],
                progress=task_data["progress"],
                assignee_id=1,
                created_by=1,
                estimated_hours=10.0,
                is_active=True
            )
            db_session.add(task)
            created_tasks.append(task)

        db_session.commit()

        # 执行聚合（使用最后一个任务触发）
        result = aggregate_task_progress(db=db_session, task_id=created_tasks[-1].id)

        # 验证聚合结果
        assert result['project_progress_updated'] is True

        # 预期进度 = (0 + 50 + 100) / 3 = 50.0
        assert result['new_project_progress'] == 50.0

        # 验证数据库已更新
        db_session.refresh(project)
        assert project.progress_pct == 50.0

    def test_aggregation_excludes_cancelled_tasks(self, db_session: Session):
        """测试聚合排除已取消的任务"""
        # 创建项目
        project = Project(
            id=2,
            project_code="TEST-002",
            project_name="测试项目2",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建任务
        tasks = [
            TaskUnified(
                id=11,
                task_code="TASK-ACTIVE-1",
                project_id=project.id,
                title="活跃任务1",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=60,
                assignee_id=1,
                created_by=1,
                is_active=True
            ),
            TaskUnified(
                id=12,
                task_code="TASK-CANCELLED",
                project_id=project.id,
                title="已取消任务",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="CANCELLED",  # 已取消
                progress=100,         # 即使100%也应被排除
                assignee_id=1,
                created_by=1,
                is_active=False
            ),
            TaskUnified(
                id=13,
                task_code="TASK-ACTIVE-2",
                project_id=project.id,
                title="活跃任务2",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=40,
                assignee_id=1,
                created_by=1,
                is_active=True
            ),
        ]

        for task in tasks:
            db_session.add(task)
        db_session.commit()

        # 执行聚合
        result = aggregate_task_progress(db=db_session, task_id=11)

        # 预期进度 = (60 + 40) / 2 = 50.0 (CANCELLED任务被排除)
        assert result['new_project_progress'] == 50.0

    def test_aggregation_handles_zero_tasks(self, db_session: Session):
        """测试零任务边界情况"""
        # 创建空项目
        project = Project(
            id=3,
            project_code="TEST-003",
            project_name="空项目",
            customer_name="测试客户",
            stage="S1",
            health="H1",
            progress_pct=0,
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建一个任务然后立即取消（模拟删除场景）
        task = TaskUnified(
            id=21,
            task_code="TASK-TEMP",
            project_id=project.id,
            title="临时任务",
            task_importance="GENERAL",
            task_type="PROJECT",
            status="CANCELLED",
            progress=0,
            assignee_id=1,
            created_by=1,
            is_active=False
        )
        db_session.add(task)
        db_session.commit()

        # 执行聚合
        result = aggregate_task_progress(db=db_session, task_id=21)

        # 没有活跃任务，project_progress_updated应为False（因为project_tasks为空）
        # 进度不应更新
        db_session.refresh(project)
        assert project.progress_pct == 0  # 保持原值

    def test_aggregation_handles_zero_progress(self, db_session: Session):
        """测试所有任务进度为0的情况"""
        project = Project(
            id=4,
            project_code="TEST-004",
            project_name="零进度项目",
            customer_name="测试客户",
            stage="S2",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建多个0%进度的任务
        for i in range(1, 4):
            task = TaskUnified(
                id=30 + i,
                task_code=f"TASK-ZERO-{i}",
                project_id=project.id,
                title=f"零进度任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="ACCEPTED",
                progress=0,  # 所有任务0%
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)
        db_session.commit()

        # 执行聚合
        result = aggregate_task_progress(db=db_session, task_id=31)

        # 预期进度 = (0 + 0 + 0) / 3 = 0.0
        assert result['new_project_progress'] == 0.0
        assert result['project_progress_updated'] is True

    def test_aggregation_precision(self, db_session: Session):
        """测试精度控制（保留2位小数）"""
        project = Project(
            id=5,
            project_code="TEST-005",
            project_name="精度测试",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建会产生循环小数的进度
        tasks = [
            {"progress": 33},   # 33%
            {"progress": 33},   # 33%
            {"progress": 34},   # 34%
        ]

        for i, task_data in enumerate(tasks, 1):
            task = TaskUnified(
                id=40 + i,
                task_code=f"TASK-PREC-{i}",
                project_id=project.id,
                title=f"精度任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=task_data["progress"],
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)
        db_session.commit()

        result = aggregate_task_progress(db=db_session, task_id=41)

        # 预期：(33 + 33 + 34) / 3 = 33.333... -> 33.33
        assert result['new_project_progress'] == 33.33

        # 验证确实保留2位小数
        assert isinstance(result['new_project_progress'], float)
        assert len(str(result['new_project_progress']).split('.')[-1]) <= 2

    def test_aggregation_returns_metadata(self, db_session: Session):
        """测试聚合返回完整元数据"""
        project = Project(
            id=6,
            project_code="TEST-006",
            project_name="元数据测试",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        task = TaskUnified(
            id=51,
            task_code="TASK-META",
            project_id=project.id,
            title="元数据任务",
            task_importance="GENERAL",
            task_type="PROJECT",
            status="IN_PROGRESS",
            progress=75,
            assignee_id=1,
            created_by=1,
            is_active=True
        )
        db_session.add(task)
        db_session.commit()

        result = aggregate_task_progress(db=db_session, task_id=51)

        # 验证返回的元数据结构
        assert 'project_progress_updated' in result
        assert 'stage_progress_updated' in result
        assert 'project_id' in result
        assert 'new_project_progress' in result

        assert result['project_id'] == project.id
        assert result['project_progress_updated'] is True

    def test_aggregation_triggers_on_task_update(self, db_session: Session):
        """测试任务更新时触发聚合（模拟实际使用场景）"""
        # 这个测试模拟 engineers.py:323 的调用
        project = Project(
            id=7,
            project_code="TEST-007",
            project_name="触发测试",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            progress_pct=0,  # 初始0%
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        task = TaskUnified(
            id=61,
            task_code="TASK-TRIGGER",
            project_id=project.id,
            title="触发任务",
            task_importance="GENERAL",
            task_type="PROJECT",
            status="ACCEPTED",
            progress=0,  # 初始0%
            assignee_id=1,
            created_by=1,
            is_active=True
        )
        db_session.add(task)
        db_session.commit()

        # 模拟进度更新到50%
        task.progress = 50
        task.status = "IN_PROGRESS"
        db_session.commit()

        # 触发聚合（模拟API调用）
        result = aggregate_task_progress(db=db_session, task_id=task.id)

        # 验证项目进度已更新
        db_session.refresh(project)
        assert project.progress_pct == 50.0
        assert result['project_progress_updated'] is True

        # 再次更新进度到100%
        task.progress = 100
        task.status = "COMPLETED"
        db_session.commit()

        result = aggregate_task_progress(db=db_session, task_id=task.id)

        # 验证项目进度再次更新
        db_session.refresh(project)
        assert project.progress_pct == 100.0


@pytest.mark.unit
@pytest.mark.aggregation
class TestHealthStatusAggregation:
    """测试健康度自动计算"""

    def test_health_status_normal(self, db_session: Session):
        """测试H1（正常）健康度"""
        project = Project(
            id=101,
            project_code="HEALTH-001",
            project_name="健康项目",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建10个任务，只有1个延期（10%，应为H1）
        for i in range(1, 11):
            task = TaskUnified(
                id=100 + i,
                task_code=f"TASK-H1-{i}",
                project_id=project.id,
                title=f"任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=50,
                is_delayed=(i == 1),  # 只有第1个延期
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)
        db_session.commit()

        # 触发健康度检查
        _check_and_update_health(db=db_session, project_id=project.id)

        db_session.refresh(project)
        # 延期率 = 1/10 = 10%，逾期率 = 0%
        # 应保持H1（正常）
        assert project.health == "H1"

    def test_health_status_at_risk(self, db_session: Session):
        """测试H2（有风险）健康度"""
        project = Project(
            id=102,
            project_code="HEALTH-002",
            project_name="风险项目",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 创建10个任务，3个延期（30%，应为H3）
        for i in range(1, 11):
            task = TaskUnified(
                id=120 + i,
                task_code=f"TASK-H2-{i}",
                project_id=project.id,
                title=f"任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=40,
                is_delayed=(i <= 3),  # 前3个延期
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)
        db_session.commit()

        _check_and_update_health(db=db_session, project_id=project.id)

        db_session.refresh(project)
        # 延期率 = 3/10 = 30% > 25%
        # 应变为H3（阻塞）
        assert project.health == "H3"

    def test_health_status_ignores_completed_tasks(self, db_session: Session):
        """测试健康度计算忽略已完成任务"""
        project = Project(
            id=103,
            project_code="HEALTH-003",
            project_name="部分完成项目",
            customer_name="测试客户",
            stage="S4",
            health="H1",
            is_active=True
        )
        db_session.add(project)
        db_session.commit()

        # 5个已完成任务（即使有延期标记也应忽略）
        for i in range(1, 6):
            task = TaskUnified(
                id=140 + i,
                task_code=f"TASK-COMP-{i}",
                project_id=project.id,
                title=f"已完成任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="COMPLETED",
                progress=100,
                is_delayed=True,  # 有延期标记
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)

        # 5个进行中任务，0个延期
        for i in range(6, 11):
            task = TaskUnified(
                id=140 + i,
                task_code=f"TASK-PROG-{i}",
                project_id=project.id,
                title=f"进行中任务{i}",
                task_importance="GENERAL",
                task_type="PROJECT",
                status="IN_PROGRESS",
                progress=50,
                is_delayed=False,
                assignee_id=1,
                created_by=1,
                is_active=True
            )
            db_session.add(task)

        db_session.commit()

        _check_and_update_health(db=db_session, project_id=project.id)

        db_session.refresh(project)
        # 只统计进行中的5个任务，延期率 = 0/5 = 0%
        # 应为H1（正常）
        assert project.health == "H1"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-m", "aggregation"])
