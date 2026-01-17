# -*- coding: utf-8 -*-
"""
优势产品导入服务
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models.advantage_product import AdvantageProduct, AdvantageProductCategory

# 类别映射（列索引 -> 类别信息）
COLUMN_CATEGORY_MAP = {
    0: {"code": "HOME_APPLIANCE", "name": "白色家电"},
    1: {"code": "AUTOMOTIVE", "name": "汽车电子"},
    2: {"code": "NEW_ENERGY", "name": "新能源"},
    3: {"code": "SEMICONDUCTOR", "name": "半导体"},
    4: {"code": "POWER_TOOLS", "name": "电动工具"},
    5: {"code": "AUTOMATION_LINE", "name": "自动化线体"},
    6: {"code": "OTHER_EQUIPMENT", "name": "其他设备"},
    7: {"code": "EDUCATION", "name": "教育实训"}
}


def clear_existing_data(db: Session) -> None:
    """
    清空现有产品数据
    """
    db.query(AdvantageProduct).delete()
    db.query(AdvantageProductCategory).delete()
    db.commit()


def ensure_categories_exist(
    db: Session,
    clear_existing: bool
) -> Tuple[Dict[int, int], int]:
    """
    确保类别存在

    Returns:
        Tuple[Dict[int, int], int]: (列索引到类别ID的映射, 创建的类别数量)
    """
    category_id_map = {}
    categories_created = 0

    if clear_existing:
        clear_existing_data(db)

    existing_categories = {c.code: c.id for c in db.query(AdvantageProductCategory).all()}

    for col_idx, cat_info in COLUMN_CATEGORY_MAP.items():
        if cat_info["code"] in existing_categories:
            category_id_map[col_idx] = existing_categories[cat_info["code"]]
        else:
            new_cat = AdvantageProductCategory(
                code=cat_info["code"],
                name=cat_info["name"],
                sort_order=col_idx + 1,
                is_active=True
            )
            db.add(new_cat)
            db.flush()
            category_id_map[col_idx] = new_cat.id
            categories_created += 1

    return category_id_map, categories_created


def parse_product_from_cell(
    cell_str: str,
    current_series: Optional[str],
    row_idx: int,
    col_idx: int
) -> Tuple[Optional[str], str]:
    """
    从单元格解析产品编码和名称

    Returns:
        Tuple[Optional[str], str]: (产品编码, 产品名称)
    """
    # 检查是否是系列编号（纯编号如 KC2700）
    if cell_str.startswith("KC") and len(cell_str) <= 10 and cell_str[2:].isdigit():
        return None, cell_str  # 返回系列编号，产品编码为None

    product_code = None
    product_name = cell_str

    if cell_str.startswith("KC"):
        # 尝试提取编码
        for i in range(6, len(cell_str)):
            if not cell_str[i].isdigit():
                product_code = cell_str[:i]
                product_name = cell_str[i:]
                break
        if not product_code:
            product_code = cell_str
            product_name = cell_str
    else:
        # 没有编码，使用系列+行号生成
        if current_series:
            product_code = f"{current_series}_{row_idx}"
        else:
            product_code = f"PRD_{col_idx}_{row_idx}"

    return product_code, product_name


def process_product_row(
    db: Session,
    product_code: str,
    product_name: str,
    category_id: int,
    current_series: Optional[str],
    clear_existing: bool
) -> Tuple[bool, bool, bool]:
    """
    处理单行产品数据

    Returns:
        Tuple[bool, bool, bool]: (是否创建, 是否更新, 是否跳过)
    """
    existing = db.query(AdvantageProduct).filter(
        AdvantageProduct.product_code == product_code
    ).first()

    if existing:
        if clear_existing:
            existing.product_name = product_name
            existing.category_id = category_id
            existing.series_code = current_series
            existing.is_active = True
            return False, True, False
        else:
            return False, False, True
    else:
        new_product = AdvantageProduct(
            product_code=product_code,
            product_name=product_name,
            category_id=category_id,
            series_code=current_series,
            is_active=True
        )
        db.add(new_product)
        return True, False, False
