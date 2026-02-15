# -*- coding: utf-8 -*-
"""
AI进度排期优化器测试
"""

import pytest
import json
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models import Project
from app.models.ai_planning import AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import AIScheduleOptimizer


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code="SCH_TEST_001",
        project_name="排期测试项目",
        project_type="WEB_DEV",
        status="ST01"
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def sample_wbs_tasks(db: Session, sample_project):
    """创建测试WBS任务链"""
    task1 = AIWbsSuggestion(
        suggestion_code="WBS_SCH_001",
        project_id=sample_project.id,
        wbs_level=1,
        wbs_code="1",
        sequence=1,
        task_name="需求分析",
        estimated_duration_days=10,
        is_active=True
    )
    
    task2 = AIWbsSuggestion(
        suggestion_code="WBS_SCH_002",
        project_id=sample_project.id,
        wbs_level=1,
        wbs_code="2",
        sequence=2,
        task_name="系统设计",
        estimated_duration_days=15,
        is_active=True
    )
    
    task3 = AIWbsSuggestion(
        suggestion_code="WBS_SCH_003",
        project_id=sample_project.id,
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
    
    return [task1, task2, task3]


class TestAIScheduleOptimizer:
    """AI进度排期优化器测试类"""
    
    def test_optimize_schedule_basic(self, db: Session, sample_project, sample_wbs_tasks):
        """测试：基本排期优化"""
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=sample_project.id,
            start_date=date(2026, 3, 1)
        )
        
        assert result is not None
        assert 'total_duration_days' in result
        assert 'gantt_data' in result
        assert 'critical_path' in result
        assert result['total_duration_days'] > 0
    
    def test_calculate_cpm(self, db: Session, sample_wbs_tasks):
        """测试：关键路径法计算"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, start_date)
        
        assert 'es' in cpm_result
        assert 'ef' in cpm_result
        assert 'ls' in cpm_result
        assert 'lf' in cpm_result
        assert 'slack' in cpm_result
        assert 'total_duration' in cpm_result
        
        # 验证总工期 = 10 + 15 + 30 = 55天
        assert cpm_result['total_duration'] == 55
    
    def test_identify_critical_path(self, db: Session, sample_wbs_tasks):
        """测试：关键路径识别"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, start_date)
        
        critical_path = optimizer._identify_critical_path(sample_wbs_tasks, cpm_result)
        
        assert len(critical_path) > 0
        # 在串行任务中，所有任务都应该在关键路径上
        assert len(critical_path) == len(sample_wbs_tasks)
    
    def test_generate_gantt_data(self, db: Session, sample_wbs_tasks):
        """测试：甘特图数据生成"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, start_date)
        
        gantt_data = optimizer._generate_gantt_data(
            sample_wbs_tasks, cpm_result, start_date
        )
        
        assert len(gantt_data) == len(sample_wbs_tasks)
        
        # 验证每个任务都有完整的甘特图数据
        for item in gantt_data:
            assert 'task_id' in item
            assert 'task_name' in item
            assert 'start_date' in item
            assert 'end_date' in item
            assert 'is_critical' in item
    
    def test_detect_conflicts(self, db: Session, sample_project, sample_wbs_tasks):
        """测试：冲突检测"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, start_date)
        resource_load = {}
        
        conflicts = optimizer._detect_conflicts(
            sample_wbs_tasks, cpm_result, resource_load
        )
        
        # 冲突列表应该是一个列表（可能为空）
        assert isinstance(conflicts, list)
    
    def test_detect_resource_overload(self, db: Session, sample_project, sample_wbs_tasks):
        """测试：资源过载检测"""
        optimizer = AIScheduleOptimizer(db)
        
        # 模拟资源过载
        resource_load = {
            1: {
                "user_id": 1,
                "total_hours": 600,  # 超过3个月的标准工时(160*3=480)
                "task_count": 5,
                "tasks": []
            }
        }
        
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, date.today())
        
        conflicts = optimizer._detect_conflicts(
            sample_wbs_tasks, cpm_result, resource_load
        )
        
        # 应该检测到资源过载冲突
        overload_conflicts = [c for c in conflicts if c['type'] == 'RESOURCE_OVERLOAD']
        assert len(overload_conflicts) > 0
    
    def test_generate_recommendations(self, db: Session, sample_wbs_tasks):
        """测试：优化建议生成"""
        optimizer = AIScheduleOptimizer(db)
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm(sample_wbs_tasks, start_date)
        critical_path = optimizer._identify_critical_path(sample_wbs_tasks, cpm_result)
        
        recommendations = optimizer._generate_recommendations(
            sample_wbs_tasks, critical_path, [], {}
        )
        
        assert isinstance(recommendations, list)
        # 应该有关键路径相关的建议
        if critical_path:
            critical_path_recs = [r for r in recommendations if r['category'] == 'CRITICAL_PATH']
            assert len(critical_path_recs) > 0
    
    def test_calculate_resource_utilization(self, db: Session):
        """测试：资源利用率计算"""
        optimizer = AIScheduleOptimizer(db)
        
        resource_load = {
            1: {"total_hours": 400},
            2: {"total_hours": 300},
            3: {"total_hours": 200},
        }
        
        utilization = optimizer._calculate_resource_utilization(resource_load)
        
        assert 0 <= utilization <= 100
    
    def test_optimize_schedule_performance(self, db: Session, sample_project, sample_wbs_tasks):
        """测试：排期优化性能"""
        import time
        
        optimizer = AIScheduleOptimizer(db)
        
        start_time = time.time()
        
        optimizer.optimize_schedule(
            project_id=sample_project.id
        )
        
        elapsed_time = time.time() - start_time
        
        # 排期优化应该很快（< 3秒）
        assert elapsed_time < 3
    
    def test_parallel_tasks_scheduling(self, db: Session, sample_project):
        """测试：并行任务排期"""
        # 创建并行任务
        task1 = AIWbsSuggestion(
            suggestion_code="WBS_PAR_001",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="并行任务1",
            estimated_duration_days=10,
            is_active=True
        )
        
        task2 = AIWbsSuggestion(
            suggestion_code="WBS_PAR_002",
            project_id=sample_project.id,
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
        
        start_date = date(2026, 3, 1)
        cpm_result = optimizer._calculate_cpm([task1, task2], start_date)
        
        # 并行任务应该同时开始
        assert cpm_result['es'][task1.id] == cpm_result['es'][task2.id]
        
        # 总工期应该是较长任务的工期
        assert cpm_result['total_duration'] == 15
    
    def test_slack_calculation(self, db: Session, sample_project):
        """测试：浮动时间计算"""
        # 创建有浮动时间的任务
        task1 = AIWbsSuggestion(
            suggestion_code="WBS_SLACK_001",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="主路径任务",
            estimated_duration_days=20,
            is_active=True
        )
        
        task2 = AIWbsSuggestion(
            suggestion_code="WBS_SLACK_002",
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="2",
            task_name="非关键任务",
            estimated_duration_days=10,  # 比主路径短
            is_active=True,
            dependencies=None
        )
        
        db.add_all([task1, task2])
        db.commit()
        
        optimizer = AIScheduleOptimizer(db)
        
        cpm_result = optimizer._calculate_cpm([task1, task2], date.today())
        
        # task1在关键路径上，浮动时间为0
        assert cpm_result['slack'][task1.id] == 0
        
        # task2不在关键路径上，有浮动时间
        assert cpm_result['slack'][task2.id] > 0
