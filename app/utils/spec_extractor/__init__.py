# -*- coding: utf-8 -*-
"""
技术规格要求提取器模块

聚合所有技术规格要求提取相关的服务，保持向后兼容
"""
from .base import SpecExtractor
from .extraction import auto_extract_from_file, extract_from_document
from .formats import extract_from_excel, extract_from_pdf, extract_from_word
from .utils import create_requirement, extract_key_parameters

__all__ = ["SpecExtractor"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    SpecExtractor.extract_from_document = lambda self, db, document_id, project_id, extracted_by, auto_extract=False: extract_from_document(self, db, document_id, project_id, extracted_by, auto_extract)
    SpecExtractor._auto_extract_from_file = lambda self, db, document, project_id, extracted_by: auto_extract_from_file(self, db, document, project_id, extracted_by)
    SpecExtractor._extract_from_excel = lambda self, db, file_path, project_id, document_id, extracted_by: extract_from_excel(self, db, file_path, project_id, document_id, extracted_by)
    SpecExtractor._extract_from_word = lambda self, db, file_path, project_id, document_id, extracted_by: extract_from_word(self, db, file_path, project_id, document_id, extracted_by)
    SpecExtractor._extract_from_pdf = lambda self, db, file_path, project_id, document_id, extracted_by: extract_from_pdf(self, db, file_path, project_id, document_id, extracted_by)
    SpecExtractor.extract_key_parameters = lambda self, specification: extract_key_parameters(specification)
    SpecExtractor.create_requirement = lambda self, db, project_id, document_id, material_name, specification, extracted_by, material_code=None, brand=None, model=None, requirement_level="REQUIRED", remark=None: create_requirement(self, db, project_id, document_id, material_name, specification, extracted_by, material_code, brand, model, requirement_level, remark)

_patch_methods()
