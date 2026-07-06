# -*- coding: utf-8 -*-
"""CI 幽灵表门禁守护。"""

from scripts import ci_guard_ghost_tables


def test_import_scripts_count_as_write_evidence_for_master_data_tables():
    """主数据导入脚本是合法写入口径，不应被幽灵表门禁误报。"""
    evidence = ci_guard_ghost_tables.collect_write_evidence()

    assert "INSERT INTO company_profile" in evidence
    assert "INSERT INTO competitors" in evidence or "INSERT OR REPLACE INTO competitors" in evidence


def test_company_profile_and_competitor_are_not_new_ghost_tables():
    ghosts = set(ci_guard_ghost_tables.find_ghosts())

    assert "CompanyProfile(company_profile)" not in ghosts
    assert "Competitor(competitors)" not in ghosts
