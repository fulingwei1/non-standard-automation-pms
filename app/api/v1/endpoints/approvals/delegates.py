# -*- coding: utf-8 -*-
"""
审批代理人管理 API
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.approval import ApprovalDelegate
from app.schemas.approval.task import DelegateCreate, DelegateResponse, DelegateUpdate
from app.services.approval_engine import ApprovalDelegateService
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("", response_model=list[DelegateResponse])
def list_my_delegates(
    include_inactive: bool = Query(False, description="是否包含已失效的配置"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取我的代理人配置列表

    返回当前用户设置的所有代理人配置（作为原审批人）
    """
    service = ApprovalDelegateService(db)
    delegates = service.get_user_delegates(
        user_id=current_user.id,
        include_inactive=include_inactive,
    )

    result = []
    for d in delegates:
        item = DelegateResponse(
            id=d.id,
            user_id=d.user_id,
            delegate_id=d.delegate_id,
            delegate_name=d.delegate.name if d.delegate else None,
            scope=d.scope,
            template_ids=d.template_ids,
            categories=d.categories,
            start_date=d.start_date.isoformat(),
            end_date=d.end_date.isoformat(),
            is_active=d.is_active,
            reason=d.reason,
            notify_original=d.notify_original,
            notify_delegate=d.notify_delegate,
            created_at=d.created_at,
        )
        result.append(item)

    return result


@router.get("/delegated-to-me", response_model=list[DelegateResponse])
def list_delegated_to_me(
    include_inactive: bool = Query(False, description="是否包含已失效的配置"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取委托给我的配置列表

    返回其他用户委托给当前用户的所有代理配置
    """
    service = ApprovalDelegateService(db)
    delegates = service.get_delegated_to_user(
        delegate_id=current_user.id,
        include_inactive=include_inactive,
    )

    result = []
    for d in delegates:
        item = DelegateResponse(
            id=d.id,
            user_id=d.user_id,
            delegate_id=d.delegate_id,
            delegate_name=d.delegate.name if d.delegate else None,
            scope=d.scope,
            template_ids=d.template_ids,
            categories=d.categories,
            start_date=d.start_date.isoformat(),
            end_date=d.end_date.isoformat(),
            is_active=d.is_active,
            reason=d.reason,
            notify_original=d.notify_original,
            notify_delegate=d.notify_delegate,
            created_at=d.created_at,
        )
        result.append(item)

    return result


@router.post("", response_model=DelegateResponse)
def create_delegate(
    data: DelegateCreate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    创建代理人配置

    设置审批代理人，在指定时间段内由代理人处理审批
    """
    service = ApprovalDelegateService(db)

    try:
        start_date = date.fromisoformat(data.start_date)
        end_date = date.fromisoformat(data.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    try:
        delegate = service.create_delegate(
            user_id=current_user.id,
            delegate_id=data.delegate_id,
            start_date=start_date,
            end_date=end_date,
            scope=data.scope,
            template_ids=data.template_ids,
            categories=data.categories,
            reason=data.reason,
            notify_original=data.notify_original,
            notify_delegate=data.notify_delegate,
            created_by=current_user.id,
        )

        db.commit()

        return DelegateResponse(
            id=delegate.id,
            user_id=delegate.user_id,
            delegate_id=delegate.delegate_id,
            delegate_name=delegate.delegate.name if delegate.delegate else None,
            scope=delegate.scope,
            template_ids=delegate.template_ids,
            categories=delegate.categories,
            start_date=delegate.start_date.isoformat(),
            end_date=delegate.end_date.isoformat(),
            is_active=delegate.is_active,
            reason=delegate.reason,
            notify_original=delegate.notify_original,
            notify_delegate=delegate.notify_delegate,
            created_at=delegate.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{delegate_id}", response_model=DelegateResponse)
def update_delegate(
    delegate_id: int,
    data: DelegateUpdate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """更新代理人配置"""
    delegate = get_or_404(db, ApprovalDelegate, delegate_id, "配置不存在")

    if delegate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此配置")

    service = ApprovalDelegateService(db)

    # 处理日期
    update_data = data.model_dump(exclude_unset=True)
    if "start_date" in update_data:
        try:
            update_data["start_date"] = date.fromisoformat(update_data["start_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误")
    if "end_date" in update_data:
        try:
            update_data["end_date"] = date.fromisoformat(update_data["end_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误")

    delegate = service.update_delegate(delegate_id, **update_data)
    db.commit()

    return DelegateResponse(
        id=delegate.id,
        user_id=delegate.user_id,
        delegate_id=delegate.delegate_id,
        delegate_name=delegate.delegate.name if delegate.delegate else None,
        scope=delegate.scope,
        template_ids=delegate.template_ids,
        categories=delegate.categories,
        start_date=delegate.start_date.isoformat(),
        end_date=delegate.end_date.isoformat(),
        is_active=delegate.is_active,
        reason=delegate.reason,
        notify_original=delegate.notify_original,
        notify_delegate=delegate.notify_delegate,
        created_at=delegate.created_at,
    )


@router.delete("/{delegate_id}")
def cancel_delegate(
    delegate_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """取消代理人配置"""
    delegate = get_or_404(db, ApprovalDelegate, delegate_id, "配置不存在")

    if delegate.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权取消此配置")

    service = ApprovalDelegateService(db)
    success = service.cancel_delegate(delegate_id)
    db.commit()

    if success:
        return {"message": "取消成功"}
    else:
        return {"message": "取消失败"}


@router.get("/active")
def get_active_delegate(
    template_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    获取当前生效的代理人

    检查当前用户是否有生效的代理人配置
    """
    service = ApprovalDelegateService(db)
    delegate = service.get_active_delegate(
        user_id=current_user.id,
        template_id=template_id,
    )

    if delegate:
        return {
            "has_delegate": True,
            "delegate_id": delegate.delegate_id,
            "delegate_name": delegate.delegate.name if delegate.delegate else None,
            "start_date": delegate.start_date.isoformat(),
            "end_date": delegate.end_date.isoformat(),
            "reason": delegate.reason,
        }
    else:
        return {"has_delegate": False}
