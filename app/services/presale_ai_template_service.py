"""
售前AI方案模板管理服务
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.presale_ai_solution import PresaleSolutionTemplate


class PresaleAITemplateService:
    """方案模板管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_template(
        self,
        data: Dict[str, Any],
        user_id: int
    ) -> PresaleSolutionTemplate:
        """创建方案模板"""
        template = PresaleSolutionTemplate(
            **data,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def update_template(
        self,
        template_id: int,
        data: Dict[str, Any]
    ) -> PresaleSolutionTemplate:
        """更新方案模板"""
        template = self.db.query(PresaleSolutionTemplate).filter_by(id=template_id).first()
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        for key, value in data.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def get_template(self, template_id: int) -> Optional[PresaleSolutionTemplate]:
        """获取模板"""
        return self.db.query(PresaleSolutionTemplate).filter_by(id=template_id).first()
    
    def delete_template(self, template_id: int) -> bool:
        """删除模板（软删除）"""
        template = self.get_template(template_id)
        
        if not template:
            return False
        
        template.is_active = 0
        self.db.commit()
        
        return True
    
    def increment_usage(self, template_id: int):
        """增加使用次数"""
        template = self.get_template(template_id)
        
        if template:
            template.usage_count = (template.usage_count or 0) + 1
            self.db.commit()
    
    def update_quality_score(self, template_id: int, new_score: float):
        """更新平均质量评分"""
        template = self.get_template(template_id)
        
        if template:
            current_avg = float(template.avg_quality_score or 0)
            usage_count = template.usage_count or 1
            
            # 计算新的平均分
            new_avg = ((current_avg * usage_count) + new_score) / (usage_count + 1)
            
            template.avg_quality_score = round(new_avg, 2)
            self.db.commit()
