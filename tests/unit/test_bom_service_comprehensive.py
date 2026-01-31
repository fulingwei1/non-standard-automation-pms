# -*- coding: utf-8 -*-
"""
BomService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换为响应对象
- list_boms: 获取BOM列表
"""

from unittest.mock import MagicMock, patch

import pytest


class TestBomServiceInit:
    """测试 BomService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()

        service = BomService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "BOM"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.bom_service import BomService
        from app.models.material import BomHeader

        mock_db = MagicMock()

        service = BomService(mock_db)

        assert service.model == BomHeader


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_model_to_response(self):
        """测试将模型转换为响应对象"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_bom = MagicMock()
        mock_bom.id = 1
        mock_bom.bom_code = "BOM001"
        mock_bom.bom_name = "测试BOM"
        mock_bom.version = "1.0"
        mock_bom.project_id = 10
        mock_bom.machine_id = 20
        mock_bom.is_latest = True
        mock_bom.status = "ACTIVE"
        mock_bom.created_at = None
        mock_bom.updated_at = None

        with patch('app.schemas.material.BomResponse.model_validate') as mock_validate:
            mock_response = MagicMock()
            mock_validate.return_value = mock_response

            result = service._to_response(mock_bom)

            mock_validate.assert_called_once_with(mock_bom)
            assert result == mock_response


class TestListBoms:
    """测试 list_boms 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        # Mock the list method
        mock_result = MagicMock()
        mock_result.items = [MagicMock(), MagicMock()]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_boms(page=1, page_size=20)

            assert result['items'] == mock_result.items
            assert result['total'] == 2
            assert result['page'] == 1
            assert result['page_size'] == 20

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms(project_id=10)

            # 验证调用了list方法
            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('project_id') == 10

    def test_filters_by_machine_id(self):
        """测试按机台ID过滤"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms(machine_id=5)

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('machine_id') == 5

    def test_filters_by_is_latest(self):
        """测试按是否最新版本过滤"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms(is_latest=True)

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('is_latest') is True

    def test_filters_with_multiple_params(self):
        """测试多参数过滤"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 10

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms(
                page=2,
                page_size=10,
                project_id=100,
                machine_id=50,
                is_latest=False
            )

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.page == 2
            assert call_args.page_size == 10
            assert call_args.filters.get('project_id') == 100
            assert call_args.filters.get('machine_id') == 50
            assert call_args.filters.get('is_latest') is False

    def test_calculates_pages(self):
        """测试计算总页数"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 55
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_boms()

            # (55 + 20 - 1) // 20 = 3
            assert result['pages'] == 3

    def test_handles_zero_total(self):
        """测试处理零条记录"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_boms()

            assert result['pages'] == 0
            assert result['total'] == 0

    def test_default_sort_order(self):
        """测试默认排序"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms()

            call_args = mock_list.call_args[0][0]
            assert call_args.sort_by == "created_at"
            assert call_args.sort_order == "desc"

    def test_loads_relationships(self):
        """测试加载关联关系"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_boms()

            call_args = mock_list.call_args[0][0]
            assert "project" in call_args.load_relationships
            assert "machine" in call_args.load_relationships


class TestQueryParams:
    """测试查询参数构建"""

    def test_builds_query_params_correctly(self):
        """测试正确构建查询参数"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            service.list_boms(page=3, page_size=50)

            call_args = mock_list.call_args[0][0]
            assert call_args.page == 3
            assert call_args.page_size == 50

    def test_excludes_none_filters(self):
        """测试排除None值的过滤条件"""
        from app.services.bom_service import BomService

        mock_db = MagicMock()
        service = BomService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            service.list_boms(project_id=None, machine_id=None, is_latest=None)

            call_args = mock_list.call_args[0][0]
            assert 'project_id' not in call_args.filters
            assert 'machine_id' not in call_args.filters
            assert 'is_latest' not in call_args.filters
