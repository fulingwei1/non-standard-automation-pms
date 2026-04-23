from app.models import presale


def test_presale_enums_are_complete():
    assert [item.value for item in presale.TicketTypeEnum] == [
        "CONSULT",
        "SURVEY",
        "SOLUTION",
        "QUOTATION",
        "TENDER",
        "MEETING",
        "SITE_VISIT",
    ]
    assert [item.value for item in presale.TicketUrgencyEnum] == [
        "NORMAL",
        "URGENT",
        "VERY_URGENT",
    ]
    assert [item.value for item in presale.TicketStatusEnum] == [
        "PENDING",
        "ACCEPTED",
        "PROCESSING",
        "REVIEW",
        "COMPLETED",
        "CLOSED",
        "CANCELLED",
    ]
    assert [item.value for item in presale.DeliverableStatusEnum] == [
        "DRAFT",
        "SUBMITTED",
        "APPROVED",
        "REJECTED",
    ]
    assert [item.value for item in presale.SolutionStatusEnum] == [
        "DRAFT",
        "REVIEW",
        "APPROVED",
        "DELIVERED",
        "WON",
        "LOST",
    ]
    assert [item.value for item in presale.TenderResultEnum] == [
        "PENDING",
        "WON",
        "LOST",
        "CANCELLED",
    ]


def test_presale_support_ticket_table_and_defaults():
    table = presale.PresaleSupportTicket.__table__

    assert table.name == "presale_support_ticket"
    assert table.c.ticket_no.unique is True
    assert table.c.title.nullable is False
    assert table.c.urgency.default.arg == "NORMAL"
    assert table.c.status.default.arg == "PENDING"
    assert table.c.pm_involvement_required.default.arg is False
    assert table.c.pm_assigned.default.arg is False
    assert {idx.name for idx in table.indexes} == {
        "idx_presale_ticket_no",
        "idx_presale_ticket_status",
        "idx_presale_ticket_applicant",
        "idx_presale_ticket_assignee",
        "idx_presale_ticket_customer",
    }
    assert "deliverables" in presale.PresaleSupportTicket.__dict__
    assert "progress_records" in presale.PresaleSupportTicket.__dict__


def test_deliverable_progress_and_solution_tables():
    deliverable = presale.PresaleTicketDeliverable.__table__
    progress = presale.PresaleTicketProgress.__table__
    solution = presale.PresaleSolution.__table__
    cost = presale.PresaleSolutionCost.__table__

    assert deliverable.c.version.default.arg == "V1.0"
    assert deliverable.c.status.default.arg == "DRAFT"
    assert {idx.name for idx in deliverable.indexes} == {"idx_deliverable_ticket"}

    assert progress.c.progress_type.nullable is False
    assert {idx.name for idx in progress.indexes} == {"idx_progress_ticket"}

    assert solution.c.solution_no.unique is True
    assert solution.c.solution_type.default.arg == "CUSTOM"
    assert solution.c.status.default.arg == "DRAFT"
    assert solution.c.version.default.arg == "V1.0"
    assert {idx.name for idx in solution.indexes} == {
        "idx_solution_no",
        "idx_solution_ticket",
        "idx_solution_customer",
        "idx_solution_industry",
    }
    assert "cost_items" in presale.PresaleSolution.__dict__
    assert "parent_version" in presale.PresaleSolution.__dict__

    assert cost.c.category.nullable is False
    assert cost.c.item_name.nullable is False
    assert cost.c.sort_order.default.arg == 0
    assert {idx.name for idx in cost.indexes} == {"idx_cost_solution"}


def test_template_workload_profile_and_tender_tables():
    template = presale.PresaleSolutionTemplate.__table__
    workload = presale.PresaleWorkload.__table__
    profile = presale.PresaleCustomerTechProfile.__table__
    tender = presale.PresaleTenderRecord.__table__

    assert template.c.template_no.unique is True
    assert template.c.use_count.default.arg == 0
    assert template.c.is_active.default.arg is True
    assert {idx.name for idx in template.indexes} == {
        "idx_template_no",
        "idx_template_industry",
    }

    assert workload.c.user_id.nullable is False
    assert workload.c.stat_date.nullable is False
    assert workload.c.pending_tickets.default.arg == 0
    assert workload.c.processing_tickets.default.arg == 0
    assert workload.c.completed_tickets.default.arg == 0
    assert workload.c.planned_hours.default.arg == 0
    assert workload.c.actual_hours.default.arg == 0
    assert workload.c.solutions_count.default.arg == 0
    unique_index = next(idx for idx in workload.indexes if idx.name == "idx_workload_user_date")
    assert unique_index.unique is True
    assert {idx.name for idx in workload.indexes} == {
        "idx_workload_user_date",
        "idx_workload_date",
    }

    assert profile.c.customer_id.unique is True
    assert profile.name == "presale_customer_tech_profile"

    assert tender.c.tender_name.nullable is False
    assert tender.c.result.default.arg == "PENDING"
    assert {idx.name for idx in tender.indexes} == {
        "idx_tender_opportunity",
        "idx_tender_result",
    }
