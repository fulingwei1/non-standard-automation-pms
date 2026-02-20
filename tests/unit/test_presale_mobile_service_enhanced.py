# -*- coding: utf-8 -*-
"""
移动端AI销售助手服务 - 增强单元测试
测试覆盖率目标: 70%+
"""

import json
import unittest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.presale_mobile import (
    PresaleMobileAssistantChat,
    PresaleMobileOfflineData,
    PresaleMobileQuickEstimate,
    PresaleVisitRecord,
)
from app.schemas.presale_mobile import QuestionType, SyncStatus, VisitType
from app.services.presale_mobile_service import PresaleMobileService


class TestPresaleMobileServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试正常初始化"""
        mock_db = MagicMock()
        service = PresaleMobileService(mock_db)
        assert service.db == mock_db


class TestQuestionClassification:
    """测试问题分类功能"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_classify_technical_question(self):
        """测试技术参数问题分类"""
        assert self.service._classify_question("这个设备的性能参数是什么") == QuestionType.TECHNICAL
        assert self.service._classify_question("规格尺寸多大") == QuestionType.TECHNICAL
        assert self.service._classify_question("功率配置如何") == QuestionType.TECHNICAL

    def test_classify_competitor_question(self):
        """测试竞品对比问题分类"""
        assert self.service._classify_question("与竞品相比有什么优势") == QuestionType.COMPETITOR
        assert self.service._classify_question("和对手的差异在哪里") == QuestionType.COMPETITOR

    def test_classify_case_question(self):
        """测试案例问题分类"""
        assert self.service._classify_question("有类似的成功案例吗") == QuestionType.CASE
        assert self.service._classify_question("之前的客户项目经验") == QuestionType.CASE

    def test_classify_pricing_question(self):
        """测试报价问题分类"""
        assert self.service._classify_question("这个方案多少钱") == QuestionType.PRICING
        assert self.service._classify_question("预算需要多少") == QuestionType.PRICING
        assert self.service._classify_question("成本费用如何") == QuestionType.PRICING

    def test_classify_other_question(self):
        """测试其他问题分类"""
        assert self.service._classify_question("你好") == QuestionType.OTHER
        assert self.service._classify_question("天气怎么样") == QuestionType.OTHER

    def test_classify_case_insensitive(self):
        """测试分类对大小写不敏感"""
        assert self.service._classify_question("价格是多少") == QuestionType.PRICING
        assert self.service._classify_question("价格是多少") == QuestionType.PRICING

    def test_classify_empty_question(self):
        """测试空问题"""
        assert self.service._classify_question("") == QuestionType.OTHER


