"""Compatibility imports for PPT slide builders."""

from app.services.ppt_generator.base_builder import BaseSlideBuilder
from app.services.ppt_generator.content_builder import ContentSlideBuilder
from app.services.ppt_generator.table_builder import TableSlideBuilder

__all__ = ["BaseSlideBuilder", "ContentSlideBuilder", "TableSlideBuilder"]
