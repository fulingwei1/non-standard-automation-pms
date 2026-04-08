# -*- coding: utf-8 -*-
"""
Timesheet Reminders 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for timesheet_reminders
    from .timesheetreminders import router
except ImportError:
    try:
        from .timesheet import router
    except ImportError:
        try:
            from .common.timesheet_reminders import router
        except ImportError:
            try:
                from .admin.timesheet_reminders import router
            except ImportError:
                # Create a simple router as fallback
                from fastapi import APIRouter
                router = APIRouter()
                @router.get('/')
                def read_root():
                    return {'message': 'timesheet_reminders module placeholder'}

__all__ = ['router']
