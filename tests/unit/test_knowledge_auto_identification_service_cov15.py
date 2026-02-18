# -*- coding: utf-8 -*-
"""第十五批: knowledge_auto_identification_service 单元测试"""
import pytest

pytest.importorskip("app.services.knowledge_auto_identification_service")

from unittest.mock import MagicMock, patch
from app.services.knowledge_auto_identification_service import KnowledgeAutoIdentificationService


def make_db():
    return MagicMock()


def test_identify_from_ticket_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = KnowledgeAutoIdentificationService(db)
    result = svc.identify_from_service_ticket(99)
    assert result is None


def test_identify_from_ticket_not_closed():
    db = make_db()
    ticket = MagicMock()
    ticket.status = "OPEN"
    ticket.solution = "some solution"
    db.query.return_value.filter.return_value.first.return_value = ticket
    svc = KnowledgeAutoIdentificationService(db)
    result = svc.identify_from_service_ticket(1)
    assert result is None


def test_identify_from_ticket_no_solution():
    db = make_db()
    ticket = MagicMock()
    ticket.status = "CLOSED"
    ticket.solution = None
    db.query.return_value.filter.return_value.first.return_value = ticket
    svc = KnowledgeAutoIdentificationService(db)
    result = svc.identify_from_service_ticket(1)
    assert result is None


def test_identify_from_ticket_existing_contribution():
    db = make_db()
    ticket = MagicMock()
    ticket.status = "CLOSED"
    ticket.solution = "Fixed it"
    ticket.ticket_no = "TK-001"
    existing = MagicMock()

    with patch(
        "app.services.knowledge_auto_identification_service.apply_keyword_filter"
    ) as mock_filter:
        mock_q = MagicMock()
        mock_q.first.return_value = existing
        mock_filter.return_value = mock_q
        db.query.return_value.filter.return_value.first.return_value = ticket
        svc = KnowledgeAutoIdentificationService(db)
        result = svc.identify_from_service_ticket(1)
        assert result == existing


def test_identify_from_ticket_creates_new():
    db = make_db()
    ticket = MagicMock()
    ticket.status = "CLOSED"
    ticket.solution = "Fixed it"
    ticket.ticket_no = "TK-002"
    new_article = MagicMock()
    new_contrib = MagicMock()

    with patch(
        "app.services.knowledge_auto_identification_service.apply_keyword_filter"
    ) as mock_filter, patch(
        "app.services.knowledge_auto_identification_service.auto_extract_knowledge_from_ticket"
    ) as mock_extract, patch(
        "app.services.knowledge_auto_identification_service.save_obj"
    ):
        mock_q = MagicMock()
        mock_q.first.return_value = None
        mock_filter.return_value = mock_q
        mock_extract.return_value = new_article
        db.query.return_value.filter.return_value.first.return_value = ticket
        # After save, db.query for KnowledgeContribution returns new_contrib
        svc = KnowledgeAutoIdentificationService(db)
        # Just verify it calls auto_extract
        result = svc.identify_from_service_ticket(1)
        mock_extract.assert_called_once()


def test_identify_from_ticket_extract_returns_none():
    db = make_db()
    ticket = MagicMock()
    ticket.status = "CLOSED"
    ticket.solution = "Fixed"
    ticket.ticket_no = None

    with patch(
        "app.services.knowledge_auto_identification_service.auto_extract_knowledge_from_ticket",
        return_value=None
    ):
        db.query.return_value.filter.return_value.first.return_value = ticket
        svc = KnowledgeAutoIdentificationService(db)
        result = svc.identify_from_service_ticket(1)
        assert result is None
