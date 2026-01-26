# -*- coding: utf-8 -*-
"""
报告配置数据模型

使用 Pydantic 定义配置 Schema
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """数据源类型"""
    QUERY = "query"
    SERVICE = "service"
    AGGREGATE = "aggregate"


class SectionType(str, Enum):
    """Section 类型"""
    METRICS = "metrics"
    TABLE = "table"
    CHART = "chart"


class ChartType(str, Enum):
    """图表类型"""
    PIE = "pie"
    BAR = "bar"
    LINE = "line"
    AREA = "area"


class ParameterType(str, Enum):
    """参数类型"""
    INTEGER = "integer"
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"
    FLOAT = "float"
    LIST = "list"


# === 元数据 ===
class ReportMeta(BaseModel):
    """报告元数据"""
    name: str
    code: str
    description: Optional[str] = None
    version: str = "1.0"


# === 权限配置 ===
class PermissionConfig(BaseModel):
    """权限配置"""
    roles: List[str] = Field(default_factory=list)
    data_scope: str = "project"  # project | department | company | custom


# === 参数定义 ===
class ParameterConfig(BaseModel):
    """参数配置"""
    name: str
    type: ParameterType
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None


# === 缓存配置 ===
class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = False
    ttl: int = 3600  # 秒
    key_pattern: Optional[str] = None


# === 定时任务配置 ===
class ScheduleConfig(BaseModel):
    """定时任务配置"""
    enabled: bool = False
    cron: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


# === 数据源配置 ===
class DataSourceConfig(BaseModel):
    """数据源配置"""
    type: DataSourceType
    sql: Optional[str] = None  # for query type
    method: Optional[str] = None  # for service type
    args: Dict[str, Any] = Field(default_factory=dict)
    function: Optional[str] = None  # for aggregate type


# === Section 配置 ===
class MetricItem(BaseModel):
    """指标项"""
    label: str
    value: str  # Jinja2 表达式


class TableColumn(BaseModel):
    """表格列"""
    field: str
    label: str
    format: Optional[str] = None  # 格式化器名称
    width: Optional[int] = None


class SectionConfig(BaseModel):
    """Section 配置"""
    id: str
    title: Optional[str] = None
    type: SectionType
    # metrics 类型专用
    items: Optional[List[MetricItem]] = None
    # table 类型专用
    source: Optional[str] = None  # 数据源名称
    columns: Optional[List[TableColumn]] = None
    # chart 类型专用
    chart_type: Optional[ChartType] = None
    label_field: Optional[str] = None
    value_field: Optional[str] = None


# === 导出配置 ===
class JsonExportConfig(BaseModel):
    """JSON 导出配置"""
    enabled: bool = True


class PdfExportConfig(BaseModel):
    """PDF 导出配置"""
    enabled: bool = False
    template: Optional[str] = None
    orientation: str = "portrait"  # portrait | landscape


class ExcelSheetConfig(BaseModel):
    """Excel Sheet 配置"""
    name: str
    section: str  # section id


class ExcelExportConfig(BaseModel):
    """Excel 导出配置"""
    enabled: bool = False
    sheets: List[ExcelSheetConfig] = Field(default_factory=list)


class WordExportConfig(BaseModel):
    """Word 导出配置"""
    enabled: bool = False
    template: Optional[str] = None


class ExportConfig(BaseModel):
    """导出配置"""
    json_export: JsonExportConfig = Field(default_factory=JsonExportConfig, alias="json")
    pdf: PdfExportConfig = Field(default_factory=PdfExportConfig)
    excel: ExcelExportConfig = Field(default_factory=ExcelExportConfig)
    word: WordExportConfig = Field(default_factory=WordExportConfig)

    class Config:
        populate_by_name = True


# === 完整报告配置 ===
class ReportConfig(BaseModel):
    """完整报告配置"""
    meta: ReportMeta
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)
    parameters: List[ParameterConfig] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    data_sources: Dict[str, DataSourceConfig] = Field(default_factory=dict)
    sections: List[SectionConfig] = Field(default_factory=list)
    exports: ExportConfig = Field(default_factory=ExportConfig)

    class Config:
        """Pydantic 配置"""
        use_enum_values = True
