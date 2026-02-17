# -*- coding: utf-8 -*-
"""
I1组: PresaleMobileService 单元测试
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.presale_mobile_service import PresaleMobileService
from app.schemas.presale_mobile import QuestionType, SyncStatus


# ============================================================
# Helper factory
# ============================================================

def _make_service():
    db = MagicMock()
    return PresaleMobileService(db), db


def _make_visit_record(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", 1)
    r.presale_ticket_id = kwargs.get("presale_ticket_id", 10)
    r.customer_id = kwargs.get("customer_id", 20)
    r.visit_date = kwargs.get("visit_date", date(2024, 1, 15))
    r.visit_type = kwargs.get("visit_type", "现场拜访")
    r.attendees = kwargs.get("attendees", [{"name": "张三"}])
    r.discussion_points = kwargs.get("discussion_points", "讨论了技术方案")
    r.customer_feedback = kwargs.get("customer_feedback", "满意")
    r.next_steps = kwargs.get("next_steps", "发送报价")
    r.ai_generated_summary = kwargs.get("ai_generated_summary", None)
    r.created_at = kwargs.get("created_at", MagicMock())
    r.created_at.isoformat.return_value = "2024-01-15T10:00:00"
    return r


# ============================================================
# TestClassifyQuestion
# ============================================================

class TestClassifyQuestion:
    def setup_method(self):
        self.svc, _ = _make_service()

    def test_technical_question(self):
        result = self.svc._classify_question("这个设备的技术参数是什么？")
        assert result == QuestionType.TECHNICAL

    def test_competitor_question(self):
        result = self.svc._classify_question("与竞品相比有什么优势？")
        assert result == QuestionType.COMPETITOR

    def test_case_question(self):
        result = self.svc._classify_question("有没有类似的成功案例？")
        assert result == QuestionType.CASE

    def test_pricing_question(self):
        result = self.svc._classify_question("这套系统多少钱？")
        assert result == QuestionType.PRICING

    def test_other_question(self):
        result = self.svc._classify_question("你好，请问")
        assert result == QuestionType.OTHER

    def test_technical_keyword_规格(self):
        result = self.svc._classify_question("规格要求是什么")
        assert result == QuestionType.TECHNICAL

    def test_pricing_keyword_预算(self):
        result = self.svc._classify_question("预算控制在多少")
        assert result == QuestionType.PRICING


# ============================================================
# TestBuildChatPrompt
# ============================================================

class TestBuildChatPrompt:
    def setup_method(self):
        self.svc, _ = _make_service()

    def test_technical_prompt(self):
        prompt = self.svc._build_chat_prompt("精度要求", QuestionType.TECHNICAL, None)
        assert "技术参数" in prompt
        assert "精度要求" in prompt

    def test_competitor_prompt(self):
        prompt = self.svc._build_chat_prompt("竞品对比", QuestionType.COMPETITOR, None)
        assert "竞品" in prompt

    def test_case_prompt(self):
        prompt = self.svc._build_chat_prompt("成功案例", QuestionType.CASE, None)
        assert "案例" in prompt

    def test_pricing_prompt(self):
        prompt = self.svc._build_chat_prompt("报价", QuestionType.PRICING, None)
        assert "报价" in prompt

    def test_with_context(self):
        context = {"project_type": "装配线"}
        prompt = self.svc._build_chat_prompt("问题", QuestionType.OTHER, context)
        assert "装配线" in prompt


# ============================================================
# TestChat (async)
# ============================================================

class TestChat:
    @pytest.mark.asyncio
    async def test_chat_basic(self):
        svc, db = _make_service()
        mock_chat_record = MagicMock()
        mock_chat_record.id = 1
        mock_chat_record.created_at = MagicMock()

        with patch("app.services.presale_mobile_service.save_obj") as mock_save, \
             patch.object(svc, "_call_ai_service", new=AsyncMock(return_value="AI回答内容")):
            result = await svc.chat(
                user_id=1,
                question="这个设备的技术参数是多少？",  # "技术" is in the keyword list
                presale_ticket_id=10,
            )

        mock_save.assert_called_once()
        assert result["answer"] == "AI回答内容"
        assert result["question_type"] == QuestionType.TECHNICAL

    @pytest.mark.asyncio
    async def test_chat_without_ticket(self):
        svc, db = _make_service()

        with patch("app.services.presale_mobile_service.save_obj"), \
             patch.object(svc, "_call_ai_service", new=AsyncMock(return_value="回答")):
            result = await svc.chat(user_id=1, question="价格多少？")

        assert result["answer"] == "回答"
        assert result["question_type"] == QuestionType.PRICING

    @pytest.mark.asyncio
    async def test_chat_records_response_time(self):
        svc, db = _make_service()

        with patch("app.services.presale_mobile_service.save_obj"), \
             patch.object(svc, "_call_ai_service", new=AsyncMock(return_value="回答")):
            result = await svc.chat(user_id=1, question="问题")

        assert result["response_time"] >= 0


# ============================================================
# TestVoiceQuestion (async)
# ============================================================

class TestVoiceQuestion:
    @pytest.mark.asyncio
    async def test_voice_question_basic(self):
        svc, db = _make_service()

        with patch.object(svc, "_speech_to_text", new=AsyncMock(return_value="识别的文字")), \
             patch.object(svc, "_text_to_speech", new=AsyncMock(return_value="http://audio.url")), \
             patch.object(svc, "_call_ai_service", new=AsyncMock(return_value="AI回答")), \
             patch("app.services.presale_mobile_service.save_obj"):

            result = await svc.voice_question(
                user_id=1,
                audio_base64="base64data",
                presale_ticket_id=10,
            )

        assert result["transcription"] == "识别的文字"
        assert result["audio_url"] == "http://audio.url"
        assert "answer" in result


# ============================================================
# TestGetVisitPreparation
# ============================================================

class TestGetVisitPreparation:
    def test_get_visit_preparation(self):
        svc, db = _make_service()
        result = svc.get_visit_preparation(ticket_id=1, user_id=1)

        assert "ticket_id" in result
        assert result["ticket_id"] == 1
        assert "recommended_scripts" in result
        assert "attention_points" in result


# ============================================================
# TestQuickEstimate (async)
# ============================================================

class TestQuickEstimate:
    @pytest.mark.asyncio
    async def test_quick_estimate_without_photo(self):
        svc, db = _make_service()

        with patch("app.services.presale_mobile_service.save_obj"):
            result = await svc.quick_estimate(
                user_id=1,
                equipment_description="六轴工业机器人",
                presale_ticket_id=10,
                customer_id=20,
            )

        assert "recognized_equipment" in result
        assert result["recognized_equipment"] == "六轴工业机器人"
        assert result["estimated_cost"] > 0
        assert result["price_range_min"] < result["price_range_max"]

    @pytest.mark.asyncio
    async def test_quick_estimate_with_photo(self):
        svc, db = _make_service()

        with patch.object(svc, "_recognize_equipment", new=AsyncMock(return_value={
            "equipment_name": "识别出的机器人",
            "confidence": 90,
        })), patch("app.services.presale_mobile_service.save_obj"):
            result = await svc.quick_estimate(
                user_id=1,
                equipment_description="机器人",
                equipment_photo_base64="base64data",
            )

        assert result["recognized_equipment"] == "识别出的机器人"
        assert result["confidence_score"] == 90

    @pytest.mark.asyncio
    async def test_quick_estimate_bom_items(self):
        svc, db = _make_service()

        with patch("app.services.presale_mobile_service.save_obj"):
            result = await svc.quick_estimate(
                user_id=1,
                equipment_description="机器人系统",
            )

        assert "bom_items" in result
        assert len(result["bom_items"]) > 0


# ============================================================
# TestMatchBomAndEstimate
# ============================================================

class TestMatchBomAndEstimate:
    def test_match_bom_and_estimate(self):
        svc, _ = _make_service()
        bom_items, total_cost = svc._match_bom_and_estimate("工业机器人")

        assert len(bom_items) > 0
        assert total_cost > 0
        # 验证总额等于各项之和
        expected = sum(item["amount"] for item in bom_items)
        assert total_cost == expected


# ============================================================
# TestCreateVisitRecord
# ============================================================

class TestCreateVisitRecord:
    def test_create_visit_record_success(self):
        svc, db = _make_service()

        # mock PresaleVisitRecord 以保证 created_at 有值
        mock_record = _make_visit_record()
        with patch("app.services.presale_mobile_service.save_obj"), \
             patch("app.services.presale_mobile_service.PresaleVisitRecord", return_value=mock_record):
            result = svc.create_visit_record(
                user_id=1,
                presale_ticket_id=10,
                customer_id=20,
                visit_date="2024-01-15",
                visit_type="现场拜访",
                attendees=[{"name": "张三", "title": "经理"}],
                discussion_points="讨论了自动化改造方案",
                customer_feedback="客户很满意",
                next_steps="发送详细报价",
            )

        assert "visit_type" in result
        assert "discussion_points" in result

    def test_format_visit_record(self):
        svc, db = _make_service()
        mock_record = _make_visit_record()
        result = svc._format_visit_record(mock_record)

        assert result["id"] == 1
        assert result["customer_id"] == 20
        assert result["visit_type"] == "现场拜访"
        assert "visit_date" in result


# ============================================================
# TestVoiceToVisitRecord (async)
# ============================================================

class TestVoiceToVisitRecord:
    @pytest.mark.asyncio
    async def test_voice_to_visit_record(self):
        svc, db = _make_service()
        mock_record = _make_visit_record(visit_type="电话会议")

        with patch.object(svc, "_speech_to_text", new=AsyncMock(return_value="会议录音内容")), \
             patch.object(svc, "_extract_visit_info", new=AsyncMock(return_value={
                 "attendees": [{"name": "李四"}],
                 "discussion_points": "技术方案讨论",
                 "customer_feedback": "需要调整价格",
                 "next_steps": "发送修改后的方案",
                 "summary": "综合讨论了技术和价格",
             })), \
             patch("app.services.presale_mobile_service.save_obj"), \
             patch("app.services.presale_mobile_service.PresaleVisitRecord", return_value=mock_record):

            result = await svc.voice_to_visit_record(
                user_id=1,
                audio_base64="base64audio",
                presale_ticket_id=10,
                customer_id=20,
                visit_date="2024-01-15",
                visit_type="电话会议",
            )

        assert result["visit_type"] == "电话会议"


# ============================================================
# TestGetVisitHistory
# ============================================================

class TestGetVisitHistory:
    def test_get_visit_history_empty(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = svc.get_visit_history(customer_id=99)
        assert result["visits"] == []
        assert result["total_visits"] == 0
        assert result["latest_visit"] is None

    def test_get_visit_history_with_visits(self):
        svc, db = _make_service()
        mock_record = _make_visit_record()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_record]

        result = svc.get_visit_history(customer_id=20)
        assert result["total_visits"] == 1
        assert result["latest_visit"] is not None


# ============================================================
# TestGetCustomerSnapshot
# ============================================================

class TestGetCustomerSnapshot:
    def test_get_customer_snapshot(self):
        svc, _ = _make_service()
        result = svc.get_customer_snapshot(customer_id=1)

        assert "customer_id" in result
        assert result["customer_id"] == 1
        assert "decision_makers" in result
        assert len(result["decision_makers"]) > 0


# ============================================================
# TestSyncOfflineData
# ============================================================

class TestSyncOfflineData:
    def test_sync_chat_data_new(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        db.flush.return_value = None

        result = svc.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="local_001",
            data_payload={
                "question": "测试问题",
                "answer": "测试回答",
                "question_type": "other",
            },
        )

        assert result["success"] is True
        assert "同步成功" in result["message"]

    def test_sync_visit_data_new(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        db.flush.return_value = None

        result = svc.sync_offline_data(
            user_id=1,
            data_type="visit",
            local_id="local_002",
            data_payload={
                "presale_ticket_id": 10,
                "customer_id": 20,
                "visit_date": "2024-01-15",
                "visit_type": "现场拜访",
                "attendees": [],
                "discussion_points": "技术讨论",
            },
        )
        assert result["success"] is True

    def test_sync_estimate_data_new(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        db.flush.return_value = None

        result = svc.sync_offline_data(
            user_id=1,
            data_type="estimate",
            local_id="local_003",
            data_payload={
                "recognized_equipment": "机器人",
                "equipment_description": "六轴机器人",
                "estimated_cost": 100000,
                "price_range_min": 130000,
                "price_range_max": 150000,
                "bom_items": [],
                "confidence_score": 80,
            },
        )
        assert result["success"] is True

    def test_sync_already_synced(self):
        svc, db = _make_service()
        mock_existing = MagicMock()
        mock_existing.sync_status = SyncStatus.SYNCED.value
        db.query.return_value.filter.return_value.first.return_value = mock_existing

        result = svc.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="already_synced",
            data_payload={},
        )
        assert result["success"] is True
        assert "已同步" in result["message"]

    def test_sync_failure_handling(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        # flush 失败导致同步失败
        db.flush.side_effect = Exception("DB Flush Error")
        # except 块中的 commit 正常
        db.commit.return_value = None

        result = svc.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="fail_001",
            data_payload={"question": "q"},
        )
        # 异常时返回失败结果
        assert result["success"] is False
        assert "同步失败" in result["message"]
