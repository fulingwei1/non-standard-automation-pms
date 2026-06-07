# -*- coding: utf-8 -*-
"""Response serializers for technical specification endpoints."""

from app.schemas.technical_spec import TechnicalSpecRequirementResponse

DEFAULT_REQUIREMENT_LEVEL = "REQUIRED"


def serialize_requirement(requirement) -> TechnicalSpecRequirementResponse:
    return TechnicalSpecRequirementResponse(
        id=requirement.id,
        project_id=requirement.project_id,
        document_id=requirement.document_id,
        material_code=requirement.material_code,
        material_name=requirement.material_name,
        specification=requirement.specification,
        brand=requirement.brand,
        model=requirement.model,
        key_parameters=requirement.key_parameters,
        requirement_level=requirement.requirement_level or DEFAULT_REQUIREMENT_LEVEL,
        remark=requirement.remark,
        extracted_by=requirement.extracted_by,
        extracted_by_name=requirement.extractor.name if requirement.extractor else None,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
    )
