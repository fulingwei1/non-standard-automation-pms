# -*- coding: utf-8 -*-
"""
权限检查模块 - 机台文档权限
"""

from app.models.user import User


def has_machine_document_permission(user: User, doc_type: str) -> bool:
    """
    检查用户是否有权限访问（上传/下载）指定类型的设备文档

    文档类型与角色权限映射：
    - CIRCUIT_DIAGRAM: 电气工程师、PLC工程师、研发工程师、项目经理
    - PLC_PROGRAM: PLC工程师、电气工程师、研发工程师、项目经理
    - LABELWORK_PROGRAM: 电气工程师、PLC工程师、研发工程师、项目经理
    - BOM_DOCUMENT: PMC、物料工程师、项目经理、工程师
    - FAT_DOCUMENT: 质量工程师、项目经理、总经理
    - SAT_DOCUMENT: 质量工程师、项目经理、总经理
    - OTHER: 项目成员（项目经理、工程师、PMC等）
    """
    if user.is_superuser:
        return True

    # 获取用户角色代码列表（转换为小写以便匹配）
    user_role_codes = []
    user_role_names = []
    for user_role in user.roles:
        role_code = user_role.role.role_code.upper() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code:
            user_role_codes.append(role_code)
        if role_name:
            user_role_names.append(role_name)

    doc_type = doc_type.upper()

    # 根据文档类型检查权限
    if doc_type == "CIRCUIT_DIAGRAM":
        # 电路图：电气工程师、PLC工程师、研发工程师、项目经理、PMO总监
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "PLC_PROGRAM":
        # PLC程序：PLC工程师、电气工程师、研发工程师、项目经理、PMO总监
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "LABELWORK_PROGRAM":
        # Labelwork程序：电气工程师、PLC工程师、研发工程师、项目经理、PMO总监
        allowed_codes = ["ENGINEER", "PM", "PMC", "RD_ENGINEER", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["电气", "plc", "研发", "工程师", "项目经理", "pm", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "BOM_DOCUMENT":
        # BOM文档：PMC、物料工程师、项目经理、工程师、PMO总监
        allowed_codes = ["PMC", "PM", "ENGINEER", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["物料", "pmc", "项目经理", "pm", "工程师", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "FAT_DOCUMENT":
        # FAT文档：质量工程师、项目经理、总经理、PMO总监
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "SAT_DOCUMENT":
        # SAT文档：质量工程师、项目经理、总经理、PMO总监
        allowed_codes = ["QA", "QUALITY", "PM", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["质量", "qa", "项目经理", "pm", "总经理", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    elif doc_type == "OTHER":
        # 其他文档：项目成员都可以访问
        allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "RD_ENGINEER", "GM", "ADMIN", "PMO_DIR"]
        allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa", "研发", "项目管理部总监"]
        return any(code in user_role_codes for code in allowed_codes) or any(
            name in user_role_names for name in allowed_names
        )

    # 默认：项目成员都可以访问
    allowed_codes = ["PM", "ENGINEER", "PMC", "QA", "GM", "ADMIN", "PMO_DIR"]
    allowed_names = ["项目经理", "pm", "工程师", "pmc", "质量", "qa", "项目管理部总监"]
    return any(code in user_role_codes for code in allowed_codes) or any(
        name in user_role_names for name in allowed_names
    )


def has_machine_document_upload_permission(user: User, doc_type: str) -> bool:
    """
    检查用户是否有权限上传指定类型的设备文档（兼容性函数，内部调用通用权限检查）
    """
    # 调用通用权限检查函数
    return has_machine_document_permission(user, doc_type)