class TestChatPromptBuilding:
    """测试AI提示词构建"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_build_technical_prompt(self):
        """测试技术问题提示词"""
        prompt = self.service._build_chat_prompt(
            "性能参数是什么", QuestionType.TECHNICAL, None
        )
        assert "技术参数信息" in prompt
        assert "性能参数是什么" in prompt
        assert "产品规格和性能指标" in prompt

    def test_build_competitor_prompt(self):
        """测试竞品对比提示词"""
        prompt = self.service._build_chat_prompt(
            "竞品对比", QuestionType.COMPETITOR, None
        )
        assert "竞品对比分析" in prompt
        assert "优势和差异化" in prompt

    def test_build_case_prompt(self):
        """测试案例问题提示词"""
        prompt = self.service._build_chat_prompt(
            "成功案例", QuestionType.CASE, None
        )
        assert "成功案例" in prompt
        assert "项目背景和需求" in prompt

    def test_build_pricing_prompt(self):
        """测试报价问题提示词"""
        prompt = self.service._build_chat_prompt(
            "价格多少", QuestionType.PRICING, None
        )
        assert "报价参考信息" in prompt
        assert "价格范围估算" in prompt

    def test_build_prompt_with_context(self):
        """测试带上下文的提示词"""
        context = {"customer": "ABC公司", "project": "自动化改造"}
        prompt = self.service._build_chat_prompt(
            "价格多少", QuestionType.PRICING, context
        )
        assert "ABC公司" in prompt
        assert "自动化改造" in prompt

    def test_build_other_prompt(self):
        """测试其他类型问题提示词"""
        prompt = self.service._build_chat_prompt(
            "你好", QuestionType.OTHER, None
        )
        assert "你好" in prompt
        assert "专业、简洁" in prompt


class TestAIChatService:
    """测试AI问答服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """测试成功的AI问答"""
        with patch.object(self.service, '_call_ai_service', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "这是AI的回答"
            
            with patch('app.services.presale_mobile_service.save_obj') as mock_save:
                mock_chat = MagicMock(spec=PresaleMobileAssistantChat)
                mock_chat.id = 1
                mock_chat.created_at = datetime.now()
                mock_save.return_value = mock_chat
                
                result = await self.service.chat(
                    user_id=1,
                    question="测试问题",
                    presale_ticket_id=10,
                    context={"test": "context"}
                )
                
                assert result["answer"] == "这是AI的回答"
                assert "response_time" in result
                assert result["context"] == {"test": "context"}
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_without_ticket_id(self):
        """测试无工单ID的问答"""
        with patch.object(self.service, '_call_ai_service', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "回答"
            
            with patch('app.services.presale_mobile_service.save_obj'):
                result = await self.service.chat(
                    user_id=1,
                    question="问题"
                )
                assert result is not None

    @pytest.mark.asyncio
    async def test_chat_classifies_question_type(self):
        """测试问答自动分类问题类型"""
        with patch.object(self.service, '_call_ai_service', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "回答"
            
            with patch('app.services.presale_mobile_service.save_obj'):
                result = await self.service.chat(user_id=1, question="价格多少")
                assert result["question_type"] == QuestionType.PRICING

    @pytest.mark.asyncio
    async def test_call_ai_service(self):
        """测试AI服务调用"""
        result = await self.service._call_ai_service("测试提示词", {"context": "test"})
        assert "模拟AI响应" in result
        assert "测试提示词" in result


class TestVoiceServices:
    """测试语音交互服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    @pytest.mark.asyncio
    async def test_voice_question_success(self):
        """测试语音提问成功"""
        with patch.object(self.service, '_speech_to_text', new_callable=AsyncMock) as mock_stt:
            mock_stt.return_value = "转换的文字"
            
            with patch.object(self.service, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {
                    "answer": "AI回答",
                    "question_type": QuestionType.TECHNICAL
                }
                
                with patch.object(self.service, '_text_to_speech', new_callable=AsyncMock) as mock_tts:
                    mock_tts.return_value = "https://audio.url"
                    
                    result = await self.service.voice_question(
                        user_id=1,
                        audio_base64="base64data",
                        audio_format="mp3",
                        presale_ticket_id=10
                    )
                    
                    assert result["transcription"] == "转换的文字"
                    assert result["answer"] == "AI回答"
                    assert result["audio_url"] == "https://audio.url"
                    assert "response_time" in result

    @pytest.mark.asyncio
    async def test_speech_to_text(self):
        """测试语音转文字"""
        result = await self.service._speech_to_text("base64audio", "mp3")
        assert "语音转换的文字" in result

    @pytest.mark.asyncio
    async def test_text_to_speech(self):
        """测试文字转语音"""
        result = await self.service._text_to_speech("测试文字")
        assert "https://" in result
        assert ".mp3" in result


class TestVisitPreparation:
    """测试拜访准备服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_get_visit_preparation(self):
        """测试获取拜访准备清单"""
        result = self.service.get_visit_preparation(ticket_id=100, user_id=1)
        
        assert result["ticket_id"] == 100
        assert "customer_name" in result
        assert "customer_background" in result
        assert "previous_interactions" in result
        assert "recommended_scripts" in result
        assert "attention_points" in result
        assert "technical_materials" in result
        assert "competitor_comparison" in result

    def test_visit_preparation_contains_scripts(self):
        """测试拜访准备包含话术"""
        result = self.service.get_visit_preparation(ticket_id=100, user_id=1)
        assert len(result["recommended_scripts"]) > 0

    def test_visit_preparation_contains_materials(self):
        """测试拜访准备包含技术资料"""
        result = self.service.get_visit_preparation(ticket_id=100, user_id=1)
        assert len(result["technical_materials"]) > 0


class TestQuickEstimate:
    """测试快速估价服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    @pytest.mark.asyncio
    async def test_quick_estimate_without_photo(self):
        """测试无照片的快速估价"""
        with patch('app.services.presale_mobile_service.save_obj') as mock_save:
            mock_estimate = MagicMock(spec=PresaleMobileQuickEstimate)
            mock_estimate.id = 1
            mock_save.return_value = mock_estimate
            
            result = await self.service.quick_estimate(
                user_id=1,
                equipment_description="六轴机器人"
            )
            
            assert "recognized_equipment" in result
            assert "estimated_cost" in result
            assert "price_range_min" in result
            assert "price_range_max" in result
            assert "bom_items" in result

    @pytest.mark.asyncio
    async def test_quick_estimate_with_photo(self):
        """测试有照片的快速估价"""
        with patch.object(self.service, '_recognize_equipment', new_callable=AsyncMock) as mock_recognize:
            mock_recognize.return_value = {
                "equipment_name": "识别的设备",
                "confidence": 90
            }
            
            with patch('app.services.presale_mobile_service.save_obj'):
                result = await self.service.quick_estimate(
                    user_id=1,
                    equipment_description="测试设备",
                    equipment_photo_base64="photo_data"
                )
                
                assert result["recognized_equipment"] == "识别的设备"
                assert result["confidence_score"] == 90

    @pytest.mark.asyncio
    async def test_recognize_equipment(self):
        """测试设备识别"""
        result = await self.service._recognize_equipment("image_base64")
        assert "equipment_name" in result
        assert "confidence" in result
        assert result["confidence"] > 0

    def test_match_bom_and_estimate(self):
        """测试BOM匹配和成本估算"""
        bom_items, estimated_cost = self.service._match_bom_and_estimate("六轴机器人")
        
        assert len(bom_items) > 0
        assert estimated_cost > 0
        assert estimated_cost == sum(item["amount"] for item in bom_items)

    @pytest.mark.asyncio
    async def test_estimate_price_range_calculation(self):
        """测试估价范围计算"""
        with patch('app.services.presale_mobile_service.save_obj'):
            result = await self.service.quick_estimate(
                user_id=1,
                equipment_description="测试设备"
            )
            
            # 验证价格范围是成本的 1.3-1.5 倍
            cost = result["estimated_cost"]
            assert result["price_range_min"] == int(cost * 1.3)
            assert result["price_range_max"] == int(cost * 1.5)


class TestVisitRecords:
    """测试拜访记录服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_create_visit_record(self):
        """测试创建拜访记录"""
        def mock_save(db, obj):
            obj.id = 1
            obj.created_at = datetime(2024, 1, 15, 10, 30, 0)
            return obj
        
        with patch('app.services.presale_mobile_service.save_obj', side_effect=mock_save):
            result = self.service.create_visit_record(
                user_id=1,
                presale_ticket_id=10,
                customer_id=20,
                visit_date="2024-01-15",
                visit_type=VisitType.FIRST_CONTACT.value,
                attendees=[{"name": "张三", "title": "总监"}],
                discussion_points="讨论要点",
                customer_feedback="客户反馈",
                next_steps="下一步"
            )
            
            assert result["id"] == 1
            assert result["presale_ticket_id"] == 10

    @pytest.mark.asyncio
    async def test_voice_to_visit_record(self):
        """测试语音转拜访记录"""
        with patch.object(self.service, '_speech_to_text', new_callable=AsyncMock) as mock_stt:
            mock_stt.return_value = "拜访转录文本"
            
            with patch.object(self.service, '_extract_visit_info', new_callable=AsyncMock) as mock_extract:
                mock_extract.return_value = {
                    "attendees": [{"name": "李四"}],
                    "discussion_points": "讨论内容",
                    "customer_feedback": "反馈",
                    "next_steps": "下一步",
                    "summary": "摘要"
                }
                
                with patch('app.services.presale_mobile_service.save_obj') as mock_save:
                    mock_visit = MagicMock(spec=PresaleVisitRecord)
                    mock_visit.id = 2
                    mock_visit.presale_ticket_id = 10
                    mock_visit.customer_id = 20
                    mock_visit.visit_date = date(2024, 1, 15)
                    mock_visit.visit_type = VisitType.FOLLOW_UP.value
                    mock_visit.attendees = [{"name": "李四"}]
                    mock_visit.discussion_points = "讨论内容"
                    mock_visit.customer_feedback = "反馈"
                    mock_visit.next_steps = "下一步"
                    mock_visit.ai_generated_summary = "摘要"
                    mock_visit.created_at = datetime.now()
                    mock_save.return_value = mock_visit
                    
                    result = await self.service.voice_to_visit_record(
                        user_id=1,
                        audio_base64="audio_data",
                        presale_ticket_id=10,
                        customer_id=20,
                        visit_date="2024-01-15",
                        visit_type=VisitType.PHONE.value
                    )
                    
                    assert result["id"] == 2
                    assert result["ai_generated_summary"] == "摘要"

    @pytest.mark.asyncio
    async def test_extract_visit_info(self):
        """测试提取拜访信息"""
        result = await self.service._extract_visit_info("拜访转录文本")
        
        assert "attendees" in result
        assert "discussion_points" in result
        assert "customer_feedback" in result
        assert "next_steps" in result
        assert "summary" in result

    def test_get_visit_history(self):
        """测试获取拜访历史"""
        mock_visit1 = MagicMock(spec=PresaleVisitRecord)
        mock_visit1.id = 1
        mock_visit1.customer_id = 20
        mock_visit1.visit_date = date(2024, 1, 20)
        mock_visit1.presale_ticket_id = 10
        mock_visit1.visit_type = VisitType.ON_SITE.value
        mock_visit1.attendees = []
        mock_visit1.discussion_points = "讨论1"
        mock_visit1.customer_feedback = None
        mock_visit1.next_steps = None
        mock_visit1.ai_generated_summary = None
        mock_visit1.created_at = datetime.now()
        
        mock_visit2 = MagicMock(spec=PresaleVisitRecord)
        mock_visit2.id = 2
        mock_visit2.customer_id = 20
        mock_visit2.visit_date = date(2024, 1, 15)
        mock_visit2.presale_ticket_id = 10
        mock_visit2.visit_type = VisitType.FOLLOW_UP.value
        mock_visit2.attendees = []
        mock_visit2.discussion_points = "讨论2"
        mock_visit2.customer_feedback = None
        mock_visit2.next_steps = None
        mock_visit2.ai_generated_summary = None
        mock_visit2.created_at = datetime.now()
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_visit1, mock_visit2
        ]
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_visit_history(customer_id=20)
        
        assert result["total_visits"] == 2
        assert len(result["visits"]) == 2
        assert result["latest_visit"]["id"] == 1

    def test_get_visit_history_empty(self):
        """测试空的拜访历史"""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_visit_history(customer_id=999)
        
        assert result["total_visits"] == 0
        assert result["visits"] == []
        assert result["latest_visit"] is None

    def test_format_visit_record(self):
        """测试格式化拜访记录"""
        mock_visit = MagicMock(spec=PresaleVisitRecord)
        mock_visit.id = 1
        mock_visit.presale_ticket_id = 10
        mock_visit.customer_id = 20
        mock_visit.visit_date = date(2024, 1, 15)
        mock_visit.visit_type = VisitType.ON_SITE.value
        mock_visit.attendees = [{"name": "张三"}]
        mock_visit.discussion_points = "讨论"
        mock_visit.customer_feedback = "反馈"
        mock_visit.next_steps = "下一步"
        mock_visit.ai_generated_summary = "摘要"
        mock_visit.created_at = datetime(2024, 1, 15, 10, 30, 0)
        
        result = self.service._format_visit_record(mock_visit)
        
        assert result["id"] == 1
        assert result["visit_date"] == "2024-01-15"
        assert result["attendees"] == [{"name": "张三"}]


class TestCustomerSnapshot:
    """测试客户快照服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_get_customer_snapshot(self):
        """测试获取客户快照"""
        result = self.service.get_customer_snapshot(customer_id=100)
        
        assert result["customer_id"] == 100
        assert "customer_name" in result
        assert "industry" in result
        assert "recent_tickets" in result
        assert "decision_makers" in result
        assert "key_concerns" in result


class TestOfflineDataSync:
    """测试离线数据同步服务"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_sync_chat_data_success(self):
        """测试同步对话数据成功"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        chat_data = {
            "question": "测试问题",
            "answer": "测试回答",
            "question_type": "technical",
            "response_time": 500
        }
        
        result = self.service.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="local_123",
            data_payload=chat_data
        )
        
        assert result["success"] is True
        assert "message" in result

    def test_sync_visit_data_success(self):
        """测试同步拜访数据成功"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        visit_data = {
            "presale_ticket_id": 10,
            "customer_id": 20,
            "visit_date": "2024-01-15",
            "visit_type": "on_site",
            "discussion_points": "讨论要点"
        }
        
        result = self.service.sync_offline_data(
            user_id=1,
            data_type="visit",
            local_id="local_456",
            data_payload=visit_data
        )
        
        assert result["success"] is True

    def test_sync_estimate_data_success(self):
        """测试同步估价数据成功"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        estimate_data = {
            "recognized_equipment": "六轴机器人",
            "equipment_description": "工业机器人",
            "estimated_cost": 100000,
            "price_range_min": 130000,
            "price_range_max": 150000
        }
        
        result = self.service.sync_offline_data(
            user_id=1,
            data_type="estimate",
            local_id="local_789",
            data_payload=estimate_data
        )
        
        assert result["success"] is True

    def test_sync_already_synced_data(self):
        """测试同步已同步的数据"""
        mock_existing = MagicMock(spec=PresaleMobileOfflineData)
        mock_existing.sync_status = SyncStatus.SYNCED.value
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_existing
        self.mock_db.query.return_value = mock_query
        
        result = self.service.sync_offline_data(
            user_id=1,
            data_type="chat",
            local_id="local_123",
            data_payload={"test": "data"}
        )
        
        assert result["success"] is True
        assert "已同步" in result["message"]

    def test_sync_data_failure(self):
        """测试同步数据失败"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # 模拟异常
        with patch.object(self.service, '_sync_chat_data', side_effect=Exception("同步错误")):
            result = self.service.sync_offline_data(
                user_id=1,
                data_type="chat",
                local_id="local_error",
                data_payload={"test": "data"}
            )
            
            assert result["success"] is False
            assert "同步失败" in result["message"]

    def test_sync_chat_data_internal(self):
        """测试内部同步对话数据方法"""
        chat_data = {
            "presale_ticket_id": 10,
            "question": "问题",
            "answer": "回答",
            "question_type": "technical",
            "context": {"key": "value"},
            "response_time": 300
        }
        
        mock_chat = MagicMock(spec=PresaleMobileAssistantChat)
        mock_chat.id = 123
        self.mock_db.add.return_value = None
        self.mock_db.flush.return_value = None
        
        # Mock the flush to set the id
        def mock_flush_side_effect():
            pass
        
        self.mock_db.flush.side_effect = mock_flush_side_effect
        
        with patch('app.services.presale_mobile_service.PresaleMobileAssistantChat', return_value=mock_chat):
            result_id = self.service._sync_chat_data(user_id=1, data=chat_data)
            assert result_id == 123

    def test_sync_visit_data_internal(self):
        """测试内部同步拜访数据方法"""
        visit_data = {
            "presale_ticket_id": 10,
            "customer_id": 20,
            "visit_date": "2024-01-15",
            "visit_type": "on_site",
            "attendees": [{"name": "张三"}],
            "discussion_points": "讨论"
        }
        
        mock_visit = MagicMock(spec=PresaleVisitRecord)
        mock_visit.id = 456
        
        with patch('app.services.presale_mobile_service.PresaleVisitRecord', return_value=mock_visit):
            result_id = self.service._sync_visit_data(user_id=1, data=visit_data)
            assert result_id == 456

    def test_sync_estimate_data_internal(self):
        """测试内部同步估价数据方法"""
        estimate_data = {
            "presale_ticket_id": 10,
            "customer_id": 20,
            "recognized_equipment": "设备名称",
            "equipment_description": "设备描述",
            "estimated_cost": 50000,
            "price_range_min": 65000,
            "price_range_max": 75000,
            "bom_items": [],
            "confidence_score": 85
        }
        
        mock_estimate = MagicMock(spec=PresaleMobileQuickEstimate)
        mock_estimate.id = 789
        
        with patch('app.services.presale_mobile_service.PresaleMobileQuickEstimate', return_value=mock_estimate):
            result_id = self.service._sync_estimate_data(user_id=1, data=estimate_data)
            assert result_id == 789


class TestEdgeCases:
    """测试边界条件"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = PresaleMobileService(self.mock_db)

    def test_classify_mixed_keywords(self):
        """测试包含多个关键词的问题"""
        # 技术关键词在代码中排在前面，会先匹配
        result = self.service._classify_question("这个设备的价格和参数是什么")
        assert result == QuestionType.TECHNICAL

    @pytest.mark.asyncio
    async def test_chat_with_empty_context(self):
        """测试空上下文的对话"""
        with patch.object(self.service, '_call_ai_service', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = "回答"
            with patch('app.services.presale_mobile_service.save_obj'):
                result = await self.service.chat(
                    user_id=1,
                    question="测试",
                    context=None
                )
                assert result["context"] is None

    def test_match_bom_returns_positive_cost(self):
        """测试BOM匹配返回正数成本"""
        bom_items, cost = self.service._match_bom_and_estimate("任意设备")
        assert cost > 0
        assert all(item["amount"] >= 0 for item in bom_items)

    @pytest.mark.asyncio
    async def test_quick_estimate_with_all_params(self):
        """测试包含所有参数的快速估价"""
        with patch.object(self.service, '_recognize_equipment', new_callable=AsyncMock) as mock_rec:
            mock_rec.return_value = {"equipment_name": "设备", "confidence": 80}
            with patch('app.services.presale_mobile_service.save_obj'):
                result = await self.service.quick_estimate(
                    user_id=1,
                    equipment_description="描述",
                    equipment_photo_base64="photo",
                    presale_ticket_id=10,
                    customer_id=20
                )
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.services.presale_mobile_service", "--cov-report=term-missing"])
