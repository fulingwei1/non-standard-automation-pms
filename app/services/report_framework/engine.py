# -*- coding: utf-8 -*-
"""
报告引擎

核心编排器，协调配置加载、数据获取、缓存和渲染
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.report_framework.cache_manager import CacheManager
from app.services.report_framework.config_loader import ConfigLoader, ConfigError
from app.services.report_framework.data_resolver import DataResolver
from app.services.report_framework.expressions import ExpressionParser
from app.services.report_framework.models import (
    ParameterType,
    ReportConfig,
    ReportMeta,
    SectionConfig,
    SectionType,
)
from app.services.report_framework.renderers import JsonRenderer, Renderer, ReportResult


class PermissionError(Exception):
    """权限错误"""
    pass


class ParameterError(Exception):
    """参数错误"""
    pass


class ReportEngine:
    """
    报告引擎

    核心编排器，负责：
    1. 加载配置
    2. 权限检查
    3. 参数验证
    4. 数据获取
    5. Section 渲染
    6. 缓存管理
    """

    def __init__(
        self,
        db: Session,
        config_dir: str = "app/report_configs",
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        初始化报告引擎

        Args:
            db: 数据库会话
            config_dir: 配置文件目录
            cache_manager: 缓存管理器（可选）
        """
        self.db = db
        self.config_loader = ConfigLoader(config_dir)
        self.data_resolver = DataResolver(db)
        self.cache = cache_manager or CacheManager()
        self.expression_parser = ExpressionParser()

        # 注册渲染器
        self.renderers: Dict[str, Renderer] = {
            "json": JsonRenderer(),
        }

    def generate(
        self,
        report_code: str,
        params: Dict[str, Any],
        format: str = "json",
        user: Optional[User] = None,
        skip_cache: bool = False,
    ) -> ReportResult:
        """
        生成报告

        Args:
            report_code: 报告代码
            params: 参数字典
            format: 导出格式
            user: 当前用户（用于权限检查）
            skip_cache: 是否跳过缓存

        Returns:
            ReportResult: 报告结果

        Raises:
            ConfigError: 配置错误
            PermissionError: 权限错误
            ParameterError: 参数错误
        """
        # 1. 加载配置
        config = self.config_loader.get(report_code)

        # 2. 权限检查
        if user:
            self._check_permission(config, user)

        # 3. 参数验证
        validated_params = self._validate_params(config, params)

        # 4. 检查缓存
        if not skip_cache:
            cached = self.cache.get(config, validated_params)
            if cached:
                return cached

        # 5. 获取数据
        context = self.data_resolver.resolve_all(
            config.data_sources,
            validated_params,
        )

        # 添加参数到上下文供 section 渲染使用
        context["params"] = validated_params

        # 6. 渲染 sections
        rendered_sections = self._render_sections(config.sections, context)

        # 7. 导出
        renderer = self.renderers.get(format)
        if not renderer:
            raise ConfigError(f"Unsupported format: {format}")

        metadata = {
            "code": config.meta.code,
            "name": config.meta.name,
            "parameters": validated_params,
        }

        result = renderer.render(rendered_sections, metadata)

        # 8. 缓存结果
        if not skip_cache:
            self.cache.set(config, validated_params, result)

        return result

    def list_available(self, user: Optional[User] = None) -> List[ReportMeta]:
        """
        列出用户可用的报告

        Args:
            user: 当前用户（用于过滤）

        Returns:
            可用报告的元数据列表
        """
        all_reports = self.config_loader.list_available()

        if not user:
            return all_reports

        # 按权限过滤
        available = []
        for meta in all_reports:
            try:
                config = self.config_loader.get(meta.code)
                self._check_permission(config, user)
                available.append(meta)
            except PermissionError:
                continue

        return available

    def get_schema(self, report_code: str) -> Dict[str, Any]:
        """
        获取报告参数 Schema

        Args:
            report_code: 报告代码

        Returns:
            参数 Schema 字典（供前端动态生成表单）
        """
        config = self.config_loader.get(report_code)

        return {
            "report_code": config.meta.code,
            "report_name": config.meta.name,
            "description": config.meta.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.value if hasattr(p.type, "value") else p.type,
                    "required": p.required,
                    "default": p.default,
                    "description": p.description,
                }
                for p in config.parameters
            ],
            "exports": {
                "json": config.exports.json_export.enabled,
                "pdf": config.exports.pdf.enabled,
                "excel": config.exports.excel.enabled,
                "word": config.exports.word.enabled,
            },
        }

    def register_renderer(self, format_name: str, renderer: Renderer) -> None:
        """
        注册渲染器

        Args:
            format_name: 格式名称
            renderer: 渲染器实例
        """
        self.renderers[format_name] = renderer

    def _check_permission(self, config: ReportConfig, user: User) -> None:
        """
        检查用户权限

        Args:
            config: 报告配置
            user: 当前用户

        Raises:
            PermissionError: 无权限
        """
        # 超级管理员有所有权限
        if hasattr(user, "is_superuser") and user.is_superuser:
            return

        # 获取用户角色
        user_roles = set()
        if hasattr(user, "roles"):
            for role in user.roles:
                if hasattr(role, "role_code"):
                    user_roles.add(role.role_code)
                elif hasattr(role, "role") and hasattr(role.role, "role_code"):
                    user_roles.add(role.role.role_code)

        # 检查角色权限
        allowed_roles = set(config.permissions.roles)
        if not allowed_roles:
            # 没有配置角色限制，允许所有人
            return

        if not user_roles.intersection(allowed_roles):
            raise PermissionError(
                f"User does not have permission for report: {config.meta.code}"
            )

    def _validate_params(
        self,
        config: ReportConfig,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        验证参数

        Args:
            config: 报告配置
            params: 输入参数

        Returns:
            验证后的参数

        Raises:
            ParameterError: 参数无效
        """
        validated = {}

        for param_config in config.parameters:
            name = param_config.name
            value = params.get(name)

            # 检查必填
            if param_config.required and value is None:
                raise ParameterError(f"Required parameter missing: {name}")

            # 使用默认值
            if value is None:
                value = param_config.default

            # 类型转换
            if value is not None:
                value = self._convert_param_type(value, param_config.type)

            validated[name] = value

        return validated

    def _convert_param_type(self, value: Any, param_type: ParameterType) -> Any:
        """
        参数类型转换

        Args:
            value: 原始值
            param_type: 目标类型

        Returns:
            转换后的值
        """
        from datetime import date, datetime

        type_value = param_type.value if hasattr(param_type, "value") else param_type

        try:
            if type_value == "integer":
                return int(value)
            elif type_value == "float":
                return float(value)
            elif type_value == "boolean":
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ("true", "1", "yes")
            elif type_value == "date":
                if isinstance(value, date):
                    return value
                return datetime.strptime(str(value), "%Y-%m-%d").date()
            elif type_value == "string":
                return str(value)
            elif type_value == "list":
                if isinstance(value, list):
                    return value
                return [value]
        except (ValueError, TypeError) as e:
            raise ParameterError(f"Invalid parameter value: {e}")

        return value

    def _render_sections(
        self,
        sections: List[SectionConfig],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        渲染所有 sections

        Args:
            sections: section 配置列表
            context: 数据上下文

        Returns:
            渲染后的 section 数据列表
        """
        rendered = []

        for section in sections:
            section_data = self._render_section(section, context)
            rendered.append(section_data)

        return rendered

    def _render_section(
        self,
        section: SectionConfig,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        渲染单个 section

        Args:
            section: section 配置
            context: 数据上下文

        Returns:
            渲染后的 section 数据
        """
        section_type = section.type
        if isinstance(section_type, str):
            section_type = SectionType(section_type)

        base_data = {
            "id": section.id,
            "title": section.title,
            "type": section_type.value if hasattr(section_type, "value") else section_type,
        }

        if section_type == SectionType.METRICS:
            base_data["items"] = self._render_metrics(section, context)
        elif section_type == SectionType.TABLE:
            base_data["data"] = self._render_table(section, context)
            base_data["columns"] = [
                {"field": c.field, "label": c.label, "format": c.format}
                for c in (section.columns or [])
            ]
        elif section_type == SectionType.CHART:
            base_data["chart_type"] = section.chart_type
            base_data["data"] = self._render_chart(section, context)

        return base_data

    def _render_metrics(
        self,
        section: SectionConfig,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """渲染指标项"""
        items = []
        for item in (section.items or []):
            value = self.expression_parser.evaluate(item.value, context)
            items.append({
                "label": item.label,
                "value": value,
            })
        return items

    def _render_table(
        self,
        section: SectionConfig,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """渲染表格数据"""
        if not section.source:
            return []
        return context.get(section.source, [])

    def _render_chart(
        self,
        section: SectionConfig,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """渲染图表数据"""
        if not section.source:
            return []

        data = context.get(section.source, [])
        if isinstance(data, list):
            return data

        # 如果是字典（如 group_by 结果），转换为图表格式
        if isinstance(data, dict):
            return [
                {"label": k, "value": v if isinstance(v, (int, float)) else len(v)}
                for k, v in data.items()
            ]

        return []
