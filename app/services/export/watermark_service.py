# -*- coding: utf-8 -*-
"""
导出水印服务

为导出的 PDF 和 Excel 文档添加水印，包含：
- 操作者信息
- 导出时间
- 系统标识
- 可选的自定义水印文本
"""

import io
import logging
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 尝试导入 PDF 处理库
try:
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab 未安装，PDF 水印功能不可用")

# 尝试导入 PDF 合并库
try:
    from pypdf import PdfReader, PdfWriter

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logger.warning("pypdf 未安装，PDF 水印合并功能不可用")

# 尝试导入 Excel 处理库
try:
    from openpyxl.styles import Alignment, Font

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl 未安装，Excel 水印功能不可用")


class WatermarkConfig:
    """水印配置"""

    def __init__(
        self,
        text: Optional[str] = None,
        operator_name: Optional[str] = None,
        operator_id: Optional[int] = None,
        include_timestamp: bool = True,
        include_system_name: bool = True,
        system_name: str = "非标自动化项目管理系统",
        font_size: int = 36,
        font_color: Tuple[int, int, int] = (200, 200, 200),  # 浅灰色 RGB
        opacity: float = 0.3,
        angle: int = -45,  # 旋转角度
        spacing: int = 150,  # 水印间距
    ):
        self.text = text
        self.operator_name = operator_name
        self.operator_id = operator_id
        self.include_timestamp = include_timestamp
        self.include_system_name = include_system_name
        self.system_name = system_name
        self.font_size = font_size
        self.font_color = font_color
        self.opacity = opacity
        self.angle = angle
        self.spacing = spacing

    def build_watermark_text(self) -> str:
        """构建水印文本"""
        parts = []

        # 自定义文本
        if self.text:
            parts.append(self.text)

        # 操作者信息
        if self.operator_name:
            parts.append(f"操作者: {self.operator_name}")
        elif self.operator_id:
            parts.append(f"用户ID: {self.operator_id}")

        # 时间戳
        if self.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            parts.append(timestamp)

        # 系统名称
        if self.include_system_name:
            parts.append(self.system_name)

        return " | ".join(parts) if parts else "CONFIDENTIAL"


