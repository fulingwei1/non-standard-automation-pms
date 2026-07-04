# -*- coding: utf-8 -*-
"""AS-10/AS-11: after-sales tickets and service records must bind machines."""

import uuid
from datetime import date, datetime

from app.api.v1.endpoints.service.tickets.crud import create_service_ticket
from app.models.project import Customer, Machine, Project
from app.models.service import ServiceRecord, ServiceTicket
from app.models.user import User
from app.schemas.service import ServiceTicketCreate
from app.services.machine_custom.service import MachineCustomService


def _user(username: str) -> User:
    return User(
        username=username,
        password_hash="x",
        real_name=username.title(),
        is_active=True,
        is_superuser=True,
    )


def _seed_device_archive(db_session):
    suffix = uuid.uuid4().hex[:8]
    user = _user(f"as10-admin-{suffix}")
    customer = Customer(
        customer_code=f"AS10-CUST-{suffix}",
        customer_name="AS10 客户",
    )
    db_session.add_all([user, customer])
    db_session.flush()

    project = Project(
        project_code=f"AS10-PROJ-{suffix}",
        project_name="AS10 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.flush()

    machine = Machine(
        project_id=project.id,
        customer_id=customer.id,
        machine_code=f"AS10-M-{suffix}",
        machine_name="AS10 客户侧设备",
        machine_no=1,
        serial_no=f"SN-AS10-{suffix}",
        warranty="24个月",
    )
    db_session.add(machine)
    db_session.commit()
    db_session.refresh(machine)
    return user, customer, project, machine


def test_create_service_ticket_binds_machine_archive(db_session):
    user, customer, project, machine = _seed_device_archive(db_session)

    ticket = create_service_ticket(
        db=db_session,
        ticket_in=ServiceTicketCreate(
            project_id=project.id,
            customer_id=customer.id,
            machine_id=machine.id,
            problem_type="MECHANICAL",
            problem_desc="设备异响",
            urgency="HIGH",
            reported_by=str(user.id),
            reported_time=datetime(2026, 7, 4, 9, 0),
        ),
        current_user=user,
    )

    stored = db_session.query(ServiceTicket).filter_by(id=ticket.id).one()
    assert stored.machine_id == machine.id
    assert ticket.machine_id == machine.id
    assert ticket.machine_name == machine.machine_name
    assert ticket.machine_serial_no == machine.serial_no


def test_machine_service_history_uses_machine_id_before_legacy_machine_no(db_session):
    user, customer, project, machine = _seed_device_archive(db_session)
    record = ServiceRecord(
        record_no=f"SR-AS10-{uuid.uuid4().hex[:8]}",
        service_type="REPAIR",
        project_id=project.id,
        machine_id=machine.id,
        machine_no="unrelated-legacy-text",
        customer_id=customer.id,
        service_date=date(2026, 7, 4),
        service_engineer_id=user.id,
        service_engineer_name=user.real_name,
        service_content="更换轴承",
        status="COMPLETED",
    )
    db_session.add(record)
    db_session.commit()

    history = MachineCustomService(db_session).get_service_history(machine)

    assert history["summary"]["total_records"] == 1
    assert history["pagination"]["total"] == 1
    assert history["items"][0]["record_no"] == record.record_no
