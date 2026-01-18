# -*- coding: utf-8 -*-
"""
统一数据导入服务
功能：支持多种数据类型的Excel导入：项目、用户、工时、任务、物料、BOM

向后兼容：保持原有的类接口
"""

from .base import ImportBase
from .bom_importer import BomImporter
from .material_importer import MaterialImporter
from .task_importer import TaskImporter
from .timesheet_importer import TimesheetImporter
from .unified_importer import UnifiedImporter
from .user_importer import UserImporter


class UnifiedImportService(ImportBase):
    """统一数据导入服务 - 统一接口类"""

    # 委托给统一导入器
    import_data = UnifiedImporter.import_data

    # 委托给具体导入器
    import_user_data = UserImporter.import_user_data
    import_timesheet_data = TimesheetImporter.import_timesheet_data
    import_task_data = TaskImporter.import_task_data
    import_material_data = MaterialImporter.import_material_data
    import_bom_data = BomImporter.import_bom_data

    # 保留原有的工具方法（向后兼容）
    _check_required_columns = ImportBase.check_required_columns
    _parse_work_date = ImportBase.parse_work_date
    _parse_hours = ImportBase.parse_hours
    _parse_progress = TimesheetImporter.parse_progress
    _create_timesheet_record = TimesheetImporter.create_timesheet_record


# 向后兼容：创建单例
unified_import_service = UnifiedImportService()

# 向后兼容：导出主服务类和单例
__all__ = [
    'UnifiedImportService',
    'unified_import_service',  # 单例
    # 基类
    'ImportBase',
    # 统一导入器
    'UnifiedImporter',
    # 具体导入器
    'UserImporter',
    'TimesheetImporter',
    'TaskImporter',
    'MaterialImporter',
    'BomImporter',
]
