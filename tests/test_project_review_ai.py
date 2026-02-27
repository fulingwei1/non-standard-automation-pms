"""
项目复盘AI服务测试
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

try:
    from app.services.project_review_ai import (
        ProjectReviewReportGenerator,
        ProjectLessonExtractor,
        ProjectComparisonAnalyzer,
        ProjectKnowledgeSyncer
    )
    from app.models.project import Project
    from app.models.project_review import ProjectReview, ProjectLesson
    from app.models.presale_knowledge_case import PresaleKnowledgeCase
except ImportError as e:
    pytest.skip(f"project_review_ai dependencies not available: {e}", allow_module_level=True)


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code="TEST001",
        project_name="测试自动化项目",
        description="这是一个测试项目",
        status="COMPLETED",
        project_type="自动化",
        planned_start_date=date(2024, 1, 1),
        planned_end_date=date(2024, 6, 30),
        actual_start_date=date(2024, 1, 5),
        actual_end_date=date(2024, 7, 15),
        budget_amount=Decimal("1000000.00")
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def sample_review(db: Session, sample_project):
    """创建测试复盘报告"""
    review = ProjectReview(
        review_no="REV20240715001",
        project_id=sample_project.id,
        project_code=sample_project.code,
        review_date=date.today(),
        review_type="POST_MORTEM",
        plan_duration=180,
        actual_duration=196,
        schedule_variance=16,
        budget_amount=Decimal("1000000.00"),
        actual_cost=Decimal("1050000.00"),
        cost_variance=Decimal("50000.00"),
        change_count=5,
        customer_satisfaction=4,
        success_factors="团队配合默契\\n技术方案先进\\n客户支持到位",
        problems="需求变更频繁\\n部分模块延期\\n资源不足",
        improvements="加强需求评审\\n提前资源预留\\n改进沟通机制",
        best_practices="敏捷开发模式\\n每日站会制度\\n代码审查流程",
        conclusion="项目总体成功，但需改进需求管理",
        reviewer_id=1,
        reviewer_name="张经理",
        status="PUBLISHED"
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


class TestProjectReviewReportGenerator:
    """测试报告生成器"""
    
    def test_generate_report(self, db: Session, sample_project):
        """测试生成复盘报告"""
        generator = ProjectReviewReportGenerator(db)
        
        result = generator.generate_report(
            project_id=sample_project.id,
            review_type="POST_MORTEM"
        )
        
        assert result is not None
        assert result['project_id'] == sample_project.id
        assert result['project_code'] == sample_project.code
        assert 'ai_summary' in result
        assert 'success_factors' in result
        assert result['ai_generated'] is True
        assert 'ai_metadata' in result
    
    def test_generate_report_invalid_project(self, db: Session):
        """测试无效项目ID"""
        generator = ProjectReviewReportGenerator(db)
        
        with pytest.raises(ValueError):
            generator.generate_report(project_id=99999)
    
    def test_report_contains_metrics(self, db: Session, sample_project):
        """测试报告包含关键指标"""
        generator = ProjectReviewReportGenerator(db)
        result = generator.generate_report(project_id=sample_project.id)
        
        assert 'plan_duration' in result
        assert 'actual_duration' in result
        assert 'schedule_variance' in result
        assert 'budget_amount' in result
        assert 'actual_cost' in result


class TestProjectLessonExtractor:
    """测试经验提取器"""
    
    def test_extract_lessons(self, db: Session, sample_review):
        """测试提取经验教训"""
        extractor = ProjectLessonExtractor(db)
        
        lessons = extractor.extract_lessons(
            review_id=sample_review.id,
            min_confidence=0.5
        )
        
        assert len(lessons) > 0
        assert all('lesson_type' in lesson for lesson in lessons)
        assert all('title' in lesson for lesson in lessons)
        assert all('ai_confidence' in lesson for lesson in lessons)
        assert all(lesson['ai_confidence'] >= 0.5 for lesson in lessons)
    
    def test_categorize_lessons(self, db: Session):
        """测试经验分类"""
        extractor = ProjectLessonExtractor(db)
        
        lessons = [
            {'category': '进度', 'title': '测试1'},
            {'category': '成本', 'title': '测试2'},
            {'category': '进度', 'title': '测试3'},
        ]
        
        categorized = extractor.categorize_lessons(lessons)
        
        assert '进度' in categorized
        assert '成本' in categorized
        assert len(categorized['进度']) == 2
        assert len(categorized['成本']) == 1
    
    def test_rank_lessons_by_priority(self, db: Session):
        """测试经验优先级排序"""
        extractor = ProjectLessonExtractor(db)
        
        lessons = [
            {'priority': 'LOW', 'ai_confidence': 0.6, 'title': 'A'},
            {'priority': 'HIGH', 'ai_confidence': 0.8, 'title': 'B'},
            {'priority': 'MEDIUM', 'ai_confidence': 0.7, 'title': 'C'},
        ]
        
        ranked = extractor.rank_lessons_by_priority(lessons)
        
        assert ranked[0]['priority'] == 'HIGH'
        assert ranked[-1]['priority'] == 'LOW'


class TestProjectComparisonAnalyzer:
    """测试对比分析器"""
    
    def test_compare_with_history(self, db: Session, sample_review):
        """测试历史对比"""
        analyzer = ProjectComparisonAnalyzer(db)
        
        result = analyzer.compare_with_history(
            review_id=sample_review.id,
            similarity_type='type',
            limit=3
        )
        
        assert 'current_review' in result
        assert 'similar_reviews' in result
        assert 'comparison' in result
        assert 'analysis' in result
        assert 'improvements' in result
    
    def test_identify_improvements(self, db: Session, sample_review):
        """测试识别改进点"""
        analyzer = ProjectComparisonAnalyzer(db)
        
        improvements = analyzer.identify_improvements(sample_review.id)
        
        assert isinstance(improvements, list)
        for imp in improvements:
            assert 'priority' in imp
            assert 'feasibility' in imp
            assert 'estimated_impact' in imp


class TestProjectKnowledgeSyncer:
    """测试知识库同步器"""
    
    def test_sync_to_knowledge_base(self, db: Session, sample_review):
        """测试同步到知识库"""
        syncer = ProjectKnowledgeSyncer(db)
        
        result = syncer.sync_to_knowledge_base(
            review_id=sample_review.id,
            auto_publish=True
        )
        
        assert result['success'] is True
        assert 'knowledge_case_id' in result
        assert 'case_name' in result
        assert 'quality_score' in result
        
        # 验证知识库记录已创建
        case = db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.id == result['knowledge_case_id']
        ).first()
        assert case is not None
    
    def test_calculate_quality_score(self, db: Session, sample_review):
        """测试质量评分计算"""
        syncer = ProjectKnowledgeSyncer(db)
        score = syncer._calculate_quality_score(sample_review)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # 高满意度项目应该有较高分数
    
    def test_extract_tags(self, db: Session, sample_review, sample_project):
        """测试标签提取"""
        syncer = ProjectKnowledgeSyncer(db)
        tags = syncer._extract_tags(sample_review, sample_project)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        # 应该包含规模、满意度、进度等标签
    
    def test_get_sync_status(self, db: Session, sample_review):
        """测试获取同步状态"""
        syncer = ProjectKnowledgeSyncer(db)
        
        # 未同步状态
        status1 = syncer.get_sync_status(sample_review.id)
        assert status1['synced'] is False
        
        # 同步后状态
        syncer.sync_to_knowledge_base(sample_review.id)
        status2 = syncer.get_sync_status(sample_review.id)
        assert status2['synced'] is True
        assert 'case_id' in status2


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_full_workflow(self, db: Session, sample_project):
        """测试完整工作流：生成报告 -> 提取经验 -> 同步知识库"""
        # 1. 生成报告
        generator = ProjectReviewReportGenerator(db)
        report_data = generator.generate_report(sample_project.id)
        
        review = ProjectReview(
            review_no="REV_TEST_001",
            reviewer_id=1,
            reviewer_name="测试员",
            **report_data
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # 2. 提取经验教训
        extractor = ProjectLessonExtractor(db)
        lessons = extractor.extract_lessons(review.id)
        assert len(lessons) > 0
        
        # 3. 同步到知识库
        syncer = ProjectKnowledgeSyncer(db)
        sync_result = syncer.sync_to_knowledge_base(review.id)
        assert sync_result['success'] is True
        
        # 4. 验证数据完整性
        case = db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.id == sync_result['knowledge_case_id']
        ).first()
        assert case is not None
        assert case.case_name == f"{sample_project.code} - {sample_project.name}"
        assert case.quality_score > 0


# 性能测试
class TestPerformance:
    """性能测试"""
    
    def test_report_generation_time(self, db: Session, sample_project):
        """测试报告生成时间"""
        import time
        
        generator = ProjectReviewReportGenerator(db)
        start = time.time()
        generator.generate_report(sample_project.id)
        duration = (time.time() - start) * 1000
        
        # 应该在30秒内完成
        assert duration < 30000, f"报告生成耗时{duration}ms，超过30秒限制"
    
    def test_lesson_extraction_time(self, db: Session, sample_review):
        """测试经验提取时间"""
        import time
        
        extractor = ProjectLessonExtractor(db)
        start = time.time()
        extractor.extract_lessons(sample_review.id)
        duration = (time.time() - start) * 1000
        
        # 应该在20秒内完成
        assert duration < 20000, f"经验提取耗时{duration}ms，超过20秒限制"
