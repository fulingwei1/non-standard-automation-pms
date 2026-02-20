# -*- coding: utf-8 -*-
"""
AI进度排期优化器增强测试 - 提升覆盖率到50%+
重点测试核心逻辑的输入输出
"""

import pytest
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.models import Project
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import AIScheduleOptimizer


@pytest.fixture
def test_project(db: Session):
    """创建测试项目（使用唯一ID）"""
    import uuid
    code = f"SCH_TEST_{uuid.uuid4().hex[:8].upper()}"
    project = Project(
        project_code=code,
        project_name="排期测试项目",
        project_type="WEB_DEV",
        status="ST01"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def test_wbs_chain(db: Session, test_project):
    """创建测试WBS任务链（串行任务）"""
    import uuid
    
    task1 = AIWbsSuggestion(
        suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
        project_id=test_project.id,
        wbs_level=1,
        wbs_code="1",
        sequence=1,
        task_name="需求分析",
        estimated_duration_days=10,
        is_active=True
    )
    
    task2 = AIWbsSuggestion(
        suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
        project_id=test_project.id,
        wbs_level=1,
        wbs_code="2",
        sequence=2,
        task_name="系统设计",
        estimated_duration_days=15,
        is_active=True
    )
    
    task3 = AIWbsSuggestion(
        suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
        project_id=test_project.id,
        wbs_level=1,
        wbs_code="3",
        sequence=3,
        task_name="开发实施",
        estimated_duration_days=30,
        is_active=True
    )
    
    db.add_all([task1, task2, task3])
    db.flush()
    
    # 设置依赖关系
    task2.dependencies = json.dumps([{"task_id": task1.id, "type": "FS"}])
    task3.dependencies = json.dumps([{"task_id": task2.id, "type": "FS"}])
    
    db.commit()
    for t in [task1, task2, task3]:
        db.refresh(t)
    
    return [task1, task2, task3]


class TestAIScheduleOptimizerEnhanced:
    """AI进度排期优化器增强测试"""
    
    def test_optimize_schedule_empty_tasks(self, db: Session, test_project):
        """测试：无任务时的排期优化"""
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=test_project.id,
            start_date=date(2026, 3, 1)
        )
        
        # 无任务应返回空结果
        assert result == {}
    
    def test_optimize_schedule_invalid_project(self, db: Session):
        """测试：无效项目ID"""
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=99999,  # 不存在的ID
            start_date=date(2026, 3, 1)
        )
        
        assert result == {}
    
    def test_optimize_schedule_default_start_date(self, db: Session, test_project, test_wbs_chain):
        """测试：默认开始日期（今天）"""
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=test_project.id,
            start_date=None  # 使用默认值
        )
        
        assert result is not None
        assert 'start_date' in result
        # 默认应该是今天
        assert result['start_date'] == date.today().isoformat()
    
    def test_optimize_schedule_with_constraints(self, db: Session, test_project, test_wbs_chain):
        """测试：带约束条件的排期"""
        optimizer = AIScheduleOptimizer(db)
        
        constraints = {
            "max_duration": 60,
            "critical_path_limit": 0.3
        }
        
        result = optimizer.optimize_schedule(
            project_id=test_project.id,
            start_date=date(2026, 3, 1),
            constraints=constraints
        )
        
        assert result is not None
        assert 'total_duration_days' in result
    
    def test_calculate_cpm_single_task(self, db: Session):
        """测试：单任务的CPM计算"""
        optimizer = AIScheduleOptimizer(db)
        
        task = Mock()
        task.id = 1
        task.estimated_duration_days = 10
        task.dependencies = None
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm([task], start_date)
        
        assert cpm_result['es'][1] == 0  # 第一个任务ES=0
        assert cpm_result['ef'][1] == 10  # EF=0+10
        assert cpm_result['slack'][1] == 0  # 单任务无浮动
        assert cpm_result['total_duration'] == 10
    
    def test_calculate_cpm_serial_tasks(self, db: Session, test_wbs_chain):
        """测试：串行任务的CPM计算"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(test_wbs_chain, start_date)
        
        # 验证总工期 = 10 + 15 + 30 = 55
        assert cpm_result['total_duration'] == 55
        
        # 验证ES递增
        assert cpm_result['es'][test_wbs_chain[0].id] == 0
        assert cpm_result['es'][test_wbs_chain[1].id] == 10
        assert cpm_result['es'][test_wbs_chain[2].id] == 25
        
        # 验证结束日期
        expected_end = start_date + timedelta(days=55)
        assert cpm_result['end_date'] == expected_end.isoformat()
    
    def test_calculate_cpm_parallel_tasks(self, db: Session, test_project):
        """测试：并行任务的CPM计算"""
        import uuid
        
        task1 = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="并行任务1",
            estimated_duration_days=10,
            is_active=True,
            dependencies=None
        )
        
        task2 = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            wbs_level=1,
            wbs_code="2",
            task_name="并行任务2",
            estimated_duration_days=15,
            is_active=True,
            dependencies=None  # 无依赖，可并行
        )
        
        db.add_all([task1, task2])
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        cpm_result = optimizer._calculate_cpm([task1, task2], date.today())
        
        # 并行任务应该同时开始
        assert cpm_result['es'][task1.id] == cpm_result['es'][task2.id] == 0
        
        # 总工期应该是较长任务的工期
        assert cpm_result['total_duration'] == 15
    
    def test_calculate_cpm_with_slack(self, db: Session, test_project):
        """测试：计算浮动时间"""
        import uuid
        
        # 创建有浮动时间的任务结构
        main_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            wbs_code="1",
            task_name="主路径任务",
            estimated_duration_days=20,
            is_active=True,
            dependencies=None
        )
        
        short_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            wbs_code="2",
            task_name="非关键任务",
            estimated_duration_days=10,
            is_active=True,
            dependencies=None
        )
        
        db.add_all([main_task, short_task])
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        cpm_result = optimizer._calculate_cpm([main_task, short_task], date.today())
        
        # 主路径任务浮动时间应为0
        assert cpm_result['slack'][main_task.id] == 0
        
        # 非关键任务应有浮动时间
        assert cpm_result['slack'][short_task.id] > 0
    
    def test_get_predecessors_no_dependencies(self, db: Session, test_project):
        """测试：无前置任务"""
        import uuid
        
        task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            task_name="独立任务",
            estimated_duration_days=10,
            dependencies=None
        )
        db.add(task)
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        task_dict = {task.id: task}
        
        predecessors = optimizer._get_predecessors(task, task_dict)
        
        assert predecessors == []
    
    def test_get_predecessors_with_dependencies(self, db: Session, test_wbs_chain):
        """测试：有前置任务"""
        optimizer = AIScheduleOptimizer(db)
        
        task_dict = {t.id: t for t in test_wbs_chain}
        
        # task2应该有task1作为前置任务
        predecessors = optimizer._get_predecessors(test_wbs_chain[1], task_dict)
        
        assert len(predecessors) == 1
        assert predecessors[0].id == test_wbs_chain[0].id
    
    def test_get_successors(self, db: Session, test_wbs_chain):
        """测试：获取后继任务"""
        optimizer = AIScheduleOptimizer(db)
        
        task_dict = {t.id: t for t in test_wbs_chain}
        
        # task1应该有task2作为后继任务
        successors = optimizer._get_successors(test_wbs_chain[0], task_dict)
        
        assert len(successors) == 1
        assert successors[0].id == test_wbs_chain[1].id
    
    def test_generate_gantt_data_structure(self, db: Session, test_wbs_chain):
        """测试：甘特图数据结构"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(test_wbs_chain, start_date)
        
        gantt_data = optimizer._generate_gantt_data(
            test_wbs_chain, cpm_result, start_date
        )
        
        assert len(gantt_data) == 3
        
        # 验证第一个任务的甘特图数据
        task1_data = gantt_data[0]
        assert 'task_id' in task1_data
        assert 'task_name' in task1_data
        assert 'start_date' in task1_data
        assert 'end_date' in task1_data
        assert 'duration_days' in task1_data
        assert 'es' in task1_data
        assert 'ef' in task1_data
        assert 'slack' in task1_data
        assert 'is_critical' in task1_data
    
    def test_generate_gantt_data_dates(self, db: Session, test_wbs_chain):
        """测试：甘特图日期计算"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(test_wbs_chain, start_date)
        
        gantt_data = optimizer._generate_gantt_data(
            test_wbs_chain, cpm_result, start_date
        )
        
        # 第一个任务应该从start_date开始
        assert gantt_data[0]['start_date'] == start_date.isoformat()
        
        # 第一个任务应该在start_date + 10天结束
        expected_end = start_date + timedelta(days=10)
        assert gantt_data[0]['end_date'] == expected_end.isoformat()
    
    def test_identify_critical_path_all_serial(self, db: Session, test_wbs_chain):
        """测试：全串行任务的关键路径"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(test_wbs_chain, start_date)
        
        critical_path = optimizer._identify_critical_path(test_wbs_chain, cpm_result)
        
        # 串行任务都应在关键路径上
        assert len(critical_path) == 3
        
        # 验证关键路径包含所有任务ID
        critical_ids = {item['task_id'] for item in critical_path}
        expected_ids = {t.id for t in test_wbs_chain}
        assert critical_ids == expected_ids
    
    def test_identify_critical_path_with_parallel(self, db: Session, test_project):
        """测试：并行任务的关键路径识别"""
        import uuid
        
        long_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            task_name="长任务",
            estimated_duration_days=20,
            is_active=True,
            dependencies=None
        )
        
        short_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            task_name="短任务",
            estimated_duration_days=10,
            is_active=True,
            dependencies=None
        )
        
        db.add_all([long_task, short_task])
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        cpm_result = optimizer._calculate_cpm([long_task, short_task], date.today())
        critical_path = optimizer._identify_critical_path([long_task, short_task], cpm_result)
        
        # 只有长任务在关键路径上
        assert len(critical_path) == 1
        assert critical_path[0]['task_id'] == long_task.id
    
    def test_analyze_resource_load_empty(self, db: Session, test_project):
        """测试：无资源分配的负载分析"""
        optimizer = AIScheduleOptimizer(db)
        
        cpm_result = {'es': {}, 'ef': {}}
        resource_load = optimizer._analyze_resource_load(test_project.id, cpm_result)
        
        assert resource_load == {}
    
    def test_analyze_resource_load_with_allocations(self, db: Session, test_project, test_wbs_chain):
        """测试：有资源分配的负载分析"""
        # 创建一些资源分配
        alloc1 = AIResourceAllocation(
            allocation_code="RA_TEST_001",
            project_id=test_project.id,
            wbs_suggestion_id=test_wbs_chain[0].id,
            user_id=1,
            allocated_hours=40,
            is_active=True
        )
        
        alloc2 = AIResourceAllocation(
            allocation_code="RA_TEST_002",
            project_id=test_project.id,
            wbs_suggestion_id=test_wbs_chain[1].id,
            user_id=1,
            allocated_hours=60,
            is_active=True
        )
        
        db.add_all([alloc1, alloc2])
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        cpm_result = {'es': {}, 'ef': {}}
        resource_load = optimizer._analyze_resource_load(test_project.id, cpm_result)
        
        assert 1 in resource_load
        assert resource_load[1]['total_hours'] == 100  # 40 + 60
        assert resource_load[1]['task_count'] == 2
    
    def test_detect_conflicts_no_issues(self, db: Session, test_wbs_chain):
        """测试：无冲突检测"""
        optimizer = AIScheduleOptimizer(db)
        
        cpm_result = {
            'es': {t.id: 0 for t in test_wbs_chain},
            'ef': {t.id: 10 for t in test_wbs_chain},
            'slack': {t.id: 0 for t in test_wbs_chain}
        }
        
        conflicts = optimizer._detect_conflicts(test_wbs_chain, cpm_result, {})
        
        assert isinstance(conflicts, list)
    
    def test_detect_conflicts_resource_overload(self, db: Session, test_wbs_chain):
        """测试：资源过载检测"""
        optimizer = AIScheduleOptimizer(db)
        
        # 模拟资源过载（超过480小时）
        resource_load = {
            1: {
                "user_id": 1,
                "total_hours": 600,  # 超过3个月的标准工时
                "task_count": 8,
                "tasks": []
            }
        }
        
        cpm_result = {'slack': {t.id: 0 for t in test_wbs_chain}}
        
        conflicts = optimizer._detect_conflicts(test_wbs_chain, cpm_result, resource_load)
        
        # 应该检测到资源过载冲突
        overload_conflicts = [c for c in conflicts if c['type'] == 'RESOURCE_OVERLOAD']
        assert len(overload_conflicts) > 0
        assert overload_conflicts[0]['severity'] == 'HIGH'
    
    def test_detect_conflicts_too_many_critical(self, db: Session, test_wbs_chain):
        """测试：关键任务过多检测"""
        optimizer = AIScheduleOptimizer(db)
        
        # 所有任务都是关键任务（slack=0）
        cpm_result = {'slack': {t.id: 0 for t in test_wbs_chain}}
        
        conflicts = optimizer._detect_conflicts(test_wbs_chain, cpm_result, {})
        
        # 应该检测到关键任务过多
        critical_conflicts = [c for c in conflicts if c['type'] == 'TOO_MANY_CRITICAL_TASKS']
        assert len(critical_conflicts) > 0
    
    def test_detect_conflicts_task_too_long(self, db: Session, test_project):
        """测试：任务工期过长检测"""
        import uuid
        
        long_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            task_name="超长任务",
            estimated_duration_days=100,  # 超过60天
            is_active=True
        )
        db.add(long_task)
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        cpm_result = {'slack': {long_task.id: 0}}
        
        conflicts = optimizer._detect_conflicts([long_task], cpm_result, {})
        
        # 应该检测到任务过长
        long_task_conflicts = [c for c in conflicts if c['type'] == 'TASK_TOO_LONG']
        assert len(long_task_conflicts) > 0
        assert long_task_conflicts[0]['severity'] == 'LOW'
    
    def test_generate_recommendations_with_critical_path(self, db: Session, test_wbs_chain):
        """测试：有关键路径的建议生成"""
        optimizer = AIScheduleOptimizer(db)
        
        critical_path = [
            {"task_id": t.id, "task_name": t.task_name}
            for t in test_wbs_chain
        ]
        
        recommendations = optimizer._generate_recommendations(
            test_wbs_chain, critical_path, [], {}
        )
        
        # 应该包含关键路径相关建议
        critical_recs = [r for r in recommendations if r['category'] == 'CRITICAL_PATH']
        assert len(critical_recs) > 0
        assert critical_recs[0]['priority'] == 'HIGH'
    
    def test_generate_recommendations_resource_imbalance(self, db: Session, test_wbs_chain):
        """测试：资源不均衡建议"""
        optimizer = AIScheduleOptimizer(db)
        
        # 模拟不均衡的资源负载
        resource_load = {
            1: {"total_hours": 400},
            2: {"total_hours": 100}  # 显著低于平均值
        }
        
        recommendations = optimizer._generate_recommendations(
            test_wbs_chain, [], [], resource_load
        )
        
        # 应该包含资源平衡建议
        balance_recs = [r for r in recommendations if r['category'] == 'RESOURCE_BALANCE']
        assert len(balance_recs) > 0
    
    def test_generate_recommendations_high_risk_tasks(self, db: Session, test_project):
        """测试：高风险任务建议"""
        import uuid
        
        high_risk_task = AIWbsSuggestion(
            suggestion_code=f"WBS_{uuid.uuid4().hex[:6]}",
            project_id=test_project.id,
            task_name="高风险任务",
            estimated_duration_days=10,
            risk_level="HIGH",
            is_active=True
        )
        db.add(high_risk_task)
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        
        recommendations = optimizer._generate_recommendations(
            [high_risk_task], [], [], {}
        )
        
        # 应该包含风险管理建议
        risk_recs = [r for r in recommendations if r['category'] == 'RISK_MANAGEMENT']
        assert len(risk_recs) > 0
        assert risk_recs[0]['priority'] == 'HIGH'
    
    def test_calculate_resource_utilization_empty(self, db: Session):
        """测试：空资源利用率"""
        optimizer = AIScheduleOptimizer(db)
        
        utilization = optimizer._calculate_resource_utilization({})
        
        assert utilization == 0.0
    
    def test_calculate_resource_utilization_normal(self, db: Session):
        """测试：正常资源利用率"""
        optimizer = AIScheduleOptimizer(db)
        
        resource_load = {
            1: {"total_hours": 240},  # 50%利用率
            2: {"total_hours": 360},  # 75%利用率
        }
        
        utilization = optimizer._calculate_resource_utilization(resource_load)
        
        # 平均62.5%利用率
        assert 60.0 <= utilization <= 65.0
    
    def test_calculate_resource_utilization_over_100(self, db: Session):
        """测试：超100%利用率的限制"""
        optimizer = AIScheduleOptimizer(db)
        
        resource_load = {
            1: {"total_hours": 600},  # 超过标准工时
        }
        
        utilization = optimizer._calculate_resource_utilization(resource_load)
        
        # 应该被限制在100%
        assert utilization == 100.0
    
    def test_optimize_schedule_complete_integration(self, db: Session, test_project, test_wbs_chain):
        """测试：完整的排期优化集成"""
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=test_project.id,
            start_date=date(2026, 3, 1)
        )
        
        # 验证返回结果的完整性
        assert 'project_id' in result
        assert 'start_date' in result
        assert 'total_duration_days' in result
        assert 'end_date' in result
        assert 'gantt_data' in result
        assert 'critical_path' in result
        assert 'critical_path_length' in result
        assert 'resource_load' in result
        assert 'conflicts' in result
        assert 'recommendations' in result
        assert 'optimization_summary' in result
        
        # 验证优化摘要
        summary = result['optimization_summary']
        assert 'total_tasks' in summary
        assert 'critical_tasks' in summary
        assert 'conflicts_found' in summary
        assert 'resource_utilization' in summary
        
        # 验证数值合理性
        assert result['total_duration_days'] == 55  # 10+15+30
        assert len(result['gantt_data']) == 3
        assert len(result['critical_path']) == 3  # 全部串行
