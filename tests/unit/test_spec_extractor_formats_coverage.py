from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.utils.spec_extractor import formats


class FakeCell:
    def __init__(self, value):
        self.value = value


class FakeWorksheet:
    def __init__(self, rows):
        self._rows = {index + 1: [FakeCell(value) for value in row] for index, row in enumerate(rows)}
        self.max_row = len(rows)

    def __getitem__(self, index):
        return self._rows[index]


class FakeWorkbook:
    def __init__(self, rows):
        self.active = FakeWorksheet(rows)


def install_module(monkeypatch, name, **attrs):
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    monkeypatch.setitem(__import__("sys").modules, name, module)
    return module


@pytest.mark.unit
def test_extract_from_excel_reads_headers_skips_invalid_rows_and_commits(monkeypatch, tmp_path):
    workbook = FakeWorkbook(
        [
            ["物料编码", "物料名称", "规格", "品牌", "型号"],
            ["MC-1", "传感器", "24V", "BrandA", "ModelX"],
            ["MC-2", " ", "ignored", "BrandB", "ModelY"],
            [None, "控制器", None, None, None],
        ]
    )
    install_module(monkeypatch, "openpyxl", load_workbook=lambda *_args, **_kwargs: workbook)

    db = MagicMock()
    create_requirement = MagicMock(side_effect=[{"id": 1}, {"id": 2}])
    monkeypatch.setattr(formats, "create_requirement", create_requirement)

    requirements = formats.extract_from_excel(
        service=object(),
        db=db,
        file_path=tmp_path / "spec.xlsx",
        project_id=10,
        document_id=20,
        extracted_by=30,
    )

    assert requirements == [{"id": 1}, {"id": 2}]
    assert create_requirement.call_count == 2
    first_call = create_requirement.call_args_list[0].kwargs
    assert first_call["material_name"] == "传感器"
    assert first_call["specification"] == "24V"
    assert first_call["material_code"] == "MC-1"
    assert first_call["brand"] == "BrandA"
    assert first_call["model"] == "ModelX"

    second_call = create_requirement.call_args_list[1].kwargs
    assert second_call["material_name"] == "控制器"
    assert second_call["specification"] == "控制器"
    assert second_call["material_code"] is None
    assert second_call["brand"] is None
    assert second_call["model"] is None
    db.commit.assert_called_once()


@pytest.mark.unit
def test_extract_from_excel_raises_import_error_when_dependency_missing(monkeypatch, tmp_path):
    monkeypatch.setitem(__import__("sys").modules, "openpyxl", None)

    with pytest.raises(ImportError, match="需要安装 openpyxl"):
        formats.extract_from_excel(object(), MagicMock(), tmp_path / "missing.xlsx", 1, 2, 3)


