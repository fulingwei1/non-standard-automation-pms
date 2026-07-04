# -*- coding: utf-8 -*-
"""
API权限数据初始化 - 内嵌版本

不依赖外部SQL文件，直接在代码中定义权限数据
确保幂等性，可重复执行
"""

import logging

from sqlalchemy.orm import Session

from app.core.permission_codes import canonicalize_permission_code, get_equivalent_permission_codes
from app.models.user import ApiPermission, Role, RoleApiPermission

logger = logging.getLogger(__name__)


def _get_existing_permission(db: Session, perm_code: str) -> ApiPermission | None:
    """按新旧口径查找已存在权限。"""
    normalized_code = canonicalize_permission_code(perm_code)

    existing = db.query(ApiPermission).filter(ApiPermission.perm_code == normalized_code).first()
    if existing:
        return existing

    legacy_codes = [
        code for code in get_equivalent_permission_codes(normalized_code) if code != normalized_code
    ]
    if not legacy_codes:
        return None

    return db.query(ApiPermission).filter(ApiPermission.perm_code.in_(legacy_codes)).first()

# 定义所有API权限
API_PERMISSIONS = [
    # 用户管理权限
    {"perm_code": "user:read", "perm_name": "查看用户", "module": "USER", "action": "VIEW"},
    {"perm_code": "user:create", "perm_name": "创建用户", "module": "USER", "action": "CREATE"},
    {"perm_code": "user:update", "perm_name": "编辑用户", "module": "USER", "action": "UPDATE"},
    {"perm_code": "user:delete", "perm_name": "删除用户", "module": "USER", "action": "DELETE"},
    # 角色管理权限
    {"perm_code": "role:read", "perm_name": "查看角色", "module": "ROLE", "action": "VIEW"},
    {"perm_code": "role:create", "perm_name": "创建角色", "module": "ROLE", "action": "CREATE"},
    {"perm_code": "role:update", "perm_name": "编辑角色", "module": "ROLE", "action": "UPDATE"},
    {"perm_code": "role:delete", "perm_name": "删除角色", "module": "ROLE", "action": "DELETE"},
    {"perm_code": "role:assign", "perm_name": "分配角色", "module": "ROLE", "action": "EDIT"},
    # 权限管理
    {
        "perm_code": "permission:read",
        "perm_name": "查看权限",
        "module": "PERMISSION",
        "action": "VIEW",
    },
    {
        "perm_code": "permission:update",
        "perm_name": "修改权限",
        "module": "PERMISSION",
        "action": "UPDATE",
    },
    # 项目管理权限
    {"perm_code": "project:read", "perm_name": "查看项目", "module": "PROJECT", "action": "VIEW"},
    {
        "perm_code": "project:create",
        "perm_name": "创建项目",
        "module": "PROJECT",
        "action": "CREATE",
    },
    {
        "perm_code": "project:update",
        "perm_name": "编辑项目",
        "module": "PROJECT",
        "action": "UPDATE",
    },
    {
        "perm_code": "project:delete",
        "perm_name": "删除项目",
        "module": "PROJECT",
        "action": "DELETE",
    },
    # 商机管理权限
    {
        "perm_code": "opportunity:read",
        "perm_name": "查看商机",
        "module": "OPPORTUNITY",
        "action": "VIEW",
    },
    {
        "perm_code": "opportunity:create",
        "perm_name": "创建商机",
        "module": "OPPORTUNITY",
        "action": "CREATE",
    },
    {
        "perm_code": "opportunity:update",
        "perm_name": "编辑商机",
        "module": "OPPORTUNITY",
        "action": "UPDATE",
    },
    {
        "perm_code": "opportunity:delete",
        "perm_name": "删除商机",
        "module": "OPPORTUNITY",
        "action": "DELETE",
    },
    # 合同管理权限
    {"perm_code": "contract:read", "perm_name": "查看合同", "module": "CONTRACT", "action": "VIEW"},
    {
        "perm_code": "contract:create",
        "perm_name": "创建合同",
        "module": "CONTRACT",
        "action": "CREATE",
    },
    {
        "perm_code": "contract:update",
        "perm_name": "编辑合同",
        "module": "CONTRACT",
        "action": "UPDATE",
    },
    {
        "perm_code": "contract:delete",
        "perm_name": "删除合同",
        "module": "CONTRACT",
        "action": "DELETE",
    },
    {
        "perm_code": "contract:approve",
        "perm_name": "审批合同",
        "module": "CONTRACT",
        "action": "APPROVE",
    },
    {
        "perm_code": "contract:sign",
        "perm_name": "签订合同",
        "module": "CONTRACT",
        "action": "SIGN",
    },
    {
        "perm_code": "contract:export",
        "perm_name": "导出合同",
        "module": "CONTRACT",
        "action": "EXPORT",
    },
    # 任务管理权限
    {"perm_code": "task:read", "perm_name": "查看任务", "module": "TASK", "action": "VIEW"},
    {"perm_code": "task:create", "perm_name": "创建任务", "module": "TASK", "action": "CREATE"},
    {"perm_code": "task:update", "perm_name": "编辑任务", "module": "TASK", "action": "UPDATE"},
    {"perm_code": "task:delete", "perm_name": "删除任务", "module": "TASK", "action": "DELETE"},
    {
        "perm_code": "task_center:read",
        "perm_name": "查看任务中心",
        "module": "TASK_CENTER",
        "action": "VIEW",
    },
    {
        "perm_code": "task_center:create",
        "perm_name": "创建任务中心任务",
        "module": "TASK_CENTER",
        "action": "CREATE",
    },
    {
        "perm_code": "task_center:update",
        "perm_name": "编辑任务中心任务",
        "module": "TASK_CENTER",
        "action": "UPDATE",
    },
    {
        "perm_code": "task_center:assign",
        "perm_name": "分配任务中心任务",
        "module": "TASK_CENTER",
        "action": "EDIT",
    },
    # 仓储管理权限
    {"perm_code": "warehouse:view", "perm_name": "查看仓库", "module": "WAREHOUSE", "action": "VIEW"},
    {"perm_code": "warehouse:create", "perm_name": "创建库位", "module": "WAREHOUSE", "action": "CREATE"},
    {"perm_code": "warehouse:update", "perm_name": "编辑库位", "module": "WAREHOUSE", "action": "UPDATE"},
    {"perm_code": "warehouse:delete", "perm_name": "删除库位", "module": "WAREHOUSE", "action": "DELETE"},
    # 库存管理权限
    {"perm_code": "inventory:view", "perm_name": "查看库存", "module": "INVENTORY", "action": "VIEW"},
    {"perm_code": "inventory:create", "perm_name": "创建出入库单", "module": "INVENTORY", "action": "CREATE"},
    {"perm_code": "inventory:update", "perm_name": "更新出入库状态", "module": "INVENTORY", "action": "UPDATE"},
    {"perm_code": "inventory:count", "perm_name": "盘点操作", "module": "INVENTORY", "action": "EDIT"},
    # 财务管理权限
    {"perm_code": "finance:read", "perm_name": "查看财务", "module": "FINANCE", "action": "VIEW"},
    {
        "perm_code": "finance:create",
        "perm_name": "创建财务记录",
        "module": "FINANCE",
        "action": "CREATE",
    },
    {
        "perm_code": "finance:update",
        "perm_name": "编辑财务",
        "module": "FINANCE",
        "action": "UPDATE",
    },
    {
        "perm_code": "finance:delete",
        "perm_name": "删除财务记录",
        "module": "FINANCE",
        "action": "DELETE",
    },
    # 成本管理权限
    {"perm_code": "cost:read", "perm_name": "查看成本", "module": "COST", "action": "READ"},
    # 预警管理权限
    {"perm_code": "alert:read", "perm_name": "查看预警", "module": "ALERT", "action": "VIEW"},
    {"perm_code": "alert:manage", "perm_name": "管理预警规则", "module": "ALERT", "action": "EDIT"},
    # 人事管理权限
    {"perm_code": "hr:read", "perm_name": "查看HR数据", "module": "HR", "action": "VIEW"},
    {"perm_code": "hr:create", "perm_name": "创建HR数据", "module": "HR", "action": "CREATE"},
    {"perm_code": "hr:update", "perm_name": "编辑HR数据", "module": "HR", "action": "UPDATE"},
    {
        "perm_code": "hr:read_sensitive",
        "perm_name": "查看HR敏感数据",
        "module": "HR",
        "action": "VIEW",
    },
    # 奖金发放权限
    {"perm_code": "bonus:read", "perm_name": "查看奖金发放", "module": "BONUS", "action": "VIEW"},
    {
        "perm_code": "bonus:distribute",
        "perm_name": "创建奖金发放",
        "module": "BONUS",
        "action": "CREATE",
    },
    {"perm_code": "bonus:pay", "perm_name": "确认奖金付款", "module": "BONUS", "action": "APPROVE"},
    {
        "perm_code": "bonus:manage",
        "perm_name": "管理全部奖金发放",
        "module": "BONUS",
        "action": "EDIT",
    },
    # 审批管理权限
    {"perm_code": "approval:view", "perm_name": "查看审批", "module": "APPROVAL", "action": "VIEW"},
    {"perm_code": "approval:create", "perm_name": "发起审批", "module": "APPROVAL", "action": "CREATE"},
    {"perm_code": "approval:approve", "perm_name": "审批操作", "module": "APPROVAL", "action": "APPROVE"},
    {
        "perm_code": "approval:template:view",
        "perm_name": "查看审批模板",
        "module": "APPROVAL",
        "action": "VIEW",
    },
    {
        "perm_code": "approval:template:manage",
        "perm_name": "管理审批模板",
        "module": "APPROVAL",
        "action": "EDIT",
    },
]

