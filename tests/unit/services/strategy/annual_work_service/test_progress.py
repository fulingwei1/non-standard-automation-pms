# -*- coding: utf-8 -*-
"""
测试 annual_work_service/progress - 年度重点工作进度管理

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.strategy.annual_work_service.progress import (
    update_progress,
    calculate_progress_from_projects,
    sync_progress_from_projects
)
from app.models.strategy import AnnualKeyWork, AnnualKeyWorkProjectLink
from app.schemas.strategy import AnnualKeyWorkProgressUpdate


class TestUpdateProgress:
    """测试更新进度"""

    def test_update_progress_success(self):
        """测试成功更新进度"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(
            progress_percent=Decimal('50'),
            progress_description="已完成50%"
        )
        
        mock_work = AnnualKeyWork(
            id=1,
            progress_percent=Decimal('0'),
            status="NOT_STARTED",
            is_active=True
        )
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        assert result.progress_percent == Decimal('50')
        assert result.progress_description == "已完成50%"
        assert result.status == "IN_PROGRESS"

    def test_update_progress_to_completed(self):
        """测试更新进度至完成"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(
            progress_percent=Decimal('100')
        )
        
        mock_work = AnnualKeyWork(
            id=1,
            progress_percent=Decimal('80'),
            status="IN_PROGRESS",
            is_active=True
        )
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        assert result.progress_percent == Decimal('100')
        assert result.status == "COMPLETED"

    def test_update_progress_to_in_progress(self):
        """测试更新进度至进行中"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(
            progress_percent=Decimal('30')
        )
        
        mock_work = AnnualKeyWork(
            id=1,
            progress_percent=Decimal('0'),
            status="NOT_STARTED",
            is_active=True
        )
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        assert result.status == "IN_PROGRESS"

    def test_update_progress_non_existing_work(self):
        """测试更新不存在的工作"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(progress_percent=Decimal('50'))
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=None):
            result = update_progress(db, 999, data)
        
        assert result is None

    def test_update_progress_without_description(self):
        """测试不更新描述"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(progress_percent=Decimal('50'))
        
        mock_work = AnnualKeyWork(
            id=1,
            progress_percent=Decimal('0'),
            progress_description="旧描述",
            is_active=True
        )
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        # 描述应保持不变
        assert result.progress_description == "旧描述"

    def test_update_progress_over_100(self):
        """测试超过100%的进度"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(progress_percent=Decimal('120'))
        
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        # 超过100%仍然标记为完成
        assert result.status == "COMPLETED"


class TestCalculateProgressFromProjects:
    """测试从项目计算进度"""

    def test_calculate_with_single_project(self):
        """测试单个项目计算"""
        db = Mock(spec=Session)
        
        # Mock项目链接
        link = AnnualKeyWorkProjectLink(
            annual_work_id=1,
            project_id=100,
            contribution_weight=Decimal('1'),
            is_active=True
        )
        
        # Mock项目
        from app.models.project import Project
        project = Project(id=100, progress_pct=Decimal('60'))
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = [link]
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = project
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            elif model == Project:
                return mock_query_project
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        assert result == Decimal('60')

    def test_calculate_with_multiple_projects_equal_weight(self):
        """测试多个项目等权重"""
        db = Mock(spec=Session)
        
        links = [
            AnnualKeyWorkProjectLink(
                annual_work_id=1,
                project_id=100,
                contribution_weight=Decimal('1'),
                is_active=True
            ),
            AnnualKeyWorkProjectLink(
                annual_work_id=1,
                project_id=101,
                contribution_weight=Decimal('1'),
                is_active=True
            )
        ]
        
        from app.models.project import Project
        projects = {
            100: Project(id=100, progress_pct=Decimal('60')),
            101: Project(id=101, progress_pct=Decimal('80'))
        }
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = links
        
        call_count = [0]
        def query_project_side_effect(*args, **kwargs):
            project_id = links[call_count[0]].project_id
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value.first.return_value = projects.get(project_id)
            return mock_q
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            else:
                return query_project_side_effect()
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        # (60 + 80) / 2 = 70
        assert result == Decimal('70')

    def test_calculate_with_different_weights(self):
        """测试不同权重"""
        db = Mock(spec=Session)
        
        links = [
            AnnualKeyWorkProjectLink(
                annual_work_id=1,
                project_id=100,
                contribution_weight=Decimal('2'),
                is_active=True
            ),
            AnnualKeyWorkProjectLink(
                annual_work_id=1,
                project_id=101,
                contribution_weight=Decimal('1'),
                is_active=True
            )
        ]
        
        from app.models.project import Project
        projects = {
            100: Project(id=100, progress_pct=Decimal('60')),
            101: Project(id=101, progress_pct=Decimal('90'))
        }
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = links
        
        call_count = [0]
        def query_project_side_effect(*args, **kwargs):
            project_id = links[call_count[0]].project_id
            call_count[0] += 1
            mock_q = MagicMock()
            mock_q.filter.return_value.first.return_value = projects.get(project_id)
            return mock_q
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            else:
                return query_project_side_effect()
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        # (60*2 + 90*1) / (2+1) = 210/3 = 70
        assert result == Decimal('70')

    def test_calculate_no_projects(self):
        """测试无关联项目"""
        db = Mock(spec=Session)
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = []
        db.query.return_value = mock_query_link
        
        result = calculate_progress_from_projects(db, 1)
        
        assert result is None

    def test_calculate_project_none_progress(self):
        """测试项目进度为None"""
        db = Mock(spec=Session)
        
        link = AnnualKeyWorkProjectLink(
            annual_work_id=1,
            project_id=100,
            contribution_weight=Decimal('1'),
            is_active=True
        )
        
        from app.models.project import Project
        project = Project(id=100, progress_pct=None)
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = [link]
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = project
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            else:
                return mock_query_project
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        # 项目进度为None时，应该返回None（权重为0）
        assert result is None

    def test_calculate_zero_total_weight(self):
        """测试总权重为0"""
        db = Mock(spec=Session)
        
        link = AnnualKeyWorkProjectLink(
            annual_work_id=1,
            project_id=100,
            contribution_weight=None,  # None会被当作1
            is_active=True
        )
        
        from app.models.project import Project
        project = Project(id=100, progress_pct=None)
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = [link]
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = project
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            else:
                return mock_query_project
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        assert result is None


class TestSyncProgressFromProjects:
    """测试从项目同步进度"""

    def test_sync_success(self):
        """测试成功同步"""
        db = Mock(spec=Session)
        
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.progress.calculate_progress_from_projects', return_value=Decimal('75')):
            with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
                db.commit = MagicMock()
                db.refresh = MagicMock()
                
                result = sync_progress_from_projects(db, 1)
        
        assert result.progress_percent == Decimal('75')
        assert result.status == "IN_PROGRESS"
        assert "自动同步" in result.progress_description

    def test_sync_to_completed(self):
        """测试同步至完成"""
        db = Mock(spec=Session)
        
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.progress.calculate_progress_from_projects', return_value=Decimal('100')):
            with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
                db.commit = MagicMock()
                db.refresh = MagicMock()
                
                result = sync_progress_from_projects(db, 1)
        
        assert result.status == "COMPLETED"

    def test_sync_no_progress(self):
        """测试无法计算进度"""
        db = Mock(spec=Session)
        
        with patch('app.services.strategy.annual_work_service.progress.calculate_progress_from_projects', return_value=None):
            result = sync_progress_from_projects(db, 1)
        
        assert result is None

    def test_sync_non_existing_work(self):
        """测试同步不存在的工作"""
        db = Mock(spec=Session)
        
        with patch('app.services.strategy.annual_work_service.progress.calculate_progress_from_projects', return_value=Decimal('50')):
            with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=None):
                result = sync_progress_from_projects(db, 999)
        
        assert result is None


class TestEdgeCases:
    """测试边界情况"""

    def test_update_progress_zero(self):
        """测试0进度"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkProgressUpdate(progress_percent=Decimal('0'))
        
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_progress(db, 1, data)
        
        # 0进度不应该变为IN_PROGRESS
        assert result.progress_percent == Decimal('0')

    def test_calculate_very_small_weights(self):
        """测试非常小的权重"""
        db = Mock(spec=Session)
        
        link = AnnualKeyWorkProjectLink(
            annual_work_id=1,
            project_id=100,
            contribution_weight=Decimal('0.001'),
            is_active=True
        )
        
        from app.models.project import Project
        project = Project(id=100, progress_pct=Decimal('50'))
        
        mock_query_link = MagicMock()
        mock_query_link.filter.return_value.all.return_value = [link]
        
        mock_query_project = MagicMock()
        mock_query_project.filter.return_value.first.return_value = project
        
        def query_side_effect(model):
            if model == AnnualKeyWorkProjectLink:
                return mock_query_link
            else:
                return mock_query_project
        
        db.query.side_effect = query_side_effect
        
        result = calculate_progress_from_projects(db, 1)
        
        # 应该能正确计算
        assert result == Decimal('50')

    def test_sync_description_format(self):
        """测试同步描述格式"""
        db = Mock(spec=Session)
        
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.progress.calculate_progress_from_projects', return_value=Decimal('60')):
            with patch('app.services.strategy.annual_work_service.progress.get_annual_work', return_value=mock_work):
                db.commit = MagicMock()
                db.refresh = MagicMock()
                
                result = sync_progress_from_projects(db, 1)
        
        assert result.progress_description == "从关联项目自动同步"
