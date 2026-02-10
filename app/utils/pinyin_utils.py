# -*- coding: utf-8 -*-
"""
拼音工具函数
用于生成用户名和密码
"""
import secrets
from typing import Optional

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - 可选依赖
    Style = None

    def lazy_pinyin(text: str, style=None):
        # 降级策略：无拼音库时直接返回字符列表
        if not text:
            return []
        if style is not None:
            return [str(ch)[0].lower() for ch in text]
        return [str(ch).lower() for ch in text]
from sqlalchemy.orm import Session

# 模块级导入，支持 unittest.mock.patch 在测试中替换
from app.models.user import User
from app.models.organization import Employee


def name_to_pinyin(name: str) -> str:
    """
    将中文姓名转换为拼音（小写，无空格）

    Args:
        name: 中文姓名，如 "姚洪"

    Returns:
        拼音字符串，如 "yaohong"
    """
    if not name:
        return ""
    # 转换为拼音并拼接
    pinyin_list = lazy_pinyin(name)
    return ''.join(pinyin_list).lower()


def name_to_pinyin_initials(name: str) -> str:
    """
    将中文姓名转换为拼音首字母（大写）

    Args:
        name: 中文姓名，如 "姚洪"

    Returns:
        拼音首字母，如 "YH"
    """
    if not name:
        return ""
    style = Style.FIRST_LETTER if Style is not None else True
    initials = lazy_pinyin(name, style=style)
    return ''.join(initials).upper()


def generate_unique_username(name: str, db: Session, existing_usernames: Optional[set] = None) -> str:
    """
    生成唯一的用户名，处理重名情况

    Args:
        name: 中文姓名
        db: 数据库会话
        existing_usernames: 已存在的用户名集合（用于批量处理时避免重复查询）

    Returns:
        唯一的用户名，如 "yaohong" 或 "yaohong2"
    """

    base_username = name_to_pinyin(name)
    if not base_username:
        base_username = "user"

    username = base_username
    counter = 1

    while True:
        # 检查是否在传入的集合中存在
        if existing_usernames is not None:
            if username in existing_usernames:
                counter += 1
                username = f"{base_username}{counter}"
                continue

        # 检查数据库中是否存在
        exists = db.query(User).filter(User.username == username).first()
        if not exists:
            break
        counter += 1
        username = f"{base_username}{counter}"

    return username


def generate_initial_password(username: str = None, id_card: str = None, employee_code: str = None) -> str:
    """
    生成安全的随机初始密码

    安全改进：使用 secrets.token_urlsafe 生成密码，不再使用可预测的规则

    Args:
        username: 已废弃，保留参数以兼容旧代码
        id_card: 已废弃，保留参数以兼容旧代码
        employee_code: 已废弃，保留参数以兼容旧代码

    Returns:
        16字符的安全随机密码，如 "Xa3b_cD5eF2gH7jK"
    """

    # 生成 12 字节的随机数据，base64url 编码后为 16 字符
    return secrets.token_urlsafe(12)


def batch_generate_pinyin_for_employees(db: Session) -> int:
    """
    批量为员工生成拼音名（更新 pinyin_name 字段）

    Args:
        db: 数据库会话

    Returns:
        更新的记录数
    """

    employees = db.query(Employee).filter(
        Employee.pinyin_name.is_(None) | (Employee.pinyin_name == '')
    ).all()

    updated_count = 0
    for emp in employees:
        if emp.name:
            emp.pinyin_name = name_to_pinyin(emp.name)
            updated_count += 1

    if updated_count > 0:
        db.commit()

    return updated_count


