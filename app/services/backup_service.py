"""
备份管理服务
提供备份、恢复、列表、验证等功能的Python API
"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BackupService:
    """备份管理服务"""
    
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/var/backups/pms"))
    SCRIPT_DIR = Path(__file__).parent.parent.parent / "scripts"
    
    @classmethod
    def create_backup(cls, backup_type: str = "full") -> Dict:
        """
        创建备份
        
        Args:
            backup_type: 备份类型
                - full: 完整备份（数据库+文件）
                - database: 仅数据库
                - files: 仅文件
        
        Returns:
            备份结果字典
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 根据类型选择脚本
            script_map = {
                "full": "backup_full.sh",
                "database": "backup_database.sh",
                "files": "backup_files.sh"
            }
            
            script_name = script_map.get(backup_type, "backup_full.sh")
            script_path = cls.SCRIPT_DIR / script_name
            
            if not script_path.exists():
                return {
                    "status": "error",
                    "message": f"备份脚本不存在: {script_path}"
                }
            
            # 执行备份脚本
            logger.info(f"执行备份: {backup_type}")
            result = subprocess.run(
                ["bash", str(script_path)],
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            if result.returncode == 0:
                logger.info(f"备份成功: {backup_type}")
                return {
                    "status": "success",
                    "timestamp": timestamp,
                    "backup_type": backup_type,
                    "message": "备份成功",
                    "output": result.stdout
                }
            else:
                logger.error(f"备份失败: {result.stderr}")
                return {
                    "status": "failed",
                    "backup_type": backup_type,
                    "error": result.stderr,
                    "message": "备份失败"
                }
                
        except subprocess.TimeoutExpired:
            logger.error("备份超时")
            return {
                "status": "failed",
                "message": "备份超时（超过1小时）"
            }
        except Exception as e:
            logger.error(f"备份异常: {str(e)}")
            return {
                "status": "error",
                "message": f"备份异常: {str(e)}"
            }
    
    @classmethod
    def list_backups(cls, backup_type: str = "database") -> List[Dict]:
        """
        列出所有备份文件
        
        Args:
            backup_type: 备份类型 (database/uploads/configs/logs/full)
        
        Returns:
            备份文件列表
        """
        backups = []
        
        # 根据类型设置文件模式
        pattern_map = {
            "database": "pms_*.sql.gz",
            "uploads": "uploads_*.tar.gz",
            "configs": "configs_*.tar.gz",
            "logs": "logs_*.tar.gz",
            "full": "pms_full_*.tar.gz"
        }
        
        pattern = pattern_map.get(backup_type, "pms_*.sql.gz")
        
        try:
            for file in cls.BACKUP_DIR.glob(pattern):
                if not file.is_file():
                    continue
                
                stat = file.stat()
                md5_file = Path(str(file) + ".md5")
                
                # 读取MD5
                md5_hash = None
                if md5_file.exists():
                    try:
                        md5_hash = md5_file.read_text().strip()
                    except Exception:
                        pass
                
                backups.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": stat.st_size,
                    "size_human": cls._format_size(stat.st_size),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "has_checksum": md5_file.exists(),
                    "md5": md5_hash,
                    "type": backup_type
                })
            
            # 按时间倒序排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"列出备份失败: {str(e)}")
        
        return backups
    
    @classmethod
    def get_latest_backup(cls, backup_type: str = "database") -> Optional[Dict]:
        """获取最新的备份"""
        backups = cls.list_backups(backup_type)
        return backups[0] if backups else None
    
    @classmethod
    def verify_backup(cls, backup_file: str) -> Dict:
        """
        验证备份文件完整性
        
        Args:
            backup_file: 备份文件路径或文件名
        
        Returns:
            验证结果
        """
        try:
            # 处理文件路径
            file_path = Path(backup_file)
            if not file_path.is_absolute():
                file_path = cls.BACKUP_DIR / backup_file
            
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"备份文件不存在: {file_path}"
                }
            
            # 执行验证脚本
            script_path = cls.SCRIPT_DIR / "verify_backup.sh"
            
            result = subprocess.run(
                ["bash", str(script_path), str(file_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "备份验证通过",
                    "output": result.stdout
                }
            else:
                return {
                    "status": "failed",
                    "message": "备份验证失败",
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"验证失败: {str(e)}")
            return {
                "status": "error",
                "message": f"验证异常: {str(e)}"
            }
    
    @classmethod
    def delete_old_backups(cls, retention_days: int = 7, backup_type: str = "database") -> Dict:
        """
        删除过期备份
        
        Args:
            retention_days: 保留天数
            backup_type: 备份类型
        
        Returns:
            删除结果
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            deleted_size = 0
            
            backups = cls.list_backups(backup_type)
            
            for backup in backups:
                created_at = datetime.fromisoformat(backup["created_at"])
                
                if created_at < cutoff_date:
                    file_path = Path(backup["path"])
                    
                    # 删除备份文件
                    if file_path.exists():
                        deleted_size += backup["size"]
                        file_path.unlink()
                        deleted_count += 1
                    
                    # 删除MD5文件
                    md5_file = Path(str(file_path) + ".md5")
                    if md5_file.exists():
                        md5_file.unlink()
            
            logger.info(f"清理完成: 删除{deleted_count}个文件, 释放{cls._format_size(deleted_size)}")
            
            return {
                "status": "success",
                "deleted_count": deleted_count,
                "freed_space": deleted_size,
                "freed_space_human": cls._format_size(deleted_size)
            }
            
        except Exception as e:
            logger.error(f"清理失败: {str(e)}")
            return {
                "status": "error",
                "message": f"清理异常: {str(e)}"
            }
    
    @classmethod
    def get_backup_stats(cls) -> Dict:
        """获取备份统计信息"""
        try:
            stats = {
                "database": {"count": 0, "total_size": 0, "latest": None},
                "uploads": {"count": 0, "total_size": 0, "latest": None},
                "configs": {"count": 0, "total_size": 0, "latest": None},
                "full": {"count": 0, "total_size": 0, "latest": None}
            }
            
            for backup_type in stats.keys():
                backups = cls.list_backups(backup_type)
                
                stats[backup_type]["count"] = len(backups)
                stats[backup_type]["total_size"] = sum(b["size"] for b in backups)
                stats[backup_type]["total_size_human"] = cls._format_size(
                    stats[backup_type]["total_size"]
                )
                
                if backups:
                    stats[backup_type]["latest"] = backups[0]
            
            # 磁盘空间
            if cls.BACKUP_DIR.exists():
                disk_usage = os.statvfs(cls.BACKUP_DIR)
                stats["disk"] = {
                    "total": disk_usage.f_frsize * disk_usage.f_blocks,
                    "used": disk_usage.f_frsize * (disk_usage.f_blocks - disk_usage.f_bfree),
                    "free": disk_usage.f_frsize * disk_usage.f_bavail,
                    "percent": round(
                        (1 - disk_usage.f_bavail / disk_usage.f_blocks) * 100, 2
                    )
                }
                stats["disk"]["total_human"] = cls._format_size(stats["disk"]["total"])
                stats["disk"]["used_human"] = cls._format_size(stats["disk"]["used"])
                stats["disk"]["free_human"] = cls._format_size(stats["disk"]["free"])
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计失败: {str(e)}")
            return {}
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
