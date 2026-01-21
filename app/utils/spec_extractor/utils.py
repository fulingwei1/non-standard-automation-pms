# -*- coding: utf-8 -*-
"""
技术规格要求提取器 - 工具函数
"""
import re
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.technical_spec import TechnicalSpecRequirement


def extract_key_parameters(specification: str) -> Dict[str, Any]:
    """
    从规格描述中提取关键参数

    Args:
        specification: 规格描述文本

    Returns:
        提取的关键参数字典
    """
    params = {}

    # 提取电压（如：220V, 24V, 12VDC等）
    voltage_patterns = [
        r'(\d+(?:\.\d+)?)\s*V(?:DC|AC)?',
        r'(\d+(?:\.\d+)?)\s*伏',
    ]
    for pattern in voltage_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['voltage'] = match.group(1)
            break

    # 提取电流（如：5A, 10mA, 0.5A等）
    current_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:m|u)?A',
        r'(\d+(?:\.\d+)?)\s*安',
    ]
    for pattern in current_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['current'] = match.group(1)
            break

    # 提取精度（如：±0.1%, ±2℃, ±0.01mm等）
    accuracy_patterns = [
        r'[±\+\-](\d+(?:\.\d+)?)\s*%',
        r'[±\+\-](\d+(?:\.\d+)?)\s*℃',
        r'[±\+\-](\d+(?:\.\d+)?)\s*mm',
        r'精度[：:]\s*[±\+\-]?(\d+(?:\.\d+)?)',
    ]
    for pattern in accuracy_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['accuracy'] = match.group(1)
            break

    # 提取温度范围（如：-20~60℃, 0-50℃等）
    temp_patterns = [
        r'(-?\d+(?:\.\d+)?)\s*[~\-]\s*(\d+(?:\.\d+)?)\s*℃',
        r'温度[：:]\s*(-?\d+(?:\.\d+)?)\s*[~\-]\s*(\d+(?:\.\d+)?)',
    ]
    for pattern in temp_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['temp_min'] = match.group(1)
            params['temp_max'] = match.group(2)
            break

    # 提取功率（如：100W, 1.5kW等）
    power_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:m|k)?W',
        r'(\d+(?:\.\d+)?)\s*瓦',
    ]
    for pattern in power_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['power'] = match.group(1)
            break

    # 提取频率（如：50Hz, 60Hz等）
    freq_patterns = [
        r'(\d+(?:\.\d+)?)\s*Hz',
        r'(\d+(?:\.\d+)?)\s*赫兹',
    ]
    for pattern in freq_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            params['frequency'] = match.group(1)
            break

    # 提取尺寸（如：100x200x50mm, 直径50mm等）
    size_patterns = [
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm',
        r'直径[：:]\s*(\d+(?:\.\d+)?)\s*mm',
    ]
    for pattern in size_patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3:
                params['length'] = match.group(1)
                params['width'] = match.group(2)
                params['height'] = match.group(3)
            else:
                params['diameter'] = match.group(1)
            break

    return params


def create_requirement(
    service: "SpecExtractor",
    db: Session,
    project_id: int,
    document_id: Optional[int],
    material_name: str,
    specification: str,
    extracted_by: int,
    material_code: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    requirement_level: str = "REQUIRED",
    remark: Optional[str] = None
) -> TechnicalSpecRequirement:
    """
    创建规格要求记录

    Args:
        service: SpecExtractor实例
        db: 数据库会话
        project_id: 项目ID
        document_id: 文档ID
        material_name: 物料名称
        specification: 规格型号
        extracted_by: 提取人ID
        material_code: 物料编码
        brand: 品牌
        model: 型号
        requirement_level: 要求级别
        remark: 备注

    Returns:
        创建的规格要求对象
    """
    # 提取关键参数
    key_parameters = extract_key_parameters(specification)

    # 创建规格要求
    requirement = TechnicalSpecRequirement(
        project_id=project_id,
        document_id=document_id,
        material_code=material_code,
        material_name=material_name,
        specification=specification,
        brand=brand,
        model=model,
        key_parameters=key_parameters if key_parameters else None,
        requirement_level=requirement_level,
        remark=remark,
        extracted_by=extracted_by
    )

    db.add(requirement)
    db.flush()

    return requirement
