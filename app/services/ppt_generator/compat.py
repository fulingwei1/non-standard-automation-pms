"""python-pptx 兼容层。未安装依赖时允许模块导入，实际生成时再报错。"""

from types import SimpleNamespace

PPTX_IMPORT_ERROR = None

try:
    from pptx import Presentation  # type: ignore
    from pptx.dml.color import RGBColor as RgbColor  # type: ignore
    from pptx.enum.shapes import MSO_SHAPE  # type: ignore
    from pptx.enum.text import PP_ALIGN  # type: ignore
    from pptx.util import Inches, Pt  # type: ignore

    PPTX_AVAILABLE = True
except ModuleNotFoundError as exc:
    PPTX_IMPORT_ERROR = exc
    PPTX_AVAILABLE = False

    class MissingPptxDependencyError(ModuleNotFoundError):
        pass

    def _raise_missing() -> None:
        raise MissingPptxDependencyError(
            "python-pptx 未安装，无法使用 PPT 生成功能。请安装 api/requirements.txt 中声明的 python-pptx>=0.6.21"
        ) from PPTX_IMPORT_ERROR

    class Presentation:  # type: ignore
        def __init__(self, *args, **kwargs):
            _raise_missing()

    class RgbColor(tuple):  # type: ignore
        def __new__(cls, r, g, b):
            return tuple.__new__(cls, (r, g, b))

    def Inches(value):  # type: ignore
        return value

    def Pt(value):  # type: ignore
        return value

    PP_ALIGN = SimpleNamespace(CENTER="CENTER", RIGHT="RIGHT")  # type: ignore
    MSO_SHAPE = SimpleNamespace(RECTANGLE="RECTANGLE")  # type: ignore
else:
    class MissingPptxDependencyError(ModuleNotFoundError):
        pass
