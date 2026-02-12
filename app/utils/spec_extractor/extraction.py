# -*- coding: utf-8 -*-
"""
技术规格要求提取器 - 主要提取功能
"""
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import ProjectDocument
from app.models.technical_spec import TechnicalSpecRequirement

from .formats import extract_from_excel, extract_from_pdf, extract_from_word

if TYPE_CHECKING:
    from app.utils.spec_extractor import SpecExtractor

logger = logging.getLogger(__name__)


def extract_from_document(
    service: "SpecExtractor",
    db: Session,
    document_id: int,
    project_id: int,
    extracted_by: int,
    auto_extract: bool = False
) -> List[TechnicalSpecRequirement]:
    """
    从文档中提取规格要求

    Args:
        service: SpecExtractor实例
        db: 数据库会话
        document_id: 文档ID
        project_id: 项目ID
        extracted_by: 提取人ID
        auto_extract: 是否自动提取（目前仅支持手动录入）

    Returns:
        提取的规格要求列表
    """
    # 目前实现基础版本，支持手动录入
    # 未来可以扩展支持Excel、Word、PDF等格式的自动解析

    # 验证文档存在
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise ValueError(f"文档 {document_id} 不存在或不属于项目 {project_id}")

    # 如果启用自动提取，尝试解析文档
    if auto_extract:
        try:
            requirements = auto_extract_from_file(
                service=service,
                db=db,
                document=document,
                project_id=project_id,
                extracted_by=extracted_by
            )
            if requirements:
                return requirements
        except Exception as e:
            # 自动提取失败，记录错误但不抛出异常，允许手动录入
            logger.warning(f"自动提取失败: {e}")

    # 返回空列表，表示需要手动录入
    return []


def auto_extract_from_file(
    service: "SpecExtractor",
    db: Session,
    document: ProjectDocument,
    project_id: int,
    extracted_by: int
) -> List[TechnicalSpecRequirement]:
    """
    从文件中自动提取规格要求

    Args:
        service: SpecExtractor实例
        db: 数据库会话
        document: 文档对象
        project_id: 项目ID
        extracted_by: 提取人ID

    Returns:
        提取的规格要求列表
    """
    # 获取文件路径
    file_path = Path(settings.UPLOAD_DIR) / document.file_path if not Path(document.file_path).is_absolute() else Path(document.file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    requirements = []
    file_type = document.file_type or file_path.suffix.lower()

    # 根据文件类型选择解析方法
    if file_type in ['.xlsx', '.xls']:
        requirements = extract_from_excel(service, db, file_path, project_id, document.id, extracted_by)
    elif file_type in ['.docx', '.doc']:
        requirements = extract_from_word(service, db, file_path, project_id, document.id, extracted_by)
    elif file_type == '.pdf':
        requirements = extract_from_pdf(service, db, file_path, project_id, document.id, extracted_by)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    return requirements
