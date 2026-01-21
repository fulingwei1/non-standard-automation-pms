# -*- coding: utf-8 -*-
"""
资源分配服务模块

聚合所有资源分配相关的服务，保持向后兼容
"""
from .allocation import allocate_resources
from .base import ResourceAllocationService
from .conflicts import detect_resource_conflicts
from .utils import calculate_overlap_days, calculate_workdays
from .worker import (
    check_worker_availability,
    check_worker_skill,
    find_available_workers,
)
from .workstation import (
    check_workstation_availability,
    find_available_workstations,
)

__all__ = ["ResourceAllocationService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为类方法添加到类中"""
    ResourceAllocationService.check_workstation_availability = classmethod(lambda cls, db, workstation_id, start_date, end_date, exclude_work_order_id=None: check_workstation_availability(db, workstation_id, start_date, end_date, exclude_work_order_id))
    ResourceAllocationService.find_available_workstations = classmethod(lambda cls, db, workshop_id=None, start_date=None, end_date=None, required_capability=None: find_available_workstations(db, workshop_id, start_date, end_date, required_capability))
    ResourceAllocationService.check_worker_availability = classmethod(lambda cls, db, worker_id, start_date, end_date, required_hours=8.0, exclude_allocation_id=None: check_worker_availability(db, worker_id, start_date, end_date, required_hours, exclude_allocation_id))
    ResourceAllocationService.find_available_workers = classmethod(lambda cls, db, workshop_id=None, skill_required=None, start_date=None, end_date=None, min_available_hours=8.0: find_available_workers(db, workshop_id, skill_required, start_date, end_date, min_available_hours))
    ResourceAllocationService.detect_resource_conflicts = classmethod(lambda cls, db, project_id, machine_id, start_date, end_date: detect_resource_conflicts(db, project_id, machine_id, start_date, end_date))
    ResourceAllocationService.allocate_resources = classmethod(lambda cls, db, project_id, machine_id, suggested_start_date, suggested_end_date: allocate_resources(db, project_id, machine_id, suggested_start_date, suggested_end_date))
    ResourceAllocationService._calculate_workdays = classmethod(lambda cls, start_date, end_date: calculate_workdays(start_date, end_date))
    ResourceAllocationService._calculate_overlap_days = classmethod(lambda cls, start1, end1, start2, end2: calculate_overlap_days(start1, end1, start2, end2))
    ResourceAllocationService._check_worker_skill = classmethod(lambda cls, db, worker_id, skill_required: check_worker_skill(db, worker_id, skill_required))

_patch_methods()
