# -*- coding: utf-8 -*-
"""Tests for project/resource_service.py"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestProjectResourceService:
    def setup_method(self):
        self.db = MagicMock()

    def test_init(self):
        from app.services.project.resource_service import ProjectResourceService
        svc = ProjectResourceService(self.db)
        assert svc.db == self.db

    def test_init_with_core_service(self):
        from app.services.project.resource_service import ProjectResourceService
        core = MagicMock()
        svc = ProjectResourceService(self.db, core_service=core)
        assert svc.core_service == core

    def test_normalize_range(self):
        from app.services.project.resource_service import ProjectResourceService
        svc = ProjectResourceService(self.db)
        start, end = svc._normalize_range(date(2024, 3, 15), date(2024, 3, 20))
        assert isinstance(start, date)
        assert isinstance(end, date)
        assert start <= end
