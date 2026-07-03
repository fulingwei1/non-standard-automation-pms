# -*- coding: utf-8 -*-
"""
装配套件 API - 模块化结构
"""

from typing import Any

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.kit_rate import KitRateService

from .alert_rules import router as alert_rules_router
from .bom_attributes import router as bom_attributes_router
from .bom_attributes import smart_recommend_assembly_attrs
from .dashboard import router as dashboard_router
from .kit_analysis import router as kit_analysis_router

# Compatibility exports for unit/integration tests
from .kit_analysis.analysis import execute_kit_analysis
from .kit_rate import router as kit_rate_router
from .material_mapping import router as material_mapping_router
from .scheduling import generate_scheduling_suggestions
from .scheduling import router as scheduling_router
from .shortage_alerts import router as shortage_alerts_router
from .stages import router as stages_router
from .templates import router as templates_router
from .wechat_config import router as wechat_config_router

router = APIRouter()

router.include_router(stages_router)
router.include_router(material_mapping_router)
router.include_router(bom_attributes_router)
router.include_router(
    kit_analysis_router, prefix="/assembly-kit/kit-analysis", tags=["kit_analysis"]
)
router.include_router(shortage_alerts_router)
router.include_router(alert_rules_router)
router.include_router(wechat_config_router)
router.include_router(scheduling_router)
router.include_router(dashboard_router)
router.include_router(templates_router)
router.include_router(kit_rate_router, prefix="/kit-rate", tags=["kit-rate"])


@router.post("/assembly/material-readiness/batch-kit-rate", tags=["material-readiness"])
def get_batch_material_readiness_kit_rate(
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    """Return kit-rate summaries keyed by project id for health-monitor pages."""
    service = KitRateService(db)
    project_ids = payload.get("project_ids") or []
    kit_rates: dict[int, dict[str, Any]] = {}

    for project_id in project_ids:
        try:
            project_id_int = int(project_id)
        except (TypeError, ValueError):
            continue

        try:
            data = service.get_project_kit_rate(project_id_int, calculate_by="quantity")
            kit_rates[project_id_int] = {
                "rate": data.get("kit_rate", 0),
                "status": data.get("kit_status", "unknown"),
                "kit_rate": data.get("kit_rate", 0),
                "kit_status": data.get("kit_status", "unknown"),
                "total_items": data.get("total_items", 0),
                "fulfilled_items": data.get("fulfilled_items", 0),
                "shortage_items": data.get("shortage_items", 0),
                "in_transit_items": data.get("in_transit_items", 0),
            }
        except Exception:
            kit_rates[project_id_int] = {
                "rate": 0,
                "status": "unknown",
                "kit_rate": 0,
                "kit_status": "unknown",
                "total_items": 0,
                "fulfilled_items": 0,
                "shortage_items": 0,
                "in_transit_items": 0,
            }

    return {"kit_rates": kit_rates}

__all__ = [
    "router",
    "execute_kit_analysis",
    "smart_recommend_assembly_attrs",
    "generate_scheduling_suggestions",
]
