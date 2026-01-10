# -*- coding: utf-8 -*-
"""
优势产品管理 API 端点
"""

import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.api import deps
from app.models.advantage_product import AdvantageProduct, AdvantageProductCategory, DEFAULT_CATEGORIES
from app.schemas.advantage_product import (
    AdvantageProductCategoryCreate,
    AdvantageProductCategoryUpdate,
    AdvantageProductCategoryResponse,
    AdvantageProductCreate,
    AdvantageProductUpdate,
    AdvantageProductResponse,
    AdvantageProductSimple,
    AdvantageProductGrouped,
    AdvantageProductImportResult,
    ProductMatchCheckRequest,
    ProductMatchCheckResponse
)

router = APIRouter()


# ==================== 产品类别 API ====================

@router.get("/categories", response_model=List[AdvantageProductCategoryResponse])
def get_categories(
    include_inactive: bool = Query(False, description="是否包含已禁用的类别"),
    db: Session = Depends(deps.get_db)
):
    """获取所有产品类别"""
    query = db.query(AdvantageProductCategory)
    if not include_inactive:
        query = query.filter(AdvantageProductCategory.is_active == True)

    categories = query.order_by(AdvantageProductCategory.sort_order).all()

    # 统计每个类别的产品数量
    result = []
    for cat in categories:
        product_count = db.query(func.count(AdvantageProduct.id)).filter(
            AdvantageProduct.category_id == cat.id,
            AdvantageProduct.is_active == True
        ).scalar()

        cat_dict = {
            "id": cat.id,
            "code": cat.code,
            "name": cat.name,
            "description": cat.description,
            "sort_order": cat.sort_order,
            "is_active": cat.is_active,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "product_count": product_count
        }
        result.append(AdvantageProductCategoryResponse(**cat_dict))

    return result


@router.post("/categories", response_model=AdvantageProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: AdvantageProductCategoryCreate,
    db: Session = Depends(deps.get_db)
):
    """创建产品类别"""
    # 检查编码是否已存在
    existing = db.query(AdvantageProductCategory).filter(
        AdvantageProductCategory.code == category_in.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"类别编码 '{category_in.code}' 已存在"
        )

    category = AdvantageProductCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    return AdvantageProductCategoryResponse(
        **{**category.__dict__, "product_count": 0}
    )


@router.put("/categories/{category_id}", response_model=AdvantageProductCategoryResponse)
def update_category(
    category_id: int,
    category_in: AdvantageProductCategoryUpdate,
    db: Session = Depends(deps.get_db)
):
    """更新产品类别"""
    category = db.query(AdvantageProductCategory).filter(
        AdvantageProductCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="类别不存在"
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    product_count = db.query(func.count(AdvantageProduct.id)).filter(
        AdvantageProduct.category_id == category.id,
        AdvantageProduct.is_active == True
    ).scalar()

    return AdvantageProductCategoryResponse(
        **{**category.__dict__, "product_count": product_count}
    )


# ==================== 优势产品 API ====================

@router.get("", response_model=List[AdvantageProductResponse])
def get_products(
    category_id: Optional[int] = Query(None, description="按类别筛选"),
    search: Optional[str] = Query(None, description="搜索产品名称或编码"),
    include_inactive: bool = Query(False, description="是否包含已禁用的产品"),
    db: Session = Depends(deps.get_db)
):
    """获取优势产品列表"""
    query = db.query(AdvantageProduct)

    if not include_inactive:
        query = query.filter(AdvantageProduct.is_active == True)

    if category_id:
        query = query.filter(AdvantageProduct.category_id == category_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AdvantageProduct.product_name.like(search_pattern),
                AdvantageProduct.product_code.like(search_pattern)
            )
        )

    products = query.order_by(AdvantageProduct.product_code).all()

    # 获取类别名称映射
    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    result = []
    for p in products:
        result.append(AdvantageProductResponse(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            series_code=p.series_code,
            description=p.description,
            is_active=p.is_active,
            category_name=categories.get(p.category_id),
            created_at=p.created_at,
            updated_at=p.updated_at
        ))

    return result


