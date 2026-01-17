# -*- coding: utf-8 -*-
"""
售前系统集成 API

已拆分为模块化结构，详见 presales_integration/ 目录：
- utils.py: 辅助工具函数
- lead_conversion.py: 线索转项目
- win_rate.py: 中标率预测
- resource_analysis.py: 资源投入与浪费分析
- salesperson.py: 销售人员绩效分析
- dashboard.py: 售前分析仪表板
"""

from .presales_integration import router

__all__ = ["router"]
