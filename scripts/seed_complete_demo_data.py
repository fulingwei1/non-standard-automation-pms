#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销售模块完整演示数据生成脚本
生成所有模块的演示数据
"""

import json
from datetime import date, timedelta
from pathlib import Path

# ========== 1. 销售代表数据 ==========

sales_reps = [
    {"id": 101, "name": "张三", "team": "华南大区", "territory": "福建/广东", "quota_annual": 50000000, "quota_q1": 12500000},
    {"id": 102, "name": "李四", "team": "华东大区", "territory": "江苏/浙江", "quota_annual": 45000000, "quota_q1": 11250000},
    {"id": 103, "name": "王五", "team": "华南大区", "territory": "广东/广西", "quota_annual": 40000000, "quota_q1": 10000000},
    {"id": 104, "name": "赵六", "team": "华东大区", "territory": "江苏/安徽", "quota_annual": 35000000, "quota_q1": 8750000},
    {"id": 105, "name": "钱七", "team": "华北大区", "territory": "安徽/湖北", "quota_annual": 30000000, "quota_q1": 7500000},
]

# ========== 2. 客户数据（8 个） ==========

customers = [
    {
        "id": 1,
        "name": "宁德时代新能源科技股份有限公司",
        "short_name": "宁德时代",
        "industry": "动力电池",
        "location": "福建宁德",
        "scale": "大型",
        "annual_revenue": 30000000000,
        "employee_count": 50000,
        "stage": "战略合作客户",
        "priority": "A",
        "owner_id": 101,
        "owner_name": "张三",
        "created_at": "2024-06-15",
        "last_contact": "2026-02-28",
        "next_followup": "2026-03-05",
        "tags": ["动力电池", "储能", "头部客户", "上市公司"],
        "decision_chain": {
            "EB": {"name": "曾毓群", "title": "董事长", "attitude": "neutral"},
            "TB": {"name": "吴凯", "title": "首席科学家", "attitude": "supportive"},
            "PB": {"name": "李平", "title": "采购总监", "attitude": "neutral"},
            "UB": {"name": "赵伟", "title": "生产总监", "attitude": "supportive"},
            "Coach": {"name": "钱七", "title": "设备工程师", "attitude": "supportive"},
        },
        "relationship_score": 78,
        "maturity_level": "L4",
    },
    {
        "id": 2,
        "name": "比亚迪股份有限公司",
        "short_name": "比亚迪",
        "industry": "新能源汽车",
        "location": "广东深圳",
        "scale": "大型",
        "annual_revenue": 40000000000,
        "stage": "战略合作客户",
        "priority": "A",
        "owner_id": 102,
        "owner_name": "李四",
        "relationship_score": 85,
        "maturity_level": "L4",
    },
    {
        "id": 3,
        "name": "中创新航科技股份有限公司",
        "short_name": "中创新航",
        "industry": "动力电池",
        "location": "江苏常州",
        "scale": "中型",
        "annual_revenue": 15000000000,
        "stage": "重点开发客户",
        "priority": "A",
        "owner_id": 101,
        "owner_name": "张三",
        "relationship_score": 62,
        "maturity_level": "L3",
    },
    {
        "id": 4,
        "name": "惠州亿纬锂能股份有限公司",
        "short_name": "亿纬锂能",
        "industry": "锂电池",
        "location": "广东惠州",
        "scale": "中型",
        "annual_revenue": 12000000000,
        "stage": "合作客户",
        "priority": "B",
        "owner_id": 103,
        "owner_name": "王五",
        "relationship_score": 72,
        "maturity_level": "L3",
    },
    {
        "id": 5,
        "name": "欣旺达电子股份有限公司",
        "short_name": "欣旺达",
        "industry": "锂电池",
        "location": "广东深圳",
        "scale": "中型",
        "annual_revenue": 10000000000,
        "stage": "开发中客户",
        "priority": "B",
        "owner_id": 104,
        "owner_name": "赵六",
        "relationship_score": 42,
        "maturity_level": "L2",
    },
    {
        "id": 6,
        "name": "蜂巢能源科技有限公司",
        "short_name": "蜂巢能源",
        "industry": "锂电池",
        "location": "江苏常州",
        "scale": "中型",
        "annual_revenue": 8000000000,
        "stage": "开发中客户",
        "priority": "B",
        "owner_id": 104,
        "owner_name": "赵六",
        "relationship_score": 35,
        "maturity_level": "L2",
    },
    {
        "id": 7,
        "name": "国轩高科股份有限公司",
        "short_name": "国轩高科",
        "industry": "动力电池",
        "location": "安徽合肥",
        "scale": "中型",
        "annual_revenue": 9000000000,
        "stage": "初步接触",
        "priority": "C",
        "owner_id": 105,
        "owner_name": "钱七",
        "relationship_score": 25,
        "maturity_level": "L1",
    },
    {
        "id": 8,
        "name": "珠海冠宇电池股份有限公司",
        "short_name": "珠海冠宇",
        "industry": "消费电池",
        "location": "广东珠海",
        "scale": "中型",
        "annual_revenue": 7000000000,
        "stage": "合作客户",
        "priority": "B",
        "owner_id": 103,
        "owner_name": "王五",
        "relationship_score": 82,
        "maturity_level": "L4",
    },
]

# ========== 3. 商机数据（8 个） ==========

opportunities = [
    {
        "id": 1,
        "customer_id": 1,
        "customer_name": "宁德时代",
        "name": "FCT 测试线项目",
        "type": "FCT",
        "stage": "商务谈判",
        "amount": 3500000,
        "probability": 75,
        "expected_close_date": "2026-03-31",
        "owner_id": 101,
        "owner_name": "张三",
        "competitors": ["竞品 A（320 万）", "竞品 B（380 万）"],
        "primary_competitor": "竞品 A",
    },
    {
        "id": 2,
        "customer_id": 2,
        "customer_name": "比亚迪",
        "name": "EOL 测试设备项目",
        "type": "EOL",
        "stage": "合同审批",
        "amount": 4200000,
        "probability": 82,
        "expected_close_date": "2026-03-25",
        "owner_id": 102,
        "owner_name": "李四",
        "competitors": ["竞品 A（450 万）"],
        "primary_competitor": "竞品 A",
    },
    {
        "id": 3,
        "customer_id": 3,
        "customer_name": "中创新航",
        "name": "ICT 在线测试项目",
        "type": "ICT",
        "stage": "方案评估",
        "amount": 2800000,
        "probability": 58,
        "expected_close_date": "2026-04-15",
        "owner_id": 101,
        "owner_name": "张三",
        "competitors": ["竞品 A（250 万）", "竞品 B（270 万）", "竞品 C（290 万）"],
        "primary_competitor": "竞品 B",
    },
    {
        "id": 4,
        "customer_id": 4,
        "customer_name": "亿纬锂能",
        "name": "烧录设备采购项目",
        "type": "烧录",
        "stage": "商务谈判",
        "amount": 1800000,
        "probability": 68,
        "expected_close_date": "2026-04-05",
        "owner_id": 103,
        "owner_name": "王五",
        "competitors": ["竞品 D（160 万）"],
        "primary_competitor": "竞品 D",
    },
    {
        "id": 5,
        "customer_id": 5,
        "customer_name": "欣旺达",
        "name": "FCT 功能测试项目",
        "type": "FCT",
        "stage": "需求分析",
        "amount": 3200000,
        "probability": 35,
        "expected_close_date": "2026-05-15",
        "owner_id": 104,
        "owner_name": "赵六",
        "competitors": ["竞品 B", "竞品 C"],
        "primary_competitor": "竞品 B",
    },
    {
        "id": 6,
        "customer_id": 6,
        "customer_name": "蜂巢能源",
        "name": "EOL 检测设备项目",
        "type": "EOL",
        "stage": "初步接触",
        "amount": 2500000,
        "probability": 28,
        "expected_close_date": "2026-06-30",
        "owner_id": 104,
        "owner_name": "赵六",
        "competitors": ["竞品 A", "竞品 B", "竞品 C"],
        "primary_competitor": "竞品 A",
    },
    {
        "id": 7,
        "customer_id": 7,
        "customer_name": "国轩高科",
        "name": "ICT 测试设备项目",
        "type": "ICT",
        "stage": "线索",
        "amount": 2000000,
        "probability": 15,
        "expected_close_date": "2026-08-31",
        "owner_id": 105,
        "owner_name": "钱七",
        "competitors": ["未知"],
        "primary_competitor": "竞品 B",
    },
    {
        "id": 8,
        "customer_id": 8,
        "customer_name": "珠海冠宇",
        "name": "老化测试设备项目",
        "type": "老化",
        "stage": "合同审批",
        "amount": 1500000,
        "probability": 88,
        "expected_close_date": "2026-03-20",
        "owner_id": 103,
        "owner_name": "王五",
        "competitors": ["竞品 A（170 万）"],
        "primary_competitor": "竞品 A",
    },
]

# ========== 4. 关系成熟度评估（6 个） ==========

relationship_assessments = [
    {
        "customer_id": 1,
        "customer_name": "宁德时代",
        "assessment_date": "2026-03-01",
        "overall_score": 78,
        "maturity_level": "L4",
        "maturity_level_name": "战略级",
        "dimensions": {
            "decision_chain": 16,
            "interaction": 12,
            "relationship_depth": 14,
            "information": 13,
            "support": 16,
            "executive": 7,
        },
        "estimated_win_rate": 72,
        "trend": "improving",
    },
    {
        "customer_id": 2,
        "customer_name": "比亚迪",
        "overall_score": 85,
        "maturity_level": "L4",
        "dimensions": {"decision_chain": 19, "interaction": 14, "relationship_depth": 17, "information": 14, "support": 18, "executive": 8},
        "estimated_win_rate": 85,
        "trend": "stable",
    },
    {
        "customer_id": 3,
        "customer_name": "中创新航",
        "overall_score": 62,
        "maturity_level": "L3",
        "dimensions": {"decision_chain": 12, "interaction": 10, "relationship_depth": 12, "information": 11, "support": 12, "executive": 4},
        "estimated_win_rate": 52,
        "trend": "improving",
    },
    {
        "customer_id": 4,
        "customer_name": "亿纬锂能",
        "overall_score": 72,
        "maturity_level": "L3",
        "dimensions": {"decision_chain": 15, "interaction": 11, "relationship_depth": 14, "information": 12, "support": 14, "executive": 6},
        "estimated_win_rate": 65,
        "trend": "stable",
    },
    {
        "customer_id": 5,
        "customer_name": "欣旺达",
        "overall_score": 42,
        "maturity_level": "L2",
        "dimensions": {"decision_chain": 8, "interaction": 6, "relationship_depth": 8, "information": 8, "support": 8, "executive": 2},
        "estimated_win_rate": 32,
        "trend": "declining",
    },
    {
        "customer_id": 6,
        "customer_name": "蜂巢能源",
        "overall_score": 35,
        "maturity_level": "L2",
        "dimensions": {"decision_chain": 5, "interaction": 5, "relationship_depth": 8, "information": 6, "support": 6, "executive": 2},
        "estimated_win_rate": 25,
        "trend": "stable",
    },
]

# ========== 5. 赢单率综合评估（8 个） ==========

win_rate_assessments = [
    {
        "opportunity_id": 1,
        "opportunity_name": "宁德时代 FCT 测试线项目",
        "factors": {
            "business_relationship": 78,
            "technical_solution": 81,
            "price_competitiveness": 66,
            "other_factors": 72,
        },
        "total_win_rate": 75,
        "confidence": 85,
        "primary_weakness": "价格竞争力",
    },
    {
        "opportunity_id": 2,
        "opportunity_name": "比亚迪 EOL 测试设备项目",
        "factors": {"business_relationship": 85, "technical_solution": 88, "price_competitiveness": 75, "other_factors": 78},
        "total_win_rate": 83,
        "confidence": 90,
        "primary_weakness": "无明显短板",
    },
    {
        "opportunity_id": 3,
        "opportunity_name": "中创新航 ICT 在线测试项目",
        "factors": {"business_relationship": 62, "technical_solution": 70, "price_competitiveness": 55, "other_factors": 58},
        "total_win_rate": 62,
        "confidence": 75,
        "primary_weakness": "商务关系",
    },
    {
        "opportunity_id": 4,
        "opportunity_name": "亿纬锂能烧录设备采购项目",
        "factors": {"business_relationship": 72, "technical_solution": 75, "price_competitiveness": 60, "other_factors": 65},
        "total_win_rate": 69,
        "confidence": 80,
        "primary_weakness": "价格竞争力",
    },
    {
        "opportunity_id": 5,
        "opportunity_name": "欣旺达 FCT 功能测试项目",
        "factors": {"business_relationship": 42, "technical_solution": 50, "price_competitiveness": 55, "other_factors": 45},
        "total_win_rate": 48,
        "confidence": 60,
        "primary_weakness": "商务关系",
    },
    {
        "opportunity_id": 6,
        "opportunity_name": "蜂巢能源 EOL 检测设备项目",
        "factors": {"business_relationship": 35, "technical_solution": 45, "price_competitiveness": 50, "other_factors": 40},
        "total_win_rate": 42,
        "confidence": 55,
        "primary_weakness": "商务关系",
    },
    {
        "opportunity_id": 7,
        "opportunity_name": "国轩高科 ICT 测试设备项目",
        "factors": {"business_relationship": 25, "technical_solution": 35, "price_competitiveness": 50, "other_factors": 30},
        "total_win_rate": 35,
        "confidence": 45,
        "primary_weakness": "商务关系",
    },
    {
        "opportunity_id": 8,
        "opportunity_name": "珠海冠宇老化测试设备项目",
        "factors": {"business_relationship": 82, "technical_solution": 85, "price_competitiveness": 78, "other_factors": 80},
        "total_win_rate": 82,
        "confidence": 92,
        "primary_weakness": "无明显短板",
    },
]

# ========== 6. 竞争对手分析数据 ==========

competitor_data = {
    "analysis_date": "2026-03-01",
    "total_opportunities": 156,
    "time_range": "2024-01-01 ~ 2026-03-01",
    "competitors": [
        {
            "id": 1,
            "name": "竞品 A",
            "description": "德国知名自动化公司",
            "position": "高端市场领导者",
            "headquarters": "德国",
            "strengths": ["品牌知名度高", "技术成熟", "全球服务网络"],
            "weaknesses": ["价格高", "交付周期长", "定制化能力弱"],
        },
        {
            "id": 2,
            "name": "竞品 B",
            "description": "国内上市公司",
            "position": "中端市场主要竞争者",
            "headquarters": "上海",
            "strengths": ["价格适中", "响应速度快", "本地化好"],
            "weaknesses": ["技术积累浅", "案例较少"],
        },
        {
            "id": 3,
            "name": "竞品 C",
            "description": "新兴公司",
            "position": "低端市场挑战者",
            "headquarters": "深圳",
            "strengths": ["价格低", "灵活定制", "服务积极"],
            "weaknesses": ["品牌弱", "稳定性待验证"],
        },
        {
            "id": 4,
            "name": "竞品 D",
            "description": "台系厂商",
            "position": "中端市场细分领域",
            "headquarters": "台湾",
            "strengths": ["性价比高", "电子行业经验丰富"],
            "weaknesses": ["服务网络弱", "大项目经验少"],
        },
    ],
    "win_rate_by_competitor": [
        {"competitor": "竞品 C", "opportunities": 38, "won": 30, "lost": 8, "win_rate": 78.9},
        {"competitor": "竞品 A", "opportunities": 45, "won": 32, "lost": 13, "win_rate": 71.1},
        {"competitor": "竞品 B", "opportunities": 52, "won": 28, "lost": 24, "win_rate": 53.8},
        {"competitor": "竞品 D", "opportunities": 21, "won": 10, "lost": 11, "win_rate": 47.6},
    ],
}

# ========== 7. 销售活动数据 ==========

sales_activities = [
    {"id": 1, "sales_id": 101, "type": "拜访", "customer_id": 1, "date": "2026-02-28", "duration_hours": 3, "outcome": "技术交流"},
    {"id": 2, "sales_id": 101, "type": "电话", "customer_id": 3, "date": "2026-02-27", "duration_hours": 1, "outcome": "需求确认"},
    {"id": 3, "sales_id": 102, "type": "拜访", "customer_id": 2, "date": "2026-02-27", "duration_hours": 4, "outcome": "合同谈判"},
    {"id": 4, "sales_id": 103, "type": "拜访", "customer_id": 4, "date": "2026-02-26", "duration_hours": 2, "outcome": "商务报价"},
    {"id": 5, "sales_id": 103, "type": "拜访", "customer_id": 8, "date": "2026-02-28", "duration_hours": 2, "outcome": "合同跟进"},
    {"id": 6, "sales_id": 104, "type": "电话", "customer_id": 5, "date": "2026-02-15", "duration_hours": 0.5, "outcome": "初步沟通"},
    {"id": 7, "sales_id": 104, "type": "电话", "customer_id": 6, "date": "2026-02-10", "duration_hours": 0.5, "outcome": "初步接触"},
    {"id": 8, "sales_id": 105, "type": "拜访", "customer_id": 7, "date": "2026-02-20", "duration_hours": 2, "outcome": "需求调研"},
]

# ========== 8. 预测数据 ==========

forecast_data = {
    "period": "2026-Q1",
    "company_target": 80000000,
    "company_achieved": 51200000,
    "company_pipeline": 45000000,
    "company_weighted": 28500000,
    "company_predicted": 79700000,
    "company_completion_rate": 99.6,
    "by_team": [
        {"team": "华南大区", "target": 30000000, "achieved": 19800000, "pipeline": 18000000, "weighted": 12000000, "predicted": 31800000, "completion_rate": 106},
        {"team": "华东大区", "target": 28000000, "achieved": 17500000, "pipeline": 15000000, "weighted": 9500000, "predicted": 27000000, "completion_rate": 96.4},
        {"team": "华北大区", "target": 22000000, "achieved": 13900000, "pipeline": 12000000, "weighted": 7000000, "predicted": 20900000, "completion_rate": 95},
    ],
}

# ========== 输出数据 ==========

output_dir = Path("/Users/flw/non-standard-automation-pm/data/demo")
output_dir.mkdir(parents=True, exist_ok=True)

files_to_save = [
    ("sales_reps.json", sales_reps),
    ("customers.json", customers),
    ("opportunities.json", opportunities),
    ("relationship_assessments.json", relationship_assessments),
    ("win_rate_assessments.json", win_rate_assessments),
    ("competitor_data.json", competitor_data),
    ("sales_activities.json", sales_activities),
    ("forecast_data.json", forecast_data),
]

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📦 生成全套演示数据...")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("")

for filename, data in files_to_save:
    output_path = output_dir / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {filename}")

print("")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("📊 数据概览")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"📁 位置：{output_dir}")
print(f"👥 销售代表：{len(sales_reps)} 个")
print(f"🏢 客户：{len(customers)} 个")
print(f"💼 商机：{len(opportunities)} 个")
print(f"📈 关系评估：{len(relationship_assessments)} 个")
print(f"🎯 赢单率评估：{len(win_rate_assessments)} 个")
print(f"⚔️ 竞争对手：{len(competitor_data['competitors'])} 个")
print(f"📝 活动记录：{len(sales_activities)} 个")
print("")

total_pipeline = sum(opp["amount"] for opp in opportunities)
weighted_pipeline = sum(opp["amount"] * opp["probability"] / 100 for opp in opportunities)
print(f"💰 Pipeline 统计:")
print(f"   总额：¥{total_pipeline / 1000000:.1f}M")
print(f"   加权：¥{weighted_pipeline / 1000000:.1f}M")
print("")

print(f"🎯 赢单率分布:")
win_rates = [assess["total_win_rate"] for assess in win_rate_assessments]
print(f"   ≥80%: {sum(1 for r in win_rates if r >= 80)} 个")
print(f"   60-79%: {sum(1 for r in win_rates if 60 <= r < 80)} 个")
print(f"   40-59%: {sum(1 for r in win_rates if 40 <= r < 60)} 个")
print(f"   <40%: {sum(1 for r in win_rates if r < 40)} 个")
print("")

print(f"⚔️ 竞争对手赢单率:")
for comp in competitor_data["win_rate_by_competitor"]:
    print(f"   vs {comp['competitor']}: {comp['win_rate']}% ({comp['won']}/{comp['opportunities']})")
print("")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✨ 演示数据生成完成！")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
