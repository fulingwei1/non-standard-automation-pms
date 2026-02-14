# -*- coding: utf-8 -*-
"""
用户批量导入服务
支持Excel/CSV格式导入，包含数据验证、去重、事务处理
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models.user import User, Role, UserRole
from app.models.organization import Employee, Department

logger = logging.getLogger(__name__)


class UserImportService:
    """用户批量导入服务"""

    # 支持的字段映射
    FIELD_MAPPING = {
        "用户名": "username",
        "密码": "password",
        "真实姓名": "real_name",
        "邮箱": "email",
        "手机号": "phone",
        "工号": "employee_no",
        "部门": "department",
        "职位": "position",
        "角色": "roles",
        "是否启用": "is_active",
        # 英文字段（兼容性）
        "Username": "username",
        "Password": "password",
        "Real Name": "real_name",
        "Email": "email",
        "Phone": "phone",
        "Employee No": "employee_no",
        "Department": "department",
        "Position": "position",
        "Roles": "roles",
        "Is Active": "is_active",
    }

    # 必填字段
    REQUIRED_FIELDS = ["username", "real_name", "email"]

    # 单次导入最大数量
    MAX_IMPORT_LIMIT = 500

    @classmethod
    def validate_file_format(cls, filename: str) -> bool:
        """验证文件格式"""
        return filename.lower().endswith((".xlsx", ".xls", ".csv"))

    @classmethod
    def read_file(cls, file_path: str, file_content: bytes = None) -> pd.DataFrame:
        """
        读取Excel或CSV文件
        
        Args:
            file_path: 文件路径（用于判断格式）
            file_content: 文件内容字节流
            
        Returns:
            DataFrame
        """
        try:
            if file_path.lower().endswith(".csv"):
                if file_content:
                    import io
                    df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8-sig")
                else:
                    df = pd.read_csv(file_path, encoding="utf-8-sig")
            else:
                if file_content:
                    import io
                    df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
                else:
                    df = pd.read_excel(file_path, engine="openpyxl")

            # 去除列名首尾空格
            df.columns = df.columns.str.strip()
            return df

        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise ValueError(f"文件读取失败: {str(e)}")

    @classmethod
    def normalize_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名（中文/英文 -> 内部字段名）"""
        column_mapping = {}
        for col in df.columns:
            if col in cls.FIELD_MAPPING:
                column_mapping[col] = cls.FIELD_MAPPING[col]

        if column_mapping:
            df = df.rename(columns=column_mapping)

        return df

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame) -> List[str]:
        """
        验证DataFrame结构
        
        Returns:
            错误列表，如果为空则验证通过
        """
        errors = []

        # 检查必填列
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in df.columns]
        if missing_fields:
            errors.append(f"缺少必填列: {', '.join(missing_fields)}")

        # 检查数据量
        if len(df) == 0:
            errors.append("文件中没有数据")
        elif len(df) > cls.MAX_IMPORT_LIMIT:
            errors.append(f"单次导入不能超过 {cls.MAX_IMPORT_LIMIT} 条数据，当前: {len(df)} 条")

        return errors

    @classmethod
    def validate_row(
        cls,
        row: pd.Series,
        row_index: int,
        db: Session,
        existing_usernames: set,
        existing_emails: set,
    ) -> Optional[str]:
        """
        验证单行数据
        
        Returns:
            错误信息，如果为None则验证通过
        """
        # 必填字段检查
        for field in cls.REQUIRED_FIELDS:
            value = row.get(field)
            if pd.isna(value) or str(value).strip() == "":
                return f"第{row_index}行: {field} 不能为空"

        # 用户名格式验证（长度、字符）
        username = str(row.get("username", "")).strip()
        if len(username) < 3 or len(username) > 50:
            return f"第{row_index}行: 用户名长度必须在3-50个字符之间"

        # 用户名重复检查（文件内 + 数据库）
        if username in existing_usernames:
            return f"第{row_index}行: 用户名 '{username}' 重复"
        existing_usernames.add(username)

        # 检查数据库中是否已存在
        if db.query(User).filter(User.username == username).first():
            return f"第{row_index}行: 用户名 '{username}' 已存在于系统中"

        # 邮箱格式验证
        email = str(row.get("email", "")).strip()
        if "@" not in email or "." not in email:
            return f"第{row_index}行: 邮箱格式不正确"

        # 邮箱重复检查（文件内 + 数据库）
        if email in existing_emails:
            return f"第{row_index}行: 邮箱 '{email}' 重复"
        existing_emails.add(email)

        if db.query(User).filter(User.email == email).first():
            return f"第{row_index}行: 邮箱 '{email}' 已存在于系统中"

        # 手机号验证（如果提供）
        phone = row.get("phone")
        if pd.notna(phone) and phone:
            phone_str = str(phone).strip()
            if len(phone_str) < 11 or not phone_str.replace("-", "").replace("+", "").isdigit():
                return f"第{row_index}行: 手机号格式不正确"

        return None

    @classmethod
    def get_or_create_role(cls, db: Session, role_name: str, tenant_id: Optional[int] = None) -> Optional[Role]:
        """获取或创建角色"""
        role = db.query(Role).filter(
            Role.role_name == role_name,
            Role.tenant_id == tenant_id
        ).first()
        
        if not role:
            logger.warning(f"角色 '{role_name}' 不存在")
            return None
            
        return role

    @classmethod
    def create_user_from_row(
        cls,
        db: Session,
        row: pd.Series,
        operator_id: int,
        tenant_id: Optional[int] = None,
    ) -> User:
        """从DataFrame行创建用户"""
        
        # 准备用户数据
        user_data = {
            "username": str(row.get("username", "")).strip(),
            "real_name": str(row.get("real_name", "")).strip(),
            "email": str(row.get("email", "")).strip(),
            "phone": str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else None,
            "employee_no": str(row.get("employee_no", "")).strip() if pd.notna(row.get("employee_no")) else None,
            "department": str(row.get("department", "")).strip() if pd.notna(row.get("department")) else None,
            "position": str(row.get("position", "")).strip() if pd.notna(row.get("position")) else None,
            "tenant_id": tenant_id,
        }

        # 处理密码（如果未提供，使用默认密码）
        password = row.get("password")
        if pd.isna(password) or str(password).strip() == "":
            password = "123456"  # 默认密码
        user_data["password_hash"] = get_password_hash(str(password))

        # 处理is_active字段
        is_active = row.get("is_active")
        if pd.notna(is_active):
            if isinstance(is_active, str):
                user_data["is_active"] = is_active.lower() in ["true", "1", "是", "启用"]
            elif isinstance(is_active, bool):
                user_data["is_active"] = is_active
            else:
                user_data["is_active"] = bool(is_active)
        else:
            user_data["is_active"] = True

        # 创建用户
        user = User(**user_data)
        db.add(user)
        db.flush()  # 获取用户ID

        # 处理角色分配
        roles_str = row.get("roles")
        if pd.notna(roles_str) and str(roles_str).strip():
            role_names = [r.strip() for r in str(roles_str).split(",") if r.strip()]
            for role_name in role_names:
                role = cls.get_or_create_role(db, role_name, tenant_id)
                if role:
                    user_role = UserRole(user_id=user.id, role_id=role.id)
                    db.add(user_role)
                else:
                    logger.warning(f"用户 {user.username} 的角色 '{role_name}' 未找到，已跳过")

        return user

    @classmethod
    def import_users(
        cls,
        db: Session,
        df: pd.DataFrame,
        operator_id: int,
        tenant_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        批量导入用户
        
        Args:
            db: 数据库会话
            df: 用户数据DataFrame
            operator_id: 操作人ID
            tenant_id: 租户ID
            
        Returns:
            导入结果字典
        """
        result = {
            "total": len(df),
            "success_count": 0,
            "failed_count": 0,
            "errors": [],
            "success_users": [],
        }

        # 标准化列名
        df = cls.normalize_columns(df)

        # 验证DataFrame结构
        structure_errors = cls.validate_dataframe(df)
        if structure_errors:
            result["errors"] = structure_errors
            result["failed_count"] = len(df)
            return result

        # 用于去重检查
        existing_usernames = set()
        existing_emails = set()

        # 验证每一行
        validation_errors = []
        for idx, row in df.iterrows():
            row_index = idx + 2  # Excel行号（从2开始，因为第1行是表头）
            error = cls.validate_row(row, row_index, db, existing_usernames, existing_emails)
            if error:
                validation_errors.append({"row": row_index, "error": error})

        if validation_errors:
            result["errors"] = validation_errors
            result["failed_count"] = len(df)
            return result

        # 开始事务导入
        try:
            for idx, row in df.iterrows():
                try:
                    user = cls.create_user_from_row(db, row, operator_id, tenant_id)
                    result["success_users"].append({
                        "username": user.username,
                        "real_name": user.real_name,
                        "email": user.email,
                    })
                    result["success_count"] += 1

                except Exception as e:
                    row_index = idx + 2
                    error_msg = f"第{row_index}行导入失败: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    result["errors"].append({"row": row_index, "error": str(e)})
                    result["failed_count"] += 1
                    raise  # 抛出异常以触发回滚

            # 提交事务
            db.commit()
            logger.info(f"成功导入 {result['success_count']} 个用户")

        except Exception as e:
            db.rollback()
            logger.error(f"批量导入失败，已回滚: {e}", exc_info=True)
            result["success_count"] = 0
            result["failed_count"] = len(df)
            if not result["errors"]:
                result["errors"] = [{"error": f"事务失败: {str(e)}"}]

        return result

    @classmethod
    def generate_template(cls) -> pd.DataFrame:
        """
        生成导入模板
        
        Returns:
            模板DataFrame
        """
        template_data = {
            "用户名": ["zhangsan", "lisi", "wangwu"],
            "密码": ["123456", "123456", ""],  # 空表示使用默认密码
            "真实姓名": ["张三", "李四", "王五"],
            "邮箱": ["zhangsan@example.com", "lisi@example.com", "wangwu@example.com"],
            "手机号": ["13800138000", "13800138001", ""],
            "工号": ["EMP001", "EMP002", "EMP003"],
            "部门": ["技术部", "销售部", "市场部"],
            "职位": ["工程师", "销售经理", "市场专员"],
            "角色": ["普通用户", "销售经理,普通用户", "普通用户"],  # 多个角色用逗号分隔
            "是否启用": ["是", "是", "否"],
        }

        return pd.DataFrame(template_data)
