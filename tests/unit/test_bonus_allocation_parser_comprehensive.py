# -*- coding: utf-8 -*-
"""
bonus_allocation_parser 综合单元测试

测试覆盖:
- validate_file_type: 验证文件类型
- save_uploaded_file: 保存上传文件
- parse_excel_file: 解析Excel文件
- validate_required_columns: 验证必需的列
- get_column_value: 获取列值
- parse_row_data: 解析单行数据
- parse_date: 解析日期
- validate_row_data: 验证行数据
- parse_allocation_sheet: 解析整个分配表
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi import HTTPException


class TestValidateFileType:
    """测试 validate_file_type 函数"""

    def test_accepts_xlsx_file(self):
        """测试接受xlsx文件"""
        from app.services.bonus_allocation_parser import validate_file_type

        # 不应抛出异常
        validate_file_type("test.xlsx")

    def test_accepts_xls_file(self):
        """测试接受xls文件"""
        from app.services.bonus_allocation_parser import validate_file_type

        # 不应抛出异常
        validate_file_type("test.xls")

    def test_rejects_csv_file(self):
        """测试拒绝csv文件"""
        from app.services.bonus_allocation_parser import validate_file_type

        with pytest.raises(HTTPException) as exc_info:
            validate_file_type("test.csv")

        assert exc_info.value.status_code == 400
        assert "只支持Excel文件" in exc_info.value.detail

    def test_rejects_txt_file(self):
        """测试拒绝txt文件"""
        from app.services.bonus_allocation_parser import validate_file_type

        with pytest.raises(HTTPException):
            validate_file_type("test.txt")

    def test_rejects_no_extension(self):
        """测试拒绝无扩展名文件"""
        from app.services.bonus_allocation_parser import validate_file_type

        with pytest.raises(HTTPException):
            validate_file_type("testfile")


class TestSaveUploadedFile:
    """测试 save_uploaded_file 函数"""

    def test_returns_file_paths(self):
        """测试返回文件路径"""
        from app.services.bonus_allocation_parser import save_uploaded_file

        mock_file = MagicMock()
        mock_file.filename = "test.xlsx"

        with patch('os.makedirs'):
            file_path, relative_path, file_size = save_uploaded_file(mock_file)

            assert file_path.endswith(".xlsx")
            assert "bonus_allocation_sheets" in file_path

    def test_creates_unique_filename(self):
        """测试创建唯一文件名"""
        from app.services.bonus_allocation_parser import save_uploaded_file

        mock_file = MagicMock()
        mock_file.filename = "test.xlsx"

        with patch('os.makedirs'):
            file_path1, _, _ = save_uploaded_file(mock_file)
            file_path2, _, _ = save_uploaded_file(mock_file)

            # 两次调用应生成不同的文件名
            assert file_path1 != file_path2


class TestParseExcelFile:
    """测试 parse_excel_file 函数"""

    def test_parses_valid_excel(self):
        """测试解析有效Excel"""
        from app.services.bonus_allocation_parser import parse_excel_file

        # 创建模拟Excel内容
        df = pd.DataFrame({
            '计算记录ID*': [1, 2],
            '受益人ID*': [10, 20],
            '发放金额*': [1000, 2000],
            '发放日期*': ['2026-01-15', '2026-01-16']
        })

        import io
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        content = buffer.read()

        result = parse_excel_file(content)

        assert len(result) == 2
        assert '计算记录ID*' in result.columns

    def test_drops_empty_rows(self):
        """测试删除空行"""
        from app.services.bonus_allocation_parser import parse_excel_file

        df = pd.DataFrame({
            'A': [1, None, 3],
            'B': [10, None, 30]
        })

        import io
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        content = buffer.read()

        result = parse_excel_file(content)

        # 空行应被删除
        assert len(result) == 2

    def test_raises_error_for_invalid_content(self):
        """测试无效内容抛出异常"""
        from app.services.bonus_allocation_parser import parse_excel_file

        with pytest.raises(HTTPException) as exc_info:
            parse_excel_file(b"invalid content")

        assert exc_info.value.status_code == 400
        assert "解析失败" in exc_info.value.detail


class TestValidateRequiredColumns:
    """测试 validate_required_columns 函数"""

    def test_accepts_valid_columns_with_calc_id(self):
        """测试接受有计算记录ID的列"""
        from app.services.bonus_allocation_parser import validate_required_columns

        df = pd.DataFrame({
            '计算记录ID*': [1],
            '受益人ID*': [10],
            '发放金额*': [1000],
            '发放日期*': ['2026-01-15']
        })

        # 不应抛出异常
        validate_required_columns(df)

    def test_accepts_valid_columns_with_allocation_id(self):
        """测试接受有团队奖金分配ID的列"""
        from app.services.bonus_allocation_parser import validate_required_columns

        df = pd.DataFrame({
            '团队奖金分配ID*': [1],
            '受益人ID*': [10],
            '发放金额*': [1000],
            '发放日期*': ['2026-01-15']
        })

        # 不应抛出异常
        validate_required_columns(df)

    def test_rejects_missing_id_columns(self):
        """测试拒绝缺少ID列"""
        from app.services.bonus_allocation_parser import validate_required_columns

        df = pd.DataFrame({
            '受益人ID*': [10],
            '发放金额*': [1000],
            '发放日期*': ['2026-01-15']
        })

        with pytest.raises(HTTPException) as exc_info:
            validate_required_columns(df)

        assert "计算记录ID" in exc_info.value.detail or "团队奖金分配ID" in exc_info.value.detail

    def test_rejects_missing_required_columns(self):
        """测试拒绝缺少必需列"""
        from app.services.bonus_allocation_parser import validate_required_columns

        df = pd.DataFrame({
            '计算记录ID*': [1],
            '受益人ID*': [10]
            # 缺少发放金额和发放日期
        })

        with pytest.raises(HTTPException) as exc_info:
            validate_required_columns(df)

        assert "缺少必需的列" in exc_info.value.detail


class TestGetColumnValue:
    """测试 get_column_value 函数"""

    def test_gets_value_with_asterisk(self):
        """测试获取带*的列值"""
        from app.services.bonus_allocation_parser import get_column_value

        row = pd.Series({'计算记录ID*': 123})

        result = get_column_value(row, '计算记录ID*')

        assert result == 123

    def test_gets_value_without_asterisk(self):
        """测试获取不带*的列值"""
        from app.services.bonus_allocation_parser import get_column_value

        row = pd.Series({'计算记录ID': 456})

        result = get_column_value(row, '计算记录ID*')

        assert result == 456

    def test_prefers_asterisk_column(self):
        """测试优先使用带*的列"""
        from app.services.bonus_allocation_parser import get_column_value

        row = pd.Series({'计算记录ID*': 100, '计算记录ID': 200})

        result = get_column_value(row, '计算记录ID*')

        assert result == 100

    def test_returns_none_for_missing_column(self):
        """测试缺少列时返回None"""
        from app.services.bonus_allocation_parser import get_column_value

        row = pd.Series({'其他列': 999})

        result = get_column_value(row, '计算记录ID*')

        assert result is None


class TestParseDate:
    """测试 parse_date 函数"""

    def test_parses_string_date(self):
        """测试解析字符串日期"""
        from app.services.bonus_allocation_parser import parse_date

        result = parse_date('2026-01-15')

        assert result == date(2026, 1, 15)

    def test_parses_datetime_object(self):
        """测试解析datetime对象"""
        from app.services.bonus_allocation_parser import parse_date

        dt = datetime(2026, 1, 15, 10, 30)
        result = parse_date(dt)

        assert result == date(2026, 1, 15)

    def test_parses_pandas_timestamp(self):
        """测试解析pandas时间戳"""
        from app.services.bonus_allocation_parser import parse_date

        ts = pd.Timestamp('2026-01-15')
        result = parse_date(ts)

        assert result == date(2026, 1, 15)


class TestValidateRowData:
    """测试 validate_row_data 函数"""

    def test_returns_empty_for_valid_data(self):
        """测试有效数据返回空错误列表"""
        from app.services.bonus_allocation_parser import validate_row_data

        mock_db = MagicMock()

        mock_calculation = MagicMock()
        mock_user = MagicMock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_calculation, mock_user
        ]

        errors = validate_row_data(
            mock_db, calc_id=1, team_allocation_id=None,
            user_id=10, calc_amount=Decimal("1000"), dist_amount=Decimal("1000")
        )

        assert errors == []

    def test_validates_team_allocation_id(self):
        """测试验证团队奖金分配ID"""
        from app.services.bonus_allocation_parser import validate_row_data

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        errors = validate_row_data(
            mock_db, calc_id=None, team_allocation_id=999,
            user_id=10, calc_amount=Decimal("1000"), dist_amount=Decimal("1000")
        )

        assert any("团队奖金分配ID" in e for e in errors)

    def test_validates_calculation_id(self):
        """测试验证计算记录ID"""
        from app.services.bonus_allocation_parser import validate_row_data

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        errors = validate_row_data(
            mock_db, calc_id=999, team_allocation_id=None,
            user_id=10, calc_amount=Decimal("1000"), dist_amount=Decimal("1000")
        )

        assert any("计算记录ID" in e for e in errors)

    def test_validates_user_id(self):
        """测试验证受益人ID"""
        from app.services.bonus_allocation_parser import validate_row_data

        mock_db = MagicMock()

        mock_calculation = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_calculation, None  # calculation exists, user doesn't
        ]

        errors = validate_row_data(
            mock_db, calc_id=1, team_allocation_id=None,
            user_id=999, calc_amount=Decimal("1000"), dist_amount=Decimal("1000")
        )

        assert any("受益人ID" in e for e in errors)


class TestParseRowData:
    """测试 parse_row_data 函数"""

    def test_parses_valid_row(self):
        """测试解析有效行"""
        from app.services.bonus_allocation_parser import parse_row_data

        mock_db = MagicMock()
        mock_calculation = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_calculation, mock_user
        ]

        row = pd.Series({
            '计算记录ID*': 1,
            '受益人ID*': 10,
            '计算金额*': 1000,
            '发放金额*': 1000,
            '发放日期*': '2026-01-15'
        })

        data, errors = parse_row_data(row, 2, mock_db)

        assert errors == []
        assert data['calculation_id'] == 1
        assert data['user_id'] == 10
        assert data['distributed_amount'] == 1000.0

    def test_returns_errors_for_invalid_row(self):
        """测试无效行返回错误"""
        from app.services.bonus_allocation_parser import parse_row_data

        mock_db = MagicMock()

        row = pd.Series({
            '计算记录ID*': None,
            '团队奖金分配ID*': None,
            '受益人ID*': None,
            '发放金额*': None,
            '发放日期*': None
        })

        data, errors = parse_row_data(row, 2, mock_db)

        assert len(errors) > 0
        assert data is None


class TestParseAllocationSheet:
    """测试 parse_allocation_sheet 函数"""

    def test_parses_valid_sheet(self):
        """测试解析有效表格"""
        from app.services.bonus_allocation_parser import parse_allocation_sheet

        mock_db = MagicMock()
        mock_calculation = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_calculation, mock_user,
            mock_calculation, mock_user
        ]

        df = pd.DataFrame({
            '计算记录ID*': [1, 2],
            '受益人ID*': [10, 20],
            '计算金额*': [1000, 2000],
            '发放金额*': [1000, 2000],
            '发放日期*': ['2026-01-15', '2026-01-16']
        })

        valid_rows, errors = parse_allocation_sheet(df, mock_db)

        assert len(valid_rows) == 2
        assert len(errors) == 0

    def test_collects_errors_by_row(self):
        """测试按行收集错误"""
        from app.services.bonus_allocation_parser import parse_allocation_sheet

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        df = pd.DataFrame({
            '计算记录ID*': [1, None],
            '受益人ID*': [None, 20],
            '发放金额*': [1000, 2000],
            '发放日期*': ['2026-01-15', '2026-01-16']
        })

        valid_rows, errors = parse_allocation_sheet(df, mock_db)

        # 两行都有错误
        assert len(errors) > 0

    def test_handles_empty_dataframe(self):
        """测试处理空数据框"""
        from app.services.bonus_allocation_parser import parse_allocation_sheet

        mock_db = MagicMock()

        df = pd.DataFrame()

        valid_rows, errors = parse_allocation_sheet(df, mock_db)

        assert valid_rows == []
        assert errors == {}
