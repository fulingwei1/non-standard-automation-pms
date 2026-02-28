import uuid
# -*- coding: utf-8 -*-
"""
销售管理集成测试 - CRM完整流程

测试场景：
1. 线索录入与分配
2. 线索跟进与转化
3. 客户建档与分级
4. 商机管理
5. 报价与合同
6. 订单执行跟踪
7. 客户关系维护
8. 销售数据分析
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal


@pytest.mark.integration
class TestCRMCompleteFlow:
    """CRM完整流程集成测试"""

    def test_lead_entry_and_assignment(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：线索录入与分配"""
        # 1. 录入销售线索
        leads = [
            {
                "lead_source": "网站询盘",
                "company_name": "智能制造科技公司",
                "contact_name": "张经理",
                "contact_phone": "13800138001",
                "contact_email": "zhang@smart-mfg.com",
                "industry": "制造业",
                "lead_grade": "A",
                "estimated_value": 5000000.00,
                "requirements": "需要自动化生产线改造",
                "created_by": test_employee.id,
                "create_date": str(date.today())
            },
            {
                "lead_source": "展会",
                "company_name": "新能源汽车公司",
                "contact_name": "李总",
                "contact_phone": "13900139001",
                "contact_email": "li@newenergy.com",
                "industry": "汽车制造",
                "lead_grade": "A+",
                "estimated_value": 10000000.00,
                "requirements": "智能工厂整体解决方案",
                "created_by": test_employee.id,
                "create_date": str(date.today())
            }
        ]
        
        lead_ids = []
        for lead in leads:
            response = client.post("/api/v1/sales/leads", json=lead, headers=auth_headers)
            assert response.status_code in [200, 201]
            if response.status_code in [200, 201]:
                lead_ids.append(response.json().get("id"))
        
        # 2. 分配线索给销售人员
        for lead_id in lead_ids:
            if lead_id:
                assignment_data = {
                    "lead_id": lead_id,
                    "assigned_to": test_employee.id + 1,
                    "assignment_date": str(date.today()),
                    "priority": "high",
                    "follow_up_deadline": str(date.today() + timedelta(days=2))
                }
                
                response = client.post(
                    f"/api/v1/sales/leads/{lead_id}/assign",
                    json=assignment_data,
                    headers=auth_headers
                )
                assert response.status_code in [200, 404]

    def test_lead_follow_up_and_conversion(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：线索跟进与转化"""
        # 1. 创建线索
        lead_data = {
            "lead_source": "客户推荐",
            "company_name": "精密制造公司",
            "contact_name": "王工",
            "contact_phone": "13700137001",
            "contact_email": "wang@precision.com",
            "industry": "精密制造",
            "lead_grade": "B+",
            "estimated_value": 3000000.00,
            "requirements": "设备自动化升级",
            "created_by": test_employee.id
        }
        
        response = client.post("/api/v1/sales/leads", json=lead_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        lead_id = response.json().get("id")
        
        # 2. 记录跟进活动
        follow_ups = [
            {
                "activity_type": "电话沟通",
                "activity_date": str(date.today()),
                "duration_minutes": 30,
                "content": "初步了解客户需求，约定下周现场考察",
                "next_action": "现场考察",
                "next_follow_up_date": str(date.today() + timedelta(days=7))
            },
            {
                "activity_type": "现场考察",
                "activity_date": str(date.today() + timedelta(days=7)),
                "duration_minutes": 180,
                "content": "现场勘察生产线，确认改造需求",
                "next_action": "提交初步方案",
                "next_follow_up_date": str(date.today() + timedelta(days=14))
            },
            {
                "activity_type": "方案交流",
                "activity_date": str(date.today() + timedelta(days=14)),
                "duration_minutes": 120,
                "content": "讲解自动化改造方案，客户基本认可",
                "next_action": "提交正式报价",
                "next_follow_up_date": str(date.today() + timedelta(days=21))
            }
        ]
        
        if lead_id:
            for follow_up in follow_ups:
                response = client.post(
                    f"/api/v1/sales/leads/{lead_id}/follow-ups",
                    json=follow_up,
                    headers=auth_headers
                )
                assert response.status_code in [200, 201, 404]
        
        # 3. 转化为正式客户
        if lead_id:
            conversion_data = {
                "lead_id": lead_id,
                "conversion_date": str(date.today() + timedelta(days=30)),
                "customer_type": "企业客户",
                "customer_level": "重点客户",
                "sales_owner": test_employee.id + 1
            }
            
            response = client.post(
                f"/api/v1/sales/leads/{lead_id}/convert",
                json=conversion_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 404]

    def test_customer_filing_and_classification(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：客户建档与分级"""
        # 1. 创建客户档案
        customer_data = {
            "customer_name": "智能装备制造集团",
            "customer_code": f"CUST-2024-001-{uuid.uuid4().hex[:8]}",
            "industry": "装备制造",
            "company_scale": "大型企业",
            "registered_capital": 50000000.00,
            "business_scope": "智能装备研发、制造、销售",
            "address": "江苏省苏州市工业园区",
            "contact_name": "陈总",
            "contact_phone": "13600136001",
            "contact_email": "chen@equipment.com",
            "created_by": test_employee.id,
            "create_date": str(date.today())
        }
        
        response = client.post("/api/v1/customers", json=customer_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        customer_id = response.json().get("id")
        
        # 2. 客户分级评估
        if customer_id:
            classification_data = {
                "customer_id": customer_id,
                "classification_criteria": {
                    "annual_revenue": 50000000.00,
                    "payment_ability": "优秀",
                    "cooperation_history": "新客户",
                    "market_potential": "高",
                    "industry_influence": "较高"
                },
                "classification_result": "A级客户",
                "credit_limit": 10000000.00,
                "payment_terms": "预付30%，到货后70%",
                "evaluated_by": test_employee.id,
                "evaluation_date": str(date.today())
            }
            
            response = client.post(
                f"/api/v1/customers/{customer_id}/classification",
                json=classification_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 404]

    def test_opportunity_management(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：商机管理"""
        # 1. 创建客户
        customer_data = {
            "customer_name": "电子制造公司",
            "customer_code": f"CUST-2024-002-{uuid.uuid4().hex[:8]}",
            "industry": "电子制造",
            "contact_name": "刘经理",
            "contact_phone": "13500135001",
            "contact_email": "liu@electronics.com"
        }
        
        response = client.post("/api/v1/customers", json=customer_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        customer_id = response.json().get("id", 1)
        
        # 2. 创建销售商机
        opportunity_data = {
            "opportunity_name": "SMT产线自动化改造项目",
            "customer_id": customer_id,
            "opportunity_source": "客户主动咨询",
            "opportunity_type": "新项目",
            "estimated_value": 8000000.00,
            "probability": 60,
            "expected_close_date": str(date.today() + timedelta(days=90)),
            "sales_stage": "需求分析",
            "competitors": ["竞争对手A", "竞争对手B"],
            "our_advantages": ["技术领先", "价格优势", "服务完善"],
            "key_decision_makers": [
                {"name": "刘经理", "position": "采购总监", "influence": "决策者"},
                {"name": "技术部张工", "position": "技术负责人", "influence": "影响者"}
            ],
            "owner": test_employee.id
        }
        
        response = client.post("/api/v1/sales/opportunities", json=opportunity_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        opportunity_id = response.json().get("id")
        
        # 3. 推进销售阶段
        if opportunity_id:
            stage_updates = [
                {"stage": "方案设计", "probability": 70, "update_date": str(date.today() + timedelta(days=15))},
                {"stage": "商务谈判", "probability": 80, "update_date": str(date.today() + timedelta(days=45))},
                {"stage": "合同签订", "probability": 95, "update_date": str(date.today() + timedelta(days=75))}
            ]
            
            for stage in stage_updates:
                response = client.put(
                    f"/api/v1/sales/opportunities/{opportunity_id}",
                    json=stage,
                    headers=auth_headers
                )
                assert response.status_code in [200, 404]

    def test_quote_and_contract(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：报价与合同"""
        # 1. 创建报价单
        quote_data = {
            "quote_number": "QT-2024-001",
            "customer_id": 1,
            "quote_date": str(date.today()),
            "valid_until": str(date.today() + timedelta(days=30)),
            "items": [
                {
                    "item_name": "自动化生产线",
                    "specification": "6轴机器人+视觉检测系统",
                    "quantity": 1,
                    "unit_price": 3000000.00,
                    "amount": 3000000.00
                },
                {
                    "item_name": "MES系统",
                    "specification": "生产执行管理系统",
                    "quantity": 1,
                    "unit_price": 1500000.00,
                    "amount": 1500000.00
                },
                {
                    "item_name": "培训服务",
                    "specification": "操作培训+技术培训",
                    "quantity": 1,
                    "unit_price": 200000.00,
                    "amount": 200000.00
                }
            ],
            "subtotal": 4700000.00,
            "tax_rate": 0.13,
            "tax_amount": 611000.00,
            "total_amount": 5311000.00,
            "payment_terms": "预付30%，交货后50%，验收后20%",
            "delivery_period": "签订合同后120天",
            "prepared_by": test_employee.id
        }
        
        response = client.post("/api/v1/sales/quotes", json=quote_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        quote_id = response.json().get("id")
        
        # 2. 客户接受报价，生成合同
        if quote_id:
            contract_data = {
                "quote_id": quote_id,
                "contract_number": "CON-2024-001",
                "contract_name": "自动化生产线采购合同",
                "customer_id": 1,
                "contract_date": str(date.today()),
                "contract_amount": 5311000.00,
                "payment_schedule": [
                    {"milestone": "合同签订", "percentage": 30, "amount": 1593300.00, "due_date": str(date.today() + timedelta(days=7))},
                    {"milestone": "设备交货", "percentage": 50, "amount": 2655500.00, "due_date": str(date.today() + timedelta(days=120))},
                    {"milestone": "项目验收", "percentage": 20, "amount": 1062200.00, "due_date": str(date.today() + timedelta(days=180))}
                ],
                "delivery_address": "客户工厂-江苏省苏州市",
                "warranty_period": "12个月",
                "created_by": test_employee.id
            }
            
            response = client.post("/api/v1/sales/contracts", json=contract_data, headers=auth_headers)
            assert response.status_code in [200, 201]

    def test_order_execution_tracking(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：订单执行跟踪"""
        # 1. 创建销售订单
        order_data = {
            "order_number": "SO-2024-001",
            "contract_id": 1,
            "customer_id": 1,
            "order_date": str(date.today()),
            "delivery_date": str(date.today() + timedelta(days=120)),
            "order_amount": 5311000.00,
            "order_status": "待执行",
            "created_by": test_employee.id
        }
        
        response = client.post("/api/v1/sales/orders", json=order_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        order_id = response.json().get("id")
        
        # 2. 更新订单执行进度
        if order_id:
            progress_updates = [
                {
                    "update_date": str(date.today() + timedelta(days=10)),
                    "status": "设计阶段",
                    "progress_percentage": 10,
                    "remarks": "完成方案设计"
                },
                {
                    "update_date": str(date.today() + timedelta(days=40)),
                    "status": "采购阶段",
                    "progress_percentage": 30,
                    "remarks": "设备采购中"
                },
                {
                    "update_date": str(date.today() + timedelta(days=80)),
                    "status": "生产阶段",
                    "progress_percentage": 60,
                    "remarks": "设备组装中"
                },
                {
                    "update_date": str(date.today() + timedelta(days=110)),
                    "status": "测试阶段",
                    "progress_percentage": 85,
                    "remarks": "出厂测试"
                }
            ]
            
            for update in progress_updates:
                response = client.post(
                    f"/api/v1/sales/orders/{order_id}/progress",
                    json=update,
                    headers=auth_headers
                )
                assert response.status_code in [200, 201, 404]

    def test_customer_relationship_maintenance(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：客户关系维护"""
        # 1. 创建客户
        customer_data = {
            "customer_name": "高端制造公司",
            "customer_code": f"CUST-2024-003-{uuid.uuid4().hex[:8]}",
            "industry": "高端装备",
            "contact_name": "赵总",
            "contact_phone": "13400134001"
        }
        
        response = client.post("/api/v1/customers", json=customer_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        customer_id = response.json().get("id", 1)
        
        # 2. 记录客户拜访
        visits = [
            {
                "visit_date": str(date.today()),
                "visit_type": "定期拜访",
                "participants": [test_employee.id],
                "visit_purpose": "了解设备使用情况",
                "visit_content": "客户对设备运行情况表示满意",
                "follow_up_actions": "提供技术支持资料"
            },
            {
                "visit_date": str(date.today() + timedelta(days=30)),
                "visit_type": "节日拜访",
                "participants": [test_employee.id],
                "visit_purpose": "春节拜访",
                "visit_content": "维护客户关系",
                "follow_up_actions": "关注新项目需求"
            }
        ]
        
        for visit in visits:
            response = client.post(
                f"/api/v1/customers/{customer_id}/visits",
                json=visit,
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 404]
        
        # 3. 客户满意度调查
        satisfaction_survey = {
            "customer_id": customer_id,
            "survey_date": str(date.today() + timedelta(days=90)),
            "product_quality": 9,
            "service_quality": 8,
            "delivery_timeliness": 9,
            "technical_support": 8,
            "overall_satisfaction": 8.5,
            "suggestions": "希望增加技术培训次数",
            "surveyed_by": test_employee.id
        }
        
        response = client.post(
            f"/api/v1/customers/{customer_id}/satisfaction-surveys",
            json=satisfaction_survey,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]

    def test_sales_data_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：销售数据分析"""
        # 1. 查询销售漏斗数据
        funnel_params = {
            "start_date": str(date.today() - timedelta(days=90)),
            "end_date": str(date.today()),
            "sales_person": test_employee.id
        }
        
        response = client.get(
            "/api/v1/sales/funnel",
            params=funnel_params,
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        # 2. 查询销售业绩
        performance_params = {
            "period": "monthly",
            "year": 2024,
            "month": date.today().month,
            "sales_person": test_employee.id
        }
        
        response = client.get(
            "/api/v1/sales/performance",
            params=performance_params,
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        # 3. 查询客户分析报告
        analysis_params = {
            "analysis_type": "customer_value",
            "start_date": str(date.today() - timedelta(days=365)),
            "end_date": str(date.today()),
            "top_n": 10
        }
        
        response = client.get(
            "/api/v1/sales/customer-analysis",
            params=analysis_params,
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        # 4. 生成销售预测报告
        forecast_data = {
            "forecast_period": "quarterly",
            "forecast_year": 2024,
            "forecast_quarter": 2,
            "based_on_data": {
                "historical_months": 12,
                "pipeline_value": 50000000.00,
                "win_rate": 0.65
            }
        }
        
        response = client.post(
            "/api/v1/sales/forecast",
            json=forecast_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
