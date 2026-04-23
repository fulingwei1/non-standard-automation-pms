# -*- coding: utf-8 -*-
"""旧模块名兼容。"""


def check_deliverables_complete(service_or_db, project_id=None, milestone_type=None, *args, **kwargs):
    return False


def check_acceptance_issues_resolved(service_or_db, acceptance_order_id=None, *args, **kwargs):
    return True


__all__ = ["check_deliverables_complete", "check_acceptance_issues_resolved"]
