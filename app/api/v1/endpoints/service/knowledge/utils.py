# -*- coding: utf-8 -*-
"""
知识库管理 - 工具函数和常量
"""
from pathlib import Path

from app.core.config import settings

# 知识库上传目录
KNOWLEDGE_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "knowledge_base"
KNOWLEDGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型（文档和视频）
ALLOWED_EXTENSIONS = {
    # 文档
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.md', '.csv', '.rtf', '.odt', '.ods', '.odp',
    # 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    # 视频
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
    # 压缩包
    '.zip', '.rar', '.7z', '.tar', '.gz',
}

# 最大文件大小：200MB
MAX_FILE_SIZE = 200 * 1024 * 1024

# 用户上传配额：5GB
USER_UPLOAD_QUOTA = 5 * 1024 * 1024 * 1024


def get_user_total_upload_size(db, user_id: int) -> int:
    """获取用户已上传文件的总大小"""
    from sqlalchemy import func
    from app.models.service import KnowledgeBase

    result = db.query(func.sum(KnowledgeBase.file_size)).filter(
        KnowledgeBase.author_id == user_id,
        KnowledgeBase.file_size.isnot(None)
    ).scalar()
    return result or 0
