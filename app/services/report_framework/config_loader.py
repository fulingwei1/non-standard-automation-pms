# -*- coding: utf-8 -*-
"""
配置加载器

负责加载和验证 YAML 配置文件
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import ValidationError

from app.services.report_framework.models import ReportConfig, ReportMeta


class ConfigError(Exception):
    """配置错误"""
    pass


class ConfigLoader:
    """
    配置加载器

    加载和验证 YAML 报告配置
    """

    def __init__(self, config_dir: str = "app/report_configs"):
        """
        初始化配置加载器

        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, ReportConfig] = {}
        self._meta_cache: Dict[str, ReportMeta] = {}

    def get(self, report_code: str) -> ReportConfig:
        """
        获取报告配置

        Args:
            report_code: 报告代码，如 "PROJECT_WEEKLY"

        Returns:
            ReportConfig: 报告配置对象

        Raises:
            ConfigError: 配置不存在或无效
        """
        # 检查缓存
        if report_code in self._cache:
            return self._cache[report_code]

        # 查找配置文件
        config_path = self._find_config_file(report_code)
        if not config_path:
            raise ConfigError(f"Report config not found: {report_code}")

        # 加载并验证
        config = self._load_and_validate(config_path)

        # 验证 code 匹配
        if config.meta.code != report_code:
            raise ConfigError(
                f"Config code mismatch: expected {report_code}, got {config.meta.code}"
            )

        # 缓存
        self._cache[report_code] = config
        self._meta_cache[report_code] = config.meta

        return config

    def list_available(self) -> List[ReportMeta]:
        """
        列出所有可用的报告

        Returns:
            List[ReportMeta]: 报告元数据列表
        """
        reports = []

        # 遍历配置目录
        for yaml_file in self.config_dir.rglob("*.yaml"):
            # 跳过 schema 文件
            if yaml_file.name.startswith("_"):
                continue

            try:
                config = self._load_and_validate(yaml_file)
                reports.append(config.meta)
                # 同时缓存
                self._cache[config.meta.code] = config
                self._meta_cache[config.meta.code] = config.meta
            except (ConfigError, ValidationError) as e:
                # 记录错误但继续处理其他文件
                print(f"Warning: Failed to load {yaml_file}: {e}")

        return reports

    def reload(self, report_code: Optional[str] = None) -> None:
        """
        重新加载配置

        Args:
            report_code: 指定报告代码，None 表示全部重载
        """
        if report_code:
            # 清除指定缓存
            self._cache.pop(report_code, None)
            self._meta_cache.pop(report_code, None)
        else:
            # 清除全部缓存
            self._cache.clear()
            self._meta_cache.clear()

    def _find_config_file(self, report_code: str) -> Optional[Path]:
        """
        查找配置文件

        支持两种查找方式：
        1. 直接匹配文件名（如 project_weekly.yaml）
        2. 遍历所有文件检查 meta.code

        Args:
            report_code: 报告代码

        Returns:
            Path: 配置文件路径，未找到返回 None
        """
        # 转换代码为文件名格式
        file_name = report_code.lower().replace("_", "/") + ".yaml"
        direct_path = self.config_dir / file_name

        # 尝试直接路径
        if direct_path.exists():
            return direct_path

        # 尝试下划线格式
        file_name_underscore = report_code.lower() + ".yaml"
        for yaml_file in self.config_dir.rglob(file_name_underscore):
            return yaml_file

        # 遍历所有文件查找
        for yaml_file in self.config_dir.rglob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and data.get("meta", {}).get("code") == report_code:
                    return yaml_file
            except Exception:
                continue

        return None

    def _load_and_validate(self, config_path: Path) -> ReportConfig:
        """
        加载并验证配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            ReportConfig: 验证后的配置对象

        Raises:
            ConfigError: 配置无效
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}")

        if not data:
            raise ConfigError(f"Empty config file: {config_path}")

        try:
            return ReportConfig(**data)
        except ValidationError as e:
            raise ConfigError(f"Invalid config in {config_path}: {e}")

    def validate_config(self, config_dict: dict) -> ReportConfig:
        """
        验证配置字典

        Args:
            config_dict: 配置字典

        Returns:
            ReportConfig: 验证后的配置对象

        Raises:
            ConfigError: 配置无效
        """
        try:
            return ReportConfig(**config_dict)
        except ValidationError as e:
            raise ConfigError(f"Invalid config: {e}")
