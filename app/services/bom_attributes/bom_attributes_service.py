# -*- coding: utf-8 -*-
"""
BOM装配属性服务类
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models import (
    AssemblyStage,
    AssemblyTemplate,
    BomHeader,
    BomItem,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    Material,
    MaterialCategory,
)
from app.schemas.assembly_kit import BomItemAssemblyAttrsResponse
from app.utils.db_helpers import get_or_404


class BomAttributesService:
    """BOM装配属性业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_bom_assembly_attrs(
        self,
        bom_id: int,
        stage_code: Optional[str] = None,
        is_blocking: Optional[bool] = None
    ) -> List[BomItemAssemblyAttrsResponse]:
        """获取BOM装配属性列表"""
        # 验证BOM存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        query = self.db.query(BomItemAssemblyAttrs).filter(BomItemAssemblyAttrs.bom_id == bom_id)
        if stage_code:
            query = query.filter(BomItemAssemblyAttrs.assembly_stage == stage_code)
        if is_blocking is not None:
            query = query.filter(BomItemAssemblyAttrs.is_blocking == is_blocking)

        attrs = query.order_by(BomItemAssemblyAttrs.assembly_stage, BomItemAssemblyAttrs.stage_order).all()

        # 关联物料信息
        result = []
        for attr in attrs:
            data = BomItemAssemblyAttrsResponse.model_validate(attr)
            bom_item = self.db.query(BomItem).filter(BomItem.id == attr.bom_item_id).first()
            if bom_item:
                material = self.db.query(Material).filter(Material.id == bom_item.material_id).first()
                if material:
                    data.material_code = material.material_code
                    data.material_name = material.material_name
                data.required_qty = bom_item.quantity
            stage = self.db.query(AssemblyStage).filter(AssemblyStage.stage_code == attr.assembly_stage).first()
            if stage:
                data.stage_name = stage.stage_name
            result.append(data)

        return result

    def batch_set_assembly_attrs(
        self,
        bom_id: int,
        items: List[Any]
    ) -> Dict[str, int]:
        """批量设置BOM装配属性"""
        # 验证BOM存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        created_count = 0
        updated_count = 0

        for item in items:
            if item.bom_id != bom_id:
                continue

            existing = self.db.query(BomItemAssemblyAttrs).filter(
                BomItemAssemblyAttrs.bom_item_id == item.bom_item_id
            ).first()

            if existing:
                # 更新
                for key, value in item.model_dump().items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.now()
                updated_count += 1
            else:
                # 创建
                attr = BomItemAssemblyAttrs(**item.model_dump())
                self.db.add(attr)
                created_count += 1

        self.db.commit()

        return {"created": created_count, "updated": updated_count}

    def update_assembly_attr(
        self,
        attr_id: int,
        update_data: Dict[str, Any]
    ) -> BomItemAssemblyAttrsResponse:
        """更新单个物料装配属性"""
        attr = get_or_404(self.db, BomItemAssemblyAttrs, attr_id, "装配属性不存在")

        for key, value in update_data.items():
            setattr(attr, key, value)
        attr.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(attr)

        return BomItemAssemblyAttrsResponse.model_validate(attr)

    def auto_assign_assembly_attrs(
        self,
        bom_id: int,
        overwrite: bool = False
    ) -> Dict[str, int]:
        """自动分配装配属性（基于物料分类映射）"""
        # 验证BOM存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        # 获取BOM明细
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id == bom_id).all()

        assigned_count = 0
        skipped_count = 0

        for bom_item in bom_items:
            # 检查是否已有配置
            existing = self.db.query(BomItemAssemblyAttrs).filter(
                BomItemAssemblyAttrs.bom_item_id == bom_item.id
            ).first()

            if existing and not overwrite:
                skipped_count += 1
                continue

            # 获取物料分类
            material = self.db.query(Material).filter(Material.id == bom_item.material_id).first()
            if not material or not material.category_id:
                skipped_count += 1
                continue

            # 获取映射配置
            mapping = self.db.query(CategoryStageMapping).filter(
                CategoryStageMapping.category_id == material.category_id
            ).first()

            if not mapping:
                # 使用默认阶段
                stage_code = "MECH"
                is_blocking = True
                can_postpone = False
            else:
                stage_code = mapping.stage_code
                is_blocking = mapping.is_blocking
                can_postpone = mapping.can_postpone

            if existing:
                existing.assembly_stage = stage_code
                existing.is_blocking = is_blocking
                existing.can_postpone = can_postpone
                existing.updated_at = datetime.now()
            else:
                attr = BomItemAssemblyAttrs(
                    bom_item_id=bom_item.id,
                    bom_id=bom_id,
                    assembly_stage=stage_code,
                    importance_level="NORMAL",
                    is_blocking=is_blocking,
                    can_postpone=can_postpone
                )
                self.db.add(attr)

            assigned_count += 1

        self.db.commit()

        return {"assigned": assigned_count, "skipped": skipped_count}

    def get_assembly_attr_recommendations(
        self,
        bom_id: int
    ) -> Dict[str, Any]:
        """获取装配属性推荐结果（不应用，仅返回推荐）"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        # 验证BOM存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        # 获取BOM明细
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id == bom_id).all()

        # 批量推荐
        recommendations = AssemblyAttrRecommender.batch_recommend(self.db, bom_id, bom_items)

        # 构建响应
        result = []
        for bom_item in bom_items:
            material = self.db.query(Material).filter(Material.id == bom_item.material_id).first()
            if not material:
                continue

            rec = recommendations.get(bom_item.id)
            if rec:
                result.append({
                    "bom_item_id": bom_item.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "recommended_stage": rec.stage_code,
                    "recommended_blocking": rec.is_blocking,
                    "recommended_postpone": rec.can_postpone,
                    "recommended_importance": rec.importance_level,
                    "confidence": rec.confidence,
                    "source": rec.source,
                    "reason": rec.reason
                })

        return {"recommendations": result, "total": len(result)}

    def smart_recommend_assembly_attrs(
        self,
        bom_id: int,
        overwrite: bool = False,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """智能推荐装配属性（多级推荐规则）"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender

        # 验证BOM存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        # 获取BOM明细
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id == bom_id).all()

        # 批量推荐
        recommendations = AssemblyAttrRecommender.batch_recommend(self.db, bom_id, bom_items)

        assigned_count = 0
        skipped_count = 0
        recommendation_stats = {
            "HISTORY": 0,
            "CATEGORY": 0,
            "KEYWORD": 0,
            "SUPPLIER": 0,
            "DEFAULT": 0
        }

        for bom_item in bom_items:
            # 检查是否已有配置
            existing = self.db.query(BomItemAssemblyAttrs).filter(
                BomItemAssemblyAttrs.bom_item_id == bom_item.id
            ).first()

            if existing and not overwrite:
                skipped_count += 1
                continue

            # 获取推荐结果
            rec = recommendations.get(bom_item.id)
            if not rec:
                skipped_count += 1
                continue

            # 统计推荐来源
            recommendation_stats[rec.source] = recommendation_stats.get(rec.source, 0) + 1

            if existing:
                existing.assembly_stage = rec.stage_code
                existing.is_blocking = rec.is_blocking
                existing.can_postpone = rec.can_postpone
                existing.importance_level = rec.importance_level
                existing.setting_source = rec.source
                existing.updated_at = datetime.now()
            else:
                attr_data = {
                    "bom_item_id": bom_item.id,
                    "bom_id": bom_id,
                    "assembly_stage": rec.stage_code,
                    "importance_level": rec.importance_level,
                    "is_blocking": rec.is_blocking,
                    "can_postpone": rec.can_postpone,
                    "setting_source": rec.source,
                }
                if user_id:
                    attr_data["created_by"] = user_id

                attr = BomItemAssemblyAttrs(**attr_data)
                self.db.add(attr)

            assigned_count += 1

        self.db.commit()

        return {
            "assigned": assigned_count,
            "skipped": skipped_count,
            "recommendation_stats": recommendation_stats
        }

    def apply_assembly_template(
        self,
        bom_id: int,
        template_id: int,
        overwrite: bool = False
    ) -> Dict[str, int]:
        """套用装配模板"""
        from fastapi import HTTPException

        # 验证BOM和模板存在
        bom = get_or_404(self.db, BomHeader, bom_id, "BOM不存在")

        template = self.db.query(AssemblyTemplate).filter(AssemblyTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        if not template.stage_config:
            raise HTTPException(status_code=400, detail="模板配置为空")

        # 解析模板配置并应用
        # stage_config格式: {"category_code": {"stage": "MECH", "blocking": true, "postpone": false}}
        stage_config = template.stage_config

        bom_items = self.db.query(BomItem).filter(BomItem.bom_id == bom_id).all()
        applied_count = 0

        for bom_item in bom_items:
            material = self.db.query(Material).filter(Material.id == bom_item.material_id).first()
            if not material:
                continue

            # 查找模板中匹配的配置
            config = None
            if material.category_id:
                category = self.db.query(MaterialCategory).filter(MaterialCategory.id == material.category_id).first()
                if category and category.category_code in stage_config:
                    config = stage_config[category.category_code]

            if not config:
                continue

            existing = self.db.query(BomItemAssemblyAttrs).filter(
                BomItemAssemblyAttrs.bom_item_id == bom_item.id
            ).first()

            if existing and not overwrite:
                continue

            if existing:
                existing.assembly_stage = config.get("stage", "MECH")
                existing.is_blocking = config.get("blocking", True)
                existing.can_postpone = config.get("postpone", False)
                existing.updated_at = datetime.now()
            else:
                attr = BomItemAssemblyAttrs(
                    bom_item_id=bom_item.id,
                    bom_id=bom_id,
                    assembly_stage=config.get("stage", "MECH"),
                    importance_level="NORMAL",
                    is_blocking=config.get("blocking", True),
                    can_postpone=config.get("postpone", False)
                )
                self.db.add(attr)

            applied_count += 1

        self.db.commit()

        return {"applied": applied_count}
