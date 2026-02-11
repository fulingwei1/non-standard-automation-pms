# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch, PropertyMock


class TestContentSlideBuilder:
    def setup_method(self):
        with patch("app.services.ppt_generator.content_builder.BaseSlideBuilder.__init__", return_value=None):
            from app.services.ppt_generator.content_builder import ContentSlideBuilder
            self.builder = ContentSlideBuilder.__new__(ContentSlideBuilder)
            self.builder.prs = MagicMock()
            self.builder.config = MagicMock()
            self.builder.config.CONTENT_FONT_SIZE = MagicMock()
            self.builder.config.DARK_BLUE = MagicMock()
            self.builder._add_white_background = MagicMock()
            self.builder._add_top_bar = MagicMock()
            self.builder._add_slide_title = MagicMock()
            self.builder._add_page_number = MagicMock()

    def _mock_slide(self):
        slide = MagicMock()
        tf = MagicMock()
        p0 = MagicMock()
        tf.paragraphs = [p0]
        tf.add_paragraph.return_value = MagicMock()
        textbox = MagicMock()
        textbox.text_frame = tf
        slide.shapes.add_textbox.return_value = textbox
        self.builder.prs.slide_layouts = [MagicMock() for _ in range(7)]
        self.builder.prs.slides.add_slide.return_value = slide
        return slide

    def test_add_content_slide_string_items(self):
        self._mock_slide()
        result = self.builder.add_content_slide("Title", ["item1", "item2"])
        assert result is not None

    def test_add_content_slide_dict_items(self):
        self._mock_slide()
        items = [{"text": "bold", "size": 20, "bold": True, "color": MagicMock(), "level": 1}]
        result = self.builder.add_content_slide("Title", items, page_num=1)
        self.builder._add_page_number.assert_called_once()

    def test_add_two_column_slide(self):
        self._mock_slide()
        result = self.builder.add_two_column_slide("Title", ["left"], ["right"], page_num=2)
        assert result is not None
        self.builder._add_page_number.assert_called_once()

    def test_fill_textbox(self):
        textbox = MagicMock()
        tf = MagicMock()
        tf.paragraphs = [MagicMock()]
        tf.add_paragraph.return_value = MagicMock()
        textbox.text_frame = tf
        self.builder._fill_textbox(textbox, ["a", "b"])
