"""
项目复盘API端点测试
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal

try:
    from app.main import app
    from app.models.project import Project
    from app.models.project_review import ProjectReview
except ImportError as e:
    pytest.skip(f"project_review dependencies not available: {e}", allow_module_level=True)


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """认证头"""
    # 登录获取token
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(db, auth_headers):
    """测试项目"""
    project = Project(
        code="API_TEST_001",
        name="API测试项目",
        status="COMPLETED",
        budget_amount=Decimal("500000.00")
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestReviewsAPI:
    """复盘报告API测试"""
    
    def test_generate_review_report(self, client, auth_headers, test_project):
        """测试生成复盘报告"""
        response = client.post(
            "/api/v1/project-reviews/generate",
            headers=auth_headers,
            json={
                "project_id": test_project.id,
                "review_type": "POST_MORTEM",
                "reviewer_id": 1,
                "auto_extract_lessons": True,
                "auto_sync_knowledge": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "review_id" in data
        assert "review_no" in data
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] < 30000  # 30秒限制
    
    def test_list_reviews(self, client, auth_headers):
        """测试获取复盘列表"""
        response = client.get(
            "/api/v1/project-reviews",
            headers=auth_headers,
            params={"skip": 0, "limit": 20}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_get_review_detail(self, client, auth_headers, db, test_project):
        """测试获取复盘详情"""
        # 先创建一个复盘
        review = ProjectReview(
            review_no="TEST_REV_001",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            status="DRAFT"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.get(
            f"/api/v1/project-reviews/{review.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review.id
        assert data["review_no"] == review.review_no
    
    def test_update_review(self, client, auth_headers, db, test_project):
        """测试更新复盘"""
        review = ProjectReview(
            review_no="TEST_REV_002",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            status="DRAFT"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.patch(
            f"/api/v1/project-reviews/{review.id}",
            headers=auth_headers,
            json={
                "status": "PUBLISHED",
                "customer_satisfaction": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PUBLISHED"
        assert data["customer_satisfaction"] == 5
    
    def test_get_review_stats(self, client, auth_headers):
        """测试获取统计信息"""
        response = client.get(
            "/api/v1/project-reviews/stats/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_reviews" in data
        assert "ai_generated_count" in data
        assert "average_quality_score" in data


class TestLessonsAPI:
    """经验教训API测试"""
    
    def test_extract_lessons(self, client, auth_headers, db, test_project):
        """测试提取经验教训"""
        # 创建复盘
        review = ProjectReview(
            review_no="TEST_REV_LESSON",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            success_factors="成功要素1\\n成功要素2",
            problems="问题1\\n问题2",
            status="PUBLISHED"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.post(
            "/api/v1/project-reviews/lessons/extract",
            headers=auth_headers,
            json={
                "review_id": review.id,
                "min_confidence": 0.6,
                "auto_save": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "extracted_count" in data
        assert "saved_count" in data
    
    def test_list_lessons(self, client, auth_headers):
        """测试获取经验列表"""
        response = client.get(
            "/api/v1/project-reviews/lessons",
            headers=auth_headers,
            params={"limit": 50}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestComparisonAPI:
    """对比分析API测试"""
    
    def test_compare_with_history(self, client, auth_headers, db, test_project):
        """测试历史对比"""
        review = ProjectReview(
            review_no="TEST_REV_CMP",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            schedule_variance=10,
            cost_variance=Decimal("50000"),
            status="PUBLISHED"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.post(
            "/api/v1/project-reviews/comparison/compare",
            headers=auth_headers,
            json={
                "review_id": review.id,
                "similarity_type": "industry",
                "comparison_limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "current_metrics" in data
        assert "improvements" in data
    
    def test_get_improvements(self, client, auth_headers, db, test_project):
        """测试获取改进建议"""
        review = ProjectReview(
            review_no="TEST_REV_IMP",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            status="PUBLISHED"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.get(
            f"/api/v1/project-reviews/comparison/{review.id}/improvements",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "improvements" in data


class TestKnowledgeAPI:
    """知识库集成API测试"""
    
    def test_sync_to_knowledge(self, client, auth_headers, db, test_project):
        """测试同步到知识库"""
        review = ProjectReview(
            review_no="TEST_REV_KNOW",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            success_factors="成功要素",
            status="PUBLISHED"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.post(
            "/api/v1/project-reviews/knowledge/sync",
            headers=auth_headers,
            json={
                "review_id": review.id,
                "auto_publish": True,
                "include_lessons": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "knowledge_case_id" in data
        assert "quality_score" in data
    
    def test_get_knowledge_impact(self, client, auth_headers, db, test_project):
        """测试获取知识库影响"""
        review = ProjectReview(
            review_no="TEST_REV_IMPACT",
            project_id=test_project.id,
            project_code=test_project.code,
            review_date=date.today(),
            reviewer_id=1,
            reviewer_name="测试员",
            status="PUBLISHED"
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        response = client.get(
            f"/api/v1/project-reviews/knowledge/{review.id}/knowledge-impact",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "synced" in data


# 集成测试
class TestIntegration:
    """集成测试"""
    
    def test_complete_workflow(self, client, auth_headers, test_project):
        """测试完整工作流"""
        # 1. 生成复盘报告
        gen_response = client.post(
            "/api/v1/project-reviews/generate",
            headers=auth_headers,
            json={
                "project_id": test_project.id,
                "reviewer_id": 1,
                "auto_extract_lessons": True,
                "auto_sync_knowledge": True
            }
        )
        assert gen_response.status_code == 200
        review_id = gen_response.json()["review_id"]
        
        # 2. 获取复盘详情
        detail_response = client.get(
            f"/api/v1/project-reviews/{review_id}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200
        
        # 3. 获取经验教训
        lessons_response = client.get(
            "/api/v1/project-reviews/lessons",
            headers=auth_headers,
            params={"review_id": review_id}
        )
        assert lessons_response.status_code == 200
        
        # 4. 进行对比分析
        compare_response = client.post(
            "/api/v1/project-reviews/comparison/compare",
            headers=auth_headers,
            json={"review_id": review_id}
        )
        assert compare_response.status_code == 200
        
        # 5. 检查知识库影响
        impact_response = client.get(
            f"/api/v1/project-reviews/knowledge/{review_id}/knowledge-impact",
            headers=auth_headers
        )
        assert impact_response.status_code == 200
