# -*- coding: utf-8 -*-
"""
质量管理服务

包含质量检验、SPC分析、质量预警、返工管理等核心功能
"""
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models.alert import AlertRecord, AlertRule
from app.models.material import Material
from app.models.production import (
    DefectAnalysis,
    QualityAlertRule,
    QualityInspection,
    ReworkOrder,
)
from app.schemas.production.quality import (
    DefectAnalysisCreate,
    ParetoDataPoint,
    QualityInspectionCreate,
    QualityTrendDataPoint,
    SPCControlLimits,
    SPCDataPoint,
)
from app.utils.db_helpers import save_obj


class QualityService:
    """质量管理服务类"""

    @staticmethod
    def create_inspection(
        db: Session, 
        inspection_data: QualityInspectionCreate, 
        current_user_id: int
    ) -> QualityInspection:
        """
        创建质检记录
        
        Args:
            db: 数据库会话
            inspection_data: 质检数据
            current_user_id: 当前用户ID
            
        Returns:
            QualityInspection: 创建的质检记录
        """
        # 生成质检单号
        inspection_no = QualityService._generate_inspection_no(db)
        
        # 计算不良率
        defect_rate = 0.0
        if inspection_data.inspection_qty > 0:
            defect_rate = (inspection_data.defect_qty / inspection_data.inspection_qty) * 100
        
        # 创建质检记录
        inspection = QualityInspection(
            inspection_no=inspection_no,
            defect_rate=Decimal(str(defect_rate)),
            created_by=current_user_id,
            **inspection_data.model_dump()
        )
        
        save_obj(db, inspection)
        
        # 检查是否触发质量预警
        QualityService._check_quality_alerts(db, inspection)
        
        return inspection

    @staticmethod
    def _generate_inspection_no(db: Session) -> str:
        """生成质检单号: QI + YYYYMMDD + 4位序号"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"QI{today}"
        
        last_record = db.query(QualityInspection).filter(
            QualityInspection.inspection_no.like(f"{prefix}%")
        ).order_by(desc(QualityInspection.inspection_no)).first()
        
        if last_record:
            last_seq = int(last_record.inspection_no[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:04d}"

    @staticmethod
    def get_quality_trend(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        material_id: Optional[int] = None,
        inspection_type: Optional[str] = None,
        group_by: str = "day"
    ) -> Dict:
        """
        质量趋势分析
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            material_id: 物料ID筛选
            inspection_type: 检验类型筛选
            group_by: 聚合维度 (day/week/month)
            
        Returns:
            Dict: 包含趋势数据和统计信息
        """
        # 构建查询条件
        filters = [
            QualityInspection.inspection_date >= start_date,
            QualityInspection.inspection_date <= end_date
        ]
        
        if material_id:
            filters.append(QualityInspection.material_id == material_id)
        if inspection_type:
            filters.append(QualityInspection.inspection_type == inspection_type)
        
        # 查询数据
        inspections = db.query(QualityInspection).filter(and_(*filters)).all()
        
        # 按时间维度聚合
        trend_data = QualityService._aggregate_by_time(inspections, group_by)
        
        # 计算总体统计
        total_qty = sum(i.inspection_qty for i in inspections)
        total_defects = sum(i.defect_qty for i in inspections)
        avg_defect_rate = (total_defects / total_qty * 100) if total_qty > 0 else 0
        
        # 移动平均预测
        prediction = QualityService._calculate_moving_average(
            [d.defect_rate for d in trend_data],
            window=3
        )
        
        return {
            "trend_data": trend_data,
            "avg_defect_rate": round(avg_defect_rate, 2),
            "total_inspections": len(inspections),
            "total_qty": total_qty,
            "total_defects": total_defects,
            "prediction": prediction
        }

    @staticmethod
    def _aggregate_by_time(
        inspections: List[QualityInspection],
        group_by: str
    ) -> List[QualityTrendDataPoint]:
        """按时间维度聚合数据"""
        data_dict = {}
        
        for inspection in inspections:
            # 确定时间key
            if group_by == "day":
                key = inspection.inspection_date.strftime("%Y-%m-%d")
            elif group_by == "week":
                key = inspection.inspection_date.strftime("%Y-W%W")
            else:  # month
                key = inspection.inspection_date.strftime("%Y-%m")
            
            if key not in data_dict:
                data_dict[key] = {
                    "date": key,
                    "total_qty": 0,
                    "qualified_qty": 0,
                    "defect_qty": 0,
                    "inspection_count": 0
                }
            
            data_dict[key]["total_qty"] += inspection.inspection_qty
            data_dict[key]["qualified_qty"] += inspection.qualified_qty
            data_dict[key]["defect_qty"] += inspection.defect_qty
            data_dict[key]["inspection_count"] += 1
        
        # 转换为列表并计算不良率
        trend_data = []
        for key in sorted(data_dict.keys()):
            data = data_dict[key]
            defect_rate = (
                data["defect_qty"] / data["total_qty"] * 100
                if data["total_qty"] > 0 else 0
            )
            trend_data.append(QualityTrendDataPoint(
                date=data["date"],
                total_qty=data["total_qty"],
                qualified_qty=data["qualified_qty"],
                defect_qty=data["defect_qty"],
                defect_rate=round(defect_rate, 2),
                inspection_count=data["inspection_count"]
            ))
        
        return trend_data

    @staticmethod
    def _calculate_moving_average(data: List[float], window: int = 3) -> Optional[float]:
        """计算移动平均(用于趋势预测)"""
        if len(data) < window:
            return None
        
        recent_data = data[-window:]
        return round(sum(recent_data) / len(recent_data), 2)

    @staticmethod
    def calculate_spc_control_limits(
        db: Session,
        material_id: int,
        start_date: datetime,
        end_date: datetime,
        inspection_type: Optional[str] = None
    ) -> Dict:
        """
        计算SPC控制限 (3σ方法)
        
        Args:
            db: 数据库会话
            material_id: 物料ID
            start_date: 开始日期
            end_date: 结束日期
            inspection_type: 检验类型
            
        Returns:
            Dict: SPC控制图数据
        """
        # 查询测量数据
        filters = [
            QualityInspection.material_id == material_id,
            QualityInspection.inspection_date >= start_date,
            QualityInspection.inspection_date <= end_date,
            QualityInspection.measured_value.isnot(None)
        ]
        
        if inspection_type:
            filters.append(QualityInspection.inspection_type == inspection_type)
        
        inspections = db.query(QualityInspection).filter(and_(*filters)).all()
        
        if len(inspections) < 5:
            raise ValueError("样本数量不足，至少需要5个测量值")
        
        # 提取测量值
        values = [float(i.measured_value) for i in inspections]
        
        # 计算控制限 (3σ)
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        ucl = mean + 3 * std_dev  # 控制上限
        cl = mean                  # 中心线
        lcl = mean - 3 * std_dev  # 控制下限
        
        # 构建数据点
        data_points = []
        out_of_control_points = []
        
        for inspection in inspections:
            value = float(inspection.measured_value)
            data_points.append(SPCDataPoint(
                inspection_no=inspection.inspection_no,
                inspection_date=inspection.inspection_date,
                measured_value=value,
                spec_upper_limit=float(inspection.spec_upper_limit) if inspection.spec_upper_limit else None,
                spec_lower_limit=float(inspection.spec_lower_limit) if inspection.spec_lower_limit else None
            ))
            
            # 检查失控点
            if value > ucl or value < lcl:
                out_of_control_points.append(inspection.inspection_no)
        
        # 计算过程能力指数Cpk (如果有规格限)
        cpk = None
        spec_upper = inspections[0].spec_upper_limit if inspections[0].spec_upper_limit else None
        spec_lower = inspections[0].spec_lower_limit if inspections[0].spec_lower_limit else None
        
        if spec_upper and spec_lower and std_dev > 0:
            cpu = (float(spec_upper) - mean) / (3 * std_dev)
            cpl = (mean - float(spec_lower)) / (3 * std_dev)
            cpk = round(min(cpu, cpl), 2)
        
        return {
            "data_points": data_points,
            "control_limits": SPCControlLimits(
                ucl=round(ucl, 4),
                cl=round(cl, 4),
                lcl=round(lcl, 4),
                spec_upper_limit=float(spec_upper) if spec_upper else None,
                spec_lower_limit=float(spec_lower) if spec_lower else None
            ),
            "out_of_control_points": out_of_control_points,
            "process_capability_index": cpk
        }

    @staticmethod
    def pareto_analysis(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        material_id: Optional[int] = None,
        top_n: int = 10
    ) -> Dict:
        """
        帕累托分析 (80/20原则)
        
        识别占总不良品80%的主要不良类型
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            material_id: 物料ID筛选
            top_n: 显示Top N不良
            
        Returns:
            Dict: 帕累托分析结果
        """
        # 查询不良品数据
        filters = [
            QualityInspection.inspection_date >= start_date,
            QualityInspection.inspection_date <= end_date,
            QualityInspection.defect_qty > 0,
            QualityInspection.defect_type.isnot(None)
        ]
        
        if material_id:
            filters.append(QualityInspection.material_id == material_id)
        
        # 按不良类型聚合
        defect_stats = db.query(
            QualityInspection.defect_type,
            func.sum(QualityInspection.defect_qty).label('total_qty')
        ).filter(and_(*filters)).group_by(
            QualityInspection.defect_type
        ).order_by(desc('total_qty')).limit(top_n).all()
        
        total_defects = sum(stat.total_qty for stat in defect_stats)
        
        # 构建帕累托数据
        data_points = []
        cumulative_qty = 0
        top_80_types = []
        
        for stat in defect_stats:
            cumulative_qty += stat.total_qty
            defect_rate = (stat.total_qty / total_defects * 100) if total_defects > 0 else 0
            cumulative_rate = (cumulative_qty / total_defects * 100) if total_defects > 0 else 0
            
            data_points.append(ParetoDataPoint(
                defect_type=stat.defect_type,
                defect_qty=stat.total_qty,
                defect_rate=round(defect_rate, 2),
                cumulative_rate=round(cumulative_rate, 2)
            ))
            
            # 识别80%累计的类型
            if cumulative_rate <= 80:
                top_80_types.append(stat.defect_type)
        
        return {
            "data_points": data_points,
            "total_defects": total_defects,
            "top_80_percent_types": top_80_types
        }

    @staticmethod
    def create_defect_analysis(
        db: Session,
        analysis_data: DefectAnalysisCreate,
        current_user_id: int
    ) -> DefectAnalysis:
        """创建不良品根因分析"""
        # 生成分析单号
        analysis_no = QualityService._generate_analysis_no(db)
        
        analysis = DefectAnalysis(
            analysis_no=analysis_no,
            analysis_date=datetime.now(),
            created_by=current_user_id,
            **analysis_data.model_dump()
        )
        
        save_obj(db, analysis)
        
        return analysis

    @staticmethod
    def _generate_analysis_no(db: Session) -> str:
        """生成分析单号: DA + YYYYMMDD + 4位序号"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"DA{today}"
        
        last_record = db.query(DefectAnalysis).filter(
            DefectAnalysis.analysis_no.like(f"{prefix}%")
        ).order_by(desc(DefectAnalysis.analysis_no)).first()
        
        if last_record:
            last_seq = int(last_record.analysis_no[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:04d}"

    @staticmethod
    def _check_quality_alerts(db: Session, inspection: QualityInspection):
        """
        检查是否触发质量预警规则
        
        Args:
            db: 数据库会话
            inspection: 质检记录
        """
        # 查询启用的预警规则
        rules = db.query(QualityAlertRule).filter(
            QualityAlertRule.enabled == 1
        ).all()
        
        for rule in rules:
            # 检查是否适用该规则
            if rule.target_material_id and rule.target_material_id != inspection.material_id:
                continue
            
            # 根据预警类型检查
            if rule.alert_type == "DEFECT_RATE":
                QualityService._check_defect_rate_alert(db, rule, inspection)
            elif rule.alert_type in ("SPC_UCL", "SPC_LCL"):
                QualityService._check_spc_alert(db, rule, inspection)

    @staticmethod
    def _check_defect_rate_alert(
        db: Session,
        rule: QualityAlertRule,
        inspection: QualityInspection
    ):
        """检查不良率预警"""
        # 计算时间窗口内的不良率
        time_window_start = datetime.now() - timedelta(hours=rule.time_window_hours)
        
        filters = [
            QualityInspection.inspection_date >= time_window_start,
        ]
        
        if rule.target_material_id:
            filters.append(QualityInspection.material_id == rule.target_material_id)
        
        recent_inspections = db.query(QualityInspection).filter(and_(*filters)).all()
        
        if len(recent_inspections) < rule.min_sample_size:
            return
        
        total_qty = sum(i.inspection_qty for i in recent_inspections)
        total_defects = sum(i.defect_qty for i in recent_inspections)
        current_defect_rate = (total_defects / total_qty * 100) if total_qty > 0 else 0
        
        # 检查阈值
        threshold = float(rule.threshold_value)
        triggered = False
        
        if rule.threshold_operator == "GT" and current_defect_rate > threshold:
            triggered = True
        elif rule.threshold_operator == "GTE" and current_defect_rate >= threshold:
            triggered = True
        elif rule.threshold_operator == "LT" and current_defect_rate < threshold:
            triggered = True
        elif rule.threshold_operator == "LTE" and current_defect_rate <= threshold:
            triggered = True
        
        if triggered:
            # 更新规则触发信息
            rule.last_triggered_at = datetime.now()
            rule.trigger_count += 1
            db.commit()
            
            # TODO: 这里可以集成AlertRecord表记录预警

    @staticmethod
    def _check_spc_alert(
        db: Session,
        rule: QualityAlertRule,
        inspection: QualityInspection
    ):
        """检查SPC控制限预警"""
        if not inspection.measured_value:
            return
        
        # 计算控制限
        time_window_start = datetime.now() - timedelta(hours=rule.time_window_hours)
        
        filters = [
            QualityInspection.inspection_date >= time_window_start,
            QualityInspection.measured_value.isnot(None)
        ]
        
        if rule.target_material_id:
            filters.append(QualityInspection.material_id == rule.target_material_id)
        
        recent_inspections = db.query(QualityInspection).filter(and_(*filters)).all()
        
        if len(recent_inspections) < rule.min_sample_size:
            return
        
        values = [float(i.measured_value) for i in recent_inspections]
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        ucl = mean + 3 * std_dev
        lcl = mean - 3 * std_dev
        
        current_value = float(inspection.measured_value)
        
        triggered = False
        if rule.alert_type == "SPC_UCL" and current_value > ucl:
            triggered = True
        elif rule.alert_type == "SPC_LCL" and current_value < lcl:
            triggered = True
        
        if triggered:
            rule.last_triggered_at = datetime.now()
            rule.trigger_count += 1
            db.commit()

    @staticmethod
    def create_rework_order(
        db: Session,
        rework_data: dict,
        current_user_id: int
    ) -> ReworkOrder:
        """创建返工单"""
        # 生成返工单号
        rework_order_no = QualityService._generate_rework_order_no(db)
        
        rework_order = ReworkOrder(
            rework_order_no=rework_order_no,
            created_by=current_user_id,
            **rework_data
        )
        
        save_obj(db, rework_order)
        
        return rework_order

    @staticmethod
    def _generate_rework_order_no(db: Session) -> str:
        """生成返工单号: RW + YYYYMMDD + 4位序号"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"RW{today}"
        
        last_record = db.query(ReworkOrder).filter(
            ReworkOrder.rework_order_no.like(f"{prefix}%")
        ).order_by(desc(ReworkOrder.rework_order_no)).first()
        
        if last_record:
            last_seq = int(last_record.rework_order_no[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:04d}"

    @staticmethod
    def complete_rework_order(
        db: Session,
        rework_order_id: int,
        completion_data: dict
    ) -> ReworkOrder:
        """完成返工单"""
        rework_order = db.query(ReworkOrder).filter(
            ReworkOrder.id == rework_order_id
        ).first()
        
        if not rework_order:
            raise ValueError("返工单不存在")
        
        if rework_order.status == "COMPLETED":
            raise ValueError("返工单已完成")
        
        # 更新返工单
        rework_order.completed_qty = completion_data.get("completed_qty", 0)
        rework_order.qualified_qty = completion_data.get("qualified_qty", 0)
        rework_order.scrap_qty = completion_data.get("scrap_qty", 0)
        rework_order.actual_hours = completion_data.get("actual_hours", 0)
        rework_order.rework_cost = completion_data.get("rework_cost", 0)
        rework_order.completion_note = completion_data.get("completion_note")
        rework_order.actual_end_time = datetime.now()
        rework_order.status = "COMPLETED"
        
        db.commit()
        db.refresh(rework_order)
        
        return rework_order

    @staticmethod
    def get_quality_statistics(db: Session) -> Dict:
        """获取质量统计看板数据"""
        # 最近30天的数据
        start_date = datetime.now() - timedelta(days=30)
        
        inspections = db.query(QualityInspection).filter(
            QualityInspection.inspection_date >= start_date
        ).all()
        
        total_qty = sum(i.inspection_qty for i in inspections)
        total_qualified = sum(i.qualified_qty for i in inspections)
        total_defects = sum(i.defect_qty for i in inspections)
        
        overall_defect_rate = (total_defects / total_qty * 100) if total_qty > 0 else 0
        pass_rate = (total_qualified / total_qty * 100) if total_qty > 0 else 0
        
        # 返工单统计
        rework_orders = db.query(ReworkOrder).filter(
            ReworkOrder.created_at >= start_date
        ).all()
        
        pending_rework = db.query(ReworkOrder).filter(
            ReworkOrder.status == "PENDING"
        ).count()
        
        # Top不良类型
        defect_stats = db.query(
            QualityInspection.defect_type,
            func.count(QualityInspection.id).label('count')
        ).filter(
            QualityInspection.inspection_date >= start_date,
            QualityInspection.defect_type.isnot(None)
        ).group_by(
            QualityInspection.defect_type
        ).order_by(desc('count')).limit(5).all()
        
        top_defects = [
            {"defect_type": stat.defect_type, "count": stat.count}
            for stat in defect_stats
        ]
        
        # 最近7天趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_inspections = db.query(QualityInspection).filter(
            QualityInspection.inspection_date >= seven_days_ago
        ).all()
        
        trend = QualityService._aggregate_by_time(recent_inspections, "day")
        
        return {
            "total_inspections": len(inspections),
            "total_inspection_qty": total_qty,
            "total_qualified_qty": total_qualified,
            "total_defect_qty": total_defects,
            "overall_defect_rate": round(overall_defect_rate, 2),
            "pass_rate": round(pass_rate, 2),
            "rework_orders_count": len(rework_orders),
            "pending_rework_count": pending_rework,
            "active_alerts_count": db.query(func.count(AlertRecord.id)).join(
                AlertRule, AlertRecord.rule_id == AlertRule.id
            ).filter(
                AlertRecord.status.in_(["OPEN", "PENDING", "ACKNOWLEDGED", "PROCESSING"]),
                AlertRule.rule_type == "QUALITY_ISSUE"
            ).scalar() or 0,
            "top_defect_types": top_defects,
            "trend_last_7_days": [d.model_dump() for d in trend]
        }

    @staticmethod
    def batch_tracing(db: Session, batch_no: str) -> Dict:
        """批次质量追溯"""
        inspections = db.query(QualityInspection).filter(
            QualityInspection.batch_no == batch_no
        ).all()
        
        if not inspections:
            raise ValueError(f"未找到批次号 {batch_no} 的质检记录")
        
        # 查询相关的不良品分析
        inspection_ids = [i.id for i in inspections]
        defect_analyses = db.query(DefectAnalysis).filter(
            DefectAnalysis.inspection_id.in_(inspection_ids)
        ).all()
        
        # 查询相关的返工单
        rework_orders = db.query(ReworkOrder).filter(
            ReworkOrder.quality_inspection_id.in_(inspection_ids)
        ).all()
        
        total_defects = sum(i.defect_qty for i in inspections)
        total_qty = sum(i.inspection_qty for i in inspections)
        batch_defect_rate = (total_defects / total_qty * 100) if total_qty > 0 else 0
        
        material_name = None
        material_id = None
        if inspections and inspections[0].material_id:
            material_id = inspections[0].material_id
            material = db.query(Material.material_name).filter(
                Material.id == material_id
            ).first()
            if material:
                material_name = material.material_name
        
        return {
            "batch_no": batch_no,
            "material_id": material_id,
            "material_name": material_name,
            "inspections": inspections,
            "defect_analyses": defect_analyses,
            "rework_orders": rework_orders,
            "total_inspections": len(inspections),
            "total_defects": total_defects,
            "batch_defect_rate": round(batch_defect_rate, 2)
        }