# 定义角色权限映射（角色代码 -> 权限代码列表）
ROLE_PERMISSIONS_MAPPING = {
    # 系统管理员 - 所有权限
    "ADMIN": [p["perm_code"] for p in API_PERMISSIONS],
    # 总经理 - 查看所有，部分修改
    "GM": [
        "user:read",
        "role:read",
        "permission:read",
        "project:read",
        "project:update",
        "opportunity:read",
        "contract:read",
        "contract:update",
        "contract:approve",
        "contract:sign",
        "contract:export",
        "task:view",
        "finance:view",
        "warehouse:view",
        "inventory:view",
        "approval:view",
        "approval:create",
        "approval:approve",
        "approval:template:view",
        "approval:template:manage",
    ],
    # 项目经理 - 项目相关全权限
    "PM": [
        "project:read",
        "project:create",
        "project:update",
        "project:delete",
        "task:read",
        "task:create",
        "task:update",
        "task:delete",
        "task_center:read",
        "task_center:create",
        "task_center:update",
        "task_center:assign",
        "contract:view",
        "approval:view",
        "approval:create",
        "approval:approve",
        "approval:template:view",
    ],
    # 销售总监 - 销售相关全权限
    "SALES_DIR": [
        "opportunity:read",
        "opportunity:create",
        "opportunity:update",
        "opportunity:delete",
        "contract:read",
        "contract:create",
        "contract:update",
        "contract:approve",
        "contract:sign",
        "contract:export",
        "finance:view",
        "approval:view",
        "approval:create",
        "approval:approve",
        "approval:template:view",
    ],
    "pm": [
        "project:read",
        "project:create",
        "project:update",
        "project:delete",
        "task:read",
        "task:create",
        "task:update",
        "task:delete",
        "task_center:read",
        "task_center:create",
        "task_center:update",
        "task_center:assign",
        "contract:view",
        "approval:view",
        "approval:create",
        "approval:approve",
        "approval:template:view",
    ],
    # 销售专员 - 销售相关基础权限
    "SALES": [
        "opportunity:read",
        "opportunity:create",
        "opportunity:update",
        "contract:view",
        "contract:export",
        "approval:view",
        "approval:create",
        "approval:approve",
    ],
    # 工程师 - 项目和任务查看权限
    "ENGINEER": [
        "project:read",
        "task:read",
        "task:update",
        "approval:view",
        "approval:create",
        "approval:approve",
    ],
    # 机械工程师
    "ME": [
        "project:read",
        "task:read",
        "task:update",
        "approval:view",
        "approval:create",
        "approval:approve",
    ],
    # 电气工程师
    "EE": [
        "project:read",
        "task:read",
        "task:update",
        "approval:view",
        "approval:create",
        "approval:approve",
    ],
    # 软件工程师
    "SW": [
        "project:read",
        "task:read",
        "task:update",
        "approval:view",
        "approval:create",
        "approval:approve",
    ],
    # PMO总监 - 项目详情预算页只读成本入口
    "pmo_director": [
        "cost:read",
    ],
    "PMO_DIRECTOR": [
        "cost:read",
    ],
    # 人事经理 - HR 工作台只读入口
    "hr_manager": [
        "hr:read",
        "hr:create",
        "hr:update",
        "hr:read_sensitive",
    ],
    "HR_MGR": [
        "hr:read",
        "hr:create",
        "hr:update",
        "hr:read_sensitive",
    ],
    # 财务/奖金管理员 - 奖金发放操作入口
    "FINANCE": [
        "finance:read",
        "finance:create",
        "finance:update",
        "finance:delete",
        "bonus:read",
        "bonus:distribute",
        "bonus:pay",
        "bonus:manage",
    ],
    "FINANCE_MANAGER": [
        "finance:read",
        "finance:create",
        "finance:update",
        "finance:delete",
        "bonus:read",
        "bonus:distribute",
        "bonus:pay",
        "bonus:manage",
    ],
}


