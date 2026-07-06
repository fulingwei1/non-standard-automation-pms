# -*- coding: utf-8 -*-
"""
文件上传服务
提供统一的文件上传、验证、存储功能
"""
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings


class FileUploadService:
    """文件上传服务"""

    # 默认允许的文件类型
    DEFAULT_ALLOWED_EXTENSIONS = {
        # 文档
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".md",
        ".csv",
        ".rtf",
        ".odt",
        ".ods",
        ".odp",
        # 图片
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".svg",
        # 视频
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".mkv",
        ".webm",
        ".m4v",
        # 压缩包
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
    }

    # 默认最大文件大小: 200MB
    DEFAULT_MAX_FILE_SIZE = 200 * 1024 * 1024

    # 默认用户上传配额: 5GB
    DEFAULT_USER_QUOTA = 5 * 1024 * 1024 * 1024

    def __init__(
        self,
        upload_dir: Optional[Path] = None,
        allowed_extensions: Optional[set] = None,
        max_file_size: Optional[int] = None,
        user_quota: Optional[int] = None,
        db: Optional[Any] = None,
    ):
        """
        初始化文件上传服务

        Args:
            upload_dir: 上传目录路径
            allowed_extensions: 允许的文件扩展名集合
            max_file_size: 最大文件大小（字节）
            user_quota: 用户上传配额（字节）
        """
        if upload_dir is not None and not isinstance(upload_dir, (str, Path)):
            db = upload_dir
            upload_dir = None

        self.db = db
        self.upload_dir = Path(upload_dir) if upload_dir is not None else Path(settings.UPLOAD_DIR)
        self.allowed_extensions = allowed_extensions or self.DEFAULT_ALLOWED_EXTENSIONS
        self.max_file_size = max_file_size or self.DEFAULT_MAX_FILE_SIZE
        self.user_quota = user_quota or self.DEFAULT_USER_QUOTA

        # 确保上传目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        验证文件扩展名

        Args:
            filename: 文件名

        Returns:
            (是否有效, 错误消息)
        """
        if not filename:
            return False, "文件名不能为空"

        file_ext = Path(filename).suffix.lower()

        if not file_ext:
            return False, "文件缺少扩展名"

        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}"

        return True, None

    def validate_file_size(self, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        验证文件大小

        Args:
            file_size: 文件大小（字节）

        Returns:
            (是否有效, 错误消息)
        """
        if file_size <= 0:
            return False, "文件大小无效"

        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            current_mb = file_size / (1024 * 1024)
            return (
                False,
                f"文件大小超过限制。最大允许: {max_mb:.0f}MB，当前文件: {current_mb:.2f}MB",
            )

        return True, None

    def validate_file_content(
        self,
        file_content: bytes,
        filename: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        验证文件内容与扩展名是否匹配，防止可执行文件或脚本伪装成允许类型。

        Args:
            file_content: 文件内容
            filename: 原始文件名

        Returns:
            (是否有效, 错误消息)
        """
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")

        if not file_content:
            return False, "文件内容不能为空"

        file_ext = Path(filename).suffix.lower()
        header = file_content[:16]
        lower_sample = file_content[:1024].lower().lstrip()

        blocked_signatures = (
            (b"MZ", "Windows 可执行文件"),
            (b"\x7fELF", "Linux 可执行文件"),
            (b"#!", "脚本文件"),
        )
        for signature, label in blocked_signatures:
            if header.startswith(signature):
                return False, f"文件内容与扩展名不匹配：禁止上传{label}"

        expected_signatures = {
            ".pdf": (b"%PDF-",),
            ".png": (b"\x89PNG\r\n\x1a\n",),
            ".jpg": (b"\xff\xd8\xff",),
            ".jpeg": (b"\xff\xd8\xff",),
            ".gif": (b"GIF87a", b"GIF89a"),
            ".bmp": (b"BM",),
            ".zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
            ".docx": (b"PK\x03\x04",),
            ".xlsx": (b"PK\x03\x04",),
            ".pptx": (b"PK\x03\x04",),
            ".doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
            ".xls": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
            ".ppt": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
            ".rar": (b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00"),
            ".7z": (b"7z\xbc\xaf\x27\x1c",),
            ".gz": (b"\x1f\x8b",),
        }

        signatures = expected_signatures.get(file_ext)
        if signatures and not any(header.startswith(signature) for signature in signatures):
            return False, "文件内容与扩展名不匹配"

        text_like_extensions = {".txt", ".md", ".csv", ".rtf", ".svg"}
        if file_ext in text_like_extensions:
            if lower_sample.startswith((b"<!doctype html", b"<html")) or b"<script" in lower_sample:
                return False, "文本文件内容包含 HTML/脚本，已拒绝上传"

        if file_ext == ".webp" and not (
            header.startswith(b"RIFF") and file_content[8:12] == b"WEBP"
        ):
            return False, "文件内容与扩展名不匹配"

        return True, None

    def check_user_quota(
        self, user_id: int, file_size: int = 0, db=None, model_class=None
    ) -> Tuple[bool, Optional[str]]:
        """
        检查用户上传配额

        Args:
            user_id: 用户ID
            file_size: 文件大小（字节）
            db: 数据库会话
            model_class: 用于查询的模型类（可选）

        Returns:
            (是否通过, 错误消息)
        """
        db = db if db is not None else self.db
        current_used = self.get_user_total_upload_size(user_id, db, model_class)

        if current_used + file_size > self.user_quota:
            quota_gb = self.user_quota / (1024 * 1024 * 1024)
            used_gb = current_used / (1024 * 1024 * 1024)
            remaining = self.user_quota - current_used
            remaining_gb = remaining / (1024 * 1024 * 1024)
            file_mb = file_size / (1024 * 1024)

            return False, (
                f"上传配额不足。您的配额: {quota_gb:.0f}GB，"
                f"已使用: {used_gb:.2f}GB，"
                f"剩余: {remaining_gb:.2f}GB，"
                f"当前文件: {file_mb:.2f}MB"
            )

        return True, None

    def get_user_total_upload_size(self, user_id: int, db, model_class=None) -> int:
        """
        获取用户已上传文件的总大小

        Args:
            user_id: 用户ID
            db: 数据库会话
            model_class: 用于查询的模型类（可选）

        Returns:
            总大小（字节）
        """
        if model_class is None:
            return 0

        from sqlalchemy import func

        result = (
            db.query(func.sum(model_class.file_size))
            .filter(model_class.author_id == user_id, model_class.file_size.isnot(None))
            .scalar()
        )

        return result or 0

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        生成唯一文件名

        Args:
            original_filename: 原始文件名

        Returns:
            唯一文件名
        """
        file_ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]

        return f"{timestamp}_{unique_id}{file_ext}"

    def get_upload_path(
        self, filename: str, subdir: Optional[str] = None, use_date_subdir: bool = True
    ) -> Tuple[Path, str]:
        """
        获取文件上传路径

        Args:
            filename: 文件名
            subdir: 子目录（如 "knowledge_base"）
            use_date_subdir: 是否使用日期子目录

        Returns:
            (完整文件路径, 相对路径)
        """
        path_parts = []

        # 添加子目录
        if subdir:
            path_parts.append(subdir)

        # 添加日期子目录
        if use_date_subdir:
            date_dir = datetime.now().strftime("%Y%m")
            path_parts.append(date_dir)

        # 创建目录
        upload_dir = self.upload_dir
        for part in path_parts:
            upload_dir = upload_dir / part
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 完整路径
        full_path = upload_dir / filename

        # 相对路径（用于存储到数据库）
        relative_path = "/".join(path_parts + [filename]) if path_parts else filename

        return full_path, relative_path

    def save_file(
        self,
        file_content: bytes,
        filename: str,
        subdir: Optional[str] = None,
        use_date_subdir: bool = True,
    ) -> Tuple[Path, str]:
        """
        保存文件到磁盘

        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            subdir: 子目录
            use_date_subdir: 是否使用日期子目录

        Returns:
            (完整文件路径, 相对路径)
        """
        # 生成唯一文件名
        unique_filename = self.generate_unique_filename(filename)

        # 获取上传路径
        full_path, relative_path = self.get_upload_path(unique_filename, subdir, use_date_subdir)

        # 保存文件
        with open(full_path, "wb") as f:
            f.write(file_content)

        return full_path, relative_path

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径（相对或绝对）

        Returns:
            是否成功删除
        """
        try:
            # 处理路径
            path = Path(file_path)
            if not path.is_absolute():
                path = self.upload_dir / file_path

            # 删除文件
            if path.exists() and path.is_file():
                path.unlink()
                return True

            return False
        except Exception:
            return False

    def calculate_file_hash(self, file_content: bytes, algorithm: str = "md5") -> str:
        """
        计算文件哈希值

        Args:
            file_content: 文件内容
            algorithm: 哈希算法（md5, sha1, sha256）

        Returns:
            哈希值（十六进制字符串）
        """
        # 容错：若传入字符串则按 UTF-8 编码，避免 hashlib 抛 "Strings must be encoded"
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")
        if algorithm == "md5":
            return hashlib.md5(file_content).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(file_content).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(file_content).hexdigest()
        else:
            raise ValueError(f"不支持的哈希算法: {algorithm}")

    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.upload_dir / file_path

            if not path.exists():
                return None

            stat = path.stat()

            return {
                "filename": path.name,
                "path": str(path),
                "size": stat.st_size,
                "size_human": self.format_file_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
            }
        except Exception:
            return None

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_bytes: 文件大小（字节）

        Returns:
            格式化后的字符串（如 "1.23 MB"）
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def list_files(
        self, subdir: Optional[str] = None, extensions: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        列出文件

        Args:
            subdir: 子目录
            extensions: 文件扩展名过滤列表

        Returns:
            文件信息列表
        """
        try:
            search_dir = self.upload_dir
            if subdir:
                search_dir = search_dir / subdir

            if not search_dir.exists():
                return []

            files = []
            for file_path in search_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # 扩展名过滤
                if extensions and file_path.suffix.lower() not in extensions:
                    continue

                file_info = self.get_file_info(str(file_path))
                if file_info:
                    files.append(file_info)

            # 按修改时间倒序排序
            files.sort(key=lambda x: x["modified_at"], reverse=True)

            return files
        except Exception:
            return []
