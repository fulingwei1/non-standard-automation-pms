# -*- coding: utf-8 -*-
"""
Project machine service built on the shared BaseCRUDService.
"""

from __future__ import annotations

from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.common.crud import BaseCRUDService, SortOrder
from app.common.crud.exceptions import raise_already_exists, raise_not_found
from app.models.material import BomHeader
from app.models.project import Machine
from app.schemas.project import MachineCreate, MachineResponse, MachineUpdate
from app.services.machine_service import (
    MachineService,
    ProjectAggregationService,
    VALID_HEALTH,
    VALID_STAGES,
)


class ProjectMachineService(
    BaseCRUDService[Machine, MachineCreate, MachineUpdate, MachineResponse]
):
    """Project-scoped machine service."""

    search_fields: Sequence[str] = ("machine_name", "machine_code", "specification")
    allowed_sort_fields: Sequence[str] = (
        "created_at",
        "planned_start_date",
        "planned_end_date",
        "progress_pct",
        "machine_no",
    )
    default_sort_field: str = "created_at"
    default_sort_order: SortOrder = SortOrder.DESC
    soft_delete_field: Optional[str] = None

    def __init__(self, db: Session, project_id: int):
        super().__init__(
            model=Machine,
            db=db,
            response_schema=MachineResponse,
            resource_name="机台",
            default_filters={"project_id": project_id},
        )
        self.project_id = project_id
        self._machine_service = MachineService(db)
        self._aggregation_service = ProjectAggregationService(db)

    # ------------------------------------------------------------------ #
    # Overrides
    # ------------------------------------------------------------------ #
    def get(
        self,
        object_id: int,
        *,
        load_relationships: Optional[Sequence[str]] = None,
    ) -> MachineResponse:
        db_obj = self._get_object_or_404(object_id, load_relationships)
        return self._to_response(db_obj)

    def delete(
        self,
        object_id: int,
        *,
        soft_delete: Optional[bool] = None,
    ) -> bool:
        machine = self._get_object_or_404(object_id)
        self._ensure_can_delete(machine.id)
        return super().delete(object_id, soft_delete=soft_delete)

    def _before_create(self, obj_in: MachineCreate) -> MachineCreate:
        payload = obj_in.model_copy(update={"project_id": self.project_id})

        if payload.machine_code:
            self._ensure_unique_code(payload.machine_code)
            if not payload.machine_no:
                payload.machine_no = 1
        else:
            machine_code, machine_no = self._machine_service.generate_machine_code(self.project_id)
            payload.machine_code = machine_code
            payload.machine_no = payload.machine_no or machine_no

        self._validate_stage(getattr(payload, "stage", None))
        self._validate_health(getattr(payload, "health", None))

        return payload

    def _after_create(self, db_obj: Machine) -> Machine:
        self._aggregation_service.update_project_aggregation(self.project_id)
        return db_obj

    def _before_update(
        self,
        object_id: int,
        obj_in: MachineUpdate,
        db_obj: Machine,
    ) -> MachineUpdate:
        if db_obj.project_id != self.project_id:
            raise_not_found(self.resource_name, object_id)

        update_data = obj_in.model_dump(exclude_unset=True)

        if "machine_code" in update_data and update_data["machine_code"]:
            self._ensure_unique_code(update_data["machine_code"], current_id=object_id)

        if "stage" in update_data:
            new_stage = update_data["stage"]
            self._validate_stage(new_stage, current_stage=db_obj.stage)

        if "health" in update_data:
            new_health = update_data["health"]
            self._validate_health(new_health)

        return obj_in

    def _after_update(self, db_obj: Machine) -> Machine:
        self._aggregation_service.update_project_aggregation(self.project_id)
        return db_obj

    def _after_delete(self, object_id: int) -> None:
        self._aggregation_service.update_project_aggregation(self.project_id)
        return None

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _get_object_or_404(
        self,
        object_id: int,
        load_relationships: Optional[Sequence[str]] = None,
    ) -> Machine:
        db_obj = self.repository.get(object_id, load_relationships=load_relationships)
        if not db_obj or db_obj.project_id != self.project_id:
            raise_not_found(self.resource_name, object_id)
        return db_obj

    def _ensure_unique_code(self, machine_code: str, current_id: Optional[int] = None) -> None:
        query = self.db.query(Machine).filter(
            Machine.project_id == self.project_id,
            Machine.machine_code == machine_code,
        )
        if current_id:
            query = query.filter(Machine.id != current_id)

        if query.first():
            raise_already_exists(self.resource_name, "machine_code", machine_code)

    def _validate_stage(self, stage: Optional[str], current_stage: Optional[str] = None) -> None:
        if stage is None:
            return
        if stage not in VALID_STAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的阶段值: {stage}，有效值为 S1-S9",
            )

        if current_stage:
            is_valid, error_msg = self._machine_service.validate_stage_transition(current_stage, stage)
            if not is_valid:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    def _validate_health(self, health: Optional[str]) -> None:
        if health is None:
            return
        if health not in VALID_HEALTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的健康度: {health}，有效值为 H1-H4",
            )

    def _ensure_can_delete(self, machine_id: int) -> None:
        bom_count = (
            self.db.query(BomHeader)
            .filter(BomHeader.machine_id == machine_id)
            .count()
        )
        if bom_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。",
            )
