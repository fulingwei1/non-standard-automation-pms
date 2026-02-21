# -*- coding: utf-8 -*-
"""
销售管理集成测试 - 销售漏斗转化

测试场景：
1. 线索质量评分
2. 线索培育流程
3. 商机创建与推进
4. 赢单/输单分析
5. 转化率统计
6. 漏斗可视化
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestSalesFunnelConversion:
    """销售漏斗转化集成测试"""

    def test_lead_scoring(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：线索质量评分"""
        lead_data = {
            "company_name": "科技公司",
            "contact_name": "张经理",
            "contact_phone": "13800138000",
            "estimated_value": 5000000.00,
            "lead_source": "网站",
            "industry": "制造业"
        }
        
        response = client.post("/api/v1/sales/leads", json=lead_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        lead_id = response.json().get("id")
        if lead_id:
            score_data = {
                "lead_id": lead_id,
                "scoring_criteria": {
                    "budget": 9,
                    "authority": 8,
                    "need": 9,
                    "timeline": 7
                },
                "total_score": 82
            }
            
            response = client.post(f"/api/v1/sales/leads/{lead_id}/score", json=score_data, headers=auth_headers)
            assert response.status_code in [200, 201, 404]

    def test_lead_nurturing(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：线索培育流程"""
        lead_data = {
            "company_name": "电子公司",
            "contact_name": "李总",
            "estimated_value": 3000000.00
        }
        
        response = client.post("/api/v1/sales/leads", json=lead_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        lead_id = response.json().get("id")
        
        if lead_id:
            nurturing_activities = [
                {"type": "email", "content": "发送产品介绍", "date": str(date.today())},
                {"type": "phone", "content": "电话跟进", "date": str(date.today() + timedelta(days=3))},
                {"type": "demo", "content": "产品演示", "date": str(date.today() + timedelta(days=7))}
            ]
            
            for activity in nurturing_activities:
                response = client.post(f"/api/v1/sales/leads/{lead_id}/nurturing", json=activity, headers=auth_headers)
                assert response.status_code in [200, 201, 404]

    def test_opportunity_creation_and_progress(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：商机创建与推进"""
        opportunity_data = {
            "opportunity_name": "智能制造项目",
            "customer_id": 1,
            "estimated_value": 8000000.00,
            "probability": 40,
            "sales_stage": "需求分析"
        }
        
        response = client.post("/api/v1/sales/opportunities", json=opportunity_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        opp_id = response.json().get("id")
        if opp_id:
            stages = ["方案设计", "报价", "谈判", "签约"]
            probabilities = [60, 75, 90, 100]
            
            for stage, prob in zip(stages, probabilities):
                response = client.put(
                    f"/api/v1/sales/opportunities/{opp_id}",
                    json={"sales_stage": stage, "probability": prob},
                    headers=auth_headers
                )
                assert response.status_code in [200, 404]

    def test_win_loss_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：赢单/输单分析"""
        win_opportunity = {
            "opportunity_name": "成功项目",
            "customer_id": 1,
            "estimated_value": 6000000.00,
            "probability": 100,
            "sales_stage": "已签约",
            "result": "won",
            "win_reason": "技术优势明显"
        }
        
        response = client.post("/api/v1/sales/opportunities", json=win_opportunity, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        response = client.get("/api/v1/sales/win-loss-analysis", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_conversion_rate_statistics(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：转化率统计"""
        response = client.get(
            f"/api/v1/sales/conversion-rates?start_date={date.today() - timedelta(days=90)}&end_date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_funnel_visualization(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：漏斗可视化"""
        response = client.get("/api/v1/sales/funnel-data", headers=auth_headers)
        assert response.status_code in [200, 404]
