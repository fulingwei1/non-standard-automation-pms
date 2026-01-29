# -*- coding: utf-8 -*-
"""
ECN知识库服务测试
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.enums import EcnChangeTypeEnum
from app.services.ecn_knowledge_service import EcnKnowledgeService


@pytest.fixture
def ecn_knowledge_service(db_session: Session):
    return EcnKnowledgeService(db_session)


@pytest.fixture
def test_engineer(db_session: Session):
    from tests.conftest import _get_or_create_user

    user = _get_or_create_user(
        db_session,
        username="ecn_test_user",
        password="test123",
        real_name="ECN测试用户",
        department="工程部",
        employee_role="ENGINEER",
    )

    db_session.flush()
    return user


@pytest.fixture
def test_customer(db_session: Session):
    from app.models.project import Customer

    customer = Customer(
        customer_code="ECN-CUST",
        customer_name="ECN测试客户",
        contact_person="王五",
        contact_phone="13800000001",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()
    return customer


@pytest.fixture
def test_project(db_session: Session, test_engineer, test_customer):
    from app.models.project import Project, ProjectStage, ProjectStatus, ProjectHealth

    project = Project(
        project_code="PJ-ECN-001",
        project_name="ECN测试项目",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        stage=ProjectStage.S2.value,
        status=ProjectStatus.ST04.value,
        health=ProjectHealth.H1.value,
        pm_id=test_engineer.id,
        pm_name=test_engineer.real_name,
        created_by=test_engineer.id,
    )
    db_session.add(project)
    db_session.flush()
    return project


@pytest.fixture
def test_ecn(db_session: Session, test_project, test_engineer):
    ecn = Ecn(
        ecn_code="ECN-2025001",
        ecn_title="测试ECN",
        ecn_type=EcnChangeTypeEnum.DESIGN.value,
        project_id=test_project.id,
        project_code=test_project.project_code,
        project_name=test_project.project_name,
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        requester_id=test_engineer.id,
        requester_name=test_engineer.real_name,
        priority="HIGH",
        reason="设计优化需要",
        created_at=datetime.now(),
        created_by=test_engineer.id,
    )
    db_session.add(ecn)
    db_session.commit()
    db_session.refresh(ecn)
    return ecn


class TestEcnKnowledgeServiceInit:
    def test_init(self, ecn_knowledge_service, db_session):
        assert ecn_knowledge_service.db == db_session
        assert hasattr(ecn_knowledge_service, "logger")


class TestSearchSimilarEcns:
    def test_no_ecns(self, ecn_knowledge_service, db_session):
        """没有ECN时返回空列表"""
        results = ecn_knowledge_service.search_similar_ecns("设计变更")

        assert isinstance(results, list)
        assert len(results) == 0

    def test_with_similar_ecns(self, ecn_knowledge_service, test_ecn, db_session):
        """有相似ECN时返回结果"""
        # 创建相似的ECN
        for i in range(5):
            ecn = Ecn(
            ecn_code=f"ECN-SIM-{i:04d}",
            ecn_title=f"相似ECN{i}",
            ecn_type=EcnChangeTypeEnum.DESIGN.value,
            project_id=test_ecn.project_id,
            project_code=test_ecn.project_code,
            project_name=test_ecn.project_name,
            customer_id=test_ecn.customer_id,
            customer_name=test_ecn.customer_name,
            requester_id=test_ecn.created_by,
            requester_name="测试用户",
            priority="NORMAL",
            reason=f"相似设计变更{i}",
            change_content="修改XXX参数",
            created_at=datetime.now(),
            created_by=test_ecn.created_by,
            )
            db_session.add(ecn)

            db_session.commit()

            results = ecn_knowledge_service.search_similar_ecns("设计变更")

            assert isinstance(results, list)
            assert len(results) == 6  # 包括test_ecn

    def test_search_by_title(self, ecn_knowledge_service, test_ecn):
        """按标题搜索"""
        results = ecn_knowledge_service.search_similar_ecns("测试ECN")

        assert len(results) >= 1
        assert test_ecn.ecn_title in [r["title"] for r in results]


class TestSearchByCategory:
    def test_design_type(self, ecn_knowledge_service, test_ecn, db_session):
        """按设计类型搜索"""
        # 创建设计类型的ECN
        ecn2 = Ecn(
        ecn_code="ECN-DES-002",
        ecn_title="另一个设计ECN",
        ecn_type=EcnChangeTypeEnum.DESIGN.value,
        project_id=test_ecn.project_id,
        project_code=test_ecn.project_code,
        project_name=test_ecn.project_name,
        customer_id=test_ecn.customer_id,
        customer_name=test_ecn.customer_name,
        requester_id=test_engineer.id,
        requester_name=test_engineer.real_name,
        priority="NORMAL",
        reason="设计优化",
        change_content="修改参数",
        created_at=datetime.now(),
        created_by=test_engineer.id,
        )
        db_session.add(ecn2)
        db_session.commit()

        results = ecn_knowledge_service.search_similar_ecns(
        "设计变更",
        category=EcnChangeTypeEnum.DESIGN.value,
        )

        assert len(results) >= 2

    def test_material_type(
        self, ecn_knowledge_service, test_project, test_engineer, db_session
    ):
        """按物料类型搜索"""
        ecn_material = Ecn(
        ecn_code="ECN-MAT-001",
        ecn_title="物料变更ECN",
        ecn_type=EcnChangeTypeEnum.MATERIAL.value,
        project_id=test_project.id,
        project_code=test_project.project_code,
        project_name=test_project.project_name,
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        requester_id=test_engineer.id,
        requester_name=test_engineer.real_name,
        priority="HIGH",
        reason="BOM变更",
        change_content="替换物料",
        created_at=datetime.now(),
        created_by=test_engineer.id,
        )
        db_session.add(ecn_material)
        db_session.commit()

        results = ecn_knowledge_service.search_similar_ecns(
        "物料变更",
        category=EcnChangeTypeEnum.MATERIAL.value,
        )

        assert len(results) >= 1

    def test_all_types(self, ecn_knowledge_service):
        """搜索所有类型"""
        results = ecn_knowledge_service.search_similar_ecns(
        "",
        category=None,
        )

        assert isinstance(results, list)
        # 应该包含所有ECN
        assert len(results) >= 3


class TestGetEcnDetails:
    def test_existing_ecn(self, ecn_knowledge_service, test_ecn):
        """获取现有ECN详情"""
        details = ecn_knowledge_service.get_ecn_details(test_ecn.id)

        assert details["id"] == test_ecn.id
        assert details["ecn_code"] == test_ecn.ecn_code
        assert details["title"] == test_ecn.ecn_title
        assert "change_content" in details

    def test_nonexistent_ecn(self, ecn_knowledge_service):
        """获取不存在的ECN"""
        details = ecn_knowledge_service.get_ecn_details(99999)

        assert details is None

    def test_with_related_info(self, ecn_knowledge_service, test_ecn):
        """包含相关信息"""
        details = ecn_knowledge_service.get_ecn_details(
        test_ecn.id,
        include_evaluation=True,
        include_tasks=True,
        )

        assert details["id"] == test_ecn.id
        # 验证包含相关信息字段
        assert "evaluation" in details or "tasks" in details


class TestGetChangeImpactAnalysis:
    def test_cost_impact(self, ecn_knowledge_service, test_ecn):
        """成本影响分析"""
        ecn.change_content = "增加成本1000元"
        analysis = ecn_knowledge_service.get_change_impact_analysis(
        test_ecn.id, analysis_type="COST"
        )

        assert analysis is not None
        assert "impact" in analysis
        assert analysis["analysis_type"] == "COST"

    def test_schedule_impact(self, ecn_knowledge_service, test_ecn):
        """进度影响分析"""
        ecn.change_content = "延期2周"
        analysis = ecn_knowledge_service.get_change_impact_analysis(
        test_ecn.id, analysis_type="SCHEDULE"
        )

        assert analysis is not None
        assert analysis["impact"] in analysis
        assert analysis["analysis_type"] == "SCHEDULE"

    def test_quality_impact(self, ecn_knowledge_service, test_ecn):
        """质量影响分析"""
        ecn.change_content = "需要重新测试"
        analysis = ecn_knowledge_service.get_change_impact_analysis(
        test_ecn.id, analysis_type="QUALITY"
        )

        assert analysis is not None
        assert "impact" in analysis

    def test_all_impact_types(self, ecn_knowledge_service):
        """综合影响分析"""
        analysis = ecn_knowledge_service.get_change_impact_analysis(
        test_ecn.id, analysis_type="ALL"
        )

        assert analysis is not None
        assert isinstance(analysis, dict)
        # 应该包含多种影响类型


class TestGetBestPractices:
    def test_design_practices(self, ecn_knowledge_service):
        """设计最佳实践"""
        ecn.change_content = "优化设计参数"
        practices = ecn_knowledge_service.get_best_practices(
        test_ecn.id, knowledge_type="DESIGN"
        )

        assert isinstance(practices, list)
        if len(practices) > 0:
            assert "practice" in practices[0]

    def test_material_practices(self, ecn_knowledge_service):
        """物料变更最佳实践"""
        ecn.change_content = "优化物料采购"
        practices = ecn_knowledge_service.get_best_practices(
        test_ecn.id, knowledge_type="MATERIAL"
        )

        assert isinstance(practices, list)

    def test_no_practices_found(self, ecn_knowledge_service):
        """没有找到最佳实践"""
        practices = ecn_knowledge_service.get_best_practices(
        test_ecn.id, knowledge_type="UNKNOWN"
        )

        assert isinstance(practices, list)
        assert len(practices) == 0


class TestExtractLessonsLearned:
    def test_successful_ecn(self, ecn_knowledge_service, test_ecn, db_session):
        """成功的ECN提取经验"""
        ecn.outcome = "APPROVED"
        db_session.commit()

        lessons = ecn_knowledge_service.extract_lessons_learned(test_ecn.id, limit=5)

        assert isinstance(lessons, list)
        assert len(lessons) >= 1
        assert "lesson" in lessons[0] if lessons else {}

    def test_multiple_ecns(self, ecn_knowledge_service, db_session):
        """批量提取多ECN的经验"""
        # 创建多个ECN
        for i in range(3):
            ecn = Ecn(
            ecn_code=f"ECN-LESS-{i:04d}",
            ecn_title=f"经验提取测试{i}",
            ecn_type=EcnChangeTypeEnum.DESIGN.value,
            project_id=test_project.id,
            project_code=test_project.project_code,
            project_name=test_project.project_name,
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            requester_id=test_engineer.id,
            requester_name=test_engineer.real_name,
            priority="NORMAL",
            reason=f"测试提取{i}",
            outcome="APPROVED" if i % 2 == 0 else "REJECTED",
            change_content=f"变更内容{i}",
            created_at=datetime.now() - timedelta(days=i * 5),
            created_by=test_engineer.id,
            )
            db_session.add(ecn)

            db_session.commit()

            lessons = ecn_knowledge_service.extract_lessons_learned(
            [test_ecn.id for i in range(3)], limit=10
            )

            assert len(lessons) >= 1


class TestGenerateKnowledgeEntry:
    def test_from_existing_ecn(self, ecn_knowledge_service, test_ecn):
        """从现有ECN生成知识条目"""
        entry = ecn_knowledge_service.generate_knowledge_entry(test_ecn.id)

        assert entry is not None
        assert "title" in entry
        assert "content" in entry
        assert "tags" in entry
        assert "ecn_id" in entry

    def test_with_custom_tags(self, ecn_knowledge_service, test_ecn):
        """使用自定义标签"""
        entry = ecn_knowledge_service.generate_knowledge_entry(
        test_ecn.id, tags=["设计", "优化", "成功案例"]
        )

        assert "设计" in entry["tags"]
        assert "优化" in entry["tags"]
        assert "成功案例" in entry["tags"]


class TestBatchSearchAndAnalysis:
    def test_batch_search_similar_cases(self, ecn_knowledge_service, db_session):
        """批量搜索相似案例"""
        # 创建多个相似ECN
        for i in range(10):
            ecn = Ecn(
            ecn_code=f"ECN-BATCH-{i:04d}",
            ecn_title=f"批量搜索{i}",
            ecn_type=EcnChangeTypeEnum.DESIGN.value,
            project_id=test_project.id,
            project_code=test_project.project_code,
            project_name=test_project.project_name,
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            requester_id=test_engineer.id,
            requester_name=test_engineer.real_name,
            priority="NORMAL",
            reason=f"批量搜索{i}",
            created_at=datetime.now() - timedelta(days=i * 3),
            created_by=test_engineer.id,
            )
            db_session.add(ecn)

            db_session.commit()

            results = ecn_knowledge_service.batch_search_similar_cases(
            ["设计变更", "物料变更"]
            )

            assert isinstance(results, dict)
            assert "similar_cases" in results
            assert len(results["similar_cases"]) >= 5

    def test_batch_extract_patterns(self, ecn_knowledge_service):
        """批量提取模式"""
        patterns = ecn_knowledge_service.batch_extract_patterns(
        [test_ecn.id for i in range(5)]
        )

        assert isinstance(patterns, dict)
        assert "patterns" in patterns
        assert "common_issues" in patterns or "best_practices" in patterns


class TestValidateKnowledgeAccuracy:
    def test_historical_accuracy(self, ecn_knowledge_service):
        """基于历史数据验证知识准确度"""
        # 创建带结果标记的ECN
        for i in range(10):
            outcome = "SUCCESS" if i % 3 != 0 else "FAILURE"
            ecn = Ecn(
            ecn_code=f"ECN-ACC-{i:04d}",
            ecn_title=f"准确度测试{i}",
            ecn_type=EcnChangeTypeEnum.DESIGN.value,
            project_id=test_project.id,
            project_code=test_project.project_code,
            project_name=test_project.project_name,
            customer_id=test_customer.id,
            customer_name=test_customer.customer_name,
            requester_id=test_engineer.id,
            requester_name=test_engineer.real_name,
            priority="NORMAL",
            reason=f"准确度测试{i}",
            outcome=outcome,
            change_content=f"变更{i}",
            created_at=datetime.now() - timedelta(days=i * 10),
            created_by=test_engineer.id,
            )
            db_session.add(ecn)

            db_session.commit()

            accuracy = ecn_knowledge_service.validate_knowledge_accuracy(
            test_ecn.id, lookback_months=6
            )

            assert accuracy is not None
            assert "accuracy_score" in accuracy
            assert 0 <= accuracy["accuracy_score"] <= 1
            assert "sample_size" in accuracy


class TestGetRecommendations:
    def test_for_new_ecn(self, ecn_knowledge_service, test_ecn):
        """为新ECN提供推荐"""
        recommendations = ecn_knowledge_service.get_recommendations(
        test_ecn.id, change_type=EcnChangeTypeEnum.DESIGN.value
        )

        assert isinstance(recommendations, list)
        # 验证推荐结构
        assert len(recommendations) >= 1
        assert "recommendation" in recommendations[0]
        assert "source" in recommendations[0]

    def test_for_high_priority(self, ecn_knowledge_service, test_ecn):
        """高优先级ECN的推荐"""
        test_ecn.priority = "VERY_HIGH"
        db_session.commit()

        recommendations = ecn_knowledge_service.get_recommendations(test_ecn.id)

        # 高优先级应该有更多推荐
        assert len(recommendations) >= 2

    def test_for_material_changes(self, ecn_knowledge_service, test_ecn):
        """物料变更推荐"""
        recommendations = ecn_knowledge_service.get_recommendations(
        test_ecn.id, change_type=EcnChangeTypeEnum.MATERIAL.value
        )

        assert isinstance(recommendations, list)
        if len(recommendations) > 0:
            # 物料变更应该有成本影响分析推荐
            any_cost_analysis = any(
                "COST" in rec.get("recommendation", "") for rec in recommendations
            )
            assert any_cost_analysis

    def test_risk_mitigation(self, ecn_knowledge_service):
        """风险缓解建议"""
        test_ecn.change_content = "高风险变更"
        db_session.commit()

        recommendations = ecn_knowledge_service.get_recommendations(test_ecn.id)

        # 应该包含风险缓解措施
        any_risk = any(
        "风险" in rec.get("recommendation", "") for rec in recommendations
        )
        assert any_risk


class TestEdgeCases:
    def test_empty_change_content(self, ecn_knowledge_service, test_ecn):
        """空变更内容"""
        test_ecn.change_content = ""
        db_session.commit()

        analysis = ecn_knowledge_service.get_change_impact_analysis(test_ecn.id)

        # 应该能够处理空内容
        assert analysis is not None

    def test_very_old_ecn(self, ecn_knowledge_service, test_ecn):
        """很旧的ECN"""
        test_ecn.created_at = datetime.now() - timedelta(days=365 * 2)  # 2年前
        db_session.commit()

        knowledge = ecn_knowledge_service.get_ecn_details(test_ecn.id)

        # 旧ECN的知识应该依然有效
        assert knowledge is not None

    def test_invalid_type(self, ecn_knowledge_service):
        """无效的变更类型"""
        # 传递无效类型
        recommendations = ecn_knowledge_service.get_recommendations(
        test_ecn.id, change_type="INVALID_TYPE"
        )

        # 应该能够处理无效类型
        assert isinstance(recommendations, list)
