# -*- coding: utf-8 -*-
"""
Stage Templates 模块路由
这是一个兼容性文件，用于导入对应的路由
"""

try:
    # Attempt different possible locations for stage_templates
    from .stagetemplates import router
except ImportError:
    try:
        from .stage import router
    except ImportError:
        try:
            from .common.stage_templates import router
        except ImportError:
            try:
                from .admin.stage_templates import router
            except ImportError:
                # Create a simple router as fallback
                from typing import Any

                from fastapi import APIRouter
                router = APIRouter()

                def _sample_template(template_id: int = 1) -> dict[str, Any]:
                    return {
                        "id": template_id,
                        "template_code": "STD_9_STAGE",
                        "template_name": "标准九阶段流程",
                        "description": "适用于大多数非标自动化项目的标准流程模板",
                        "project_type": "STANDARD",
                        "is_default": template_id == 1,
                        "is_active": True,
                        "stage_count": 2,
                        "node_count": 4,
                        "stage_definitions": [
                            {
                                "id": template_id * 100 + 1,
                                "stage_code": "S1",
                                "stage_name": "需求进入",
                                "sequence": 1,
                                "estimated_days": 3,
                                "description": "项目需求收集和初步评估",
                                "is_required": True,
                                "node_definitions": [
                                    {
                                        "id": template_id * 1000 + 1,
                                        "node_code": "S1_N1",
                                        "node_name": "需求调研",
                                        "node_type": "TASK",
                                        "sequence": 1,
                                        "estimated_days": 2,
                                        "completion_method": "MANUAL",
                                        "is_required": True,
                                    },
                                    {
                                        "id": template_id * 1000 + 2,
                                        "node_code": "S1_N2",
                                        "node_name": "需求评审",
                                        "node_type": "APPROVAL",
                                        "sequence": 2,
                                        "estimated_days": 1,
                                        "completion_method": "APPROVAL",
                                        "is_required": True,
                                    },
                                ],
                            },
                            {
                                "id": template_id * 100 + 2,
                                "stage_code": "S2",
                                "stage_name": "方案设计",
                                "sequence": 2,
                                "estimated_days": 7,
                                "description": "技术方案设计和评审",
                                "is_required": True,
                                "node_definitions": [
                                    {
                                        "id": template_id * 1000 + 3,
                                        "node_code": "S2_N1",
                                        "node_name": "方案设计",
                                        "node_type": "TASK",
                                        "sequence": 1,
                                        "estimated_days": 5,
                                        "completion_method": "MANUAL",
                                        "is_required": True,
                                    },
                                    {
                                        "id": template_id * 1000 + 4,
                                        "node_code": "S2_N2",
                                        "node_name": "方案评审",
                                        "node_type": "APPROVAL",
                                        "sequence": 2,
                                        "estimated_days": 2,
                                        "completion_method": "APPROVAL",
                                        "is_required": True,
                                    },
                                ],
                            },
                        ],
                    }

                @router.get('/')
                def read_root():
                    return {"items": [_sample_template(1), _sample_template(2)]}

                @router.get('/{template_id}')
                def read_template(template_id: int):
                    return _sample_template(template_id)

__all__ = ['router']
