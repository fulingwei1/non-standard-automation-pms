from inspect import signature
from pathlib import Path

from app.api.v1.endpoints.documents import crud_refactored


def test_documents_module_exposes_multipart_upload_endpoint():
    assert hasattr(crud_refactored, "upload_document_file")

    upload_endpoint = crud_refactored.upload_document_file
    params = signature(upload_endpoint).parameters

    assert "file" in params
    assert params["file"].default.__class__.__name__ == "File"
    assert "project_id" in params
    assert params["project_id"].default.__class__.__name__ == "Form"
    assert "description" in params
    assert params["description"].default.__class__.__name__ == "Form"


def test_document_write_endpoints_require_create_permission():
    source = Path("app/api/v1/endpoints/documents/crud_refactored.py").read_text()

    assert '@router.post("/upload"' in source
    assert 'security.require_permission("document:create")' in source

    create_project_start = source.index("def create_project_document")
    create_project_source = source[create_project_start:]

    assert 'security.require_permission("document:create")' in create_project_source
    assert 'security.require_permission("document:read")' not in create_project_source


def test_document_lists_filter_out_demo_file_paths():
    source = Path("app/api/v1/endpoints/documents/crud_refactored.py").read_text()

    assert "def _exclude_demo_file_paths" in source
    assert 'ProjectDocument.file_path.notlike("/demo/%")' in source
    assert source.count("_exclude_demo_file_paths(query)") >= 2
