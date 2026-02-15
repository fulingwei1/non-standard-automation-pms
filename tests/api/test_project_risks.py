# -*- coding: utf-8 -*-
"""
项目风险管理模块单元测试
包含15+测试用例，覆盖CRUD、权限控制、风险分析等功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_risk import ProjectRisk, RiskTypeEnum, RiskStatusEnum
from app.models.user import User, ApiPermission, Role, RoleApiPermission


class TestProjectRiskCRUD:
    """测试风险CRUD功能"""

    def test_create_risk_success(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试1：成功创建风险"""
        risk_data = {
            "risk_name": "技术风险-新算法实现",
            "description": "新的视觉识别算法可能存在性能问题",
            "risk_type": "TECHNICAL",
            "probability": 4,
            "impact": 5,
            "mitigation_plan": "提前进行技术验证",
            "contingency_plan": "准备备用方案",
        }
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/risks",
            json=risk_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["risk_name"] == risk_data["risk_name"]
        assert data["data"]["risk_type"] == risk_data["risk_type"]
        assert data["data"]["risk_score"] == 20  # 4 * 5
        assert data["data"]["risk_level"] == "CRITICAL"  # score > 15
        assert "RISK-" in data["data"]["risk_code"]

    def test_create_risk_auto_calculate_score(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试2：风险评分自动计算"""
        test_cases = [
            (1, 1, 1, "LOW"),      # 1*1=1
            (2, 2, 4, "LOW"),      # 2*2=4
            (3, 2, 6, "MEDIUM"),   # 3*2=6
            (3, 4, 12, "HIGH"),    # 3*4=12
            (5, 5, 25, "CRITICAL"), # 5*5=25
        ]
        
        for probability, impact, expected_score, expected_level in test_cases:
            risk_data = {
                "risk_name": f"测试风险 P{probability}*I{impact}",
                "description": "测试用例",
                "risk_type": "COST",
                "probability": probability,
                "impact": impact,
            }
            
            response = client.post(
                f"/api/v1/projects/{test_project.id}/risks",
                json=risk_data,
                headers=admin_headers,
            )
            
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["risk_score"] == expected_score
            assert data["risk_level"] == expected_level

    def test_create_risk_invalid_type(
        self,
        client: TestClient,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试3：无效的风险类型"""
        risk_data = {
            "risk_name": "测试风险",
            "risk_type": "INVALID_TYPE",
            "probability": 3,
            "impact": 3,
        }
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/risks",
            json=risk_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_risk_invalid_probability(
        self,
        client: TestClient,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试4：无效的概率值（超出1-5范围）"""
        risk_data = {
            "risk_name": "测试风险",
            "risk_type": "TECHNICAL",
            "probability": 6,  # 超出范围
            "impact": 3,
        }
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/risks",
            json=risk_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 422

    def test_get_risks_list(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试5：获取风险列表"""
        # 创建多个风险
        for i in range(3):
            risk = ProjectRisk(
                risk_code=f"RISK-TEST-{i:04d}",
                project_id=test_project.id,
                risk_name=f"测试风险{i}",
                risk_type=RiskTypeEnum.TECHNICAL,
                probability=3,
                impact=3,
                risk_score=9,
                risk_level="MEDIUM",
                status=RiskStatusEnum.IDENTIFIED,
            )
            risk.calculate_risk_score()
            db.add(risk)
        db.commit()
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risks",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_get_risks_with_filters(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试6：使用筛选条件获取风险列表"""
        # 创建不同类型的风险
        risk1 = ProjectRisk(
            risk_code="RISK-TEST-TECH-001",
            project_id=test_project.id,
            risk_name="技术风险",
            risk_type=RiskTypeEnum.TECHNICAL,
            probability=4,
            impact=4,
            status=RiskStatusEnum.IDENTIFIED,
        )
        risk1.calculate_risk_score()
        
        risk2 = ProjectRisk(
            risk_code="RISK-TEST-COST-001",
            project_id=test_project.id,
            risk_name="成本风险",
            risk_type=RiskTypeEnum.COST,
            probability=2,
            impact=2,
            status=RiskStatusEnum.MONITORING,
        )
        risk2.calculate_risk_score()
        
        db.add_all([risk1, risk2])
        db.commit()
        
        # 筛选技术风险
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risks?risk_type=TECHNICAL",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert all(item["risk_type"] == "TECHNICAL" for item in data["items"])

    def test_get_risk_detail(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试7：获取风险详情"""
        risk = ProjectRisk(
            risk_code="RISK-TEST-DETAIL-001",
            project_id=test_project.id,
            risk_name="详情测试风险",
            risk_type=RiskTypeEnum.SCHEDULE,
            probability=3,
            impact=4,
            status=RiskStatusEnum.IDENTIFIED,
        )
        risk.calculate_risk_score()
        db.add(risk)
        db.commit()
        db.refresh(risk)
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risks/{risk.id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == risk.id
        assert data["risk_name"] == risk.risk_name
        assert data["risk_score"] == 12

    def test_update_risk(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试8：更新风险信息"""
        risk = ProjectRisk(
            risk_code="RISK-TEST-UPDATE-001",
            project_id=test_project.id,
            risk_name="待更新风险",
            risk_type=RiskTypeEnum.QUALITY,
            probability=2,
            impact=2,
            status=RiskStatusEnum.IDENTIFIED,
        )
        risk.calculate_risk_score()
        db.add(risk)
        db.commit()
        db.refresh(risk)
        
        update_data = {
            "risk_name": "已更新风险",
            "probability": 4,
            "impact": 5,
            "status": "MONITORING",
        }
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}/risks/{risk.id}",
            json=update_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["risk_name"] == "已更新风险"
        assert data["risk_score"] == 20  # 重新计算
        assert data["risk_level"] == "CRITICAL"
        assert data["status"] == "MONITORING"

    def test_update_risk_auto_close_date(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试9：更新状态为CLOSED时自动设置关闭日期"""
        risk = ProjectRisk(
            risk_code="RISK-TEST-CLOSE-001",
            project_id=test_project.id,
            risk_name="待关闭风险",
            risk_type=RiskTypeEnum.COST,
            probability=2,
            impact=2,
            status=RiskStatusEnum.MONITORING,
        )
        risk.calculate_risk_score()
        db.add(risk)
        db.commit()
        db.refresh(risk)
        
        update_data = {"status": "CLOSED"}
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}/risks/{risk.id}",
            json=update_data,
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "CLOSED"
        assert data["actual_closure_date"] is not None

    def test_delete_risk(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试10：删除风险"""
        risk = ProjectRisk(
            risk_code="RISK-TEST-DELETE-001",
            project_id=test_project.id,
            risk_name="待删除风险",
            risk_type=RiskTypeEnum.TECHNICAL,
            probability=2,
            impact=2,
            status=RiskStatusEnum.IDENTIFIED,
        )
        risk.calculate_risk_score()
        db.add(risk)
        db.commit()
        db.refresh(risk)
        
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/risks/{risk.id}",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        
        # 验证已删除
        deleted_risk = db.query(ProjectRisk).filter(ProjectRisk.id == risk.id).first()
        assert deleted_risk is None


class TestProjectRiskAnalysis:
    """测试风险分析功能"""

    def test_risk_matrix(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试11：获取风险矩阵"""
        # 创建不同概率和影响的风险
        risks_data = [
            (1, 1), (1, 5), (5, 1), (5, 5),  # 四个角
            (3, 3), (3, 3),  # 中间两个相同的
        ]
        
        for prob, imp in risks_data:
            risk = ProjectRisk(
                risk_code=f"RISK-MATRIX-P{prob}I{imp}",
                project_id=test_project.id,
                risk_name=f"风险P{prob}I{imp}",
                risk_type=RiskTypeEnum.TECHNICAL,
                probability=prob,
                impact=imp,
                status=RiskStatusEnum.MONITORING,
            )
            risk.calculate_risk_score()
            db.add(risk)
        db.commit()
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risk-matrix",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "matrix" in data
        assert "summary" in data
        assert len(data["matrix"]) == 25  # 5x5矩阵
        
        # 验证特定单元格
        cell_3_3 = [m for m in data["matrix"] if m["probability"] == 3 and m["impact"] == 3][0]
        assert cell_3_3["count"] == 2  # 有两个风险

    def test_risk_summary(
        self,
        client: TestClient,
        db: Session,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试12：获取风险汇总统计"""
        # 创建不同类型和等级的风险
        risks = [
            ("TECHNICAL", 5, 5, False),   # CRITICAL
            ("TECHNICAL", 4, 3, False),   # HIGH
            ("COST", 3, 3, False),        # MEDIUM
            ("SCHEDULE", 2, 2, False),    # LOW
            ("QUALITY", 4, 4, True),      # HIGH, occurred
        ]
        
        for risk_type, prob, imp, occurred in risks:
            risk = ProjectRisk(
                risk_code=f"RISK-SUM-{risk_type}-{prob}{imp}",
                project_id=test_project.id,
                risk_name=f"风险{risk_type}",
                risk_type=risk_type,
                probability=prob,
                impact=imp,
                is_occurred=occurred,
                status=RiskStatusEnum.MONITORING,
            )
            risk.calculate_risk_score()
            db.add(risk)
        db.commit()
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risk-summary",
            headers=admin_headers,
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert data["total_risks"] >= 5
        assert data["by_type"]["TECHNICAL"] >= 2
        assert data["by_type"]["COST"] >= 1
        assert data["by_level"]["CRITICAL"] >= 1
        assert data["by_level"]["HIGH"] >= 2
        assert data["occurred_count"] >= 1
        assert data["high_priority_count"] >= 3  # HIGH + CRITICAL
        assert data["avg_risk_score"] > 0


class TestProjectRiskPermissions:
    """测试权限控制"""

    def test_create_risk_without_permission(
        self,
        client: TestClient,
        test_project: Project,
        user_headers: dict,
    ):
        """测试13：无权限创建风险"""
        risk_data = {
            "risk_name": "测试风险",
            "risk_type": "TECHNICAL",
            "probability": 3,
            "impact": 3,
        }
        
        # 假设user_headers没有risk:create权限
        response = client.post(
            f"/api/v1/projects/{test_project.id}/risks",
            json=risk_data,
            headers=user_headers,
        )
        
        # 应该返回403或401
        assert response.status_code in [401, 403]

    def test_read_risk_without_permission(
        self,
        client: TestClient,
        test_project: Project,
        user_headers: dict,
    ):
        """测试14：无权限读取风险"""
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risks",
            headers=user_headers,
        )
        
        assert response.status_code in [401, 403]


class TestProjectRiskValidation:
    """测试数据验证"""

    def test_risk_four_types_supported(
        self,
        client: TestClient,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试15：支持4种风险类型"""
        risk_types = ["TECHNICAL", "COST", "SCHEDULE", "QUALITY"]
        
        for risk_type in risk_types:
            risk_data = {
                "risk_name": f"{risk_type}风险测试",
                "risk_type": risk_type,
                "probability": 3,
                "impact": 3,
            }
            
            response = client.post(
                f"/api/v1/projects/{test_project.id}/risks",
                json=risk_data,
                headers=admin_headers,
            )
            
            assert response.status_code == 200
            assert response.json()["data"]["risk_type"] == risk_type

    def test_project_not_exist(
        self,
        client: TestClient,
        admin_headers: dict,
    ):
        """测试16：项目不存在"""
        response = client.get(
            "/api/v1/projects/99999/risks",
            headers=admin_headers,
        )
        
        assert response.status_code == 404

    def test_risk_not_exist(
        self,
        client: TestClient,
        test_project: Project,
        admin_headers: dict,
    ):
        """测试17：风险不存在"""
        response = client.get(
            f"/api/v1/projects/{test_project.id}/risks/99999",
            headers=admin_headers,
        )
        
        assert response.status_code == 404
