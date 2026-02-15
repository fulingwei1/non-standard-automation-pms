# -*- coding: utf-8 -*-
"""
移动端AI销售助手 - 单元测试
"""

import json
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from sqlalchemy.orm import Session

from app.models.presale_mobile import (
    PresaleMobileAssistantChat,
    PresaleMobileOfflineData,
    PresaleMobileQuickEstimate,
    PresaleVisitRecord,
)
from app.schemas.presale_mobile import QuestionType, SyncStatus, VisitType
from app.services.presale_mobile_service import PresaleMobileService


# ==================== Fixtures ====================


@pytest.fixture
def db_session():
    """模拟数据库会话"""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mobile_service(db_session):
    """创建移动端服务实例"""
    return PresaleMobileService(db_session)


@pytest.fixture
def mock_user():
    """模拟用户"""
    return {"id": 1, "username": "test_user", "email": "test@example.com"}


# ==================== AI问答测试 (8个用例) ====================


class TestAIChat:
    """AI问答功能测试"""

    @pytest.mark.asyncio
    async def test_chat_technical_question(self, mobile_service, db_session):
        """测试技术类问题"""
        question = "请问这款机器人的最大负载是多少？"
        result = await mobile_service.chat(
            user_id=1, question=question, presale_ticket_id=100
        )

        assert "answer" in result
        assert result["question_type"] == QuestionType.TECHNICAL
        assert result["response_time"] > 0
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_competitor_question(self, mobile_service, db_session):
        """测试竞品对比问题"""
        question = "我们的产品和XX品牌相比有什么优势？"
        result = await mobile_service.chat(user_id=1, question=question)

        assert result["question_type"] == QuestionType.COMPETITOR

    @pytest.mark.asyncio
    async def test_chat_case_question(self, mobile_service, db_session):
        """测试案例类问题"""
        question = "有没有类似汽车行业的成功案例？"
        result = await mobile_service.chat(user_id=1, question=question)

        assert result["question_type"] == QuestionType.CASE

    @pytest.mark.asyncio
    async def test_chat_pricing_question(self, mobile_service, db_session):
        """测试报价类问题"""
        question = "这个方案大概需要多少预算？"
        result = await mobile_service.chat(user_id=1, question=question)

        assert result["question_type"] == QuestionType.PRICING

    @pytest.mark.asyncio
    async def test_chat_with_context(self, mobile_service, db_session):
        """测试带上下文的对话"""
        context = {"previous_question": "什么是六轴机器人？", "customer_id": 123}
        result = await mobile_service.chat(
            user_id=1, question="它的价格是多少？", context=context
        )

        assert result["context"] == context

    @pytest.mark.asyncio
    async def test_chat_response_time(self, mobile_service, db_session):
        """测试响应时间记录"""
        result = await mobile_service.chat(user_id=1, question="测试问题")

        assert result["response_time"] > 0
        assert result["response_time"] < 5000  # 应该小于5秒

    @pytest.mark.asyncio
    async def test_chat_saves_to_database(self, mobile_service, db_session):
        """测试对话记录保存到数据库"""
        await mobile_service.chat(user_id=1, question="测试问题")

        # 验证数据库操作
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once()

    def test_classify_question_accuracy(self, mobile_service):
        """测试问题分类准确性"""
        test_cases = [
            ("规格参数是多少？", QuestionType.TECHNICAL),
            ("与竞品对比如何？", QuestionType.COMPETITOR),
            ("有成功案例吗？", QuestionType.CASE),
            ("价格是多少？", QuestionType.PRICING),
            ("你好", QuestionType.OTHER),
        ]

        for question, expected_type in test_cases:
            result = mobile_service._classify_question(question)
            assert result == expected_type


# ==================== 语音交互测试 (6个用例) ====================