class WatermarkService:
    """水印服务"""

    @staticmethod
    def add_pdf_watermark(
        pdf_content: bytes,
        config: WatermarkConfig,
    ) -> bytes:
        """
        为 PDF 添加水印

        Args:
            pdf_content: 原始 PDF 内容
            config: 水印配置

        Returns:
            添加水印后的 PDF 内容
        """
        if not REPORTLAB_AVAILABLE or not PYPDF_AVAILABLE:
            logger.warning("PDF 水印依赖库不可用，返回原始内容")
            return pdf_content

        try:
            # 读取原始 PDF
            original_pdf = PdfReader(io.BytesIO(pdf_content))
            if len(original_pdf.pages) == 0:
                return pdf_content

            # 获取第一页尺寸作为水印页尺寸
            first_page = original_pdf.pages[0]
            page_width = float(first_page.mediabox.width)
            page_height = float(first_page.mediabox.height)

            # 创建水印 PDF
            watermark_buffer = io.BytesIO()
            c = canvas.Canvas(watermark_buffer, pagesize=(page_width, page_height))

            # 设置透明度
            c.setFillAlpha(config.opacity)

            # 设置颜色
            r, g, b = config.font_color
            c.setFillColorRGB(r / 255, g / 255, b / 255)

            # 获取水印文本
            watermark_text = config.build_watermark_text()

            # 绘制平铺水印
            c.saveState()
            c.translate(page_width / 2, page_height / 2)
            c.rotate(config.angle)

            # 计算需要绘制的范围（确保覆盖整页）
            diagonal = (page_width**2 + page_height**2) ** 0.5
            start = -int(diagonal / 2)
            end = int(diagonal / 2)

            # 平铺绘制水印
            y = start
            while y < end:
                x = start
                while x < end:
                    c.setFont("Helvetica", config.font_size)
                    c.drawCentredString(x, y, watermark_text)
                    x += config.spacing
                y += config.spacing

            c.restoreState()
            c.save()

            # 合并水印到每一页
            watermark_buffer.seek(0)
            watermark_pdf = PdfReader(watermark_buffer)
            watermark_page = watermark_pdf.pages[0]

            output = PdfWriter()
            for page in original_pdf.pages:
                page.merge_page(watermark_page)
                output.add_page(page)

            # 输出结果
            result_buffer = io.BytesIO()
            output.write(result_buffer)
            result_buffer.seek(0)

            logger.info(f"PDF 水印添加成功，共 {len(original_pdf.pages)} 页")
            return result_buffer.getvalue()

        except Exception as e:
            logger.error(f"添加 PDF 水印失败: {e}", exc_info=True)
            return pdf_content

    @staticmethod
    def add_excel_watermark(
        workbook,
        config: WatermarkConfig,
    ):
        """
        为 Excel 工作簿添加水印

        通过在每个工作表的页眉/页脚添加水印文本，
        以及在特定单元格添加浅色水印文本

        Args:
            workbook: openpyxl Workbook 对象
            config: 水印配置

        Returns:
            修改后的 Workbook 对象
        """
        if not OPENPYXL_AVAILABLE:
            logger.warning("openpyxl 不可用，跳过 Excel 水印")
            return workbook

        try:
            watermark_text = config.build_watermark_text()

            for sheet in workbook.worksheets:
                # 方法1：设置页眉页脚水印（打印时可见）
                sheet.oddHeader.center.text = watermark_text
                sheet.oddHeader.center.font = "Arial,Regular"
                sheet.oddHeader.center.size = 8
                sheet.oddHeader.center.color = "CCCCCC"

                sheet.oddFooter.center.text = watermark_text
                sheet.oddFooter.center.font = "Arial,Regular"
                sheet.oddFooter.center.size = 8
                sheet.oddFooter.center.color = "CCCCCC"

                # 方法2：在工作表右上角添加水印信息（屏幕可见）
                # 找到数据范围外的位置
                max_col = sheet.max_column or 1
                watermark_col = max_col + 2

                # 添加水印信息到右侧列
                watermark_cell = sheet.cell(row=1, column=watermark_col)
                watermark_cell.value = f"[水印] {watermark_text}"
                watermark_cell.font = Font(
                    size=8,
                    color="CCCCCC",
                    italic=True,
                )
                watermark_cell.alignment = Alignment(
                    horizontal="right",
                    vertical="top",
                )

            logger.info(f"Excel 水印添加成功，共 {len(workbook.worksheets)} 个工作表")
            return workbook

        except Exception as e:
            logger.error(f"添加 Excel 水印失败: {e}", exc_info=True)
            return workbook

    @staticmethod
    def create_watermark_config_from_user(
        user,
        custom_text: Optional[str] = None,
        **kwargs,
    ) -> WatermarkConfig:
        """
        从用户对象创建水印配置

        Args:
            user: 用户对象（需要有 id 和 real_name/username 属性）
            custom_text: 自定义水印文本
            **kwargs: 其他配置参数

        Returns:
            WatermarkConfig 配置对象
        """
        operator_name = getattr(user, "real_name", None) or getattr(
            user, "username", None
        )
        operator_id = getattr(user, "id", None)

        return WatermarkConfig(
            text=custom_text,
            operator_name=operator_name,
            operator_id=operator_id,
            **kwargs,
        )


# 便捷函数
def add_watermark_to_pdf(
    pdf_content: bytes,
    operator_name: Optional[str] = None,
    custom_text: Optional[str] = None,
    **kwargs,
) -> bytes:
    """便捷函数：为 PDF 添加水印"""
    config = WatermarkConfig(
        text=custom_text,
        operator_name=operator_name,
        **kwargs,
    )
    return WatermarkService.add_pdf_watermark(pdf_content, config)


def add_watermark_to_excel(
    workbook,
    operator_name: Optional[str] = None,
    custom_text: Optional[str] = None,
    **kwargs,
):
    """便捷函数：为 Excel 添加水印"""
    config = WatermarkConfig(
        text=custom_text,
        operator_name=operator_name,
        **kwargs,
    )
    return WatermarkService.add_excel_watermark(workbook, config)