@pytest.mark.unit
def test_extract_from_excel_wraps_unexpected_errors(monkeypatch, tmp_path):
    install_module(monkeypatch, "openpyxl", load_workbook=lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad workbook")))

    with pytest.raises(Exception, match="Excel解析失败: bad workbook"):
        formats.extract_from_excel(object(), MagicMock(), tmp_path / "broken.xlsx", 1, 2, 3)


@pytest.mark.unit
def test_extract_from_excel_skips_rows_when_material_name_header_is_missing(monkeypatch, tmp_path):
    workbook = FakeWorkbook([["物料编码", "规格"], ["MC-1", "24V"]])
    install_module(monkeypatch, "openpyxl", load_workbook=lambda *_args, **_kwargs: workbook)

    db = MagicMock()
    create_requirement = MagicMock()
    monkeypatch.setattr(formats, "create_requirement", create_requirement)

    assert formats.extract_from_excel(object(), db, tmp_path / "no_name.xlsx", 1, 2, 3) == []
    create_requirement.assert_not_called()
    db.commit.assert_called_once()


@pytest.mark.unit
def test_extract_from_word_extracts_table_rows_and_falls_back_to_empty_paragraph_scan(monkeypatch, tmp_path):
    header = SimpleNamespace(cells=[SimpleNamespace(text=text) for text in ["物料编码", "物料名称", "规格", "品牌", "型号"]])
    data = SimpleNamespace(cells=[SimpleNamespace(text=text) for text in ["M-1", "伺服电机", "750W", "BrandB", "Mdl-7"]])
    missing_name = SimpleNamespace(cells=[SimpleNamespace(text=text) for text in ["M-2", "", "", "", ""]])

    document_with_table = SimpleNamespace(
        tables=[SimpleNamespace(rows=[header, data, missing_name])],
        paragraphs=[SimpleNamespace(text="ignored")],
    )
    install_module(monkeypatch, "docx", Document=lambda *_args, **_kwargs: document_with_table)

    db = MagicMock()
    create_requirement = MagicMock(return_value={"id": 9})
    monkeypatch.setattr(formats, "create_requirement", create_requirement)

    requirements = formats.extract_from_word(object(), db, tmp_path / "spec.docx", 5, 6, 7)

    assert requirements == [{"id": 9}]
    assert create_requirement.call_args.kwargs["material_name"] == "伺服电机"
    assert create_requirement.call_args.kwargs["specification"] == "750W"
    assert create_requirement.call_args.kwargs["brand"] == "BrandB"
    assert create_requirement.call_args.kwargs["model"] == "Mdl-7"
    db.commit.assert_called_once()

    empty_doc = SimpleNamespace(tables=[], paragraphs=[SimpleNamespace(text="无可提取内容")])
    monkeypatch.setitem(__import__("sys").modules, "docx", ModuleType("docx"))
    __import__("sys").modules["docx"].Document = lambda *_args, **_kwargs: empty_doc
    db = MagicMock()
    create_requirement.reset_mock()

    assert formats.extract_from_word(object(), db, tmp_path / "empty.docx", 5, 6, 7) == []
    create_requirement.assert_not_called()
    db.commit.assert_called_once()

    no_name_header_doc = SimpleNamespace(
        tables=[
            SimpleNamespace(
                rows=[
                    SimpleNamespace(cells=[SimpleNamespace(text="规格"), SimpleNamespace(text="品牌")]),
                    SimpleNamespace(cells=[SimpleNamespace(text="24V"), SimpleNamespace(text="BrandC")]),
                ]
            )
        ],
        paragraphs=[],
    )
    monkeypatch.setitem(__import__("sys").modules, "docx", ModuleType("docx"))
    __import__("sys").modules["docx"].Document = lambda *_args, **_kwargs: no_name_header_doc
    db = MagicMock()
    create_requirement.reset_mock()

    assert formats.extract_from_word(object(), db, tmp_path / "no_name.docx", 5, 6, 7) == []
    create_requirement.assert_not_called()
    db.commit.assert_called_once()


@pytest.mark.unit
def test_extract_from_word_raises_import_error_and_wraps_generic_error(monkeypatch, tmp_path):
    monkeypatch.setitem(__import__("sys").modules, "docx", None)
    with pytest.raises(ImportError, match="需要安装 python-docx"):
        formats.extract_from_word(object(), MagicMock(), tmp_path / "missing.docx", 1, 2, 3)

    install_module(monkeypatch, "docx", Document=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(Exception, match="Word解析失败: boom"):
        formats.extract_from_word(object(), MagicMock(), tmp_path / "broken.docx", 1, 2, 3)


@pytest.mark.unit
def test_extract_from_pdf_parses_material_lines_and_commits(monkeypatch, tmp_path):
    pdf_path = tmp_path / "spec.pdf"
    pdf_path.write_bytes(b"pdf")

    reader = lambda _file: SimpleNamespace(
        pages=[
            SimpleNamespace(extract_text=lambda: "物料 传感器 24V\n无关内容\n零件 电机 380V"),
            SimpleNamespace(extract_text=lambda: "材料 A\n材料 控制器 Modbus"),
        ]
    )
    install_module(monkeypatch, "pypdf", PdfReader=reader)

    db = MagicMock()
    create_requirement = MagicMock(side_effect=[{"id": 1}, {"id": 2}, {"id": 3}])
    monkeypatch.setattr(formats, "create_requirement", create_requirement)

    requirements = formats.extract_from_pdf(object(), db, pdf_path, 9, 10, 11)

    assert requirements == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [call.kwargs["material_name"] for call in create_requirement.call_args_list] == [
        "传感器",
        "电机",
        "控制器",
    ]
    assert create_requirement.call_args_list[0].kwargs["specification"] == "传感器 24V"
    db.commit.assert_called_once()


@pytest.mark.unit
def test_extract_from_pdf_raises_import_error_and_wraps_generic_error(monkeypatch, tmp_path):
    pdf_path = tmp_path / "bad.pdf"
    pdf_path.write_bytes(b"pdf")

    monkeypatch.setitem(__import__("sys").modules, "pypdf", None)
    with pytest.raises(ImportError, match="需要安装 pypdf"):
        formats.extract_from_pdf(object(), MagicMock(), pdf_path, 1, 2, 3)

    install_module(monkeypatch, "pypdf", PdfReader=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("read failed")))
    with pytest.raises(Exception, match="PDF解析失败: read failed"):
        formats.extract_from_pdf(object(), MagicMock(), pdf_path, 1, 2, 3)
