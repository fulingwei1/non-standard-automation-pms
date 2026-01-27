# -*- coding: utf-8 -*-
"""
验收服务模块
"""

from app.services.acceptance.report_utils import (
    build_report_content,
    generate_report_no,
    get_report_version,
    save_report_file,
)

__all__ = [
    "generate_report_no",
    "get_report_version",
    "save_report_file",
    "build_report_content",
]
