"""
为现有案例生成向量嵌入
用于支持语义搜索功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.presale_knowledge_case import PresaleKnowledgeCase
from app.services.presale_ai_knowledge_service import PresaleAIKnowledgeService


def generate_embeddings_for_all_cases():
    """为所有案例生成嵌入向量"""
    db = SessionLocal()
    service = PresaleAIKnowledgeService(db)
    
    # 查询所有没有嵌入的案例
    cases = db.query(PresaleKnowledgeCase).all()
    
    print("=" * 80)
    print(f"开始为 {len(cases)} 个案例生成嵌入向量...")
    print("=" * 80)
    
    updated_count = 0
    skipped_count = 0
    
    for i, case in enumerate(cases, 1):
        try:
            # 如果已有嵌入且有摘要，跳过
            if case.embedding and case.project_summary:
                print(f"[{i}/{len(cases)}] ⏭️  跳过 (已有嵌入): {case.case_name}")
                skipped_count += 1
                continue
            
            # 生成嵌入文本
            embedding_text = case.project_summary or case.case_name
            
            if embedding_text:
                # 生成嵌入向量
                embedding = service._generate_embedding(embedding_text)
                case.embedding = service._serialize_embedding(embedding)
                
                db.commit()
                updated_count += 1
                print(f"[{i}/{len(cases)}] ✅ 生成成功: {case.case_name}")
            else:
                print(f"[{i}/{len(cases)}] ⚠️  无内容: {case.case_name}")
                
        except Exception as e:
            print(f"[{i}/{len(cases)}] ❌ 生成失败: {case.case_name} - {str(e)}")
    
    db.close()
    
    print("=" * 80)
    print("嵌入向量生成完成!")
    print(f"✅ 更新: {updated_count}")
    print(f"⏭️  跳过: {skipped_count}")
    print(f"📊 总计: {len(cases)}")
    print("=" * 80)


if __name__ == "__main__":
    generate_embeddings_for_all_cases()
