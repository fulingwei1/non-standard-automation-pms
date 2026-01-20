# -*- coding: utf-8 -*-
"""
简易快速开发模板（简化流程）

TPL_QUICK - 简易快速开发（简单新产品）
"""

from typing import Any, Dict

# 简易快速开发模板（简化流程）
QUICK_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_QUICK",
    "template_name": "简易快速开发",
    "description": "适用于简单新产品或小型改造项目，精简流程快速交付",
    "project_type": "SIMPLE",
    "stages": [
        {
            "stage_code": "Q1",
            "stage_name": "立项启动",
            "sequence": 0,
            "estimated_days": 3,
            "description": "快速立项和需求确认",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q1N01",
                    "node_name": "需求确认",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "确认客户需求",
                },
                {
                    "node_code": "Q1N02",
                    "node_name": "快速方案",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制简易技术方案",
                    "dependency_node_codes": ["Q1N01"],
                },
            ]
        },
        {
            "stage_code": "Q2",
            "stage_name": "物料准备",
            "sequence": 1,
            "estimated_days": 14,
            "description": "物料采购和准备",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q2N01",
                    "node_name": "BOM编制",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "编制物料清单",
                },
                {
                    "node_code": "Q2N02",
                    "node_name": "采购下单",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "采购物料下单",
                    "dependency_node_codes": ["Q2N01"],
                },
                {
                    "node_code": "Q2N03",
                    "node_name": "物���齐套",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 12,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "物料到齐确认",
                    "dependency_node_codes": ["Q2N02"],
                },
            ]
        },
        {
            "stage_code": "Q3",
            "stage_name": "生产装配",
            "sequence": 2,
            "estimated_days": 10,
            "description": "生产装配和调试",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q3N01",
                    "node_name": "装配组装",
                    "node_type": "TASK",
                    "sequence": 0,
                    "estimated_days": 5,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备装配",
                },
                {
                    "node_code": "Q3N02",
                    "node_name": "调试测试",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 3,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "设备调试",
                    "dependency_node_codes": ["Q3N01"],
                },
                {
                    "node_code": "Q3N03",
                    "node_name": "内部检验",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "内部质量检验",
                    "dependency_node_codes": ["Q3N02"],
                },
            ]
        },
        {
            "stage_code": "Q4",
            "stage_name": "验收交付",
            "sequence": 3,
            "estimated_days": 5,
            "description": "客户验收和交付",
            "is_required": True,
            "nodes": [
                {
                    "node_code": "Q4N01",
                    "node_name": "客户验收",
                    "node_type": "APPROVAL",
                    "sequence": 0,
                    "estimated_days": 2,
                    "completion_method": "APPROVAL",
                    "is_required": True,
                    "description": "客户验收确认",
                },
                {
                    "node_code": "Q4N02",
                    "node_name": "发货交付",
                    "node_type": "TASK",
                    "sequence": 1,
                    "estimated_days": 2,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "发货并交付",
                    "dependency_node_codes": ["Q4N01"],
                },
                {
                    "node_code": "Q4N03",
                    "node_name": "项目结项",
                    "node_type": "TASK",
                    "sequence": 2,
                    "estimated_days": 1,
                    "completion_method": "MANUAL",
                    "is_required": True,
                    "description": "项目结项归档",
                    "dependency_node_codes": ["Q4N02"],
                },
            ]
        },
    ]
}