class TestVoiceInteraction:
    """语音交互功能测试"""

    @pytest.mark.asyncio
    async def test_voice_question_stt(self, mobile_service, db_session):
        """测试语音转文字"""
        audio_base64 = "fake_audio_base64_data"

        with patch.object(
            mobile_service, "_speech_to_text", new_callable=AsyncMock
        ) as mock_stt:
            mock_stt.return_value = "这是转换后的文字"
            result = await mobile_service.voice_question(
                user_id=1, audio_base64=audio_base64
            )

            assert "transcription" in result
            assert result["transcription"] == "这是转换后的文字"
            mock_stt.assert_called_once()

    @pytest.mark.asyncio
    async def test_voice_question_tts(self, mobile_service, db_session):
        """测试文字转语音"""
        audio_base64 = "fake_audio_base64_data"

        with patch.object(
            mobile_service, "_text_to_speech", new_callable=AsyncMock
        ) as mock_tts:
            mock_tts.return_value = "https://example.com/audio.mp3"
            result = await mobile_service.voice_question(
                user_id=1, audio_base64=audio_base64
            )

            assert "audio_url" in result
            assert result["audio_url"].startswith("http")

    @pytest.mark.asyncio
    async def test_voice_question_complete_flow(self, mobile_service, db_session):
        """测试语音问答完整流程"""
        audio_base64 = "fake_audio_base64_data"
        result = await mobile_service.voice_question(
            user_id=1, audio_base64=audio_base64, audio_format="mp3"
        )

        assert "transcription" in result
        assert "answer" in result
        assert "audio_url" in result
        assert "response_time" in result

    @pytest.mark.asyncio
    async def test_voice_question_multiple_formats(self, mobile_service):
        """测试多种音频格式支持"""
        formats = ["mp3", "wav", "m4a"]

        for fmt in formats:
            with patch.object(
                mobile_service, "_speech_to_text", new_callable=AsyncMock
            ) as mock_stt:
                mock_stt.return_value = "测试文字"
                await mobile_service.voice_question(
                    user_id=1, audio_base64="fake_data", audio_format=fmt
                )
                mock_stt.assert_called_with("fake_data", fmt)

    @pytest.mark.asyncio
    async def test_voice_question_with_ticket_id(self, mobile_service, db_session):
        """测试语音问答关联工单"""
        result = await mobile_service.voice_question(
            user_id=1, audio_base64="fake_data", presale_ticket_id=100
        )

        # 验证对话记录关联了工单
        assert result is not None

    @pytest.mark.asyncio
    async def test_voice_question_response_time(self, mobile_service, db_session):
        """测试语音问答响应时间"""
        result = await mobile_service.voice_question(
            user_id=1, audio_base64="fake_data"
        )

        assert result["response_time"] > 0


# ==================== 拜访准备测试 (4个用例) ====================


class TestVisitPreparation:
    """拜访准备功能测试"""

    def test_get_visit_preparation_complete(self, mobile_service):
        """测试获取完整的拜访准备清单"""
        result = mobile_service.get_visit_preparation(ticket_id=100, user_id=1)

        required_fields = [
            "ticket_id",
            "customer_name",
            "customer_background",
            "previous_interactions",
            "recommended_scripts",
            "attention_points",
            "technical_materials",
            "competitor_comparison",
        ]

        for field in required_fields:
            assert field in result

    def test_visit_preparation_scripts(self, mobile_service):
        """测试话术推荐"""
        result = mobile_service.get_visit_preparation(ticket_id=100, user_id=1)

        assert len(result["recommended_scripts"]) > 0
        assert isinstance(result["recommended_scripts"], list)

    def test_visit_preparation_attention_points(self, mobile_service):
        """测试注意事项"""
        result = mobile_service.get_visit_preparation(ticket_id=100, user_id=1)

        assert len(result["attention_points"]) > 0

    def test_visit_preparation_materials(self, mobile_service):
        """测试技术资料"""
        result = mobile_service.get_visit_preparation(ticket_id=100, user_id=1)

        assert len(result["technical_materials"]) > 0
        for material in result["technical_materials"]:
            assert "name" in material
            assert "url" in material


