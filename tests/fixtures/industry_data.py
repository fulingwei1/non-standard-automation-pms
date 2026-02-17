# -*- coding: utf-8 -*-
"""
金凯博非标自动化测试行业 - 测试数据基础库

提供符合真实业务场景的测试数据，避免通用的 mock_item/project_1 等无意义数据。
覆盖：ICT/FCT/EOL测试设备、汽车电子、消费电子等典型场景。
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

# ─────────────────────────────────────────────
# 典型客户数据
# ─────────────────────────────────────────────
CUSTOMERS = [
    {"id": 1, "name": "比亚迪电子", "industry": "汽车电子", "region": "深圳",
     "contact": "王工", "phone": "13800138001", "level": "A"},
    {"id": 2, "name": "立讯精密", "industry": "消费电子", "region": "深圳",
     "contact": "李经理", "phone": "13800138002", "level": "A"},
    {"id": 3, "name": "伯恩光学", "industry": "消费电子", "region": "惠州",
     "contact": "陈总", "phone": "13800138003", "level": "B"},
    {"id": 4, "name": "蓝思科技", "industry": "消费电子", "region": "长沙",
     "contact": "赵工", "phone": "13800138004", "level": "B"},
    {"id": 5, "name": "德赛西威", "industry": "汽车电子", "region": "惠州",
     "contact": "刘总监", "phone": "13800138005", "level": "A"},
]

# ─────────────────────────────────────────────
# 典型项目类型及参数
# ─────────────────────────────────────────────
PROJECT_TYPES = {
    "ICT": {
        "full_name": "ICT在线测试系统",
        "avg_budget": 280000,        # 元
        "avg_duration_days": 90,
        "complexity": "MEDIUM",
        "typical_risks": ["物料供货期长", "夹具精度要求高", "程序调试周期长"],
    },
    "FCT": {
        "full_name": "FCT功能测试台",
        "avg_budget": 180000,
        "avg_duration_days": 60,
        "complexity": "MEDIUM",
        "typical_risks": ["需求变更频繁", "多版本兼容"],
    },
    "EOL": {
        "full_name": "EOL终线综合测试系统",
        "avg_budget": 450000,
        "avg_duration_days": 120,
        "complexity": "HIGH",
        "typical_risks": ["多工位同步难度大", "节拍要求严苛", "与产线MES集成复杂"],
    },
    "AGING": {
        "full_name": "老化测试炉",
        "avg_budget": 320000,
        "avg_duration_days": 75,
        "complexity": "MEDIUM",
        "typical_risks": ["温控精度要求高", "安规认证周期长"],
    },
    "VISION": {
        "full_name": "视觉检测系统",
        "avg_budget": 220000,
        "avg_duration_days": 80,
        "complexity": "HIGH",
        "typical_risks": ["光源方案验证周期长", "算法误判率调优难"],
    },
    "BURN": {
        "full_name": "烧录编程系统",
        "avg_budget": 95000,
        "avg_duration_days": 45,
        "complexity": "LOW",
        "typical_risks": ["量产节拍压力大"],
    },
}

# ─────────────────────────────────────────────
# 典型项目案例（真实场景）
# ─────────────────────────────────────────────
SAMPLE_PROJECTS = [
    {
        "id": 1,
        "project_code": "PJ250901001",
        "name": "比亚迪电子ADAS域控制器ICT测试系统",
        "customer_id": 1,
        "type": "ICT",
        "budget": 320000,
        "contract_amount": 320000,
        "start_date": date(2025, 9, 1),
        "planned_end_date": date(2025, 11, 30),
        "status": "IN_PROGRESS",
        "stage": "S6",  # 装配联调
        "pm_id": 3,
        "team_size": 5,
        "description": "ADAS域控制器主板ICT在线测试，兼容8个测试点版本",
    },
    {
        "id": 2,
        "project_code": "PJ250801002",
        "name": "立讯精密AirPods主板FCT功能测试台",
        "customer_id": 2,
        "type": "FCT",
        "budget": 165000,
        "contract_amount": 168000,
        "start_date": date(2025, 8, 1),
        "planned_end_date": date(2025, 10, 15),
        "status": "COMPLETED",
        "stage": "S9",  # 质保结项
        "pm_id": 2,
        "team_size": 3,
        "description": "AirPods Pro主板功能测试，含音频、蓝牙、传感器测试",
    },
    {
        "id": 3,
        "project_code": "PJ260101003",
        "name": "德赛西威车载娱乐系统EOL测试线",
        "customer_id": 5,
        "type": "EOL",
        "budget": 520000,
        "contract_amount": 520000,
        "start_date": date(2026, 1, 15),
        "planned_end_date": date(2026, 5, 31),
        "status": "IN_PROGRESS",
        "stage": "S4",  # 方案设计
        "pm_id": 1,
        "team_size": 7,
        "description": "车载娱乐IVI系统EOL终线测试，4工位，节拍45秒/件",
    },
    {
        "id": 4,
        "project_code": "PJ251101004",
        "name": "蓝思科技摄像头模组视觉检测系统",
        "customer_id": 4,
        "type": "VISION",
        "budget": 198000,
        "contract_amount": 200000,
        "start_date": date(2025, 11, 1),
        "planned_end_date": date(2026, 1, 31),
        "status": "DELAYED",
        "stage": "S6",
        "pm_id": 4,
        "team_size": 4,
        "description": "手机摄像头模组外观视觉检测，检测划痕/污点/焦距偏差",
    },
]

# ─────────────────────────────────────────────
# 典型物料/BOM数据
# ─────────────────────────────────────────────
SAMPLE_MATERIALS = [
    {"id": 1, "code": "MAT-NI-001", "name": "NI PXI机箱", "brand": "NI",
     "unit": "台", "unit_price": 35000, "lead_time_days": 30, "category": "仪器仪表"},
    {"id": 2, "code": "MAT-NI-002", "name": "NI数字IO板卡", "brand": "NI",
     "unit": "块", "unit_price": 8500, "lead_time_days": 21, "category": "仪器仪表"},
    {"id": 3, "code": "MAT-KK-001", "name": "气缸（SMC CQ2B32-50D）", "brand": "SMC",
     "unit": "个", "unit_price": 280, "lead_time_days": 7, "category": "气动元件"},
    {"id": 4, "code": "MAT-KK-002", "name": "工业相机（海康MV-CS050-10GM）", "brand": "海康",
     "unit": "台", "unit_price": 3200, "lead_time_days": 14, "category": "视觉器件"},
    {"id": 5, "code": "MAT-KK-003", "name": "伺服驱动器（汇川IS620N）", "brand": "汇川",
     "unit": "台", "unit_price": 2800, "lead_time_days": 10, "category": "运动控制"},
    {"id": 6, "code": "MAT-KK-004", "name": "铝合金型材（40×40）", "brand": "通用",
     "unit": "米", "unit_price": 45, "lead_time_days": 3, "category": "结构件"},
]

# ─────────────────────────────────────────────
# 典型工时数据（工程师工时记录）
# ─────────────────────────────────────────────
SAMPLE_TIMESHEETS = [
    {"id": 1, "engineer_id": 10, "project_id": 1, "date": date(2026, 2, 10),
     "hours": 8.0, "type": "HARDWARE", "description": "ICT夹具机械设计，完成上压板结构",
     "status": "APPROVED"},
    {"id": 2, "engineer_id": 11, "project_id": 1, "date": date(2026, 2, 10),
     "hours": 8.0, "type": "SOFTWARE", "description": "ICT测试程序开发，完成基础通信框架",
     "status": "APPROVED"},
    {"id": 3, "engineer_id": 10, "project_id": 3, "date": date(2026, 2, 10),
     "hours": 4.0, "type": "DESIGN", "description": "EOL测试线方案评审，确认工位布局",
     "status": "PENDING"},
    {"id": 4, "engineer_id": 12, "project_id": 2, "date": date(2026, 2, 8),
     "hours": 6.5, "type": "DEBUGGING", "description": "FCT联调，修复蓝牙测试误判问题",
     "status": "APPROVED"},
]

# ─────────────────────────────────────────────
# 典型成本数据
# ─────────────────────────────────────────────
SAMPLE_COSTS = [
    {"project_id": 1, "category": "硬件采购", "budgeted": 180000, "actual": 175000,
     "description": "NI机箱+板卡+夹具材料"},
    {"project_id": 1, "category": "人工成本", "budgeted": 80000, "actual": 72000,
     "description": "5人×2个月工时"},
    {"project_id": 1, "category": "外协加工", "budgeted": 25000, "actual": 28000,
     "description": "铝合金夹具机加工，超预算12%"},
    {"project_id": 1, "category": "差旅费用", "budgeted": 15000, "actual": 8500,
     "description": "客户现场调试出差"},
    {"project_id": 3, "category": "硬件采购", "budgeted": 280000, "actual": 0,
     "description": "EOL系统核心仪器（尚未采购）"},
]

# ─────────────────────────────────────────────
# 典型销售线索数据
# ─────────────────────────────────────────────
SAMPLE_LEADS = [
    {"id": 1, "customer": "华为终端", "product_type": "FCT",
     "estimated_amount": 250000, "probability": 0.7,
     "source": "展会", "stage": "方案评估",
     "description": "Mate系列手机主板FCT，年需求3-5台"},
    {"id": 2, "customer": "宁德时代", "product_type": "EOL",
     "estimated_amount": 800000, "probability": 0.4,
     "source": "老客户介绍", "stage": "需求确认",
     "description": "BMS电池管理系统EOL测试线，8工位"},
    {"id": 3, "customer": "欣旺达", "product_type": "AGING",
     "estimated_amount": 380000, "probability": 0.6,
     "source": "主动拜访", "stage": "报价中",
     "description": "动力电芯老化测试炉，100通道"},
]

# ─────────────────────────────────────────────
# 典型KPI/绩效指标
# ─────────────────────────────────────────────
KPI_BENCHMARKS = {
    "project_on_time_rate": 0.85,        # 项目准时交付率目标 85%
    "gross_margin_target": 0.35,          # 毛利率目标 35%
    "customer_satisfaction": 4.2,         # 客户满意度目标 4.2/5
    "rework_rate_limit": 0.05,            # 返工率上限 5%
    "fat_pass_rate_target": 0.90,         # FAT一次通过率目标 90%
    "kit_rate_target": 0.95,              # 套件率目标 95%
    "timesheet_fill_rate": 0.98,          # 工时填报率 98%
}

# ─────────────────────────────────────────────
# Mock 工厂函数（快速创建 Mock 对象）
# ─────────────────────────────────────────────

def make_mock_project(project_data: dict = None) -> MagicMock:
    """创建一个有真实字段的项目 Mock 对象"""
    data = project_data or SAMPLE_PROJECTS[0]
    obj = MagicMock()
    for k, v in data.items():
        setattr(obj, k, v)
    return obj


def make_mock_customer(customer_data: dict = None) -> MagicMock:
    """创建客户 Mock 对象"""
    data = customer_data or CUSTOMERS[0]
    obj = MagicMock()
    for k, v in data.items():
        setattr(obj, k, v)
    return obj


def make_mock_db_with_projects(projects: list = None) -> MagicMock:
    """创建一个预加载了项目数据的 Mock db session"""
    db = MagicMock()
    project_list = [make_mock_project(p) for p in (projects or SAMPLE_PROJECTS)]
    db.query.return_value.filter.return_value.all.return_value = project_list
    db.query.return_value.all.return_value = project_list
    db.query.return_value.filter.return_value.first.return_value = project_list[0] if project_list else None
    db.query.return_value.first.return_value = project_list[0] if project_list else None
    return db


def make_mock_timesheet(timesheet_data: dict = None) -> MagicMock:
    """创建工时记录 Mock 对象"""
    data = timesheet_data or SAMPLE_TIMESHEETS[0]
    obj = MagicMock()
    for k, v in data.items():
        setattr(obj, k, v)
    return obj
