import importlib
import sys
from enum import Enum
from types import ModuleType


def test_service_record_photo_normalizes_legacy_string_payload(monkeypatch):
    models_pkg = ModuleType("app.models")
    models_pkg.__path__ = []
    service_pkg = ModuleType("app.models.service")
    service_pkg.__path__ = []
    enums_mod = ModuleType("app.models.service.enums")

    class ServiceTicketStatusEnum(str, Enum):
        OPEN = "OPEN"

    class ServiceRecordStatusEnum(str, Enum):
        SCHEDULED = "SCHEDULED"

    class SurveyStatusEnum(str, Enum):
        DRAFT = "DRAFT"

    class KnowledgeBaseStatusEnum(str, Enum):
        DRAFT = "DRAFT"

    def _normalize(value):
        return value

    enums_mod.ServiceTicketStatusEnum = ServiceTicketStatusEnum
    enums_mod.ServiceRecordStatusEnum = ServiceRecordStatusEnum
    enums_mod.SurveyStatusEnum = SurveyStatusEnum
    enums_mod.KnowledgeBaseStatusEnum = KnowledgeBaseStatusEnum
    enums_mod.normalize_service_ticket_status = _normalize
    enums_mod.normalize_service_record_status = _normalize
    enums_mod.normalize_survey_status = _normalize
    enums_mod.normalize_knowledge_base_status = _normalize

    monkeypatch.setitem(sys.modules, "app.models", models_pkg)
    monkeypatch.setitem(sys.modules, "app.models.service", service_pkg)
    monkeypatch.setitem(sys.modules, "app.models.service.enums", enums_mod)
    sys.modules.pop("app.schemas.service", None)

    service_schema = importlib.import_module("app.schemas.service")
    photo = service_schema.ServiceRecordPhoto.model_validate("/uploads/service/photo-1.png")
    raw = {"url": "/uploads/service/photo-2.png", "filename": "photo-2.png"}
    normalized = service_schema.ServiceRecordPhoto.normalize_legacy_payload(raw)

    assert photo.url == "/uploads/service/photo-1.png"
    assert photo.filename == "photo-1.png"
    assert normalized == raw
