# -*- coding: utf-8 -*-
"""
PERM-17: BOM / ECN（工程变更）域数据权限过滤挂载测试

验证以下 LIST 端点新挂载的 DataScopeService.filter_by_scope 在
ALL 范围（超级管理员）与 OWN 范围（普通用户，无角色时默认按 OWN 归一化）
两种口径下的行为：
    - ALL / 超级管理员：可见全部记录（跨用户）
    - OWN：仅可见自己创建（或 approved_by / applicant_id 等所有者字段命中）的记录

覆盖端点：
    - app.api.v1.endpoints.bom.list.list_boms
    - app.api.v1.endpoints.bom.machine_bom.get_machine_bom_list
    - app.api.v1.endpoints.ecn.core.read_ecns

直接以 Python 函数调用的方式驱动端点函数（不经过 FastAPI 依赖注入/HTTP层），
使用项目共享的 db_session（真实数据库 session，测试结束自动回滚），
避免引入与本次修复无关的路由权限（require_permission）依赖。
"""

import uuid

from sqlalchemy.orm import Session

from app.common.pagination import get_pagination_params
from app.models.ecn.core import Ecn
from app.models.material import BomHeader
from app.models.project.core import Machine, Project
from app.models.user import User


def _make_user(db: Session, *, is_superuser: bool = False) -> User:
    """创建一个普通用户；不分配任何角色时，UserScopeService 默认归一化为 OWN 范围。"""
    user = User(
        username=f"perm17_{uuid.uuid4().hex[:10]}",
        password_hash="not-used",
        auth_type="password",
        real_name="PERM17测试用户",
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.flush()
    return user


def _make_project(db: Session) -> Project:
    project = Project(
        project_code=f"PERM17-{uuid.uuid4().hex[:8].upper()}",
        project_name="PERM17测试项目",
        stage="S1",
        status="ST01",
        health="H1",
    )
    db.add(project)
    db.flush()
    return project


def _make_machine(db: Session, project_id: int) -> Machine:
    machine = Machine(
        project_id=project_id,
        machine_code=f"PN{uuid.uuid4().hex[:8]}",
        machine_name="PERM17测试机台",
    )
    db.add(machine)
    db.flush()
    return machine


def _make_bom(db: Session, *, project_id: int, created_by: int, machine_id=None) -> BomHeader:
    bom = BomHeader(
        bom_no=f"BOM-PERM17-{uuid.uuid4().hex[:10]}",
        bom_name="PERM17测试BOM",
        project_id=project_id,
        machine_id=machine_id,
        created_by=created_by,
        status="DRAFT",
    )
    db.add(bom)
    db.flush()
    return bom


def _make_ecn(db: Session, *, project_id: int, created_by: int) -> Ecn:
    ecn = Ecn(
        ecn_no=f"ECN-PERM17-{uuid.uuid4().hex[:10]}",
        ecn_title="PERM17测试ECN",
        project_id=project_id,
        created_by=created_by,
        status="DRAFT",
    )
    db.add(ecn)
    db.flush()
    return ecn


class TestListBomsDataScope:
    """bom/list.py::list_boms 挂载的 BOM_DATA_SCOPE_CONFIG"""

    def test_all_scope_superuser_sees_every_bom(self, db_session: Session):
        from app.api.v1.endpoints.bom.list import list_boms

        project = _make_project(db_session)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        viewer = _make_user(db_session, is_superuser=True)
        bom_a = _make_bom(db_session, project_id=project.id, created_by=owner_a.id)
        bom_b = _make_bom(db_session, project_id=project.id, created_by=owner_b.id)
        db_session.commit()

        result = list_boms(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            project_id=None,
            machine_id=None,
            is_latest=None,
            current_user=viewer,
        )

        ids = {item.id for item in result.items}
        assert bom_a.id in ids
        assert bom_b.id in ids

    def test_own_scope_sees_only_own_boms(self, db_session: Session):
        from app.api.v1.endpoints.bom.list import list_boms

        project = _make_project(db_session)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        bom_a = _make_bom(db_session, project_id=project.id, created_by=owner_a.id)
        bom_b = _make_bom(db_session, project_id=project.id, created_by=owner_b.id)
        db_session.commit()

        result = list_boms(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            project_id=None,
            machine_id=None,
            is_latest=None,
            current_user=owner_a,
        )

        ids = {item.id for item in result.items}
        assert bom_a.id in ids
        assert bom_b.id not in ids

    def test_own_scope_sees_bom_approved_by_self(self, db_session: Session):
        """additional_owner_fields=["approved_by"]：审批人也应可见该 BOM。"""
        from app.api.v1.endpoints.bom.list import list_boms

        project = _make_project(db_session)
        creator = _make_user(db_session)
        approver = _make_user(db_session)
        bom = _make_bom(db_session, project_id=project.id, created_by=creator.id)
        bom.approved_by = approver.id
        db_session.commit()

        result = list_boms(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            project_id=None,
            machine_id=None,
            is_latest=None,
            current_user=approver,
        )

        ids = {item.id for item in result.items}
        assert bom.id in ids


class TestMachineBomListDataScope:
    """bom/machine_bom.py::get_machine_bom_list 挂载的 BOM_DATA_SCOPE_CONFIG"""

    def test_all_scope_superuser_sees_every_machine_bom(self, db_session: Session):
        from app.api.v1.endpoints.bom.machine_bom import get_machine_bom_list

        project = _make_project(db_session)
        machine = _make_machine(db_session, project.id)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        viewer = _make_user(db_session, is_superuser=True)
        bom_a = _make_bom(
            db_session, project_id=project.id, created_by=owner_a.id, machine_id=machine.id
        )
        bom_b = _make_bom(
            db_session, project_id=project.id, created_by=owner_b.id, machine_id=machine.id
        )
        db_session.commit()

        result = get_machine_bom_list(db=db_session, machine_id=machine.id, current_user=viewer)

        ids = {item.id for item in result}
        assert bom_a.id in ids
        assert bom_b.id in ids

    def test_own_scope_sees_only_own_machine_bom(self, db_session: Session):
        from app.api.v1.endpoints.bom.machine_bom import get_machine_bom_list

        project = _make_project(db_session)
        machine = _make_machine(db_session, project.id)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        bom_a = _make_bom(
            db_session, project_id=project.id, created_by=owner_a.id, machine_id=machine.id
        )
        bom_b = _make_bom(
            db_session, project_id=project.id, created_by=owner_b.id, machine_id=machine.id
        )
        db_session.commit()

        result = get_machine_bom_list(db=db_session, machine_id=machine.id, current_user=owner_a)

        ids = {item.id for item in result}
        assert bom_a.id in ids
        assert bom_b.id not in ids


class TestReadEcnsDataScope:
    """ecn/core.py::read_ecns 挂载的 ECN_DATA_SCOPE_CONFIG"""

    def test_all_scope_superuser_sees_every_ecn(self, db_session: Session):
        from app.api.v1.endpoints.ecn.core import read_ecns

        project = _make_project(db_session)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        viewer = _make_user(db_session, is_superuser=True)
        ecn_a = _make_ecn(db_session, project_id=project.id, created_by=owner_a.id)
        ecn_b = _make_ecn(db_session, project_id=project.id, created_by=owner_b.id)
        db_session.commit()

        result = read_ecns(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            keyword=None,
            project_id=None,
            machine_id=None,
            ecn_type=None,
            ecn_status=None,
            priority=None,
            current_user=viewer,
        )

        ids = {item.id for item in result["items"]}
        assert ecn_a.id in ids
        assert ecn_b.id in ids

    def test_own_scope_sees_only_own_ecns(self, db_session: Session):
        from app.api.v1.endpoints.ecn.core import read_ecns

        project = _make_project(db_session)
        owner_a = _make_user(db_session)
        owner_b = _make_user(db_session)
        ecn_a = _make_ecn(db_session, project_id=project.id, created_by=owner_a.id)
        ecn_b = _make_ecn(db_session, project_id=project.id, created_by=owner_b.id)
        db_session.commit()

        result = read_ecns(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            keyword=None,
            project_id=None,
            machine_id=None,
            ecn_type=None,
            ecn_status=None,
            priority=None,
            current_user=owner_a,
        )

        ids = {item.id for item in result["items"]}
        assert ecn_a.id in ids
        assert ecn_b.id not in ids

    def test_own_scope_sees_ecn_as_applicant(self, db_session: Session):
        """additional_owner_fields=["applicant_id", "final_approver_id"]。"""
        from app.api.v1.endpoints.ecn.core import read_ecns

        project = _make_project(db_session)
        creator = _make_user(db_session)
        applicant = _make_user(db_session)
        ecn = _make_ecn(db_session, project_id=project.id, created_by=creator.id)
        ecn.applicant_id = applicant.id
        db_session.commit()

        result = read_ecns(
            db=db_session,
            pagination=get_pagination_params(page=1, page_size=50),
            keyword=None,
            project_id=None,
            machine_id=None,
            ecn_type=None,
            ecn_status=None,
            priority=None,
            current_user=applicant,
        )

        ids = {item.id for item in result["items"]}
        assert ecn.id in ids
