"""
AI客户端服务
支持 OpenAI GPT-4、Kimi API 和 智谱 GLM-5
"""

import json
import logging
import os
import time
from typing import Any, Dict

import httpx

_ai_logger = logging.getLogger("ai.usage")

# 尝试导入 OpenAI SDK
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

# 尝试导入 zai-sdk（智谱AI）
try:
    from zai import ZhipuAiClient

    ZAI_AVAILABLE = True
except ImportError:
    ZAI_AVAILABLE = False
    ZhipuAiClient = None


_AI_SETTINGS_CACHE: Dict[str, Any] = {"data": {}, "ts": 0.0}


def load_ai_settings(force: bool = False) -> Dict[str, str]:
    """读取管理员在后台配置的 AI 参数（DB 覆盖 env）。best-effort + 30s 缓存。"""
    now = time.time()
    if not force and _AI_SETTINGS_CACHE["data"] and now - _AI_SETTINGS_CACHE["ts"] < 30:
        return _AI_SETTINGS_CACHE["data"]
    data: Dict[str, str] = {}
    try:
        from sqlalchemy import text as _t

        from app.models.base import SessionLocal

        db = SessionLocal()
        try:
            for row in db.execute(_t("SELECT key, value FROM ai_settings")).all():
                if row[1] not in (None, ""):
                    data[row[0]] = row[1]
        finally:
            db.close()
    except Exception:  # noqa: BLE001 - 表不存在/DB不可用时静默回退 env
        data = {}
    _AI_SETTINGS_CACHE["data"] = data
    _AI_SETTINGS_CACHE["ts"] = now
    return data


def is_mock_response(response) -> bool:
    """判断 AI 响应是否为降级演示数据（模型名带 -mock 后缀）。

    业务侧在把 AI 输出写入真实数据前必须调用本函数把关，
    演示数据静默入库是审计判定的共性根因之一。
    """
    if not isinstance(response, dict):
        return False
    return str(response.get("model") or "").endswith("-mock")