@router.get("/grouped", response_model=List[AdvantageProductGrouped])
def get_products_grouped(
    include_inactive: bool = Query(False, description="是否包含已禁用的"),
    db: Session = Depends(deps.get_db)
):
    """获取按类别分组的产品列表"""
    # 获取所有类别
    cat_query = db.query(AdvantageProductCategory)
    if not include_inactive:
        cat_query = cat_query.filter(AdvantageProductCategory.is_active == True)
    categories = cat_query.order_by(AdvantageProductCategory.sort_order).all()

    result = []
    for cat in categories:
        # 获取该类别下的产品
        prod_query = db.query(AdvantageProduct).filter(
            AdvantageProduct.category_id == cat.id
        )
        if not include_inactive:
            prod_query = prod_query.filter(AdvantageProduct.is_active == True)
        products = prod_query.order_by(AdvantageProduct.product_code).all()

        product_count = len(products)

        cat_response = AdvantageProductCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            product_count=product_count
        )

        prod_responses = [
            AdvantageProductResponse(
                id=p.id,
                product_code=p.product_code,
                product_name=p.product_name,
                category_id=p.category_id,
                series_code=p.series_code,
                description=p.description,
                is_active=p.is_active,
                category_name=cat.name,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in products
        ]

        result.append(AdvantageProductGrouped(
            category=cat_response,
            products=prod_responses
        ))

    return result


@router.get("/simple", response_model=List[AdvantageProductSimple])
def get_products_simple(
    category_id: Optional[int] = Query(None, description="按类别筛选"),
    db: Session = Depends(deps.get_db)
):
    """获取产品简略列表（用于下拉选择）"""
    query = db.query(AdvantageProduct).filter(AdvantageProduct.is_active == True)

    if category_id:
        query = query.filter(AdvantageProduct.category_id == category_id)

    products = query.order_by(AdvantageProduct.product_code).all()

    # 获取类别名称映射
    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    return [
        AdvantageProductSimple(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            category_name=categories.get(p.category_id)
        )
        for p in products
    ]


@router.post("", response_model=AdvantageProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: AdvantageProductCreate,
    db: Session = Depends(deps.get_db)
):
    """创建优势产品"""
    # 检查产品编码是否已存在
    existing = db.query(AdvantageProduct).filter(
        AdvantageProduct.product_code == product_in.product_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产品编码 '{product_in.product_code}' 已存在"
        )

    # 检查类别是否存在
    if product_in.category_id:
        category = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product_in.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的类别不存在"
            )

    product = AdvantageProduct(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    category_name = None
    if product.category_id:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product.category_id
        ).first()
        category_name = cat.name if cat else None

    return AdvantageProductResponse(
        id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        category_id=product.category_id,
        series_code=product.series_code,
        description=product.description,
        is_active=product.is_active,
        category_name=category_name,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/{product_id}", response_model=AdvantageProductResponse)
def update_product(
    product_id: int,
    product_in: AdvantageProductUpdate,
    db: Session = Depends(deps.get_db)
):
    """更新优势产品"""
    product = db.query(AdvantageProduct).filter(
        AdvantageProduct.id == product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )

    update_data = product_in.model_dump(exclude_unset=True)

    # 检查类别是否存在
    if "category_id" in update_data and update_data["category_id"]:
        category = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == update_data["category_id"]
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的类别不存在"
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    category_name = None
    if product.category_id:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product.category_id
        ).first()
        category_name = cat.name if cat else None

    return AdvantageProductResponse(
        id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        category_id=product.category_id,
        series_code=product.series_code,
        description=product.description,
        is_active=product.is_active,
        category_name=category_name,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(deps.get_db)
):
    """删除优势产品（软删除）"""
    product = db.query(AdvantageProduct).filter(
        AdvantageProduct.id == product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )

    product.is_active = False
    db.commit()


# ==================== Excel 导入 ====================

