# -*- coding: utf-8 -*-
"""Shared helpers for project cost basis semantics."""

from sqlalchemy import func

from app.models.project import ProjectCost

COST_BASIS_PLAN = "PLAN"
COST_BASIS_ACTUAL = "ACTUAL"


def actual_cost_basis_expr():
    """Treat legacy NULL cost_basis rows as ACTUAL for backwards compatibility."""
    return func.coalesce(func.upper(ProjectCost.cost_basis), COST_BASIS_ACTUAL)


def actual_project_cost_filter():
    return actual_cost_basis_expr() == COST_BASIS_ACTUAL
