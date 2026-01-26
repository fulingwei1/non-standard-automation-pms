# -*- coding: utf-8 -*-
"""
统一响应格式和验证器使用示例

这个文件展示了如何使用统一响应格式和验证器。
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, field_validator

from app.core.schemas.response import (
    SuccessResponse,
    PaginatedResponse,
    success_response,
    paginated_response,
)
from app.core.schemas.validators import (
    validate_project_code,
    validate_phone,
    validate_email,
    validate_non_empty_string,
    validate_decimal,
    validate_status,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ========== Schema定义示例 ==========

class ProjectCreate(BaseModel):
    """项目创建Schema - 展示验证器使用"""
    code: str
    name: str
    amount: Decimal
    status: str = "ACTIVE"
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """验证项目编码"""
        return validate_project_code(v)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证项目名称"""
        return validate_non_empty_string(
            v,
            field_name="项目名称",
            min_length=2,
            max_length=100
        )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """验证项目金额"""
        return validate_decimal(
            v,
            min_value=Decimal("0"),
            precision=2,
            field_name="项目金额"
        )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证项目状态"""
        return validate_status(
            v,
            allowed_statuses=["ACTIVE", "INACTIVE", "COMPLETED"],
            field_name="项目状态"
        )


class ContactCreate(BaseModel):
    """联系方式创建Schema"""
    phone: Optional[str] = None
    email: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """验证手机号"""
        if v:
            return validate_phone(v)
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """验证邮箱"""
        if v:
            return validate_email(v)
        return v


# ========== API端点示例 ==========

@router.post("/projects", response_model=SuccessResponse)
async def create_project_example(
    project: ProjectCreate,
    db: AsyncSession = Depends(lambda: None)  # 示例，实际需要get_db
):
    """
    创建项目示例
    
    展示：
    1. 使用SuccessResponse作为响应模型
    2. 使用success_response便捷函数
    3. Schema自动验证（通过field_validator）
    """
    # 业务逻辑（示例）
    # project_data = await service.create(project)
    
    # 返回成功响应
    return success_response(
        data={"id": 1, "code": project.code, "name": project.name},
        message="项目创建成功"
    )


@router.get("/projects/{id}", response_model=SuccessResponse)
async def get_project_example(
    id: int,
    db: AsyncSession = Depends(lambda: None)
):
    """
    获取项目示例
    
    展示：
    1. 使用HTTPException处理错误（自动转换为统一格式）
    2. 使用success_response返回成功响应
    """
    # 业务逻辑（示例）
    # project = await service.get(id)
    
    # 模拟项目不存在
    if id > 100:
        raise HTTPException(
            status_code=404,
            detail="项目不存在"
        )
    
    return success_response(
        data={"id": id, "name": "示例项目"},
        message="获取成功"
    )


@router.get("/projects", response_model=PaginatedResponse)
async def list_projects_example(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(lambda: None)
):
    """
    列表查询项目示例
    
    展示：
    1. 使用PaginatedResponse作为响应模型
    2. 使用paginated_response便捷函数
    3. 自动计算pages
    """
    # 业务逻辑（示例）
    # result = await service.list(skip=(page-1)*page_size, limit=page_size, keyword=keyword)
    
    # 模拟数据
    items = [
        {"id": i, "name": f"项目{i}"} 
        for i in range((page-1)*page_size+1, min(page*page_size+1, 101))
    ]
    total = 100
    
    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/contacts", response_model=SuccessResponse)
async def create_contact_example(
    contact: ContactCreate,
    db: AsyncSession = Depends(lambda: None)
):
    """
    创建联系方式示例
    
    展示：
    1. 可选字段的验证
    2. 多个验证器的使用
    """
    # 至少提供一个联系方式
    if not contact.phone and not contact.email:
        raise HTTPException(
            status_code=400,
            detail="至少需要提供一个联系方式（手机号或邮箱）"
        )
    
    return success_response(
        data={"phone": contact.phone, "email": contact.email},
        message="联系方式创建成功"
    )


# ========== 验证器直接使用示例 ==========

def example_validate_in_service():
    """
    在Service层直接使用验证器（不推荐，应该在Schema中验证）
    
    仅用于特殊情况，如动态验证
    """
    try:
        code = validate_project_code("PJ250101001")
        print(f"验证通过：{code}")
    except ValueError as e:
        print(f"验证失败：{e}")


if __name__ == "__main__":
    # 测试验证器
    print("=== 验证器测试 ===")
    
    # 测试项目编码
    try:
        code = validate_project_code("PJ250101001")
        print(f"✅ 项目编码验证通过：{code}")
    except ValueError as e:
        print(f"❌ 项目编码验证失败：{e}")
    
    # 测试手机号
    try:
        phone = validate_phone("13800138000")
        print(f"✅ 手机号验证通过：{phone}")
    except ValueError as e:
        print(f"❌ 手机号验证失败：{e}")
    
    # 测试邮箱
    try:
        email = validate_email("test@example.com")
        print(f"✅ 邮箱验证通过：{email}")
    except ValueError as e:
        print(f"❌ 邮箱验证失败：{e}")