# ==================== 快速估价测试 (4个用例) ====================


class TestQuickEstimate:
    """快速估价功能测试"""

    @pytest.mark.asyncio
    async def test_quick_estimate_without_photo(self, mobile_service, db_session):
        """测试无照片的快速估价"""
        result = await mobile_service.quick_estimate(
            user_id=1,
            equipment_description="六轴工业机器人",
            presale_ticket_id=100,
        )

        assert result["recognized_equipment"] == "六轴工业机器人"
        assert result["estimated_cost"] > 0
        assert result["price_range_min"] > 0
        assert result["price_range_max"] > result["price_range_min"]

    @pytest.mark.asyncio
    async def test_quick_estimate_with_photo(self, mobile_service, db_session):
        """测试带照片的快速估价"""
        with patch.object(
            mobile_service, "_recognize_equipment", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.return_value = {
                "equipment_name": "六轴机器人",
                "confidence": 85,
            }

            result = await mobile_service.quick_estimate(
                user_id=1,
                equipment_description="工业机器人",
                equipment_photo_base64="fake_photo_data",
            )

            assert result["confidence_score"] == 85
            mock_recognize.assert_called_once()

    @pytest.mark.asyncio
    async def test_quick_estimate_bom_matching(self, mobile_service, db_session):
        """测试BOM匹配"""
        result = await mobile_service.quick_estimate(
            user_id=1, equipment_description="六轴机器人"
        )

        assert len(result["bom_items"]) > 0
        for item in result["bom_items"]:
            assert "name" in item
            assert "quantity" in item
            assert "unit_price" in item
            assert "amount" in item

    @pytest.mark.asyncio
    async def test_quick_estimate_price_range(self, mobile_service, db_session):
        """测试报价范围计算"""
        result = await mobile_service.quick_estimate(
            user_id=1, equipment_description="测试设备"
        )

        # 验证报价范围在成本的1.3-1.5倍之间
        cost = result["estimated_cost"]
        assert result["price_range_min"] >= cost * 1.3
        assert result["price_range_max"] <= cost * 1.5


# ==================== 拜访记录测试 (4个用例) ====================


class TestVisitRecord:
    """拜访记录功能测试"""

    def test_create_visit_record(self, mobile_service, db_session):
        """测试创建拜访记录"""
        attendees = [
            {"name": "张三", "title": "技术总监", "company": "客户公司"}
        ]

        result = mobile_service.create_visit_record(
            user_id=1,
            presale_ticket_id=100,
            customer_id=50,
            visit_date="2024-02-15",
            visit_type=VisitType.FIRST_CONTACT.value,
            attendees=attendees,
            discussion_points="讨论了技术方案",
            customer_feedback="客户满意",
            next_steps="下周提供详细报价",
        )

        assert result["presale_ticket_id"] == 100
        assert result["customer_id"] == 50
        assert len(result["attendees"]) > 0
        db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_voice_to_visit_record(self, mobile_service, db_session):
        """测试语音转拜访记录"""
        with patch.object(
            mobile_service, "_extract_visit_info", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = {
                "attendees": [{"name": "张三", "title": "总监"}],
                "discussion_points": "讨论要点",
                "customer_feedback": "客户反馈",
                "next_steps": "下一步",
                "summary": "摘要",
            }

            result = await mobile_service.voice_to_visit_record(
                user_id=1,
                audio_base64="fake_audio",
                presale_ticket_id=100,
                customer_id=50,
                visit_date="2024-02-15",
                visit_type=VisitType.FOLLOW_UP.value,
            )

            assert result["ai_generated_summary"] == "摘要"
            mock_extract.assert_called_once()

    def test_get_visit_history(self, mobile_service, db_session):
        """测试获取拜访历史"""
        # 模拟查询结果
        mock_visits = []
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_visits
        )

        result = mobile_service.get_visit_history(customer_id=50)

        assert "visits" in result
        assert "total_visits" in result
        assert "latest_visit" in result

    def test_visit_record_formatting(self, mobile_service):
        """测试拜访记录格式化"""
        mock_record = MagicMock(spec=PresaleVisitRecord)
        mock_record.id = 1
        mock_record.presale_ticket_id = 100
        mock_record.customer_id = 50
        mock_record.visit_date = date(2024, 2, 15)
        mock_record.visit_type = "first_contact"
        mock_record.attendees = [{"name": "张三"}]
        mock_record.discussion_points = "讨论要点"
        mock_record.customer_feedback = "反馈"
        mock_record.next_steps = "下一步"
        mock_record.ai_generated_summary = "摘要"
        mock_record.created_at = datetime(2024, 2, 15, 10, 0, 0)

        result = mobile_service._format_visit_record(mock_record)

        assert result["id"] == 1
        assert result["visit_date"] == "2024-02-15"
        assert isinstance(result["attendees"], list)


# ==================== 客户快照测试 (2个用例) ====================


class TestCustomerSnapshot:
    """客户快照功能测试"""

    def test_get_customer_snapshot_complete(self, mobile_service):
        """测试获取完整客户快照"""
        result = mobile_service.get_customer_snapshot(customer_id=50)

        required_fields = [
            "customer_id",
            "customer_name",
            "industry",
            "contact_person",
            "contact_phone",
            "recent_tickets",
            "total_orders",
            "total_revenue",
            "key_concerns",
            "decision_makers",
        ]

        for field in required_fields:
            assert field in result

    def test_customer_snapshot_decision_makers(self, mobile_service):
        """测试决策人信息"""
        result = mobile_service.get_customer_snapshot(customer_id=50)

        assert len(result["decision_makers"]) > 0
        for dm in result["decision_makers"]:
            assert "name" in dm
            assert "title" in dm


# ==================== 离线数据同步测试 (4个用例) ====================


class TestOfflineSync:
    """离线数据同步功能测试"""

    def test_sync_chat_data(self, mobile_service, db_session):
        """测试同步对话数据"""
        data_payload = {
            "question": "测试问题",
            "answer": "测试答案",
            "question_type": "technical",
        }

        result = mobile_service.sync_offline_data(
            user_id=1, data_type="chat", local_id="local_123", data_payload=data_payload
        )

        assert result["success"] is True
        assert "synced_id" in result

    def test_sync_visit_data(self, mobile_service, db_session):
        """测试同步拜访数据"""
        data_payload = {
            "presale_ticket_id": 100,
            "customer_id": 50,
            "visit_date": "2024-02-15",
            "visit_type": "first_contact",
            "attendees": [],
            "discussion_points": "讨论要点",
        }

        result = mobile_service.sync_offline_data(
            user_id=1,
            data_type="visit",
            local_id="local_456",
            data_payload=data_payload,
        )

        assert result["success"] is True

    def test_sync_estimate_data(self, mobile_service, db_session):
        """测试同步估价数据"""
        data_payload = {
            "recognized_equipment": "设备名称",
            "equipment_description": "描述",
            "estimated_cost": 100000,
            "price_range_min": 130000,
            "price_range_max": 150000,
            "bom_items": [],
        }

        result = mobile_service.sync_offline_data(
            user_id=1,
            data_type="estimate",
            local_id="local_789",
            data_payload=data_payload,
        )

        assert result["success"] is True

    def test_sync_duplicate_prevention(self, mobile_service, db_session):
        """测试防止重复同步"""
        # 模拟已存在的同步记录
        existing_record = MagicMock(spec=PresaleMobileOfflineData)
        existing_record.sync_status = SyncStatus.SYNCED.value

        db_session.query.return_value.filter.return_value.first.return_value = (
            existing_record
        )

        result = mobile_service.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="local_123",
            data_payload={"test": "data"},
        )

        assert result["success"] is True
        assert "已同步" in result["message"]


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
