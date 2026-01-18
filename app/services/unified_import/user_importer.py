# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 用户数据导入
"""

from typing import Any, Dict, List, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.services.employee_import_service import import_employees_from_dataframe

from .base import ImportBase


class UserImporter(ImportBase):
    """用户数据导入器"""

    @classmethod
    def import_user_data(
        cls,
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入用户数据（使用员工导入服务）
        """
        try:
            result = import_employees_from_dataframe(db, df, current_user_id)
            return (
                result.get('imported', 0),
                result.get('updated', 0),
                [{"row_index": i + 2, "error": err} for i, err in enumerate(result.get('errors', []))]
            )
        except Exception as e:
            return 0, 0, [{"row_index": 0, "error": str(e)}]
