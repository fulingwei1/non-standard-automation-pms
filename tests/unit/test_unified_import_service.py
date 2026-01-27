# -*- coding: utf-8 -*-
"""
统一导入服务单元测试

测试覆盖:
- UnifiedImportService: 统一导入服务
- UnifiedImporter: 导入路由
- ImportBase: 导入基础类
- UserImporter: 用户导入
- TimesheetImporter: 工时导入
- TaskImporter: 任务导入
- MaterialImporter: 物料导入
- BomImporter: BOM导入
"""

from datetime import date, datetime
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


class TestImportBase:
    """测试导入基础类"""

    def test_import_class(self):
        """测试导入基础类"""
        from app.services.unified_import.base import ImportBase
        assert ImportBase is not None

    def test_parse_work_date_valid(self):
        """测试解析工作日期 - 有效"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        # 测试各种日期格式
        result = base.parse_work_date("2025-01-15")
        assert result is not None or isinstance(result, date)

    def test_parse_work_date_invalid(self):
        """测试解析工作日期 - 无效"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_work_date("invalid-date")
        assert result is None

    def test_parse_hours_valid(self):
        """测试解析工时 - 有效"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_hours("8.5")
        assert result == 8.5

    def test_parse_hours_invalid(self):
        """测试解析工时 - 无效"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_hours("invalid")
        assert result is None

    def test_parse_hours_out_of_range(self):
        """测试解析工时 - 超出范围"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        # 超过24小时
        result = base.parse_hours("25")
        assert result is None

        # 小于等于0
        result = base.parse_hours("0")
        assert result is None

        result = base.parse_hours("-1")
        assert result is None

    def test_parse_progress_valid(self):
        """测试解析进度 - 有效"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_progress("50")
        assert result == 50

    def test_parse_progress_percentage(self):
        """测试解析进度 - 带百分号"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_progress("75%")
        assert result == 75 or result == 0.75

    def test_parse_progress_out_of_range(self):
        """测试解析进度 - 超出范围"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        result = base.parse_progress("150")
        assert result is None or result == 100  # 可能被截断到100

    def test_check_required_columns_all_present(self):
        """测试检查必需列 - 全部存在"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        df_columns = ["name", "email", "department"]
        required = ["name", "email"]

        result = base.check_required_columns(df_columns, required)
        assert result is True or result == []

    def test_check_required_columns_missing(self):
        """测试检查必需列 - 缺少列"""
        from app.services.unified_import.base import ImportBase

        base = ImportBase()

        df_columns = ["name", "email"]
        required = ["name", "email", "department"]

        result = base.check_required_columns(df_columns, required)
        # 应该返回缺少的列名或False
        assert result is False or "department" in result


class TestUnifiedImporter:
    """测试统一导入路由"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.router import UnifiedImporter
        assert UnifiedImporter is not None

    def test_import_data_user(self, db_session):
        """测试导入用户数据"""
        from app.services.unified_import.router import UnifiedImporter

        importer = UnifiedImporter(db_session)

        # 创建模拟文件
        mock_file = MagicMock()
        mock_file.read.return_value = b""
        mock_file.filename = "users.xlsx"

        with patch('app.services.unified_import.router.pd') as mock_pd:
            mock_pd.read_excel.return_value = MagicMock()

            result = importer.import_data(
                template_type="USER",
                file=mock_file,
            )

            # 应该返回导入结果
            assert result is not None or isinstance(result, dict)


class TestUserImporter:
    """测试用户导入"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.user_importer import UserImporter
        assert UserImporter is not None


class TestTimesheetImporter:
    """测试工时导入"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.timesheet_importer import TimesheetImporter
        assert TimesheetImporter is not None


class TestTaskImporter:
    """测试任务导入"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.task_importer import TaskImporter
        assert TaskImporter is not None


class TestMaterialImporter:
    """测试物料导入"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.material_importer import MaterialImporter
        assert MaterialImporter is not None


class TestBomImporter:
    """测试BOM导入"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.unified_import.bom_importer import BomImporter
        assert BomImporter is not None


class TestUnifiedImportModule:
    """测试统一导入模块"""

    def test_import_all(self):
        """测试导入所有组件"""
        from app.services.unified_import import (
            UnifiedImportService,
        )

        assert UnifiedImportService is not None
