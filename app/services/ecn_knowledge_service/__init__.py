# -*- coding: utf-8 -*-
"""
ECN知识库服务模块

聚合所有ECN知识库相关的服务，保持向后兼容
"""
from typing import TYPE_CHECKING

from .base import EcnKnowledgeService
from .similarity import find_similar_ecns
from .solution_extraction import extract_solution
from .template import (
    apply_solution_template,
    create_solution_template,
    recommend_solutions,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

__all__ = ["EcnKnowledgeService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    EcnKnowledgeService.extract_solution = lambda self, ecn_id, auto_extract=True: extract_solution(self, ecn_id, auto_extract)
    EcnKnowledgeService.find_similar_ecns = lambda self, ecn_id, top_n=5, min_similarity=0.3: find_similar_ecns(self, ecn_id, top_n, min_similarity)
    EcnKnowledgeService.recommend_solutions = lambda self, ecn_id, top_n=5: recommend_solutions(self, ecn_id, top_n)
    EcnKnowledgeService.create_solution_template = lambda self, ecn_id, template_data, created_by: create_solution_template(self, ecn_id, template_data, created_by)
    EcnKnowledgeService.apply_solution_template = lambda self, ecn_id, template_id: apply_solution_template(self, ecn_id, template_id)

_patch_methods()
