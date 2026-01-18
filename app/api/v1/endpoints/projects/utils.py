# -*- coding: utf-8 -*-
"""
项目模块公共工具函数 - 聚合器

已拆分为模块化结构：
- gate_checks.py: 阶段门检查函数
- sync_utils.py: 同步工具函数（ERP、开票申请）
- serialization.py: 序列化函数
- code_generation.py: 编号生成函数
"""

# 导入所有工具函数，保持向后兼容
from .code_generation import generate_review_no
from .gate_checks import (
    check_gate,
    check_gate_detailed,
    check_gate_s1_to_s2,
    check_gate_s2_to_s3,
    check_gate_s3_to_s4,
    check_gate_s4_to_s5,
    check_gate_s5_to_s6,
    check_gate_s6_to_s7,
    check_gate_s7_to_s8,
    check_gate_s8_to_s9,
)
from .serialization import _serialize_project_status_log
from .sync_utils import _sync_invoice_request_receipt_status, _sync_to_erp_system

__all__ = [
    # 阶段门检查
    "check_gate",
    "check_gate_detailed",
    "check_gate_s1_to_s2",
    "check_gate_s2_to_s3",
    "check_gate_s3_to_s4",
    "check_gate_s4_to_s5",
    "check_gate_s5_to_s6",
    "check_gate_s6_to_s7",
    "check_gate_s7_to_s8",
    "check_gate_s8_to_s9",
    # 同步工具
    "_sync_invoice_request_receipt_status",
    "_sync_to_erp_system",
    # 序列化
    "_serialize_project_status_log",
    # 编号生成
    "generate_review_no",
]
