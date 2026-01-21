# -*- coding: utf-8 -*-
"""
阶段模板服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .core import StageTemplateCore
from .default_template import DefaultTemplateMixin
from .helpers import HelpersMixin
from .import_export import ImportExportMixin
from .node_management import NodeManagementMixin
from .stage_management import StageManagementMixin
from .template_crud import TemplateCrudMixin


class StageTemplateService(
    StageTemplateCore,
    TemplateCrudMixin,
    StageManagementMixin,
    NodeManagementMixin,
    DefaultTemplateMixin,
    HelpersMixin,
    ImportExportMixin,
):
    """阶段模板服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        StageTemplateCore.__init__(self, db)


__all__ = ["StageTemplateService"]
