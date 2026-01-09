# -*- coding: utf-8 -*-
"""
拼音工具函数
用于生成用户名和密码
"""
from typing import Optional
from pypinyin import lazy_pinyin, Style
from sqlalchemy.orm import Session


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
    initials = lazy_pinyin(name, style=Style.FIRST_LETTER)
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
    from app.models.user import User

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


def generate_initial_password(username: str, id_card: str = None, employee_code: str = None) -> str:
    """
    生成初始密码
    规则：用户名 + 身份证后4位（优先）或工号后4位（回退）

    Args:
        username: 用户名（拼音）
        id_card: 身份证号，如 "310101199001011234"
        employee_code: 员工编码（回退选项），如 "EMP0001"

    Returns:
        初始密码，如 "yaohong1234"（身份证后4位）或 "yaohong0001"（工号后4位）
    """
    # 优先使用身份证后4位
    if id_card and len(id_card) >= 4:
        suffix = id_card[-4:]
    # 回退使用工号后4位
    elif employee_code and len(employee_code) >= 4:
        suffix = employee_code[-4:]
    else:
        suffix = "0000"

    return f"{username}{suffix}"


def batch_generate_pinyin_for_employees(db: Session) -> int:
    """
    批量为员工生成拼音名（更新 pinyin_name 字段）

    Args:
        db: 数据库会话

    Returns:
        更新的记录数
    """
    from app.models.organization import Employee

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


# 测试函数
if __name__ == "__main__":
    # 测试拼音转换
    test_names = ["姚洪", "张三", "李四", "王五"]
    for name in test_names:
        pinyin = name_to_pinyin(name)
        initials = name_to_pinyin_initials(name)
        print(f"{name} -> {pinyin} (首字母: {initials})")

    # 测试密码生成
    print("\n密码生成测试:")
    print(f"yaohong + EMP0001 -> {generate_initial_password('yaohong', 'EMP0001')}")
    print(f"zhangsan + EMP0123 -> {generate_initial_password('zhangsan', 'EMP0123')}")
