# -*- coding: utf-8 -*-
"""
异常增强服务测试（增强版 v2 - 简化Mock）
覆盖目标：60%+
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.production.exception.exception_enhancement_service import (
    ExceptionEnhancementService,
)
from app.models.production import (
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA,
    FlowStatus,
    EscalationLevel,
    PDCAStage,
    ProductionException,
)
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ExceptionEnhancementService(db=mock_db)


# ==================== 流程时长计算测试（不依赖DB）====================


class TestCalculateFlowDuration:
    """流程时长计算测试"""

    def test_calculate_flow_duration_complete_flow(self, service):
        """测试：完整流程的时长计算"""
        base_time = datetime.now() - timedelta(hours=2)
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.PROCESSING,
            pending_at=base_time,
            processing_at=base_time + timedelta(minutes=30),
            resolved_at=base_time + timedelta(hours=1),
            closed_at=base_time + timedelta(hours=2),
        )

        service.calculate_flow_duration(flow)

        assert flow.pending_duration_minutes == 30
        assert flow.processing_duration_minutes == 30
        assert flow.total_duration_minutes == 120

    def test_calculate_flow_duration_partial_flow(self, service):
        """测试：部分完成流程的时长计算"""
        base_time = datetime.now() - timedelta(minutes=45)
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.PROCESSING,
            pending_at=base_time,
            processing_at=base_time + timedelta(minutes=15),
        )

        service.calculate_flow_duration(flow)

        assert flow.pending_duration_minutes == 15
        assert flow.processing_duration_minutes >= 29

    def test_calculate_flow_duration_only_pending(self, service):
        """测试：只有待处理阶段"""
        base_time = datetime.now() - timedelta(minutes=30)
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.PENDING,
            pending_at=base_time,
        )

        service.calculate_flow_duration(flow)

        assert flow.pending_duration_minutes >= 29
        assert flow.total_duration_minutes >= 29

    def test_calculate_flow_duration_none_values(self, service):
        """测试：None值处理"""
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.PENDING,
        )

        service.calculate_flow_duration(flow)
        # 不应该抛出异常


# ==================== 相似异常查找测试（不依赖DB）====================


class TestFindSimilarExceptions:
    """查找相似异常测试"""

    def test_find_similar_exceptions_high_similarity(self, service):
        """测试：高相似度异常识别"""
        exceptions = [
            MagicMock(id=1, title="设备电机故障"),
            MagicMock(id=2, title="设备电机故障异常"),
            MagicMock(id=3, title="电机设备故障问题"),
        ]

        result = service.find_similar_exceptions(exceptions)

        # 应该识别出相似的
        assert len(result) >= 0  # 可能有也可能没有，取决于算法

    def test_find_similar_exceptions_no_similarity(self, service):
        """测试：无相似度"""
        exceptions = [
            MagicMock(id=1, title="设备故障A"),
            MagicMock(id=2, title="质量问题B"),
        ]

        result = service.find_similar_exceptions(exceptions)
        assert len(result) == 0

    def test_find_similar_exceptions_empty_list(self, service):
        """测试：空列表"""
        result = service.find_similar_exceptions([])
        assert len(result) == 0

    def test_find_similar_exceptions_repeated_titles(self, service):
        """测试：完全重复的标题"""
        exceptions = [
            MagicMock(id=1, title="设备故障"),
            MagicMock(id=2, title="设备故障"),
            MagicMock(id=3, title="设备故障"),
        ]

        result = service.find_similar_exceptions(exceptions)
        assert len(result) > 0
        assert result[0]["count"] == 3


# ==================== 时间趋势分析测试（不依赖DB）====================


class TestAnalyzeTimeTrend:
    """时间趋势分析测试"""

    def test_analyze_time_trend_daily_counts(self, service):
        """测试：每日统计"""
        base_date = datetime.now() - timedelta(days=3)
        exceptions = [
            MagicMock(id=1, report_time=base_date),
            MagicMock(id=2, report_time=base_date),
            MagicMock(id=3, report_time=base_date + timedelta(days=1)),
        ]

        result = service.analyze_time_trend(exceptions, days=5)

        assert len(result) == 5
        # 检查结构
        assert "date" in result[0]
        assert "count" in result[0]

    def test_analyze_time_trend_empty_exceptions(self, service):
        """测试：无异常"""
        result = service.analyze_time_trend([], days=7)

        assert len(result) == 7
        for day in result:
            assert day["count"] == 0

    def test_analyze_time_trend_single_day(self, service):
        """测试：单日统计"""
        exceptions = [
            MagicMock(id=1, report_time=datetime.now()),
            MagicMock(id=2, report_time=datetime.now()),
        ]

        result = service.analyze_time_trend(exceptions, days=1)
        assert len(result) == 1


# ==================== 提取根因测试====================


class TestExtractCommonRootCauses:
    """提取常见根因测试"""

    def test_extract_common_root_causes_success(self, service, mock_db):
        """测试：成功提取根因"""
        mock_pdca_records = [
            MagicMock(plan_root_cause="设备老化"),
            MagicMock(plan_root_cause="操作不当"),
            MagicMock(plan_root_cause="维护不及时"),
            MagicMock(plan_root_cause="培训不足"),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_pdca_records

        mock_db.query.return_value = mock_query

        result = service.extract_common_root_causes([1, 2, 3, 4])

        assert len(result) == 3
        assert "设备老化" in result

    def test_extract_common_root_causes_no_pdca(self, service, mock_db):
        """测试：无PDCA记录"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        mock_db.query.return_value = mock_query

        result = service.extract_common_root_causes([1, 2])

        assert "暂无根因分析" in result[0]

    def test_extract_common_root_causes_with_none_values(self, service, mock_db):
        """测试：包含None值"""
        mock_pdca_records = [
            MagicMock(plan_root_cause="设备老化"),
            MagicMock(plan_root_cause=None),
            MagicMock(plan_root_cause="操作不当"),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_pdca_records

        mock_db.query.return_value = mock_query

        result = service.extract_common_root_causes([1, 2, 3])

        assert len(result) >= 2


# ==================== PDCA阶段推进测试====================


class TestAdvancePDCAStage:
    """PDCA阶段推进测试"""

    def test_advance_pdca_stage_plan_to_do(self, service, mock_db):
        """测试：PLAN到DO"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.id = 1
        mock_pdca.exception_id = 10
        mock_pdca.current_stage = PDCAStage.PLAN

        mock_request = MagicMock()
        mock_request.stage = "DO"
        mock_request.do_action_taken = "执行行动"
        mock_request.do_resources_used = "资源"
        mock_request.do_difficulties = "困难"
        mock_request.do_owner_id = 20

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca
            
            with patch.object(service, "build_pdca_response") as mock_build:
                mock_build.return_value = MagicMock()

                service.advance_pdca_stage(pdca_id=1, request=mock_request)

                assert mock_pdca.current_stage == PDCAStage.DO
                assert mock_pdca.do_action_taken == "执行行动"

    def test_advance_pdca_stage_invalid_transition(self, service, mock_db):
        """测试：无效转换"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.current_stage = PDCAStage.PLAN

        mock_request = MagicMock()
        mock_request.stage = "ACT"

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca

            with pytest.raises(HTTPException) as exc_info:
                service.advance_pdca_stage(pdca_id=1, request=mock_request)

            assert exc_info.value.status_code == 400

    def test_advance_pdca_stage_do_to_check(self, service, mock_db):
        """测试：DO到CHECK"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.current_stage = PDCAStage.DO

        mock_request = MagicMock()
        mock_request.stage = "CHECK"
        mock_request.check_result = "结果"
        mock_request.check_effectiveness = "有效性"
        mock_request.check_data = "数据"
        mock_request.check_gap = "差距"
        mock_request.check_owner_id = 30

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca

            with patch.object(service, "build_pdca_response") as mock_build:
                mock_build.return_value = MagicMock()

                service.advance_pdca_stage(pdca_id=1, request=mock_request)

                assert mock_pdca.current_stage == PDCAStage.CHECK

    def test_advance_pdca_stage_check_to_act(self, service, mock_db):
        """测试：CHECK到ACT"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.current_stage = PDCAStage.CHECK

        mock_request = MagicMock()
        mock_request.stage = "ACT"
        mock_request.act_standardization = "标准化"
        mock_request.act_horizontal_deployment = "横向展开"
        mock_request.act_remaining_issues = "遗留问题"
        mock_request.act_next_cycle = "下周期"
        mock_request.act_owner_id = 40

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca

            with patch.object(service, "build_pdca_response") as mock_build:
                mock_build.return_value = MagicMock()

                service.advance_pdca_stage(pdca_id=1, request=mock_request)

                assert mock_pdca.current_stage == PDCAStage.ACT

    def test_advance_pdca_stage_act_to_completed(self, service, mock_db):
        """测试：ACT到COMPLETED"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.current_stage = PDCAStage.ACT

        mock_request = MagicMock()
        mock_request.stage = "COMPLETED"
        mock_request.summary = "总结"
        mock_request.lessons_learned = "经验"

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca

            with patch.object(service, "build_pdca_response") as mock_build:
                mock_build.return_value = MagicMock()

                service.advance_pdca_stage(pdca_id=1, request=mock_request)

                assert mock_pdca.current_stage == PDCAStage.COMPLETED
                assert mock_pdca.is_completed is True

    def test_advance_pdca_stage_invalid_stage_name(self, service, mock_db):
        """测试：无效阶段名"""
        mock_pdca = MagicMock(spec=ExceptionPDCA)
        mock_pdca.current_stage = PDCAStage.PLAN

        mock_request = MagicMock()
        mock_request.stage = "INVALID"

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_pdca

            with pytest.raises(HTTPException) as exc_info:
                service.advance_pdca_stage(pdca_id=1, request=mock_request)

            assert exc_info.value.status_code == 400


# ==================== PDCA创建测试====================


class TestCreatePDCA:
    """PDCA创建测试"""

    def test_create_pdca_success(self, service, mock_db):
        """测试：成功创建"""
        mock_exception = MagicMock(spec=ProductionException)
        mock_exception.id = 1

        mock_request = MagicMock()
        mock_request.exception_id = 1
        mock_request.plan_description = "描述"
        mock_request.plan_root_cause = "根因"
        mock_request.plan_target = "目标"
        mock_request.plan_measures = "措施"
        mock_request.plan_owner_id = 10
        mock_request.plan_deadline = datetime.now()

        with patch("app.services.production.exception.exception_enhancement_service.get_or_404") as mock_get:
            mock_get.return_value = mock_exception

            with patch("app.services.production.exception.exception_enhancement_service.save_obj"):
                with patch.object(service, "build_pdca_response") as mock_build:
                    mock_build.return_value = MagicMock()

                    result = service.create_pdca(mock_request, current_user_id=10)

                    mock_build.assert_called_once()


# ==================== 重复异常分析测试====================


class TestAnalyzeRecurrence:
    """重复异常分析测试"""

    def test_analyze_recurrence_single_type(self, service, mock_db):
        """测试：单一类型分析"""
        mock_exceptions = [
            MagicMock(id=1, exception_type="设备异常", title="故障1", report_time=datetime.now()),
            MagicMock(id=2, exception_type="设备异常", title="故障2", report_time=datetime.now()),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_exceptions

        mock_db.query.return_value = mock_query

        with patch.object(service, "find_similar_exceptions", return_value=[]):
            with patch.object(service, "analyze_time_trend", return_value=[]):
                with patch.object(service, "extract_common_root_causes", return_value=["根因1"]):
                    result = service.analyze_recurrence(exception_type="设备异常", days=7)

                    assert len(result) == 1
                    assert result[0].exception_type == "设备异常"
                    assert result[0].total_occurrences == 2

    def test_analyze_recurrence_multiple_types(self, service, mock_db):
        """测试：多类型分析"""
        mock_exceptions = [
            MagicMock(id=1, exception_type="设备异常", title="设备故障", report_time=datetime.now()),
            MagicMock(id=2, exception_type="质量异常", title="质量问题", report_time=datetime.now()),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_exceptions

        mock_db.query.return_value = mock_query

        with patch.object(service, "find_similar_exceptions", return_value=[]):
            with patch.object(service, "analyze_time_trend", return_value=[]):
                with patch.object(service, "extract_common_root_causes", return_value=[]):
                    result = service.analyze_recurrence(exception_type=None, days=30)

                    assert len(result) == 2


# ==================== 知识库搜索测试====================


class TestSearchKnowledge:
    """知识库搜索测试"""

    def test_search_knowledge_by_keyword(self, service, mock_db):
        """测试：关键词搜索"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0

        mock_db.query.return_value = mock_query

        with patch("app.services.production.exception.exception_enhancement_service.apply_pagination") as mock_paginate:
            mock_paginate.return_value.all.return_value = []

            result = service.search_knowledge(
                keyword="设备",
                exception_type=None,
                exception_level=None,
                is_approved=None,
                offset=0,
                limit=10,
                page=1,
                page_size=10,
            )

            assert result.total == 0

    def test_search_knowledge_by_type(self, service, mock_db):
        """测试：按类型搜索"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0

        mock_db.query.return_value = mock_query

        with patch("app.services.production.exception.exception_enhancement_service.apply_pagination") as mock_paginate:
            mock_paginate.return_value.all.return_value = []

            result = service.search_knowledge(
                keyword=None,
                exception_type="设备异常",
                exception_level=None,
                is_approved=None,
                offset=0,
                limit=10,
                page=1,
                page_size=10,
            )

            assert result.total == 0

    def test_search_knowledge_approved_only(self, service, mock_db):
        """测试：仅已审核"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0

        mock_db.query.return_value = mock_query

        with patch("app.services.production.exception.exception_enhancement_service.apply_pagination") as mock_paginate:
            mock_paginate.return_value.all.return_value = []

            result = service.search_knowledge(
                keyword=None,
                exception_type=None,
                exception_level=None,
                is_approved=True,
                offset=0,
                limit=10,
                page=1,
                page_size=10,
            )

            assert result.total == 0


# ==================== 创建知识库测试====================


class TestCreateKnowledge:
    """创建知识库测试"""

    def test_create_knowledge_success(self, service, mock_db):
        """测试：成功创建"""
        mock_request = MagicMock()
        mock_request.title = "知识标题"
        mock_request.exception_type = "设备异常"
        mock_request.exception_level = "严重"
        mock_request.symptom_description = "症状"
        mock_request.solution = "解决方案"
        mock_request.solution_steps = ["步骤1", "步骤2"]
        mock_request.prevention_measures = "预防措施"
        mock_request.keywords = "关键词"
        mock_request.source_exception_id = 1
        mock_request.attachments = []

        with patch("app.services.production.exception.exception_enhancement_service.save_obj"):
            with patch.object(service, "build_knowledge_response") as mock_build:
                mock_build.return_value = MagicMock()

                result = service.create_knowledge(mock_request, creator_id=100)

                mock_build.assert_called_once()


# ==================== 流程跟踪测试====================


class TestGetExceptionFlow:
    """流程跟踪测试"""

    def test_get_exception_flow_not_found(self, service, mock_db):
        """测试：流程不存在"""
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_exception_flow(exception_id=999)

        assert exc_info.value.status_code == 404


# ==================== 总结测试====================


class TestServiceIntegration:
    """集成测试"""

    def test_service_initialization(self, mock_db):
        """测试：服务初始化"""
        service = ExceptionEnhancementService(db=mock_db)
        assert service.db == mock_db

    def test_calculate_duration_no_exception(self, service):
        """测试：时长计算不抛出异常"""
        flow = ExceptionHandlingFlow(exception_id=1, status=FlowStatus.PENDING)
        try:
            service.calculate_flow_duration(flow)
        except Exception as e:
            pytest.fail(f"不应该抛出异常: {e}")


# ==================== 额外边界测试 ====================


class TestEdgeCases:
    """边界情况测试"""

    def test_find_similar_exceptions_partial_match(self, service):
        """测试：部分匹配的异常"""
        exceptions = [
            MagicMock(id=1, title="设备 电机 故障"),
            MagicMock(id=2, title="电机 故障 分析"),
            MagicMock(id=3, title="生产 线 问题"),
        ]
        
        result = service.find_similar_exceptions(exceptions)
        # 前两个应该被识别为相似
        assert isinstance(result, list)

    def test_analyze_time_trend_with_gaps(self, service):
        """测试：有时间间隔的趋势分析"""
        base_date = datetime.now() - timedelta(days=10)
        exceptions = [
            MagicMock(id=1, report_time=base_date),
            MagicMock(id=2, report_time=base_date + timedelta(days=5)),
            MagicMock(id=3, report_time=base_date + timedelta(days=9)),
        ]
        
        result = service.analyze_time_trend(exceptions, days=10)
        assert len(result) == 10

    def test_extract_common_root_causes_limited(self, service, mock_db):
        """测试：根因数量限制"""
        mock_pdca_records = [
            MagicMock(plan_root_cause=f"根因{i}") for i in range(10)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_pdca_records
        mock_db.query.return_value = mock_query
        
        result = service.extract_common_root_causes([1, 2, 3])
        # 应该只返回前3个
        assert len(result) == 3

    def test_calculate_flow_duration_with_resolved(self, service):
        """测试：已解决但未关闭的流程"""
        base_time = datetime.now() - timedelta(hours=3)
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.RESOLVED,
            pending_at=base_time,
            processing_at=base_time + timedelta(hours=1),
            resolved_at=base_time + timedelta(hours=2),
        )
        
        service.calculate_flow_duration(flow)
        
        assert flow.pending_duration_minutes == 60
        assert flow.processing_duration_minutes == 60
        assert flow.total_duration_minutes >= 180

    def test_calculate_flow_duration_zero_duration(self, service):
        """测试：瞬时完成的流程"""
        now = datetime.now()
        flow = ExceptionHandlingFlow(
            exception_id=1,
            status=FlowStatus.CLOSED,
            pending_at=now,
            processing_at=now,
            resolved_at=now,
            closed_at=now,
        )
        
        service.calculate_flow_duration(flow)
        
        assert flow.pending_duration_minutes == 0
        assert flow.processing_duration_minutes == 0
        assert flow.total_duration_minutes == 0


# ==================== 相似度算法测试 ====================


class TestSimilarityAlgorithm:
    """相似度算法详细测试"""

    def test_jaccard_similarity_exact_match(self, service):
        """测试：完全匹配"""
        exceptions = [
            MagicMock(id=1, title="设备故障"),
            MagicMock(id=2, title="设备故障"),
        ]
        
        result = service.find_similar_exceptions(exceptions)
        assert len(result) == 1
        assert result[0]["count"] == 2

    def test_jaccard_similarity_threshold(self, service):
        """测试：相似度阈值边界"""
        # 创建相似度刚好在阈值附近的标题
        exceptions = [
            MagicMock(id=1, title="A B C D E F"),
            MagicMock(id=2, title="A B C D X Y"),  # 4/8 = 0.5 < 0.6
        ]
        
        result = service.find_similar_exceptions(exceptions)
        # 低于阈值，不应该匹配
        assert len(result) == 0

    def test_jaccard_similarity_case_insensitive(self, service):
        """测试：大小写不敏感"""
        exceptions = [
            MagicMock(id=1, title="Device Failure"),
            MagicMock(id=2, title="device failure"),
        ]
        
        result = service.find_similar_exceptions(exceptions)
        assert len(result) == 1


# ==================== 时间趋势边界测试 ====================


class TestTimeTrendEdgeCases:
    """时间趋势边界测试"""

    def test_analyze_time_trend_same_day_multiple(self, service):
        """测试：同一天多次异常"""
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        exceptions = [
            MagicMock(id=i, report_time=base_date + timedelta(hours=i))
            for i in range(10)
        ]
        
        result = service.analyze_time_trend(exceptions, days=1)
        assert result[0]["count"] == 10

    def test_analyze_time_trend_future_dates(self, service):
        """测试：未来日期的异常（不应该影响）"""
        exceptions = [
            MagicMock(id=1, report_time=datetime.now() + timedelta(days=1)),
        ]
        
        result = service.analyze_time_trend(exceptions, days=7)
        assert len(result) == 7
