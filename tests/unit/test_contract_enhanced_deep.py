# -*- coding: utf-8 -*-
"""contract_enhanced 深度测试"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.sales.contract_enhanced import ContractEnhancedService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, count_value=0):
        self._first_value = first_value
        self._all_value = all_value or []
        self._count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value

    def count(self):
        return self._count_value


class DummySchema:
    def __init__(self, data):
        self.__dict__.update(data)

    def model_dump(self, **kwargs):
        data = dict(self.__dict__)
        if kwargs.get("exclude"):
            for key in kwargs["exclude"]:
                data.pop(key, None)
        if kwargs.get("exclude_unset"):
            return {k: v for k, v in data.items() if v is not None}
        return data


class DummyTerm:
    def __init__(self, data):
        self.data = data

    def model_dump(self):
        return dict(self.data)


class FakeContract:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = kwargs.get("id")


class FakeContractTerm:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestContractEnhancedDeep:
    def test_generate_contract_code_with_and_without_existing(self):
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=SimpleNamespace(contract_code="HT-20260412-007")),
            FakeQuery(first_value=None),
        ]

        with patch("app.services.sales.contract_enhanced.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 12, 10, 0, 0)
            mock_dt.strftime = datetime.strftime
            code1 = ContractEnhancedService._generate_contract_code(db)
            code2 = ContractEnhancedService._generate_contract_code(db)

        assert code1 == "HT-20260412-008"
        assert code2 == "HT-20260412-001"

    def test_create_contract_with_auto_code_and_terms(self):
        db = Mock()
        added = []

        def add(obj):
            if getattr(obj, "id", None) is None:
                obj.id = len(added) + 1
            added.append(obj)

        db.add.side_effect = add
        data = DummySchema({
            "contract_code": None,
            "contract_name": "合同A",
            "total_amount": 1000,
            "received_amount": 200,
            "terms": [DummyTerm({"term_type": "pay", "term_content": "款到发货"})],
        })

        with patch("app.services.sales.contract_enhanced.Contract", FakeContract), \
             patch("app.services.sales.contract_enhanced.ContractTerm", FakeContractTerm), \
             patch.object(ContractEnhancedService, "_generate_contract_code", return_value="HT-20260412-001"):
            contract = ContractEnhancedService.create_contract(db, data, user_id=8)

        assert contract.contract_code == "HT-20260412-001"
        assert contract.unreceived_amount == 800
        assert contract.status == "draft"
        assert len(added) == 2
        assert added[1].contract_id == 1
        assert added[1].term_type == "pay"
        db.flush.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(contract)

    def test_get_contract_and_get_contracts(self):
        db = Mock()
        contract = SimpleNamespace(id=1)
        contracts = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        db.query.side_effect = [
            FakeQuery(first_value=contract),
            FakeQuery(all_value=contracts, count_value=9),
        ]

        detail = ContractEnhancedService.get_contract(db, 1)
        rows, total = ContractEnhancedService.get_contracts(
            db,
            skip=5,
            limit=2,
            status="draft",
            customer_id=3,
            contract_type="sales",
            keyword="HT",
        )

        assert detail is contract
        assert rows == contracts
        assert total == 9

    def test_update_contract_recomputes_unreceived_amount_and_handles_missing(self):
        db = Mock()
        contract = SimpleNamespace(id=1, status="draft", total_amount=1000, received_amount=100, unreceived_amount=900)
        update = DummySchema({"total_amount": 1500, "received_amount": 400, "contract_name": "新合同名"})
        db.query.side_effect = [FakeQuery(first_value=contract), FakeQuery(first_value=None)]

        with patch("app.services.sales.contract_enhanced.assert_status_allows") as allow:
            updated = ContractEnhancedService.update_contract(db, 1, update)
            missing = ContractEnhancedService.update_contract(db, 99, update)

        assert updated is contract
        assert contract.contract_name == "新合同名"
        assert contract.unreceived_amount == 1100
        assert missing is None
        allow.assert_called_once_with(contract, "draft", "只能更新草稿状态的合同")
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(contract)

    def test_delete_contract(self):
        db = Mock()
        contract = SimpleNamespace(id=1, status="draft")
        db.query.side_effect = [FakeQuery(first_value=contract), FakeQuery(first_value=None)]

        with patch("app.services.sales.contract_enhanced.assert_status_allows") as allow, \
             patch("app.services.sales.contract_enhanced.delete_obj") as delete_obj:
            ok = ContractEnhancedService.delete_contract(db, 1)
            missing = ContractEnhancedService.delete_contract(db, 99)

        assert ok is True
        assert missing is False
        allow.assert_called_once_with(contract, "draft", "只能删除草稿状态的合同")
        delete_obj.assert_called_once_with(db, contract)
