# -*- coding: utf-8 -*-
"""
BOM 成本检查清单服务（对应手册 Sheet3）

12 项检查：2 项系统自动判定 + 10 项 PM/工程师勾选
  - 历史比价：同物料历史均价对比，偏差>15% 预警
  - 同类项目对比：同类项目 BOM 总成本偏差>10% 预警
  - 其余 10 项：返回 checklist 供 PM 勾选（manual）

实时聚合，不入库。
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem
from app.models.project import Project

logger = logging.getLogger(__name__)


# 12 项检查定义（id / 名称 / 详细说明 / 是否可自动判）
CHECK_ITEMS = [
    {"id": 1, "name": "标准件复用", "desc": "是否优先使用公司标准件库中的型号？非标件是否有充分理由？", "auto": False},
    {"id": 2, "name": "过度选型", "desc": "PLC/传感器/气缸等是否存在性能过剩？能否降一档满足需求？", "auto": False},
    {"id": 3, "name": "国产替代", "desc": "进口件是否有可替代的国产品牌？(继电器/连接器/电源模组)", "auto": False},
    {"id": 4, "name": "BOM数量准确", "desc": "物料数量是否准确？是否有多算/少算？余量是否合理(建议5%以内)？", "auto": False},
    {"id": 5, "name": "历史比价", "desc": "关键物料价格是否与历史项目基线对比？偏差>15%是否有原因？", "auto": True},
    {"id": 6, "name": "合并采购", "desc": "是否有可以与其他在执行项目合并采购的物料？(量大议价)", "auto": False},
    {"id": 7, "name": "供应商报价", "desc": "是否至少获取3家供应商报价？是否选了性价比最优？", "auto": False},
    {"id": 8, "name": "呆料风险", "desc": "非标定制件是否确认不会因客户变更导致呆料？", "auto": False},
    {"id": 9, "name": "线缆/辅材", "desc": "线缆/端子/扎带/标签等辅材是否计入BOM？是否漏算？", "auto": False},
    {"id": 10, "name": "包装运输", "desc": "包装材料/木箱/泡沫是否计入？运输方式确认？", "auto": False},
    {"id": 11, "name": "调试耗材", "desc": "调试阶段需要的假负载/测试样品/工装夹具是否计入？", "auto": False},
    {"id": 12, "name": "与同类项目对比", "desc": "BOM总成本与历史同类项目偏差是否<10%？偏差原因？", "auto": True},
]


class BomCostCheckService:
    """BOM 成本检查清单（手册 Sheet3）"""

    def __init__(self, db: Session):
        self.db = db

    def get_check(self, project_id: int) -> Dict[str, Any]:
        """生成项目的 BOM 成本检查清单。"""
        project = (
            self.db.query(Project).filter(Project.id == project_id).first()
        )
        if not project:
            return {"error": "项目不存在", "project_id": project_id}

        # 取项目最新 BOM
        bom = self._get_latest_bom(project_id)
        if not bom:
            return {
                "project_id": project_id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                "has_bom": False,
                "message": "项目无 BOM，请先创建 BOM 后再检查",
                "items": [],
            }

        items = []
        for cfg in CHECK_ITEMS:
            if cfg["auto"]:
                if cfg["id"] == 5:
                    result = self._check_historical_price(project_id, bom.id)
                else:  # id == 12
                    result = self._check_similar_project(
                        project_id, bom, project
                    )
                items.append({**cfg, **result})
            else:
                items.append(
                    {
                        **cfg,
                        "status": "manual",
                        "detail": "请 PM/工程师逐项检查并勾选",
                        "evidence": None,
                    }
                )

        # 汇总
        auto_total = sum(1 for i in items if i.get("auto"))
        auto_failed = sum(1 for i in items if i.get("status") == "auto_failed")
        manual_total = sum(1 for i in items if not i.get("auto"))

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "has_bom": True,
            "bom_total_amount": float(bom.total_amount or 0),
            "bom_item_count": (
                self.db.query(func.count(BomItem.id))
                .filter(BomItem.bom_id == bom.id)
                .scalar()
                or 0
            ),
            "summary": {
                "auto_checked": auto_total,
                "auto_passed": auto_total - auto_failed,
                "auto_failed": auto_failed,
                "manual_pending": manual_total,
            },
            "items": items,
            "generated_at": __import__("datetime").date.today().isoformat(),
        }

    # ================================================================
    # 自动判定1：历史比价（同物料均价对比，偏差>15% 预警）
    # ================================================================

    def _check_historical_price(
        self, project_id: int, bom_id: int
    ) -> Dict[str, Any]:
        """关键物料单价 vs 历史均价，偏差>15% 列出。"""
        # 取本项目 BOM 明细
        current_items = (
            self.db.query(BomItem)
            .filter(BomItem.bom_id == bom_id, BomItem.unit_price > 0)
            .all()
        )
        if not current_items:
            return {
                "status": "manual",
                "detail": "BOM 无有效单价明细，无法比价",
                "evidence": None,
            }

        # 取同物料历史均价（排除本项目）
        current_codes = [i.material_code for i in current_items if i.material_code]
        historical = (
            self.db.query(
                BomItem.material_code,
                func.avg(BomItem.unit_price).label("avg_price"),
                func.count(BomItem.id).label("cnt"),
            )
            .join(BomHeader, BomItem.bom_id == BomHeader.id)
            .filter(
                BomItem.material_code.in_(current_codes),
                BomHeader.project_id != project_id,
                BomItem.unit_price > 0,
            )
            .group_by(BomItem.material_code)
            .all()
        )
        hist_map = {r[0]: (float(r[1]), int(r[2])) for r in historical}

        deviations = []
        for item in current_items:
            if item.material_code in hist_map:
                avg_price, cnt = hist_map[item.material_code]
                current_price = float(item.unit_price or 0)
                if avg_price > 0:
                    dev_pct = (current_price - avg_price) / avg_price * 100
                    if abs(dev_pct) > 15:
                        deviations.append(
                            {
                                "material_code": item.material_code,
                                "material_name": item.material_name,
                                "current_price": round(current_price, 2),
                                "historical_avg": round(avg_price, 2),
                                "deviation_pct": round(dev_pct, 1),
                                "sample_count": cnt,
                            }
                        )

        if not deviations:
            return {
                "status": "auto_passed",
                "detail": f"检查 {len(current_items)} 项物料，无价格偏差>15% 的",
                "evidence": {"checked_count": len(current_items)},
            }
        return {
            "status": "auto_failed",
            "detail": f"{len(deviations)} 项物料价格偏差>15%",
            "evidence": {"deviations": deviations[:10]},
        }

    # ================================================================
    # 自动判定2：与同类项目对比（BOM 总成本偏差>10%）
    # ================================================================

    def _check_similar_project(
        self, project_id: int, bom: BomHeader, project: Project
    ) -> Dict[str, Any]:
        """同类项目（同 product_category）的 BOM 总成本对比。"""
        category = project.product_category
        if not category:
            return {
                "status": "manual",
                "detail": "项目无产品类别，无法找同类对比",
                "evidence": None,
            }

        # 同类项目的 BOM 总成本
        similar = (
            self.db.query(BomHeader.total_amount, Project.project_code)
            .join(Project, BomHeader.project_id == Project.id)
            .filter(
                Project.product_category == category,
                BomHeader.project_id != project_id,
                BomHeader.total_amount > 0,
            )
            .order_by(BomHeader.created_at.desc())
            .limit(10)
            .all()
        )
        if not similar:
            return {
                "status": "manual",
                "detail": f"无同类({category})项目 BOM 可对比",
                "evidence": None,
            }

        amounts = [float(r[0]) for r in similar]
        avg_amount = sum(amounts) / len(amounts)
        current_amount = float(bom.total_amount or 0)

        if avg_amount > 0:
            dev_pct = (current_amount - avg_amount) / avg_amount * 100
        else:
            dev_pct = 0

        if abs(dev_pct) > 10:
            return {
                "status": "auto_failed",
                "detail": (
                    f"BOM 总成本 {current_amount:.0f} vs 同类均价 {avg_amount:.0f}"
                    f"（偏差 {dev_pct:+.1f}%，{len(similar)} 个同类项目）"
                ),
                "evidence": {
                    "current_amount": round(current_amount, 2),
                    "similar_avg": round(avg_amount, 2),
                    "deviation_pct": round(dev_pct, 1),
                    "similar_count": len(similar),
                    "similar_projects": [
                        {"project_code": r[1], "amount": float(r[0])}
                        for r in similar[:5]
                    ],
                },
            }
        return {
            "status": "auto_passed",
            "detail": (
                f"BOM 总成本 {current_amount:.0f} vs 同类均价 {avg_amount:.0f}"
                f"（偏差 {dev_pct:+.1f}%，在 10% 以内）"
            ),
            "evidence": {
                "current_amount": round(current_amount, 2),
                "similar_avg": round(avg_amount, 2),
                "deviation_pct": round(dev_pct, 1),
            },
        }

    # ================================================================
    # 辅助：取项目最新 BOM
    # ================================================================

    def _get_latest_bom(self, project_id: int) -> BomHeader:
        return (
            self.db.query(BomHeader)
            .filter(BomHeader.project_id == project_id)
            .order_by(BomHeader.created_at.desc())
            .first()
        )