def init_api_permissions_data(db: Session) -> dict:
    """
    初始化API权限数据（内嵌版本）

    功能：
    1. 创建API权限记录（幂等）
    2. 为角色分配权限（幂等）

    Args:
        db: 数据库会话

    Returns:
        dict: 初始化结果统计
    """
    result = {
        "permissions_created": 0,
        "permissions_existing": 0,
        "role_mappings_created": 0,
        "role_mappings_existing": 0,
        "errors": [],
    }

    try:
        # 1. 创建API权限
        logger.info("开始初始化API权限...")

        permission_map = {}  # perm_code -> permission_id

        for perm_data in API_PERMISSIONS:
            normalized_perm_code = canonicalize_permission_code(perm_data["perm_code"])
            # 检查是否已存在
            existing = _get_existing_permission(db, normalized_perm_code)

            if existing:
                existing.perm_code = normalized_perm_code
                existing.perm_name = perm_data["perm_name"]
                existing.module = perm_data["module"]
                existing.action = perm_data["action"]
                existing.permission_type = "API"
                existing.is_active = True
                existing.is_system = True
                result["permissions_existing"] += 1
                permission_map[normalized_perm_code] = existing.id
                logger.debug(f"权限 {normalized_perm_code} 已存在")
            else:
                # 创建新权限
                new_perm = ApiPermission(
                    perm_code=normalized_perm_code,
                    perm_name=perm_data["perm_name"],
                    module=perm_data["module"],
                    action=perm_data["action"],
                    permission_type="API",
                    is_active=True,
                    is_system=True,
                )
                db.add(new_perm)
                db.flush()  # 获取ID

                permission_map[normalized_perm_code] = new_perm.id
                result["permissions_created"] += 1
                logger.info(f"创建权限: {normalized_perm_code} - {perm_data['perm_name']}")

        db.commit()
        logger.info(
            f"API权限初始化完成: 新建{result['permissions_created']}个，已存在{result['permissions_existing']}个"
        )

        # 2. 为角色分配权限
        logger.info("开始为角色分配权限...")

        for role_code, perm_codes in ROLE_PERMISSIONS_MAPPING.items():
            # 查找角色
            role = db.query(Role).filter(Role.role_code == role_code).first()
            if not role:
                logger.warning(f"角色 {role_code} 不存在，跳过权限分配")
                continue

            for perm_code in perm_codes:
                perm_code = canonicalize_permission_code(perm_code)
                if perm_code not in permission_map:
                    logger.warning(f"权限 {perm_code} 不存在，跳过")
                    continue

                permission_id = permission_map[perm_code]

                # 检查映射是否已存在
                existing_mapping = (
                    db.query(RoleApiPermission)
                    .filter(
                        RoleApiPermission.role_id == role.id,
                        RoleApiPermission.permission_id == permission_id,
                    )
                    .first()
                )

                if existing_mapping:
                    result["role_mappings_existing"] += 1
                else:
                    # 创建映射
                    new_mapping = RoleApiPermission(role_id=role.id, permission_id=permission_id)
                    db.add(new_mapping)
                    result["role_mappings_created"] += 1

        db.commit()
        logger.info(
            f"角色权限分配完成: 新建{result['role_mappings_created']}条，已存在{result['role_mappings_existing']}条"
        )

        return result

    except Exception as e:
        db.rollback()
        error_msg = f"API权限初始化失败: {str(e)}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
        return result


