# -*- coding: utf-8 -*-
"""
渲染器基类

定义渲染器的抽象接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ReportResult:
    """报告结果"""
    data: Dict[str, Any]
    format: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    content_type: str = "application/json"
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RenderError(Exception):
    """渲染错误"""
    pass


class Renderer(ABC):
    """
    渲染器抽象基类

    所有渲染器必须实现此接口
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """渲染器格式名称"""
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """输出内容类型"""
        pass

    @abstractmethod
    def render(
        self,
        sections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> ReportResult:
        """
        渲染报告

        Args:
            sections: 渲染后的 section 数据
            metadata: 报告元数据

        Returns:
            ReportResult: 渲染结果

        Raises:
            RenderError: 渲染失败
        """
        pass