@router.post("/import", response_model=AdvantageProductImportResult)
async def import_from_excel(
    file: UploadFile = File(..., description="Excel 文件"),
    clear_existing: bool = Query(True, description="是否先清空现有数据"),
    db: Session = Depends(deps.get_db)
):
    """从 Excel 文件导入优势产品"""
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器未安装 pandas 库"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传 Excel 文件 (.xlsx 或 .xls)"
        )

    errors = []
    categories_created = 0
    products_created = 0
    products_updated = 0
    products_skipped = 0

    try:
        # 读取 Excel 文件
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), header=None)

        # 类别映射（列索引 -> 类别信息）
        COLUMN_CATEGORY_MAP = {
            0: {"code": "HOME_APPLIANCE", "name": "白色家电"},
            1: {"code": "AUTOMOTIVE", "name": "汽车电子"},
            2: {"code": "NEW_ENERGY", "name": "新能源"},
            3: {"code": "SEMICONDUCTOR", "name": "半导体"},
            4: {"code": "POWER_TOOLS", "name": "电动工具"},
            5: {"code": "AUTOMATION_LINE", "name": "自动化线体"},
            6: {"code": "OTHER_EQUIPMENT", "name": "其他设备"},
            7: {"code": "EDUCATION", "name": "教育实训"}
        }

        if clear_existing:
            # 清空现有产品（硬删除）
            db.query(AdvantageProduct).delete()
            db.query(AdvantageProductCategory).delete()
            db.commit()

        # 确保类别存在
        category_id_map = {}
        for col_idx, cat_info in COLUMN_CATEGORY_MAP.items():
            existing_cat = db.query(AdvantageProductCategory).filter(
                AdvantageProductCategory.code == cat_info["code"]
            ).first()

            if not existing_cat:
                new_cat = AdvantageProductCategory(
                    code=cat_info["code"],
                    name=cat_info["name"],
                    sort_order=col_idx + 1,
                    is_active=True
                )
                db.add(new_cat)
                db.flush()
                category_id_map[col_idx] = new_cat.id
                categories_created += 1
            else:
                category_id_map[col_idx] = existing_cat.id

        # 处理每一列（每列是一个类别）
        for col_idx in range(min(len(df.columns), 8)):
            category_id = category_id_map.get(col_idx)
            if not category_id:
                continue

            current_series = None

            for row_idx, cell_value in enumerate(df.iloc[:, col_idx]):
                if pd.isna(cell_value) or str(cell_value).strip() == "":
                    continue

                cell_str = str(cell_value).strip()

                # 检查是否是系列编号（纯编号如 KC2700）
                if cell_str.startswith("KC") and len(cell_str) <= 10 and cell_str[2:].isdigit():
                    current_series = cell_str
                    continue

                # 解析产品编码和名称
                # 格式可能是 "KC2701离线双工位FCT" 或 "离线双工位FCT"
                product_code = None
                product_name = cell_str

                if cell_str.startswith("KC"):
                    # 尝试提取编码
                    for i in range(6, len(cell_str)):
                        if not cell_str[i].isdigit():
                            product_code = cell_str[:i]
                            product_name = cell_str[i:]
                            break
                    if not product_code:
                        product_code = cell_str
                        product_name = cell_str
                else:
                    # 没有编码，使用系列+行号生成
                    if current_series:
                        product_code = f"{current_series}_{row_idx}"
                    else:
                        product_code = f"PRD_{col_idx}_{row_idx}"

                # 检查产品是否已存在
                existing = db.query(AdvantageProduct).filter(
                    AdvantageProduct.product_code == product_code
                ).first()

                if existing:
                    if clear_existing:
                        # 更新
                        existing.product_name = product_name
                        existing.category_id = category_id
                        existing.series_code = current_series
                        existing.is_active = True
                        products_updated += 1
                    else:
                        products_skipped += 1
                else:
                    # 新建
                    new_product = AdvantageProduct(
                        product_code=product_code,
                        product_name=product_name,
                        category_id=category_id,
                        series_code=current_series,
                        is_active=True
                    )
                    db.add(new_product)
                    products_created += 1

        db.commit()

        return AdvantageProductImportResult(
            success=True,
            categories_created=categories_created,
            products_created=products_created,
            products_updated=products_updated,
            products_skipped=products_skipped,
            errors=errors,
            message=f"导入成功：创建 {categories_created} 个类别，{products_created} 个产品"
        )

    except Exception as e:
        db.rollback()
        errors.append(str(e))
        return AdvantageProductImportResult(
            success=False,
            categories_created=0,
            products_created=0,
            products_updated=0,
            products_skipped=0,
            errors=errors,
            message=f"导入失败：{str(e)}"
        )


# ==================== 产品匹配检查 ====================

@router.post("/check-match", response_model=ProductMatchCheckResponse)
def check_product_match(
    request: ProductMatchCheckRequest,
    db: Session = Depends(deps.get_db)
):
    """检查产品名称是否匹配优势产品"""
    product_name = request.product_name.strip()

    if not product_name:
        return ProductMatchCheckResponse(
            match_type="UNKNOWN",
            matched_product=None,
            suggestions=[]
        )

    # 精确匹配
    exact_match = db.query(AdvantageProduct).filter(
        AdvantageProduct.is_active == True,
        AdvantageProduct.product_name == product_name
    ).first()

    if exact_match:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == exact_match.category_id
        ).first()
        return ProductMatchCheckResponse(
            match_type="ADVANTAGE",
            matched_product=AdvantageProductSimple(
                id=exact_match.id,
                product_code=exact_match.product_code,
                product_name=exact_match.product_name,
                category_id=exact_match.category_id,
                category_name=cat.name if cat else None
            ),
            suggestions=[]
        )

    # 模糊匹配 - 查找相似产品
    search_pattern = f"%{product_name}%"
    similar_products = db.query(AdvantageProduct).filter(
        AdvantageProduct.is_active == True,
        or_(
            AdvantageProduct.product_name.like(search_pattern),
            AdvantageProduct.product_code.like(search_pattern)
        )
    ).limit(5).all()

    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    suggestions = [
        AdvantageProductSimple(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            category_name=categories.get(p.category_id)
        )
        for p in similar_products
    ]

    if suggestions:
        return ProductMatchCheckResponse(
            match_type="ADVANTAGE",  # 有相似产品，可能是优势产品
            matched_product=None,
            suggestions=suggestions
        )

    # 没有匹配，视为新产品
    return ProductMatchCheckResponse(
        match_type="NEW",
        matched_product=None,
        suggestions=[]
    )
