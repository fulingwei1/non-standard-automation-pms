# -*- coding: utf-8 -*-
"""
企业微信API客户端
实现access_token获取、缓存和消息发送
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:  # pragma: no cover - 运行环境可选依赖
    requests = None

from app.core.config import settings


class WeChatTokenCache:
    """企业微信Token缓存（内存缓存）"""

    _cache: Dict[str, Any] = {}

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """获取缓存的token"""
        if key not in cls._cache:
            return None

        cached = cls._cache[key]
        # 检查是否过期（提前5分钟刷新）
        if cached['expires_at'] < datetime.now() + timedelta(minutes=5):
            return None

        return cached['token']

    @classmethod
    def set(cls, key: str, token: str, expires_in: int):
        """设置token缓存"""
        expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 提前5分钟过期
        cls._cache[key] = {
            'token': token,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }

    @classmethod
    def clear(cls, key: Optional[str] = None):
        """清除缓存"""
        if key:
            cls._cache.pop(key, None)
        else:
            cls._cache.clear()


class WeChatClient:
    """企业微信API客户端"""

    BASE_URL = "https://qyapi.weixin.qq.com"
    TOKEN_CACHE_KEY = "wechat_access_token"  # nosec B105

    def __init__(self, corp_id: Optional[str] = None, agent_id: Optional[str] = None, secret: Optional[str] = None):
        """
        初始化企业微信客户端

        Args:
            corp_id: 企业ID（从配置读取）
            agent_id: 应用ID（从配置读取）
            secret: 应用Secret（从配置读取）
        """
        self.corp_id = corp_id or settings.WECHAT_CORP_ID
        self.agent_id = agent_id or settings.WECHAT_AGENT_ID
        self.secret = secret or settings.WECHAT_SECRET

        if not all([self.corp_id, self.agent_id, self.secret]):
            raise ValueError("企业微信配置不完整，请设置 WECHAT_CORP_ID, WECHAT_AGENT_ID, WECHAT_SECRET")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取access_token（带缓存）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            access_token字符串
        """
        if requests is None:
            raise RuntimeError("未安装 requests 依赖，无法调用企业微信API")

        # 检查缓存
        if not force_refresh:
            cached_token = WeChatTokenCache.get(self.TOKEN_CACHE_KEY)
            if cached_token:
                return cached_token

        # 从API获取新token
        url = f"{self.BASE_URL}/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.secret
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") != 0:
                raise Exception(f"获取access_token失败: {data.get('errmsg', '未知错误')}")

            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 7200)

            # 缓存token
            WeChatTokenCache.set(self.TOKEN_CACHE_KEY, access_token, expires_in)

            return access_token

        except requests.RequestException as e:
            raise Exception(f"请求企业微信API失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取access_token失败: {str(e)}")

    def send_message(
        self,
        user_ids: list,
        message: Dict[str, Any],
        retry_times: int = 3
    ) -> bool:
        """
        发送企业微信消息

        Args:
            user_ids: 接收消息的用户ID列表（企业微信userid）
            message: 消息内容（dict格式）
            retry_times: 重试次数

        Returns:
            是否发送成功
        """
        if requests is None:
            raise RuntimeError("未安装 requests 依赖，无法调用企业微信API")

        if not user_ids:
            return False

        access_token = self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/message/send"
        params = {"access_token": access_token}

        # 构建消息体
        payload = {
            "touser": "|".join(user_ids),
            "msgtype": message.get("msgtype", "text"),
            "agentid": self.agent_id,
        }

        # 根据消息类型设置内容
        msgtype = message.get("msgtype")
        if msgtype == "template_card":
            payload["template_card"] = message.get("template_card")
        elif msgtype == "text":
            payload["text"] = message.get("text", {})
        elif msgtype == "markdown":
            payload["markdown"] = message.get("markdown", {})
        else:
            payload.update(message)

        # 发送消息（带重试）
        for attempt in range(retry_times):
            try:
                response = requests.post(url, params=params, json=payload, timeout=10)
                response.raise_for_status()
                data = response.json()

                errcode = data.get("errcode", 0)
                if errcode == 0:
                    return True
                elif errcode == 40014:  # access_token无效，强制刷新
                    if attempt < retry_times - 1:
                        WeChatTokenCache.clear(self.TOKEN_CACHE_KEY)
                        access_token = self.get_access_token(force_refresh=True)
                        params["access_token"] = access_token
                        continue
                    else:
                        raise Exception(f"access_token刷新后仍无效: {data.get('errmsg', '未知错误')}")
                else:
                    raise Exception(f"发送消息失败: {data.get('errmsg', '未知错误')} (errcode: {errcode})")

            except requests.RequestException as e:
                if attempt < retry_times - 1:
                    time.sleep(1)  # 等待1秒后重试
                    continue
                else:
                    raise Exception(f"请求企业微信API失败: {str(e)}")

        return False

    def send_text_message(self, user_ids: list, content: str) -> bool:
        """
        发送文本消息（便捷方法）

        Args:
            user_ids: 接收消息的用户ID列表
            content: 消息内容

        Returns:
            是否发送成功
        """
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        return self.send_message(user_ids, message)

    def send_template_card(
        self,
        user_ids: list,
        template_card: Dict[str, Any]
    ) -> bool:
        """
        发送卡片消息（便捷方法）

        Args:
            user_ids: 接收消息的用户ID列表
            template_card: 卡片消息内容

        Returns:
            是否发送成功
        """
        message = {
            "msgtype": "template_card",
            "template_card": template_card
        }
        return self.send_message(user_ids, message)
