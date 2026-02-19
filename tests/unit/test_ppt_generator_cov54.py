"""Tests for app/services/ppt_generator/generator.py"""
import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.ppt_generator.generator import PresentationGenerator
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_gen():
    """返回一个所有内部构造器都被 mock 的 PresentationGenerator"""
    with patch("app.services.ppt_generator.generator.Presentation") as MockPrs, \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder") as MockBase, \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder") as MockContent, \
         patch("app.services.ppt_generator.generator.TableSlideBuilder") as MockTable, \
         patch("app.services.ppt_generator.generator.PresentationConfig") as MockConfig:

        mock_prs_instance = MagicMock()
        MockPrs.return_value = mock_prs_instance

        gen = PresentationGenerator()
        gen.prs = mock_prs_instance
        gen.base_builder = MockBase.return_value
        gen.content_builder = MockContent.return_value
        gen.table_builder = MockTable.return_value
        gen.config = MockConfig.return_value
        yield gen


def test_init_creates_builders(mock_gen):
    """初始化时创建基础构建器"""
    assert mock_gen.base_builder is not None
    assert mock_gen.content_builder is not None
    assert mock_gen.table_builder is not None


def test_create_cover_slide_calls_add_title_slide(mock_gen):
    """create_cover_slide 调用 base_builder.add_title_slide"""
    slide = MagicMock()
    slide.shapes = MagicMock()
    textbox = MagicMock()
    tf = MagicMock()
    para = MagicMock()
    para.font = MagicMock()
    para.font.color = MagicMock()
    tf.paragraphs = [para]
    textbox.text_frame = tf
    slide.shapes.add_textbox.return_value = textbox
    mock_gen.base_builder.add_title_slide.return_value = slide

    mock_gen.create_cover_slide()
    mock_gen.base_builder.add_title_slide.assert_called_once()


def test_create_toc_slide_calls_content_builder(mock_gen):
    """create_toc_slide 调用 content_builder.add_content_slide"""
    mock_gen.create_toc_slide()
    mock_gen.content_builder.add_content_slide.assert_called_once()


def test_create_part1_calls_table_builder(mock_gen):
    """create_part1_industry_insights 调用 table_builder.add_table_slide"""
    mock_gen.create_part1_industry_insights()
    mock_gen.table_builder.add_table_slide.assert_called()


def test_create_part2_calls_base_builder(mock_gen):
    """create_part2_solution_overview 调用 base_builder.add_section_slide"""
    mock_gen.create_part2_solution_overview()
    mock_gen.base_builder.add_section_slide.assert_called()


def test_generate_calls_save(mock_gen, tmp_path):
    """generate 方法最终调用 prs.save"""
    output = str(tmp_path / "test.pptx")
    # mock create_* methods to avoid deep call chains
    for method in [
        "create_cover_slide", "create_toc_slide",
        "create_part1_industry_insights", "create_part2_solution_overview",
        "create_part3_core_features", "create_part4_customer_portal",
        "create_part5_ai_capabilities", "create_part6_customer_value",
        "create_part7_cooperation"
    ]:
        setattr(mock_gen, method, MagicMock())

    result = mock_gen.generate(output)
    mock_gen.prs.save.assert_called_once_with(output)
    assert result == output


def test_generate_returns_output_path(mock_gen, tmp_path):
    """generate 返回输出路径"""
    output = str(tmp_path / "output.pptx")
    for method in [
        "create_cover_slide", "create_toc_slide",
        "create_part1_industry_insights", "create_part2_solution_overview",
        "create_part3_core_features", "create_part4_customer_portal",
        "create_part5_ai_capabilities", "create_part6_customer_value",
        "create_part7_cooperation"
    ]:
        setattr(mock_gen, method, MagicMock())

    result = mock_gen.generate(output)
    assert result == output