class AIClientService:
    """AI客户端服务"""

    def __init__(self):
        cfg = load_ai_settings()

        def _get(key, default=""):
            v = cfg.get(key)
            return v if v not in (None, "") else os.getenv(key, default)

        self.openai_api_key = _get("OPENAI_API_KEY", "")
        self.kimi_api_key = _get("KIMI_API_KEY", "")
        self.zhipu_api_key = _get("ZHIPU_API_KEY", "")  # 新增智谱API Key
        # 阿里百炼 Coding Plan（通义千问）：专属 base_url + 套餐模型（后台可配置，覆盖 env）
        self.qwen_api_key = _get("ALIBABA_API_KEY", "")
        self.qwen_base_url = _get(
            "ALIBABA_BASE_URL", "https://coding.dashscope.aliyuncs.com/v1"
        ).rstrip("/")
        self.qwen_model = _get("ALIBABA_MODEL", "qwen3.7-plus")
        # 统一超时（秒）+ 超时降级用的快模型
        try:
            self.qwen_timeout = float(_get("ALIBABA_TIMEOUT", "60"))
        except (TypeError, ValueError):
            self.qwen_timeout = 60.0
        self.qwen_fast_model = _get("ALIBABA_FAST_MODEL", "qwen3-coder-plus")
        # 默认模型：管理员显式指定 AI_DEFAULT_MODEL（qwen*/glm*/gpt*/kimi* 前缀决定厂商）优先；
        # 否则用已配置的通义千问，其次 GLM-5
        self.default_model = (
            _get("AI_DEFAULT_MODEL", "")
            or (self.qwen_model if self.qwen_api_key else "glm-5")
        )

        # 初始化OpenAI客户端
        if self.openai_api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        # 初始化智谱AI客户端
        if self.zhipu_api_key and ZAI_AVAILABLE:
            self.zhipu_client = ZhipuAiClient(api_key=self.zhipu_api_key)
        else:
            self.zhipu_client = None

    def generate_solution(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        生成方案
        支持模型: qwen*(阿里百炼Coding Plan), glm-5, gpt-4, kimi
        未配置对应厂商密钥时，自动回退到已配置的通义千问。
        """
        model = model or self.default_model
        if model.startswith("qwen"):
            return self._call_qwen(prompt, model, temperature, max_tokens)
        elif model.startswith("glm"):
            if self.zhipu_client:
                return self._call_glm5(prompt, model, temperature, max_tokens)
            return self._fallback_qwen_or(prompt, temperature, max_tokens,
                                          lambda: self._call_glm5(prompt, model, temperature, max_tokens))
        elif model.startswith("gpt"):
            if self.openai_client:
                return self._call_openai(prompt, model, temperature, max_tokens)
            return self._fallback_qwen_or(prompt, temperature, max_tokens,
                                          lambda: self._call_openai(prompt, model, temperature, max_tokens))
        elif model.startswith("kimi"):
            if self.kimi_api_key:
                return self._call_kimi(prompt, temperature, max_tokens)
            return self._fallback_qwen_or(prompt, temperature, max_tokens,
                                          lambda: self._call_kimi(prompt, temperature, max_tokens))
        else:
            return self._fallback_qwen_or(prompt, temperature, max_tokens,
                                          lambda: self._call_glm5(prompt, "glm-5", temperature, max_tokens))

    def _fallback_qwen_or(self, prompt, temperature, max_tokens, otherwise):
        """未配置目标厂商密钥时，优先回退到通义千问；否则执行原逻辑（可能走mock）。"""
        if self.qwen_api_key:
            return self._call_qwen(prompt, self.qwen_model, temperature, max_tokens)
        return otherwise()

    def generate_architecture(
        self, prompt: str, model: str = "gpt-4", temperature: float = 0.5
    ) -> Dict[str, Any]:
        """
        生成架构图
        """
        return self.generate_solution(prompt, model, temperature, max_tokens=1500)

    def _call_openai(
        self, prompt: str, model: str, temperature: float, max_tokens: int
    ) -> Dict[str, Any]:
        """调用OpenAI API"""
        if not self.openai_client:
            # 模拟响应
            return self._mock_response(prompt, model)

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位非标自动化行业的资深技术专家，擅长方案设计和系统架构。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return self._mock_response(prompt, model)

    def _call_qwen(
        self, prompt: str, model: str, temperature: float, max_tokens: int
    ) -> Dict[str, Any]:
        """调用阿里百炼 Coding Plan（通义千问，OpenAI 兼容协议）。

        统一超时（ALIBABA_TIMEOUT）+ 重试1次 + 超时/失败自动降级到快模型 + 用量日志。
        """
        if not self.qwen_api_key:
            return self._mock_response(prompt, model)

        url = f"{self.qwen_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.qwen_api_key}",
            "Content-Type": "application/json",
        }
        primary = model or self.qwen_model
        # 两次尝试：首次用目标模型；重试时降级到快模型（若目标本就是快模型则不变）
        attempts = [primary, self.qwen_fast_model if primary != self.qwen_fast_model else primary]

        last_err = None
        for i, use_model in enumerate(attempts):
            data = {
                "model": use_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位非标自动化行业的资深技术专家，擅长方案设计和系统架构。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            t0 = time.time()
            try:
                with httpx.Client() as client:
                    response = client.post(
                        url, headers=headers, json=data, timeout=self.qwen_timeout
                    )
                    response.raise_for_status()
                    result = response.json()
                usage = result.get(
                    "usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                )
                elapsed = round(time.time() - t0, 2)
                _ai_logger.info(
                    "[AI用量] model=%s tokens=%s(prompt=%s,completion=%s) 耗时=%ss 尝试=%s",
                    result.get("model", use_model),
                    usage.get("total_tokens"),
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    elapsed,
                    i + 1,
                )
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model", use_model),
                    "usage": usage,
                }
            except Exception as e:
                last_err = e
                _ai_logger.warning(
                    "[AI重试] model=%s 第%s次失败 耗时=%ss error=%s",
                    use_model,
                    i + 1,
                    round(time.time() - t0, 2),
                    str(e)[:120],
                )
                continue

        print(f"Qwen(Bailian) API Error after retries: {last_err}")
        return self._mock_response(prompt, model)

    def analyze_image(self, prompt: str, image_b64: str, mime: str = "image/jpeg",
                      max_tokens: int = 2000) -> Dict[str, Any]:
        """多模态：图纸/现场照片理解（通义千问视觉模型 qwen3.7-plus）。
        image_b64 为不含前缀的 base64 字符串。"""
        if not self.qwen_api_key:
            return self._mock_response(prompt, "qwen-vl")
        url = f"{self.qwen_base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.qwen_api_key}", "Content-Type": "application/json"}
        data = {
            "model": self.qwen_model,  # qwen3.7-plus 具备视觉能力
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                ]},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        t0 = time.time()
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=data, timeout=self.qwen_timeout)
                response.raise_for_status()
                result = response.json()
            usage = result.get("usage", {})
            _ai_logger.info("[AI用量-视觉] model=%s tokens=%s 耗时=%ss",
                            result.get("model"), usage.get("total_tokens"), round(time.time() - t0, 2))
            return {"content": result["choices"][0]["message"]["content"], "model": result.get("model"), "usage": usage}
        except Exception as e:  # noqa: BLE001
            _ai_logger.warning("[AI视觉失败] error=%s", str(e)[:150])
            return {"content": "", "error": str(e)[:200]}

    def _call_kimi(self, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """调用Kimi API"""
        if not self.kimi_api_key:
            return self._mock_response(prompt, "kimi")

        try:
            url = "https://api.moonshot.cn/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.kimi_api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "moonshot-v1-8k",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位非标自动化行业的资深技术专家，擅长方案设计和系统架构。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=data, timeout=60.0)
                response.raise_for_status()
                result = response.json()

            return {
                "content": result["choices"][0]["message"]["content"],
                "model": "kimi",
                "usage": result.get(
                    "usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                ),
            }
        except Exception as e:
            print(f"Kimi API Error: {e}")
            return self._mock_response(prompt, "kimi")

    def _call_glm5(
        self, prompt: str, model: str, temperature: float, max_tokens: int
    ) -> Dict[str, Any]:
        """
        调用智谱 GLM-5 API

        特性:
        - 200K 上下文窗口
        - 128K 最大输出
        - 支持深度思考模式
        - Agentic Coding 能力
        - Function Call 支持
        """
        if not self.zhipu_client:
            print("GLM-5 客户端未初始化，使用 Mock 模式")
            return self._mock_response(prompt, "glm-5")

        try:
            # 判断是否需要启用思考模式（复杂任务）
            enable_thinking = any(
                keyword in prompt
                for keyword in ["复杂", "设计", "架构", "优化", "分析", "规划", "方案"]
            )

            thinking_config = None
            if enable_thinking:
                thinking_config = {"type": "enabled"}

            # 调用 GLM-5
            response = self.zhipu_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位非标自动化行业的资深技术专家，擅长方案设计和系统架构。你具备深厚的工程经验，能够提供高质量的技术方案和专业建议。",
                    },
                    {"role": "user", "content": prompt},
                ],
                thinking=thinking_config,
                max_tokens=min(max_tokens, 65536),  # GLM-5 支持最大 65536
                temperature=temperature,
            )

            # 提取响应内容
            content = response.choices[0].message.content

            # 提取思考过程（如果有）
            reasoning_content = None
            if hasattr(response.choices[0].message, "reasoning_content"):
                reasoning_content = response.choices[0].message.reasoning_content

            # 构造返回结果
            result = {
                "content": content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            # 添加思考过程（如果有）
            if reasoning_content:
                result["reasoning"] = reasoning_content

            return result

        except Exception as e:
            print(f"GLM-5 API Error: {e}")
            # 降级到 Mock 模式
            return self._mock_response(prompt, "glm-5")

    def _mock_response(self, prompt: str, model: str) -> Dict[str, Any]:
        """模拟AI响应 (用于开发测试)"""
        # 检测请求类型
        if "架构图" in prompt or "Mermaid" in prompt:
            content = self._mock_architecture_diagram()
        else:
            content = self._mock_solution()

        return {
            "content": content,
            "model": f"{model}-mock",
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(prompt) + len(content)) // 4,
            },
        }

    def _mock_solution(self) -> str:
        """模拟方案内容"""
        solution = {
            "description": "基于客户需求，我们设计了一套高效的非标自动化生产线方案。该方案采用模块化设计，可根据实际需求灵活调整。",
            "technical_parameters": {
                "生产节拍": "60秒/件",
                "自动化程度": "95%",
                "设备精度": "±0.05mm",
                "能耗": "15kW",
                "占地面积": "50平方米",
            },
            "equipment_list": [
                {
                    "name": "自动上料机",
                    "model": "ZSL-100",
                    "quantity": 1,
                    "unit": "台",
                    "function": "自动上料，支持多种规格",
                },
                {
                    "name": "视觉检测系统",
                    "model": "VIS-200",
                    "quantity": 2,
                    "unit": "套",
                    "function": "产品质量检测，缺陷识别",
                },
                {
                    "name": "六轴机器人",
                    "model": "ROBOT-600",
                    "quantity": 2,
                    "unit": "台",
                    "function": "抓取、搬运、装配",
                },
                {
                    "name": "PLC控制系统",
                    "model": "PLC-S7-1500",
                    "quantity": 1,
                    "unit": "套",
                    "function": "整线控制和数据采集",
                },
            ],
            "process_flow": "1. 自动上料 → 2. 视觉定位 → 3. 机器人抓取 → 4. 装配加工 → 5. 质量检测 → 6. 自动下料",
            "key_features": [
                "模块化设计，易于扩展",
                "高精度视觉定位",
                "智能故障诊断",
                "数据可视化监控",
            ],
            "technical_advantages": [
                "提高生产效率50%以上",
                "降低人工成本60%",
                "产品合格率达到99.5%",
                "设备故障率低于0.5%",
            ],
        }

        return "```json\n" + json.dumps(solution, ensure_ascii=False, indent=2) + "\n```"

    def _mock_architecture_diagram(self) -> str:
        """模拟架构图"""
        mermaid = """```mermaid
graph TB
    A[上料单元] --> B[视觉检测单元]
    B --> C[机器人装配单元]
    C --> D[质量检测单元]
    D --> E[下料单元]
    
    F[PLC控制系统] -.-> A
    F -.-> B
    F -.-> C
    F -.-> D
    F -.-> E
    
    G[MES系统] -.-> F
    G --> H[数据可视化平台]
    
    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#FFB6C1
    style D fill:#DDA0DD
    style E fill:#F0E68C
    style F fill:#FFA07A
    style G fill:#20B2AA
```"""
        return mermaid
