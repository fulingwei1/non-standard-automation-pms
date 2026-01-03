from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.project import ProjectDocument, Project
from app.schemas.project import ProjectDocumentCreate, ProjectDocumentResponse

router = APIRouter()


@router.get("/", response_model=List[ProjectDocumentResponse])
def read_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
) -> Any:
    """
    Retrieve document records.
    """
    query = db.query(ProjectDocument)
    if project_id:
        query = query.filter(ProjectDocument.project_id == project_id)

    documents = (
        query.order_by(desc(ProjectDocument.created_at)).offset(skip).limit(limit).all()
    )
    return documents


@router.post("/", response_model=ProjectDocumentResponse)
def create_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_in: ProjectDocumentCreate,
) -> Any:
    """
    Create new document record.
    """
    project = db.query(Project).filter(Project.id == doc_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    document = ProjectDocument(**doc_in.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{doc_id}", response_model=ProjectDocumentResponse)
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
) -> Any:
    """
    Delete a document record.
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document record not found")

    db.delete(document)
    db.commit()
    return document
