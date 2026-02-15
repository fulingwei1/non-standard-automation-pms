"""
导入种子数据到数据库
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.sales_script import SalesScriptTemplate, ScenarioType, Base
from sales_script_seeds import get_all_templates, get_all_strategies


def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")


def import_templates(db: Session):
    """导入话术模板"""
    templates = get_all_templates()
    
    for template_data in templates:
        template = SalesScriptTemplate(
            scenario=ScenarioType(template_data["scenario"]),
            customer_type=template_data.get("customer_type"),
            script_content=template_data["script_content"],
            tags=template_data.get("tags"),
            success_rate=template_data.get("success_rate")
        )
        db.add(template)
    
    db.commit()
    print(f"✅ 导入 {len(templates)} 条话术模板")


def main():
    """主函数"""
    print("开始导入种子数据...")
    
    # 创建表
    create_tables()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 清空现有数据（可选）
        db.query(SalesScriptTemplate).delete()
        db.commit()
        print("✅ 清空现有数据")
        
        # 导入模板
        import_templates(db)
        
        # 验证导入
        count = db.query(SalesScriptTemplate).count()
        print(f"\n✅ 数据导入完成！共 {count} 条话术模板")
        
        # 统计各场景数量
        from collections import Counter
        scenarios = [t.scenario.value for t in db.query(SalesScriptTemplate).all()]
        scenario_counts = Counter(scenarios)
        
        print("\n各场景话术数量：")
        for scenario, count in scenario_counts.items():
            print(f"  {scenario}: {count}条")
        
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
