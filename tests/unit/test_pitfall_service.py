# -*- coding: utf-8 -*-
"""Tests for pitfall/pitfall_service.py"""
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestPitfallService:

    def _make_service(self):
        from app.services.pitfall.pitfall_service import PitfallService
        db = MagicMock()
        return PitfallService(db), db

    def test_generate_pitfall_no_first(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        no = svc.generate_pitfall_no()
        today = datetime.now()
        prefix = f"PF{today.strftime('%y%m%d')}"
        assert no == f"{prefix}001"

    def test_generate_pitfall_no_increment(self):
        svc, db = self._make_service()
        existing = MagicMock()
        today = datetime.now()
        prefix = f"PF{today.strftime('%y%m%d')}"
        existing.pitfall_no = f"{prefix}005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing
        no = svc.generate_pitfall_no()
        assert no == f"{prefix}006"

    @patch("app.services.pitfall.pitfall_service.PitfallService.generate_pitfall_no", return_value="PF240101001")
    def test_create_pitfall(self, mock_gen):
        svc, db = self._make_service()
        pitfall_mock = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = svc.create_pitfall(
            title="测试坑点",
            description="描述",
            created_by=1
        )
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_get_pitfall_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_pitfall(99, user_id=1)
        assert result is None

    def test_get_pitfall_sensitive_denied(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.is_sensitive = True
        pitfall.created_by = 2
        pitfall.visible_to = [3, 4]
        db.query.return_value.filter.return_value.first.return_value = pitfall
        result = svc.get_pitfall(1, user_id=1, is_admin=False)
        assert result is None

    def test_get_pitfall_sensitive_admin(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.is_sensitive = True
        pitfall.created_by = 2
        db.query.return_value.filter.return_value.first.return_value = pitfall
        result = svc.get_pitfall(1, user_id=1, is_admin=True)
        assert result == pitfall

    def test_get_pitfall_sensitive_creator(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.is_sensitive = True
        pitfall.created_by = 1
        db.query.return_value.filter.return_value.first.return_value = pitfall
        result = svc.get_pitfall(1, user_id=1, is_admin=False)
        assert result == pitfall

    @patch("app.services.pitfall.pitfall_service.apply_keyword_filter")
    @patch("app.services.pitfall.pitfall_service.apply_pagination")
    def test_list_pitfalls(self, mock_pag, mock_kw):
        svc, db = self._make_service()
        q = MagicMock()
        db.query.return_value = q
        q.filter.return_value = q
        mock_kw.return_value = q
        q.count.return_value = 0
        mock_pag.return_value.all.return_value = []
        q.order_by.return_value = q

        result, total = svc.list_pitfalls(user_id=1)
        assert total == 0
        assert result == []

    def test_publish_pitfall_not_found(self):
        svc, db = self._make_service()
        with patch.object(svc, "get_pitfall", return_value=None):
            result = svc.publish_pitfall(99, user_id=1)
            assert result is None

    def test_publish_pitfall_wrong_user(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.created_by = 2
        with patch.object(svc, "get_pitfall", return_value=pitfall):
            result = svc.publish_pitfall(1, user_id=1)
            assert result is None

    def test_publish_pitfall_success(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.created_by = 1
        with patch.object(svc, "get_pitfall", return_value=pitfall):
            result = svc.publish_pitfall(1, user_id=1)
            assert pitfall.status == "PUBLISHED"
            db.commit.assert_called()

    def test_verify_pitfall(self):
        svc, db = self._make_service()
        pitfall = MagicMock()
        pitfall.verify_count = 2
        db.query.return_value.filter.return_value.first.return_value = pitfall
        result = svc.verify_pitfall(1)
        assert pitfall.verified is True
        assert pitfall.verify_count == 3

    def test_verify_pitfall_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.verify_pitfall(99)
        assert result is None
