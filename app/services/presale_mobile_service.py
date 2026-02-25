# -*- coding: utf-8 -*-
"""
移动端AI销售助手 - 核心服务
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models.presale_mobile import (
    PresaleMobileAssistantChat,
    PresaleMobileOfflineData,
    PresaleMobileQuickEstimate,
    PresaleVisitRecord,
)
from app.schemas.presale_mobile import QuestionType, SyncStatus
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class PresaleMobileService:
    """移动端AI助手服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== AI问答服务 ====================

    async def chat(
        self,
        user_id: int,
        question: str,
        presale_ticket_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        实时AI问答

        Args:
            user_id: 用户ID
            question: 提问内容
            presale_ticket_id: 售前工单ID
            context: 对话上下文

        Returns:
            AI回答和相关信息
        """
        start_time = time.time()

        # 分析问题类型
        question_type = self._classify_question(question)

        # 构建AI提示词
        prompt = self._build_chat_prompt(question, question_type, context)

        # 调用AI服务
        answer = await self._call_ai_service(prompt, context)

        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)

        # 保存对话记录
        chat_record = PresaleMobileAssistantChat(
            user_id=user_id,
            presale_ticket_id=presale_ticket_id,
            question=question,
            answer=answer,
            question_type=question_type.value,
            context=context or {},
            response_time=response_time,
        )
        save_obj(self.db, chat_record)

        return {
            "id": chat_record.id,
            "answer": answer,
            "question_type": question_type,
            "response_time": response_time,
            "context": context,
            "created_at": chat_record.created_at,
        }

    def _classify_question(self, question: str) -> QuestionType:
        """分类问题类型"""
        question_lower = question.lower()

        # 技术参数相关关键词
        if any(
            kw in question_lower
            for kw in ["参数", "规格", "技术", "性能", "配置", "尺寸", "功率"]
        ):
            return QuestionType.TECHNICAL

        # 竞品对比相关关键词
        if any(kw in question_lower for kw in ["竞品", "对比", "差异", "优势", "劣势"]):
            return QuestionType.COMPETITOR

        # 案例相关关键词
        if any(kw in question_lower for kw in ["案例", "成功", "客户", "项目", "经验"]):
            return QuestionType.CASE

        # 报价相关关键词
        if any(
            kw in question_lower for kw in ["价格", "报价", "成本", "费用", "多少钱", "预算"]
        ):
            return QuestionType.PRICING

        return QuestionType.OTHER

    def _build_chat_prompt(
        self,
        question: str,
        question_type: QuestionType,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """构建AI提示词"""
        base_prompt = f"""你是一名专业的非标自动化销售助手，帮助销售人员现场解答客户问题。

问题类型：{question_type.value}
用户提问：{question}

"""
        if question_type == QuestionType.TECHNICAL:
            base_prompt += """
请提供准确的技术参数信息，包括：
- 产品规格和性能指标
- 技术特点和优势
- 适用场景和限制
- 相关技术文档参考
"""
        elif question_type == QuestionType.COMPETITOR:
            base_prompt += """
请提供竞品对比分析，包括：
- 主要竞品列表
- 功能和性能对比
- 我们的优势和差异化
- 应对策略建议
"""
        elif question_type == QuestionType.CASE:
            base_prompt += """
请提供相关成功案例，包括：
- 类似行业/规模的客户
- 项目背景和需求
- 解决方案要点
- 实施效果和客户反馈
"""
        elif question_type == QuestionType.PRICING:
            base_prompt += """
请提供报价参考信息，包括：
- 价格范围估算
- 影响价格的主要因素
- 成本构成说明
- 优惠政策和付款方式
"""

        if context:
            base_prompt += f"\n上下文信息：\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"

        base_prompt += "\n请用专业、简洁的语言回答，便于销售人员向客户转述。"
        return base_prompt

    async def _call_ai_service(
        self, prompt: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """调用AI服务"""
        # TODO: 集成真实的AI服务（OpenAI GPT-4 / Kimi API）
        # 这里返回模拟数据
        return f"这是针对您问题的专业回答。[模拟AI响应 - 生产环境需集成真实AI服务]\n\n提示词：{prompt[:100]}..."

    # ==================== 语音交互服务 ====================

    async def voice_question(
        self,
        user_id: int,
        audio_base64: str,
        audio_format: str = "mp3",
        presale_ticket_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        语音提问（STT + AI + TTS）

        Args:
            user_id: 用户ID
            audio_base64: 音频文件（base64编码）
            audio_format: 音频格式
            presale_ticket_id: 售前工单ID

        Returns:
            语音转文字、AI回答、回答音频
        """
        start_time = time.time()

        # 1. 语音转文字（STT）
        transcription = await self._speech_to_text(audio_base64, audio_format)

        # 2. AI问答
        chat_result = await self.chat(user_id, transcription, presale_ticket_id)

        # 3. 文字转语音（TTS）
        audio_url = await self._text_to_speech(chat_result["answer"])

        response_time = int((time.time() - start_time) * 1000)

        return {
            "transcription": transcription,
            "answer": chat_result["answer"],
            "audio_url": audio_url,
            "response_time": response_time,
            "question_type": chat_result["question_type"],
        }

    async def _speech_to_text(self, audio_base64: str, audio_format: str) -> str:
        """语音转文字"""
        # TODO: 集成OpenAI Whisper API
        # 模拟返回
        return "这是从语音转换的文字内容 [需要集成Whisper API]"

    async def _text_to_speech(self, text: str) -> str:
        """文字转语音"""
        # TODO: 集成OpenAI TTS API
        # 模拟返回
        return "https://example.com/tts/audio_12345.mp3"

    # ==================== 拜访准备服务 ====================

    def get_visit_preparation(
        self, ticket_id: int, user_id: int
    ) -> Dict[str, Any]:
        """
        获取拜访准备清单

        Args:
            ticket_id: 售前工单ID
            user_id: 用户ID

        Returns:
            拜访准备清单
        """
        # TODO: 从数据库查询售前工单、客户信息、历史记录
        # 这里返回模拟数据
        return {
            "ticket_id": ticket_id,
            "customer_name": "某某科技有限公司",
            "customer_background": "该公司是一家专注于智能制造的高新技术企业，主要业务包括...",
            "previous_interactions": [
                {
                    "date": "2024-01-15",
                    "type": "电话沟通",
                    "summary": "讨论了初步需求，客户关注自动化改造成本",
                },
                {
                    "date": "2024-01-20",
                    "type": "邮件往来",
                    "summary": "发送了初步方案和报价，等待客户反馈",
                },
            ],
            "recommended_scripts": [
                "开场：感谢贵公司对我们的信任，今天我们将详细讨论...",
                "需求挖掘：请问贵公司目前在生产线上遇到的主要痛点是什么？",
                "方案介绍：针对您提到的问题，我们的解决方案包括...",
                "异议处理：关于价格问题，我们可以从ROI角度分析...",
            ],
            "attention_points": [
                "客户非常关注成本，需要重点说明ROI",
                "决策人是技术总监和采购经理，需要分别准备技术和商务材料",
                "竞品是XX公司，需要准备差异化对比资料",
                "客户希望看到类似行业的成功案例",
            ],
            "technical_materials": [
                {"name": "产品技术手册", "url": "/materials/tech_manual.pdf"},
                {"name": "成功案例集", "url": "/materials/cases.pdf"},
                {"name": "ROI计算表", "url": "/materials/roi_calculator.xlsx"},
            ],
            "competitor_comparison": {
                "main_competitors": ["竞品A", "竞品B"],
                "our_advantages": [
                    "技术成熟度更高",
                    "售后服务响应更快",
                    "性价比更优",
                ],
            },
        }

    # ==================== 快速估价服务 ====================

    async def quick_estimate(
        self,
        user_id: int,
        equipment_description: str,
        equipment_photo_base64: Optional[str] = None,
        presale_ticket_id: Optional[int] = None,
        customer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        现场快速估价

        Args:
            user_id: 用户ID
            equipment_description: 设备描述
            equipment_photo_base64: 设备照片（base64）
            presale_ticket_id: 售前工单ID
            customer_id: 客户ID

        Returns:
            快速估价结果
        """
        recognized_equipment = equipment_description
        confidence_score = 70

        # 如果有照片，进行图像识别
        if equipment_photo_base64:
            recognition_result = await self._recognize_equipment(equipment_photo_base64)
            recognized_equipment = recognition_result["equipment_name"]
            confidence_score = recognition_result["confidence"]

        # 匹配BOM和估算成本
        bom_items, estimated_cost = self._match_bom_and_estimate(recognized_equipment)

        # 计算报价范围（成本 * 1.3 ~ 1.5）
        price_range_min = int(estimated_cost * 1.3)
        price_range_max = int(estimated_cost * 1.5)

        # 保存估价记录
        estimate_record = PresaleMobileQuickEstimate(
            presale_ticket_id=presale_ticket_id,
            customer_id=customer_id,
            equipment_photo_url=None,  # TODO: 上传照片到云存储
            recognized_equipment=recognized_equipment,
            equipment_description=equipment_description,
            estimated_cost=estimated_cost,
            price_range_min=price_range_min,
            price_range_max=price_range_max,
            bom_items=bom_items,
            confidence_score=confidence_score,
            created_by=user_id,
        )
        save_obj(self.db, estimate_record)

        return {
            "id": estimate_record.id,
            "recognized_equipment": recognized_equipment,
            "estimated_cost": estimated_cost,
            "price_range_min": price_range_min,
            "price_range_max": price_range_max,
            "bom_items": bom_items,
            "confidence_score": confidence_score,
            "recommendation": f"建议报价范围：{price_range_min:,} - {price_range_max:,} 元",
        }

    async def _recognize_equipment(self, image_base64: str) -> Dict[str, Any]:
        """设备图像识别"""
        # TODO: 集成OpenAI Vision API
        return {
            "equipment_name": "六轴工业机器人",
            "equipment_category": "机械臂",
            "confidence": 85,
            "specifications": {
                "payload": "10kg",
                "reach": "1400mm",
            },
        }

    def _match_bom_and_estimate(
        self, equipment_name: str
    ) -> tuple[List[Dict[str, Any]], int]:
        """匹配BOM并估算成本"""
        # TODO: 从数据库查询历史BOM数据
        # 模拟返回
        bom_items = [
            {"name": "伺服电机", "quantity": 6, "unit_price": 3000, "amount": 18000},
            {"name": "减速机", "quantity": 6, "unit_price": 2000, "amount": 12000},
            {"name": "控制器", "quantity": 1, "unit_price": 15000, "amount": 15000},
            {"name": "机械本体", "quantity": 1, "unit_price": 50000, "amount": 50000},
            {"name": "其他辅材", "quantity": 1, "unit_price": 5000, "amount": 5000},
        ]
        estimated_cost = sum(item["amount"] for item in bom_items)
        return bom_items, estimated_cost

    # ==================== 拜访记录服务 ====================

    def create_visit_record(
        self,
        user_id: int,
        presale_ticket_id: int,
        customer_id: int,
        visit_date: str,
        visit_type: str,
        attendees: List[Dict[str, str]],
        discussion_points: str,
        customer_feedback: Optional[str] = None,
        next_steps: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建拜访记录

        Args:
            user_id: 用户ID
            presale_ticket_id: 售前工单ID
            customer_id: 客户ID
            visit_date: 拜访日期
            visit_type: 拜访类型
            attendees: 参会人员
            discussion_points: 讨论要点
            customer_feedback: 客户反馈
            next_steps: 下一步行动

        Returns:
            拜访记录
        """
        visit_record = PresaleVisitRecord(
            presale_ticket_id=presale_ticket_id,
            customer_id=customer_id,
            visit_date=datetime.strptime(visit_date, "%Y-%m-%d").date(),
            visit_type=visit_type,
            attendees=attendees,
            discussion_points=discussion_points,
            customer_feedback=customer_feedback,
            next_steps=next_steps,
            created_by=user_id,
        )
        save_obj(self.db, visit_record)

        return self._format_visit_record(visit_record)

    async def voice_to_visit_record(
        self,
        user_id: int,
        audio_base64: str,
        presale_ticket_id: int,
        customer_id: int,
        visit_date: str,
        visit_type: str,
    ) -> Dict[str, Any]:
        """
        语音转拜访记录

        Args:
            user_id: 用户ID
            audio_base64: 拜访录音（base64）
            presale_ticket_id: 售前工单ID
            customer_id: 客户ID
            visit_date: 拜访日期
            visit_type: 拜访类型

        Returns:
            拜访记录
        """
        # 1. 语音转文字
        transcription = await self._speech_to_text(audio_base64, "mp3")

        # 2. AI提取关键信息
        extracted_info = await self._extract_visit_info(transcription)

        # 3. 创建拜访记录
        visit_record = PresaleVisitRecord(
            presale_ticket_id=presale_ticket_id,
            customer_id=customer_id,
            visit_date=datetime.strptime(visit_date, "%Y-%m-%d").date(),
            visit_type=visit_type,
            attendees=extracted_info.get("attendees", []),
            discussion_points=extracted_info.get("discussion_points", ""),
            customer_feedback=extracted_info.get("customer_feedback"),
            next_steps=extracted_info.get("next_steps"),
            audio_recording_url=None,  # TODO: 上传录音到云存储
            ai_generated_summary=extracted_info.get("summary"),
            created_by=user_id,
        )
        save_obj(self.db, visit_record)

        return self._format_visit_record(visit_record)

    async def _extract_visit_info(self, transcription: str) -> Dict[str, Any]:
        """从转录文本中提取拜访信息"""
        # TODO: 使用AI提取结构化信息
        return {
            "attendees": [
                {"name": "张三", "title": "技术总监", "company": "客户公司"}
            ],
            "discussion_points": "讨论了自动化改造方案的技术细节和实施计划",
            "customer_feedback": "客户对方案整体满意，但希望进一步优化成本",
            "next_steps": "1周内提供优化方案和详细报价",
            "summary": "本次拜访主要讨论了技术方案，客户反馈积极，下一步需要优化成本方案。",
        }

    def get_visit_history(self, customer_id: int) -> Dict[str, Any]:
        """获取客户拜访历史"""
        visits = (
            self.db.query(PresaleVisitRecord)
            .filter(PresaleVisitRecord.customer_id == customer_id)
            .order_by(desc(PresaleVisitRecord.visit_date))
            .all()
        )

        formatted_visits = [self._format_visit_record(v) for v in visits]

        return {
            "visits": formatted_visits,
            "total_visits": len(formatted_visits),
            "latest_visit": formatted_visits[0] if formatted_visits else None,
        }

    def _format_visit_record(self, record: PresaleVisitRecord) -> Dict[str, Any]:
        """格式化拜访记录"""
        return {
            "id": record.id,
            "presale_ticket_id": record.presale_ticket_id,
            "customer_id": record.customer_id,
            "visit_date": record.visit_date.isoformat(),
            "visit_type": record.visit_type,
            "attendees": record.attendees,
            "discussion_points": record.discussion_points,
            "customer_feedback": record.customer_feedback,
            "next_steps": record.next_steps,
            "ai_generated_summary": record.ai_generated_summary,
            "created_at": record.created_at.isoformat(),
        }

    # ==================== 客户快照服务 ====================

    def get_customer_snapshot(self, customer_id: int) -> Dict[str, Any]:
        """获取客户快照（背景信息）"""
        # TODO: 从数据库查询客户详细信息
        return {
            "customer_id": customer_id,
            "customer_name": "某某科技有限公司",
            "industry": "智能制造",
            "company_size": "500-1000人",
            "contact_person": "张经理",
            "contact_phone": "138****8888",
            "recent_tickets": [
                {
                    "id": 123,
                    "title": "生产线自动化改造",
                    "status": "进行中",
                    "created_at": "2024-01-10",
                }
            ],
            "total_orders": 5,
            "total_revenue": 2500000.0,
            "last_interaction": "2024-01-20T10:30:00",
            "key_concerns": ["成本控制", "实施周期", "售后服务"],
            "decision_makers": [
                {"name": "李总", "title": "总经理", "decision_power": "最终决策"},
                {"name": "张总监", "title": "技术总监", "decision_power": "技术评审"},
                {"name": "王经理", "title": "采购经理", "decision_power": "商务谈判"},
            ],
        }

    # ==================== 离线数据同步服务 ====================

    def sync_offline_data(
        self, user_id: int, data_type: str, local_id: str, data_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        同步离线数据

        Args:
            user_id: 用户ID
            data_type: 数据类型
            local_id: 本地临时ID
            data_payload: 数据内容

        Returns:
            同步结果
        """
        try:
            # 检查是否已同步
            existing = (
                self.db.query(PresaleMobileOfflineData)
                .filter(
                    and_(
                        PresaleMobileOfflineData.user_id == user_id,
                        PresaleMobileOfflineData.local_id == local_id,
                    )
                )
                .first()
            )

            if existing and existing.sync_status == SyncStatus.SYNCED.value:
                return {
                    "success": True,
                    "synced_id": None,
                    "message": "数据已同步，跳过",
                }

            # 根据数据类型处理数据
            synced_id = None
            if data_type == "chat":
                synced_id = self._sync_chat_data(user_id, data_payload)
            elif data_type == "visit":
                synced_id = self._sync_visit_data(user_id, data_payload)
            elif data_type == "estimate":
                synced_id = self._sync_estimate_data(user_id, data_payload)

            # 记录同步状态
            if existing:
                existing.sync_status = SyncStatus.SYNCED.value
                existing.synced_at = datetime.now()
            else:
                sync_record = PresaleMobileOfflineData(
                    user_id=user_id,
                    data_type=data_type,
                    local_id=local_id,
                    data_payload=data_payload,
                    sync_status=SyncStatus.SYNCED.value,
                    synced_at=datetime.now(),
                )
                self.db.add(sync_record)

            self.db.commit()

            return {
                "success": True,
                "synced_id": synced_id,
                "message": "同步成功",
            }

        except Exception as e:
            logger.error(f"离线数据同步失败: {str(e)}")
            # 记录失败状态
            sync_record = PresaleMobileOfflineData(
                user_id=user_id,
                data_type=data_type,
                local_id=local_id,
                data_payload=data_payload,
                sync_status=SyncStatus.FAILED.value,
                error_message=str(e),
            )
            self.db.add(sync_record)
            self.db.commit()

            return {
                "success": False,
                "synced_id": None,
                "message": f"同步失败: {str(e)}",
            }

    def _sync_chat_data(self, user_id: int, data: Dict[str, Any]) -> int:
        """同步对话数据"""
        chat = PresaleMobileAssistantChat(
            user_id=user_id,
            presale_ticket_id=data.get("presale_ticket_id"),
            question=data.get("question"),
            answer=data.get("answer"),
            question_type=data.get("question_type", "other"),
            context=data.get("context", {}),
            response_time=data.get("response_time", 0),
        )
        self.db.add(chat)
        self.db.flush()
        return chat.id

    def _sync_visit_data(self, user_id: int, data: Dict[str, Any]) -> int:
        """同步拜访数据"""
        visit = PresaleVisitRecord(
            presale_ticket_id=data["presale_ticket_id"],
            customer_id=data["customer_id"],
            visit_date=datetime.strptime(data["visit_date"], "%Y-%m-%d").date(),
            visit_type=data["visit_type"],
            attendees=data.get("attendees", []),
            discussion_points=data.get("discussion_points", ""),
            customer_feedback=data.get("customer_feedback"),
            next_steps=data.get("next_steps"),
            created_by=user_id,
        )
        self.db.add(visit)
        self.db.flush()
        return visit.id

    def _sync_estimate_data(self, user_id: int, data: Dict[str, Any]) -> int:
        """同步估价数据"""
        estimate = PresaleMobileQuickEstimate(
            presale_ticket_id=data.get("presale_ticket_id"),
            customer_id=data.get("customer_id"),
            recognized_equipment=data.get("recognized_equipment"),
            equipment_description=data.get("equipment_description"),
            estimated_cost=data.get("estimated_cost"),
            price_range_min=data.get("price_range_min"),
            price_range_max=data.get("price_range_max"),
            bom_items=data.get("bom_items", []),
            confidence_score=data.get("confidence_score", 0),
            created_by=user_id,
        )
        self.db.add(estimate)
        self.db.flush()
        return estimate.id
