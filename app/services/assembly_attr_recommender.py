# -*- coding: utf-8 -*-
"""
BOM装配属性智能推荐服务
实现多级推荐规则：历史数据匹配、分类匹配、关键词匹配、供应商类型推断
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import (
    BomItem,
    BomItemAssemblyAttrs,
    CategoryStageMapping,
    Material,
    Vendor,
)


class AssemblyAttrRecommendation:
    """装配属性推荐结果"""
    def __init__(
        self,
        stage_code: str,
        is_blocking: bool,
        can_postpone: bool,
        importance_level: str = "NORMAL",
        confidence: float = 0.0,
        source: str = "UNKNOWN",
        reason: str = ""
    ):
        self.stage_code = stage_code
        self.is_blocking = is_blocking
        self.can_postpone = can_postpone
        self.importance_level = importance_level
        self.confidence = confidence  # 置信度 0-100
        self.source = source  # 推荐来源
        self.reason = reason  # 推荐原因


class AssemblyAttrRecommender:
    """装配属性智能推荐器"""

    # 关键词到装配阶段的映射规则
    KEYWORD_STAGE_MAPPING = {
        'FRAME': ['框架', '铝型材', '钣金', '底座', '机架', '骨架', '型材', '角件', '连接件'],
        'MECH': ['模组', '气缸', '电机', '导轨', '丝杆', '轴承', '联轴器', '减速机', '直线', '滑台'],
        'ELECTRIC': ['伺服', '步进', '驱动器', '传感器', '开关', '继电器', '接触器', 'PLC', '变频器'],
        'WIRING': ['线缆', '线槽', '扎带', '端子', '接线', '电缆', '线束', '号码管', '标签'],
        'DEBUG': ['工装', '治具', '夹具', '测试', '样品', '调试', '定位'],
        'COSMETIC': ['铭牌', '标牌', '盖板', '防护', '亚克力', '警示', '标识牌']
    }

    # 供应商类型到物料类别的推断规则
    SUPPLIER_TYPE_MAPPING = {
        'MACHINING': {'stage': 'MECH', 'blocking': True},  # 机加件 -> 机械模组
        'SHEET_METAL': {'stage': 'FRAME', 'blocking': True},  # 钣金件 -> 框架
        'ELECTRIC': {'stage': 'ELECTRIC', 'blocking': True},  # 电气件 -> 电气安装
        'STANDARD': {'stage': 'MECH', 'blocking': False},  # 标准件 -> 机械模组，可后补
        'TRADE': {'stage': 'MECH', 'blocking': False},  # 贸易商 -> 通常可后补
        'MATERIAL': {'stage': 'MECH', 'blocking': True},  # 物料供应商 -> 机械模组
        'OUTSOURCE': {'stage': 'MECH', 'blocking': True},  # 外协供应商 -> 机械模组
    }

    @classmethod
    def recommend(
        cls,
        db: Session,
        bom_item: BomItem,
        material: Material,
        current_bom_id: int
    ) -> Optional[AssemblyAttrRecommendation]:
        """
        智能推荐装配属性

        推荐规则优先级（按置信度）：
        1. 历史数据匹配（95%）
        2. 物料分类匹配（90%）
        3. 关键词匹配（70%）
        4. 供应商类型推断（60%）
        """
        recommendations = []

        # 1. 历史数据匹配（置信度95%）
        history_rec = cls._match_from_history(db, material.id, current_bom_id)
        if history_rec:
            recommendations.append(history_rec)

        # 2. 物料分类匹配（置信度90%）
        category_rec = cls._match_from_category(db, material)
        if category_rec:
            recommendations.append(category_rec)

        # 3. 关键词匹配（置信度70%）
        keyword_rec = cls._match_from_keywords(material)
        if keyword_rec:
            recommendations.append(keyword_rec)

        # 4. 供应商类型推断（置信度60%）
        supplier_rec = cls._infer_from_supplier(db, material)
        if supplier_rec:
            recommendations.append(supplier_rec)

        # 选择置信度最高的推荐
        if recommendations:
            best_rec = max(recommendations, key=lambda r: r.confidence)
            return best_rec

        # 默认推荐
        return AssemblyAttrRecommendation(
            stage_code="MECH",
            is_blocking=True,
            can_postpone=False,
            importance_level="NORMAL",
            confidence=0.0,
            source="DEFAULT",
            reason="无匹配规则，使用默认配置"
        )

    @classmethod
    def _match_from_history(
        cls,
        db: Session,
        material_id: int,
        current_bom_id: int
    ) -> Optional[AssemblyAttrRecommendation]:
        """
        历史数据匹配：查找相同物料在其他项目中的装配属性设置

        置信度：95%
        """
        # 查找相同物料在其他BOM中的装配属性
        # 排除当前BOM
        history_attrs = db.query(BomItemAssemblyAttrs).join(
            BomItem, BomItemAssemblyAttrs.bom_item_id == BomItem.id
        ).filter(
            BomItem.material_id == material_id,
            BomItemAssemblyAttrs.bom_id != current_bom_id,
            BomItemAssemblyAttrs.confirmed  # 只考虑已确认的配置
        ).all()

        if not history_attrs:
            return None

        # 统计最常用的配置
        stage_counts = {}
        blocking_counts = {}
        postpone_counts = {}
        importance_counts = {}

        for attr in history_attrs:
            stage = attr.assembly_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            blocking_counts[stage] = blocking_counts.get(stage, [0, 0])
            blocking_counts[stage][1 if attr.is_blocking else 0] += 1
            postpone_counts[stage] = postpone_counts.get(stage, [0, 0])
            postpone_counts[stage][1 if attr.can_postpone else 0] += 1
            importance_counts[stage] = importance_counts.get(stage, {})
            importance_counts[stage][attr.importance_level] = importance_counts[stage].get(attr.importance_level, 0) + 1

        # 选择使用次数最多的阶段
        if not stage_counts:
            return None

        best_stage = max(stage_counts.items(), key=lambda x: x[1])[0]
        total_count = stage_counts[best_stage]

        # 确定阻塞性和可后补性（多数决定）
        is_blocking = blocking_counts[best_stage][1] > blocking_counts[best_stage][0]
        can_postpone = postpone_counts[best_stage][1] > postpone_counts[best_stage][0]

        # 确定重要程度（多数决定）
        importance_level = max(
            importance_counts[best_stage].items(),
            key=lambda x: x[1]
        )[0] if importance_counts[best_stage] else "NORMAL"

        # 置信度根据使用次数调整（使用3次以上为95%，否则降低）
        confidence = 95.0 if total_count >= 3 else 85.0 + (total_count - 1) * 5.0

        return AssemblyAttrRecommendation(
            stage_code=best_stage,
            is_blocking=is_blocking,
            can_postpone=can_postpone,
            importance_level=importance_level,
            confidence=confidence,
            source="HISTORY",
            reason=f"历史数据匹配：相同物料在{total_count}个其他项目中使用此配置"
        )

    @classmethod
    def _match_from_category(
        cls,
        db: Session,
        material: Material
    ) -> Optional[AssemblyAttrRecommendation]:
        """
        物料分类匹配：根据物料分类的默认配置

        置信度：90%
        """
        if not material.category_id:
            return None

        mapping = db.query(CategoryStageMapping).filter(
            CategoryStageMapping.category_id == material.category_id,
            CategoryStageMapping.is_active
        ).first()

        if not mapping:
            return None

        return AssemblyAttrRecommendation(
            stage_code=mapping.stage_code,
            is_blocking=mapping.is_blocking,
            can_postpone=mapping.can_postpone,
            importance_level=mapping.importance_level or "NORMAL",
            confidence=90.0,
            source="CATEGORY",
            reason=f"物料分类匹配：{material.category.name if material.category else '未知分类'}"
        )

    @classmethod
    def _match_from_keywords(
        cls,
        material: Material
    ) -> Optional[AssemblyAttrRecommendation]:
        """
        关键词匹配：根据物料名称中的关键词推断

        置信度：70%
        """
        if not material.material_name:
            return None

        material_name_lower = material.material_name.lower()

        # 检查每个阶段的关键词
        matched_stages = []
        for stage_code, keywords in cls.KEYWORD_STAGE_MAPPING.items():
            for keyword in keywords:
                if keyword in material_name_lower:
                    matched_stages.append(stage_code)
                    break

        if not matched_stages:
            return None

        # 选择第一个匹配的阶段（可以优化为选择匹配度最高的）
        stage_code = matched_stages[0]

        # 根据阶段设置默认的阻塞性和可后补性
        blocking_defaults = {
            'FRAME': True,
            'MECH': True,
            'ELECTRIC': True,
            'WIRING': False,
            'DEBUG': False,
            'COSMETIC': False
        }

        postpone_defaults = {
            'FRAME': False,
            'MECH': False,
            'ELECTRIC': False,
            'WIRING': True,
            'DEBUG': True,
            'COSMETIC': True
        }

        matched_keywords = [
            kw for kw in cls.KEYWORD_STAGE_MAPPING[stage_code]
            if kw in material_name_lower
        ]

        return AssemblyAttrRecommendation(
            stage_code=stage_code,
            is_blocking=blocking_defaults.get(stage_code, True),
            can_postpone=postpone_defaults.get(stage_code, False),
            importance_level="NORMAL",
            confidence=70.0,
            source="KEYWORD",
            reason=f"关键词匹配：物料名称包含关键词 '{', '.join(matched_keywords[:2])}'"
        )

    @classmethod
    def _infer_from_supplier(
        cls,
        db: Session,
        material: Material
    ) -> Optional[AssemblyAttrRecommendation]:
        """
        供应商类型推断：根据供应商类型推断物料类别

        置信度：60%
        """
        if not material.default_supplier_id:
            return None

        supplier = db.query(Vendor).filter(
            Vendor.id == material.default_supplier_id,
            Vendor.vendor_type == 'MATERIAL'
        ).first()

        if not supplier or not supplier.supplier_type:
            return None

        mapping = cls.SUPPLIER_TYPE_MAPPING.get(supplier.supplier_type)
        if not mapping:
            return None

        return AssemblyAttrRecommendation(
            stage_code=mapping['stage'],
            is_blocking=mapping['blocking'],
            can_postpone=not mapping['blocking'],
            importance_level="NORMAL",
            confidence=60.0,
            source="SUPPLIER",
            reason=f"供应商类型推断：供应商类型为 {supplier.supplier_type}"
        )

    @classmethod
    def batch_recommend(
        cls,
        db: Session,
        bom_id: int,
        bom_items: List[BomItem]
    ) -> Dict[int, AssemblyAttrRecommendation]:
        """
        批量推荐装配属性

        返回: {bom_item_id: recommendation}
        """
        recommendations = {}

        for bom_item in bom_items:
            material = db.query(Material).filter(
                Material.id == bom_item.material_id
            ).first()

            if not material:
                continue

            rec = cls.recommend(db, bom_item, material, bom_id)
            if rec:
                recommendations[bom_item.id] = rec

        return recommendations
