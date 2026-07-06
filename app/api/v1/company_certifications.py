from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import security
from app.models.base import get_db
from app.models.company_certification import CompanyCertification
from app.models.user import User

router = APIRouter(prefix="/company-certifications", tags=["公司资质证书"])


class CertificationBase(BaseModel):
    cert_name: str
    cert_type: str
    cert_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: str = "有效"
    description: Optional[str] = None
    scope: Optional[str] = None


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(CertificationBase):
    pass


class CertificationResponse(CertificationBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CertificationResponse])
def get_certifications(
    db: Session = Depends(get_db),
    _current_user: User = Depends(security.require_permission("presale:manage")),
):
    """获取所有资质证书"""
    return db.query(CompanyCertification).order_by(CompanyCertification.created_at.desc()).all()


@router.get("/{cert_id}", response_model=CertificationResponse)
def get_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(security.require_permission("presale:manage")),
):
    """获取单个资质证书"""
    cert = db.query(CompanyCertification).filter(CompanyCertification.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    return cert


@router.post("/", response_model=CertificationResponse)
def create_certification(
    cert: CertificationCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(security.require_permission("presale:manage")),
):
    """创建资质证书"""
    db_cert = CompanyCertification(**cert.model_dump())
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert


@router.put("/{cert_id}", response_model=CertificationResponse)
def update_certification(
    cert_id: int,
    cert: CertificationUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(security.require_permission("presale:manage")),
):
    """更新资质证书"""
    db_cert = db.query(CompanyCertification).filter(CompanyCertification.id == cert_id).first()
    if not db_cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    for key, value in cert.model_dump().items():
        setattr(db_cert, key, value)

    db.commit()
    db.refresh(db_cert)
    return db_cert


@router.delete("/{cert_id}")
def delete_certification(
    cert_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(security.require_permission("presale:manage")),
):
    """删除资质证书"""
    db_cert = db.query(CompanyCertification).filter(CompanyCertification.id == cert_id).first()
    if not db_cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    db.delete(db_cert)
    db.commit()
    return {"message": "证书已删除"}
