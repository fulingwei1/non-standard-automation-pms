# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestTableSlideBuilder:
    @patch("app.services.ppt_generator.table_builder.BaseSlideBuilder", autospec=True)
    def test_format_table_header(self, mock_base):
        from app.services.ppt_generator.table_builder import TableSlideBuilder
        builder = MagicMock(spec=TableSlideBuilder)
        builder.config = MagicMock()
        builder.config.DARK_BLUE = MagicMock()
        builder.config.WHITE = MagicMock()
        builder.config.TABLE_HEADER_FONT_SIZE = MagicMock()

        table = MagicMock()
        headers = ["Name", "Value"]
        TableSlideBuilder._format_table_header(builder, table, headers)
        assert table.cell.call_count == 2

    @patch("app.services.ppt_generator.table_builder.BaseSlideBuilder", autospec=True)
    def test_format_table_rows(self, mock_base):
        from app.services.ppt_generator.table_builder import TableSlideBuilder
        builder = MagicMock(spec=TableSlideBuilder)
        builder.config = MagicMock()
        builder.config.LIGHT_BLUE = MagicMock()
        builder.config.DARK_BLUE = MagicMock()
        builder.config.TABLE_CELL_FONT_SIZE = MagicMock()

        table = MagicMock()
        rows = [["a", "b"], ["c", "d"]]
        TableSlideBuilder._format_table_rows(builder, table, rows)
        assert table.cell.call_count == 4
