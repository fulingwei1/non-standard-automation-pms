# -*- coding: utf-8 -*-
"""
健康度批量计算性能测试

Sprint 5.2: 性能优化 - 健康度批量计算性能测试
"""

import time

import pytest
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.health_calculator import HealthCalculator


class TestHealthCalculationPerformance:
    """健康度批量计算性能测试"""

    @pytest.mark.skipif(True, reason="需要大量测试数据")
    def test_batch_calculate_performance(self, db: Session):
        """
        测试健康度批量计算性能

        目标：1000+项目批量计算时间 < 30秒
        """
        calculator = HealthCalculator(db)

        # 获取所有活跃项目
        project_ids = [
            p.id for p in db.query(Project.id).filter(
                Project.is_active == True,
                Project.is_archived == False
            ).limit(1000).all()
        ]

        if not project_ids:
            pytest.skip("没有足够的测试数据")

        start_time = time.time()

        # 执行批量计算
        result = calculator.batch_calculate(project_ids=project_ids, batch_size=100)

        elapsed_time = time.time() - start_time

        assert elapsed_time < 30, f"批量计算耗时 {elapsed_time}秒，超过30秒阈值"
        assert result["total"] == len(project_ids)
        assert result["updated"] + result["unchanged"] == result["total"]

    def test_batch_calculate_small_batch(self, db: Session):
        """测试小批量计算性能"""
        calculator = HealthCalculator(db)

        # 获取少量项目进行测试
        projects = db.query(Project).filter(
            Project.is_active == True,
            Project.is_archived == False
        ).limit(10).all()

        if not projects:
            pytest.skip("没有测试数据")

        project_ids = [p.id for p in projects]

        start_time = time.time()
        result = calculator.batch_calculate(project_ids=project_ids, batch_size=5)
        elapsed_time = time.time() - start_time

        assert elapsed_time < 5, f"小批量计算耗时 {elapsed_time}秒，超过5秒阈值"
        assert result["total"] == len(project_ids)

    def test_single_calculate_performance(self, db: Session):
        """测试单个项目健康度计算性能"""
        calculator = HealthCalculator(db)

        project = db.query(Project).filter(
            Project.is_active == True
        ).first()

        if not project:
            pytest.skip("没有测试数据")

        start_time = time.time()
        result = calculator.calculate_and_update(project, auto_save=True)
        elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒

        # 单个项目计算应该在100ms以内
        assert elapsed_time < 100, f"单个项目计算耗时 {elapsed_time}ms，超过100ms阈值"
        assert "old_health" in result
        assert "new_health" in result
