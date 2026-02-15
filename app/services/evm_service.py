# -*- coding: utf-8 -*-
"""
EVM (Earned Value Management) 挣值管理服务

实现PMBOK标准的挣值管理核心算法和业务逻辑
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models import EarnedValueData, Project


class EVMCalculator:
    """
    EVM计算器 - 实现所有PMBOK标准的挣值公式
    
    使用Decimal进行精确计算，避免浮点误差
    """
    
    # 精度配置
    DECIMAL_PLACES = 4  # 金额保留4位小数
    INDEX_DECIMAL_PLACES = 6  # 指数保留6位小数
    PERCENT_DECIMAL_PLACES = 2  # 百分比保留2位小数
    
    @staticmethod
    def decimal(value: float | Decimal | int) -> Decimal:
        """转换为Decimal类型"""
        return Decimal(str(value))
    
    @staticmethod
    def round_decimal(value: Decimal, places: int = 4) -> Decimal:
        """四舍五入到指定小数位"""
        if value is None:
            return Decimal('0.0000')
        quantize_str = '0.' + '0' * places
        return value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    
    @classmethod
    def calculate_schedule_variance(cls, ev: Decimal, pv: Decimal) -> Decimal:
        """
        计算进度偏差 (Schedule Variance - SV)
        
        公式: SV = EV - PV
        
        解释:
        - SV > 0: 进度超前（实际完成的工作价值超过计划）
        - SV = 0: 进度符合计划
        - SV < 0: 进度落后（实际完成的工作价值低于计划）
        
        Args:
            ev: 挣得价值 (Earned Value)
            pv: 计划价值 (Planned Value)
        
        Returns:
            进度偏差 (Decimal)
        """
        sv = ev - pv
        return cls.round_decimal(sv, cls.DECIMAL_PLACES)
    
    @classmethod
    def calculate_cost_variance(cls, ev: Decimal, ac: Decimal) -> Decimal:
        """
        计算成本偏差 (Cost Variance - CV)
        
        公式: CV = EV - AC
        
        解释:
        - CV > 0: 成本节约（实际成本低于预算）
        - CV = 0: 成本符合预算
        - CV < 0: 成本超支（实际成本超过预算）
        
        Args:
            ev: 挣得价值 (Earned Value)
            ac: 实际成本 (Actual Cost)
        
        Returns:
            成本偏差 (Decimal)
        """
        cv = ev - ac
        return cls.round_decimal(cv, cls.DECIMAL_PLACES)
    
    @classmethod
    def calculate_schedule_performance_index(cls, ev: Decimal, pv: Decimal) -> Optional[Decimal]:
        """
        计算进度绩效指数 (Schedule Performance Index - SPI)
        
        公式: SPI = EV / PV
        
        解释:
        - SPI > 1.0: 进度超前
        - SPI = 1.0: 进度符合计划
        - SPI < 1.0: 进度落后
        
        Args:
            ev: 挣得价值 (Earned Value)
            pv: 计划价值 (Planned Value)
        
        Returns:
            进度绩效指数 (Decimal) 或 None（当PV=0时）
        """
        if pv == 0:
            return None
        spi = ev / pv
        return cls.round_decimal(spi, cls.INDEX_DECIMAL_PLACES)
    
    @classmethod
    def calculate_cost_performance_index(cls, ev: Decimal, ac: Decimal) -> Optional[Decimal]:
        """
        计算成本绩效指数 (Cost Performance Index - CPI)
        
        公式: CPI = EV / AC
        
        解释:
        - CPI > 1.0: 成本效率高（花费少，产出多）
        - CPI = 1.0: 成本符合预算
        - CPI < 1.0: 成本效率低（花费多，产出少）
        
        Args:
            ev: 挣得价值 (Earned Value)
            ac: 实际成本 (Actual Cost)
        
        Returns:
            成本绩效指数 (Decimal) 或 None（当AC=0时）
        """
        if ac == 0:
            return None
        cpi = ev / ac
        return cls.round_decimal(cpi, cls.INDEX_DECIMAL_PLACES)
    
    @classmethod
    def calculate_estimate_at_completion(
        cls, 
        bac: Decimal, 
        ev: Decimal, 
        ac: Decimal,
        cpi: Optional[Decimal] = None
    ) -> Decimal:
        """
        计算完工估算 (Estimate at Completion - EAC)
        
        公式: EAC = AC + (BAC - EV) / CPI
        
        这是最常用的EAC计算方法，假设未来的成本绩效与当前一致
        
        特殊情况：
        - 当CPI=None或CPI=0时，使用简化公式: EAC = AC + (BAC - EV)
        
        Args:
            bac: 完工预算 (Budget at Completion)
            ev: 挣得价值 (Earned Value)
            ac: 实际成本 (Actual Cost)
            cpi: 成本绩效指数（可选，如未提供则自动计算）
        
        Returns:
            完工估算 (Decimal)
        """
        if cpi is None:
            cpi = cls.calculate_cost_performance_index(ev, ac)
        
        if cpi is None or cpi == 0:
            # CPI无法计算或为0时，使用简化公式
            eac = ac + (bac - ev)
        else:
            # 标准公式
            eac = ac + (bac - ev) / cpi
        
        return cls.round_decimal(eac, cls.DECIMAL_PLACES)
    
    @classmethod
    def calculate_estimate_to_complete(cls, eac: Decimal, ac: Decimal) -> Decimal:
        """
        计算完工尚需估算 (Estimate to Complete - ETC)
        
        公式: ETC = EAC - AC
        
        解释：完成剩余工作还需要的成本
        
        Args:
            eac: 完工估算 (Estimate at Completion)
            ac: 实际成本 (Actual Cost)
        
        Returns:
            完工尚需估算 (Decimal)
        """
        etc = eac - ac
        return cls.round_decimal(etc, cls.DECIMAL_PLACES)
    
    @classmethod
    def calculate_variance_at_completion(cls, bac: Decimal, eac: Decimal) -> Decimal:
        """
        计算完工偏差 (Variance at Completion - VAC)
        
        公式: VAC = BAC - EAC
        
        解释:
        - VAC > 0: 预计节约成本
        - VAC = 0: 预计符合预算
        - VAC < 0: 预计超出预算
        
        Args:
            bac: 完工预算 (Budget at Completion)
            eac: 完工估算 (Estimate at Completion)
        
        Returns:
            完工偏差 (Decimal)
        """
        vac = bac - eac
        return cls.round_decimal(vac, cls.DECIMAL_PLACES)
    
    @classmethod
    def calculate_to_complete_performance_index(
        cls, 
        bac: Decimal, 
        ev: Decimal, 
        ac: Decimal,
        eac: Optional[Decimal] = None
    ) -> Optional[Decimal]:
        """
        计算完工尚需绩效指数 (To-Complete Performance Index - TCPI)
        
        两种计算方法：
        1. 基于BAC: TCPI = (BAC - EV) / (BAC - AC)
           用于评估按原预算完成项目所需的成本绩效
        
        2. 基于EAC: TCPI = (BAC - EV) / (EAC - AC)
           用于评估按修正预算完成项目所需的成本绩效
        
        本方法默认使用方法1（基于BAC）
        
        解释:
        - TCPI > 1.0: 未来需要提高成本效率才能达成目标
        - TCPI = 1.0: 维持当前成本效率即可
        - TCPI < 1.0: 可以降低成本效率
        
        Args:
            bac: 完工预算 (Budget at Completion)
            ev: 挣得价值 (Earned Value)
            ac: 实际成本 (Actual Cost)
            eac: 完工估算（可选，如提供则使用方法2）
        
        Returns:
            完工尚需绩效指数 (Decimal) 或 None（当分母为0时）
        """
        work_remaining = bac - ev
        
        if eac is not None:
            # 方法2: 基于EAC
            funds_remaining = eac - ac
        else:
            # 方法1: 基于BAC
            funds_remaining = bac - ac
        
        if funds_remaining == 0:
            return None
        
        tcpi = work_remaining / funds_remaining
        return cls.round_decimal(tcpi, cls.INDEX_DECIMAL_PLACES)
    
    @classmethod
    def calculate_percent_complete(
        cls,
        value: Decimal,
        bac: Decimal
    ) -> Optional[Decimal]:
        """
        计算完成百分比
        
        公式: Percent = (Value / BAC) * 100
        
        Args:
            value: 值（PV或EV）
            bac: 完工预算 (Budget at Completion)
        
        Returns:
            完成百分比 (Decimal) 或 None（当BAC=0时）
        """
        if bac == 0:
            return None
        
        percent = (value / bac) * Decimal('100')
        return cls.round_decimal(percent, cls.PERCENT_DECIMAL_PLACES)
    
    @classmethod
    def calculate_all_metrics(
        cls,
        pv: Decimal,
        ev: Decimal,
        ac: Decimal,
        bac: Decimal
    ) -> Dict[str, Optional[Decimal]]:
        """
        一次性计算所有EVM指标
        
        Args:
            pv: 计划价值 (Planned Value)
            ev: 挣得价值 (Earned Value)
            ac: 实际成本 (Actual Cost)
            bac: 完工预算 (Budget at Completion)
        
        Returns:
            包含所有EVM指标的字典
        """
        # 转换为Decimal
        pv = cls.decimal(pv)
        ev = cls.decimal(ev)
        ac = cls.decimal(ac)
        bac = cls.decimal(bac)
        
        # 偏差指标
        sv = cls.calculate_schedule_variance(ev, pv)
        cv = cls.calculate_cost_variance(ev, ac)
        
        # 绩效指数
        spi = cls.calculate_schedule_performance_index(ev, pv)
        cpi = cls.calculate_cost_performance_index(ev, ac)
        
        # 预测指标
        eac = cls.calculate_estimate_at_completion(bac, ev, ac, cpi)
        etc = cls.calculate_estimate_to_complete(eac, ac)
        vac = cls.calculate_variance_at_completion(bac, eac)
        tcpi = cls.calculate_to_complete_performance_index(bac, ev, ac)
        
        # 完成百分比
        planned_pct = cls.calculate_percent_complete(pv, bac)
        actual_pct = cls.calculate_percent_complete(ev, bac)
        
        return {
            # 基础值
            "pv": pv,
            "ev": ev,
            "ac": ac,
            "bac": bac,
            # 偏差
            "sv": sv,
            "cv": cv,
            # 绩效指数
            "spi": spi,
            "cpi": cpi,
            # 预测
            "eac": eac,
            "etc": etc,
            "vac": vac,
            "tcpi": tcpi,
            # 百分比
            "planned_percent_complete": planned_pct,
            "actual_percent_complete": actual_pct,
        }


class EVMService:
    """EVM服务 - 数据访问和业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculator = EVMCalculator()
    
    def create_evm_data(
        self,
        project_id: int,
        period_type: str,
        period_date: date,
        pv: Decimal,
        ev: Decimal,
        ac: Decimal,
        bac: Decimal,
        currency: str = "CNY",
        data_source: str = "MANUAL",
        created_by: Optional[int] = None,
        notes: Optional[str] = None
    ) -> EarnedValueData:
        """
        创建EVM数据记录（自动计算所有派生指标）
        
        Args:
            project_id: 项目ID
            period_type: 周期类型（WEEK/MONTH/QUARTER）
            period_date: 周期截止日期
            pv: 计划价值
            ev: 挣得价值
            ac: 实际成本
            bac: 完工预算
            currency: 币种
            data_source: 数据来源
            created_by: 创建人ID
            notes: 备注
        
        Returns:
            创建的EVM数据记录
        """
        # 获取项目信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目不存在: project_id={project_id}")
        
        # 生成周期标签
        period_label = self._generate_period_label(period_type, period_date)
        
        # 计算所有EVM指标
        metrics = self.calculator.calculate_all_metrics(pv, ev, ac, bac)
        
        # 创建数据记录
        evm_data = EarnedValueData(
            project_id=project_id,
            project_code=project.project_code,
            period_type=period_type,
            period_date=period_date,
            period_label=period_label,
            planned_value=metrics["pv"],
            earned_value=metrics["ev"],
            actual_cost=metrics["ac"],
            budget_at_completion=metrics["bac"],
            currency=currency,
            schedule_variance=metrics["sv"],
            cost_variance=metrics["cv"],
            schedule_performance_index=metrics["spi"],
            cost_performance_index=metrics["cpi"],
            estimate_at_completion=metrics["eac"],
            estimate_to_complete=metrics["etc"],
            variance_at_completion=metrics["vac"],
            to_complete_performance_index=metrics["tcpi"],
            planned_percent_complete=metrics["planned_percent_complete"],
            actual_percent_complete=metrics["actual_percent_complete"],
            data_source=data_source,
            created_by=created_by,
            notes=notes
        )
        
        self.db.add(evm_data)
        self.db.commit()
        self.db.refresh(evm_data)
        
        return evm_data
    
    def _generate_period_label(self, period_type: str, period_date: date) -> str:
        """生成周期标签"""
        if period_type == "WEEK":
            # ISO周：2026-W07
            iso_calendar = period_date.isocalendar()
            return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"
        elif period_type == "MONTH":
            # 月份：2026-02
            return period_date.strftime("%Y-%m")
        elif period_type == "QUARTER":
            # 季度：2026-Q1
            quarter = (period_date.month - 1) // 3 + 1
            return f"{period_date.year}-Q{quarter}"
        else:
            return period_date.strftime("%Y-%m-%d")
    
    def get_latest_evm_data(
        self,
        project_id: int,
        period_type: Optional[str] = None
    ) -> Optional[EarnedValueData]:
        """获取项目最新的EVM数据"""
        query = self.db.query(EarnedValueData).filter(
            EarnedValueData.project_id == project_id
        )
        
        if period_type:
            query = query.filter(EarnedValueData.period_type == period_type)
        
        return query.order_by(desc(EarnedValueData.period_date)).first()
    
    def get_evm_trend(
        self,
        project_id: int,
        period_type: str = "MONTH",
        limit: Optional[int] = None
    ) -> List[EarnedValueData]:
        """
        获取EVM趋势数据
        
        Args:
            project_id: 项目ID
            period_type: 周期类型
            limit: 限制返回数量
        
        Returns:
            EVM数据列表（按时间倒序）
        """
        query = self.db.query(EarnedValueData).filter(
            and_(
                EarnedValueData.project_id == project_id,
                EarnedValueData.period_type == period_type
            )
        ).order_by(desc(EarnedValueData.period_date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def analyze_performance(self, evm_data: EarnedValueData) -> Dict:
        """
        分析项目绩效状态
        
        Returns:
            绩效分析结果
        """
        spi = evm_data.schedule_performance_index or Decimal('0')
        cpi = evm_data.cost_performance_index or Decimal('0')
        
        # 进度状态
        if spi >= Decimal('1.1'):
            schedule_status = "EXCELLENT"
            schedule_desc = "进度大幅超前"
        elif spi >= Decimal('0.95'):
            schedule_status = "GOOD"
            schedule_desc = "进度正常"
        elif spi >= Decimal('0.8'):
            schedule_status = "WARNING"
            schedule_desc = "进度轻微落后"
        else:
            schedule_status = "CRITICAL"
            schedule_desc = "进度严重落后"
        
        # 成本状态
        if cpi >= Decimal('1.1'):
            cost_status = "EXCELLENT"
            cost_desc = "成本效率优秀"
        elif cpi >= Decimal('0.95'):
            cost_status = "GOOD"
            cost_desc = "成本正常"
        elif cpi >= Decimal('0.8'):
            cost_status = "WARNING"
            cost_desc = "成本轻微超支"
        else:
            cost_status = "CRITICAL"
            cost_desc = "成本严重超支"
        
        # 综合状态
        if schedule_status in ["EXCELLENT", "GOOD"] and cost_status in ["EXCELLENT", "GOOD"]:
            overall_status = "EXCELLENT"
        elif schedule_status == "CRITICAL" or cost_status == "CRITICAL":
            overall_status = "CRITICAL"
        elif schedule_status == "WARNING" or cost_status == "WARNING":
            overall_status = "WARNING"
        else:
            overall_status = "GOOD"
        
        return {
            "overall_status": overall_status,
            "schedule_status": schedule_status,
            "schedule_description": schedule_desc,
            "cost_status": cost_status,
            "cost_description": cost_desc,
            "spi": float(spi),
            "cpi": float(cpi),
        }
