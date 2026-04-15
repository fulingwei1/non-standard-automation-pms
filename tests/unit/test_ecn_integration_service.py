# -*- coding: utf-8 -*-
"""Compatibility tests for the historical ECN integration test path."""

import unittest
from unittest.mock import MagicMock, patch

from app.services.ecn_integration.ecn_integration_service import EcnIntegrationService


class TestEcnIntegrationService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = EcnIntegrationService(self.db)

    @patch("app.services.ecn.integration.ecn_integration_service.get_or_404")
    def test_sync_to_bom_success(self, mock_get_or_404):
        mock_get_or_404.return_value = MagicMock(status="APPROVED")

        affected_material = MagicMock(
            bom_item_id=10,
            change_type="UPDATE",
            new_quantity=5,
            new_specification="新规格",
        )
        bom_item = MagicMock(qty=1, specification="旧规格")

        affected_query = MagicMock()
        affected_query.filter.return_value.all.return_value = [affected_material]

        bom_query = MagicMock()
        bom_query.filter.return_value.first.return_value = bom_item

        self.db.query.side_effect = [affected_query, bom_query]

        result = self.service.sync_to_bom(ecn_id=1)

        self.assertEqual(result, {"updated_count": 1})
        self.assertEqual(bom_item.qty, 5.0)
        self.assertEqual(bom_item.specification, "新规格")
        self.assertEqual(affected_material.status, "PROCESSED")
        self.assertIsNotNone(affected_material.processed_at)
        self.db.commit.assert_called_once()

    @patch("app.services.ecn.integration.ecn_integration_service.get_or_404")
    def test_sync_to_purchase_success(self, mock_get_or_404):
        mock_get_or_404.return_value = MagicMock()

        affected_order = MagicMock(order_id=42, action_type="CANCEL")
        purchase_order = MagicMock(status="OPEN")

        affected_query = MagicMock()
        affected_query.filter.return_value.all.return_value = [affected_order]

        purchase_query = MagicMock()
        purchase_query.filter.return_value.first.return_value = purchase_order

        self.db.query.side_effect = [affected_query, purchase_query]

        result = self.service.sync_to_purchase(ecn_id=1, current_user_id=7)

        self.assertEqual(result, {"updated_count": 1})
        self.assertEqual(purchase_order.status, "CANCELLED")
        self.assertEqual(affected_order.status, "PROCESSED")
        self.assertEqual(affected_order.processed_by, 7)
        self.assertIsNotNone(affected_order.processed_at)
        self.db.commit.assert_called_once()
