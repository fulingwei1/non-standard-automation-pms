"""
PPT生成器主类 - 统一管理幻灯片生成流程
"""

from typing import Any, Dict, List, Optional

from .compat import MissingPptxDependencyError, PPTX_AVAILABLE, Presentation, PP_ALIGN, Inches, Pt

from .base_builder import BaseSlideBuilder
from .config import PresentationConfig
from .content_builder import ContentSlideBuilder
from .table_builder import TableSlideBuilder


class PresentationGenerator:
    """PPT生成器主类"""

    def __init__(self):
        if not PPTX_AVAILABLE:
            raise MissingPptxDependencyError(
                "python-pptx 未安装，无法使用 PPT 生成功能。请安装 api/requirements.txt 中声明的 python-pptx>=0.6.21"
            )
        self.prs = Presentation()
        self.prs.slide_width = PresentationConfig.SLIDE_WIDTH
        self.prs.slide_height = PresentationConfig.SLIDE_HEIGHT

        self.base_builder = BaseSlideBuilder(self.prs)
        self.content_builder = ContentSlideBuilder(self.prs)
        self.table_builder = TableSlideBuilder(self.prs)
        self.config = PresentationConfig()

    def create_cover_slide(
        self, title: str, subtitle: str = "", slogan: Optional[str] = None
    ):
        """创建封面。所有文字必须由调用方传入。"""
        slide = self.base_builder.add_title_slide(title, subtitle)
        if slogan:
            slogan_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(9), Inches(0.5))
            p = slogan_box.text_frame.paragraphs[0]
            p.text = slogan
            p.font.size = Pt(18)
            p.font.italic = True
            p.font.color.rgb = self.config.SILVER
            p.alignment = PP_ALIGN.CENTER
        return slide

    def create_toc_slide(self, toc_items: List[str], page_num: int = 2):
        """创建目录页。"""
        if not toc_items:
            return None
        return self.content_builder.add_content_slide(
            "内容导览",
            [{"text": item, "size": 24, "bold": True} for item in toc_items],
            page_num=page_num,
        )

    def create_content_slide(self, title: str, content: List[Any], page_num: int):
        """创建内容页。"""
        return self.content_builder.add_content_slide(title, content, page_num=page_num)

    def create_table_slide(
        self, title: str, headers: List[str], rows: List[List[Any]], page_num: int
    ):
        """创建表格页。"""
        return self.table_builder.add_table_slide(title, headers, rows, page_num=page_num)

    def create_section_slide(self, title: str, subtitle: str = ""):
        """创建章节页。"""
        return self.base_builder.add_section_slide(title, subtitle)

    def generate(self, output_path: str = "完整PPT.pptx", deck_spec: Optional[Dict[str, Any]] = None):
        """
        根据外部传入的 deck_spec 生成 PPT。

        Args:
            output_path: 输出文件路径
            deck_spec: PPT 内容定义，必须显式传入，避免生成硬编码演示内容

        Returns:
            输出文件路径
        """
        deck = self._validate_deck_spec(deck_spec)
        self.create_cover_slide(
            deck["title"],
            deck.get("subtitle", ""),
            deck.get("slogan"),
        )

        page_num = 2
        toc_items = self._resolve_toc_items(deck)
        if toc_items:
            self.create_toc_slide(toc_items, page_num=page_num)
            page_num += 1

        for slide_spec in deck["slides"]:
            slide_type = slide_spec.get("type", "content")
            title = slide_spec.get("title")
            if not title:
                raise ValueError("deck_spec.slides[].title 不能为空")

            if slide_type == "section":
                self.create_section_slide(title, slide_spec.get("subtitle", ""))
            elif slide_type == "content":
                self.create_content_slide(title, slide_spec.get("content", []), page_num=page_num)
            elif slide_type == "table":
                self.create_table_slide(
                    title,
                    slide_spec.get("headers", []),
                    slide_spec.get("rows", []),
                    page_num=page_num,
                )
            else:
                raise ValueError(f"不支持的 PPT slide type: {slide_type}")

            page_num += 1

        self.prs.save(output_path)
        return output_path

    def _validate_deck_spec(self, deck_spec: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if deck_spec is None:
            raise ValueError("PPT 生成需要显式传入 deck_spec，避免输出硬编码演示内容")
        if not isinstance(deck_spec, dict):
            raise ValueError("deck_spec 必须是 dict")
        if not deck_spec.get("title"):
            raise ValueError("deck_spec.title 不能为空")
        slides = deck_spec.get("slides")
        if not isinstance(slides, list):
            raise ValueError("deck_spec.slides 必须是 list")
        return deck_spec

    def _resolve_toc_items(self, deck: Dict[str, Any]) -> List[str]:
        if deck.get("include_toc") is False:
            return []
        if "toc" in deck:
            toc = deck.get("toc") or []
            if not isinstance(toc, list):
                raise ValueError("deck_spec.toc 必须是 list")
            return [str(item) for item in toc]
        return [str(slide["title"]) for slide in deck["slides"] if slide.get("title")]