def ensure_admin_permissions(db: Session) -> bool:
    """
    确保ADMIN角色拥有所有权限

    可以单独调用此函数来修复管理员权限问题

    Args:
        db: 数据库会话

    Returns:
        bool: 是否成功
    """
    try:
        # 查找ADMIN角色
        admin_role = db.query(Role).filter(Role.role_code == "ADMIN").first()
        if not admin_role:
            logger.warning("ADMIN角色不存在，跳过管理员权限兜底同步")
            return False

        # 获取所有API权限
        all_permissions = db.query(ApiPermission).all()

        # 确保每个权限都分配给ADMIN
        added = 0
        for perm in all_permissions:
            existing = (
                db.query(RoleApiPermission)
                .filter(
                    RoleApiPermission.role_id == admin_role.id,
                    RoleApiPermission.permission_id == perm.id,
                )
                .first()
            )

            if not existing:
                db.add(RoleApiPermission(role_id=admin_role.id, permission_id=perm.id))
                added += 1

        if added > 0:
            db.commit()
            logger.info(f"为ADMIN角色添加了 {added} 个缺失的权限")
        else:
            logger.info("ADMIN角色已拥有所有权限")

        return True

    except Exception as e:
        db.rollback()
        logger.error(f"确保ADMIN权限失败: {e}")
        return False


if __name__ == "__main__":
    """独立运行测试"""
    from app.models.base import SessionLocal

    print("=" * 60)
    print("API权限数据初始化工具")
    print("=" * 60)

    db = SessionLocal()
    try:
        result = init_api_permissions_data(db)

        print("\n初始化结果:")
        print(
            f"  权限记录: 新建 {result['permissions_created']} 个，已存在 {result['permissions_existing']} 个"
        )
        print(
            f"  角色映射: 新建 {result['role_mappings_created']} 条，已存在 {result['role_mappings_existing']} 条"
        )

        if result["errors"]:
            print(f"\n错误: {', '.join(result['errors'])}")
        else:
            print("\n✓ 初始化成功！")

        # 确保ADMIN权限完整
        print("\n确保ADMIN角色权限...")
        if ensure_admin_permissions(db):
            print("✓ ADMIN权限检查完成")

    finally:
        db.close()

    print("=" * 60)
