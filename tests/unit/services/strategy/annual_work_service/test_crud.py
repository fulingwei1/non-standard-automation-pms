# -*- coding: utf-8 -*-
"""
测试 annual_work_service/crud - 年度重点工作CRUD操作

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date
from sqlalchemy.orm import Session

from app.services.strategy.annual_work_service.crud import (
    create_annual_work,
    get_annual_work,
    list_annual_works,
    update_annual_work,
    delete_annual_work
)
from app.models.strategy import AnnualKeyWork
from app.schemas.strategy import AnnualKeyWorkCreate, AnnualKeyWorkUpdate


class TestCreateAnnualWork:
    """测试创建年度重点工作"""

    def test_create_success(self):
        """测试成功创建"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkCreate(
            csf_id=1,
            code="KW001",
            name="重点工作1",
            year=2024
        )
        
        # Mock数据库操作
        mock_work = AnnualKeyWork(id=1, **data.model_dump())
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))
        
        with patch('app.services.strategy.annual_work_service.crud.AnnualKeyWork', return_value=mock_work):
            result = create_annual_work(db, data)
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_create_with_all_fields(self):
        """测试创建包含所有字段"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkCreate(
            csf_id=1,
            code="KW001",
            name="重点工作1",
            description="描述",
            voc_source="客户反馈",
            pain_point="痛点",
            solution="解决方案",
            year=2024,
            priority=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            owner_dept_id=10,
            owner_user_id=100
        )
        
        mock_work = MagicMock(spec=AnnualKeyWork)
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        
        with patch('app.services.strategy.annual_work_service.crud.AnnualKeyWork', return_value=mock_work):
            result = create_annual_work(db, data)
        
        assert db.add.called
        assert db.commit.called


class TestGetAnnualWork:
    """测试获取年度重点工作"""

    def test_get_existing_work(self):
        """测试获取存在的工作"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        mock_work = AnnualKeyWork(id=1, code="KW001", name="工作1", is_active=True)
        
        mock_query.filter.return_value.first.return_value = mock_work
        db.query.return_value = mock_query
        
        result = get_annual_work(db, 1)
        
        assert result == mock_work
        db.query.assert_called_once_with(AnnualKeyWork)

    def test_get_non_existing_work(self):
        """测试获取不存在的工作"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        result = get_annual_work(db, 999)
        
        assert result is None

    def test_get_inactive_work(self):
        """测试获取已删除的工作"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        # 过滤条件会排除is_active=False的记录
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        result = get_annual_work(db, 1)
        
        assert result is None


class TestListAnnualWorks:
    """测试列出年度重点工作"""

    def test_list_all_works(self):
        """测试列出所有工作"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        works = [
            AnnualKeyWork(id=1, code="KW001", is_active=True),
            AnnualKeyWork(id=2, code="KW002", is_active=True)
        ]
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = works
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db)
        
        assert len(items) == 2
        assert total == 2

    def test_list_with_csf_filter(self):
        """测试按CSF过滤"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        works = [AnnualKeyWork(id=1, csf_id=1, is_active=True)]
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = works
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db, csf_id=1)
        
        assert len(items) == 1

    def test_list_with_year_filter(self):
        """测试按年度过滤"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        works = [AnnualKeyWork(id=1, year=2024, is_active=True)]
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = works
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db, year=2024)
        
        assert len(items) == 1

    def test_list_with_status_filter(self):
        """测试按状态过滤"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        works = [AnnualKeyWork(id=1, status="IN_PROGRESS", is_active=True)]
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = works
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db, status="IN_PROGRESS")
        
        assert len(items) == 1

    def test_list_with_pagination(self):
        """测试分页"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        works = [AnnualKeyWork(id=i, is_active=True) for i in range(1, 11)]
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = works
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db, skip=10, limit=10)
        
        assert len(items) == 10
        assert total == 100
        mock_pagination.assert_called_once()

    def test_list_empty_result(self):
        """测试空结果"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = []
            db.query.return_value = mock_query
            
            items, total = list_annual_works(db)
        
        assert items == []
        assert total == 0


class TestUpdateAnnualWork:
    """测试更新年度重点工作"""

    def test_update_success(self):
        """测试成功更新"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkUpdate(name="新名称")
        
        mock_work = AnnualKeyWork(id=1, name="旧名称", is_active=True)
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_annual_work(db, 1, data)
        
        assert result.name == "新名称"
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_update_non_existing_work(self):
        """测试更新不存在的工作"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkUpdate(name="新名称")
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=None):
            result = update_annual_work(db, 999, data)
        
        assert result is None

    def test_update_multiple_fields(self):
        """测试更新多个字段"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkUpdate(
            name="新名称",
            description="新描述",
            priority=5
        )
        
        mock_work = AnnualKeyWork(id=1, name="旧名称", is_active=True)
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_annual_work(db, 1, data)
        
        assert result.name == "新名称"
        assert result.description == "新描述"
        assert result.priority == 5

    def test_update_partial_fields(self):
        """测试部分更新"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkUpdate(name="新名称")
        
        mock_work = AnnualKeyWork(
            id=1,
            name="旧名称",
            description="保持不变",
            is_active=True
        )
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_annual_work(db, 1, data)
        
        assert result.name == "新名称"
        assert result.description == "保持不变"


class TestDeleteAnnualWork:
    """测试删除年度重点工作"""

    def test_delete_success(self):
        """测试成功删除"""
        db = Mock(spec=Session)
        mock_work = AnnualKeyWork(id=1, is_active=True)
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            
            result = delete_annual_work(db, 1)
        
        assert result is True
        assert mock_work.is_active is False
        db.commit.assert_called_once()

    def test_delete_non_existing_work(self):
        """测试删除不存在的工作"""
        db = Mock(spec=Session)
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=None):
            result = delete_annual_work(db, 999)
        
        assert result is False

    def test_delete_already_deleted(self):
        """测试删除已删除的工作"""
        db = Mock(spec=Session)
        
        # get_annual_work会过滤is_active=False的记录
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=None):
            result = delete_annual_work(db, 1)
        
        assert result is False


class TestEdgeCases:
    """测试边界情况"""

    def test_create_with_none_optional_fields(self):
        """测试创建时可选字段为None"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkCreate(
            csf_id=1,
            code="KW001",
            name="工作1",
            year=2024,
            description=None,
            voc_source=None,
            pain_point=None
        )
        
        mock_work = MagicMock(spec=AnnualKeyWork)
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        
        with patch('app.services.strategy.annual_work_service.crud.AnnualKeyWork', return_value=mock_work):
            result = create_annual_work(db, data)
        
        assert db.add.called

    def test_list_with_all_filters(self):
        """测试所有过滤条件"""
        db = Mock(spec=Session)
        mock_query = MagicMock()
        
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        
        with patch('app.services.strategy.annual_work_service.crud.apply_pagination') as mock_pagination:
            mock_pagination.return_value.all.return_value = []
            db.query.return_value = mock_query
            
            items, total = list_annual_works(
                db,
                csf_id=1,
                strategy_id=10,
                year=2024,
                status="IN_PROGRESS"
            )
        
        assert items == []

    def test_update_with_empty_data(self):
        """测试空更新数据"""
        db = Mock(spec=Session)
        data = AnnualKeyWorkUpdate()
        
        mock_work = AnnualKeyWork(id=1, name="名称", is_active=True)
        
        with patch('app.services.strategy.annual_work_service.crud.get_annual_work', return_value=mock_work):
            db.commit = MagicMock()
            db.refresh = MagicMock()
            
            result = update_annual_work(db, 1, data)
        
        # 名称应保持不变
        assert result.name == "名称"
