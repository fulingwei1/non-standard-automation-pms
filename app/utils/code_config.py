# -*- coding: utf-8 -*-
"""
主数据编码配置模块

定义所有主数据对象的编码规则和常量
"""

# 编码前缀
CODE_PREFIX = {
    'EMPLOYEE': 'EMP',
    'CUSTOMER': 'CUS',
    'MATERIAL': 'MAT',
    'PROJECT': 'PJ',
    'MACHINE': 'PN',  # 用于机台序号
}

# 序号长度
SEQ_LENGTH = {
    'EMPLOYEE': 5,
    'CUSTOMER': 7,
    'MATERIAL': 5,
    'PROJECT': 3,
    'MACHINE': 3,
}

# 物料类别码映射（从类别编码到类别码）
# 类别编码格式：ME-01-01, EL-02-03 等
# 提取第一个部分作为类别码
MATERIAL_CATEGORY_CODES = {
    'ME': '机械件',
    'EL': '电气件',
    'PN': '气动件',
    'ST': '标准件',
    'OT': '其他',
    'TR': '贸易件',  # 扩展支持
}

# 物料类别码验证（允许的类别码）
VALID_MATERIAL_CATEGORY_CODES = set(MATERIAL_CATEGORY_CODES.keys())


def get_material_category_code(category_code: str) -> str:
    """
    从物料分类编码中提取类别码
    
    Args:
        category_code: 分类编码，如 'ME-01-01', 'EL-02-03'
    
    Returns:
        类别码，如 'ME', 'EL'
    
    Example:
        >>> get_material_category_code('ME-01-01')
        'ME'
        >>> get_material_category_code('EL-02-03')
        'EL'
    """
    if not category_code:
        return 'OT'  # 默认其他
    
    # 提取第一个部分（类别码）
    parts = category_code.split('-')
    category_code_part = parts[0].upper()
    
    # 验证类别码是否有效
    if category_code_part in VALID_MATERIAL_CATEGORY_CODES:
        return category_code_part
    
    # 如果不在有效列表中，返回默认值
    return 'OT'


def validate_material_category_code(category_code: str) -> bool:
    """
    验证物料类别码是否有效
    
    Args:
        category_code: 类别码，如 'ME', 'EL'
    
    Returns:
        是否有效
    """
    return category_code.upper() in VALID_MATERIAL_CATEGORY_CODES
