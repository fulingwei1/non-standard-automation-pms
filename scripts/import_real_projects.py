#!/usr/bin/env python3
"""
真实项目数据导入脚本

功能：
1. 从Excel/CSV文件导入金凯博真实项目数据
2. 自动创建项目、案例、客户记录
3. 关联历史案例到售前智能体知识库

使用方法：
    python scripts/import_real_projects.py --input projects.xlsx
    python scripts/import_real_projects.py --input projects.csv --dry-run

Excel/CSV字段要求：
    - project_name: 项目名称（必填）
    - customer_name: 客户名称（必填）
    - industry: 行业（如：新能源汽车、白色家电）
    - project_amount: 项目金额（万元）
    - project_duration: 项目周期（天）
    - project_date: 项目日期（YYYY-MM-DD）
    - project_type: 项目类型（如：BMS测试、ICT测试）
    - project_summary: 项目摘要
    - technical_highlights: 技术亮点
    - success_factors: 成功要素
    - lessons_learned: 经验教训
    - customer_feedback: 客户反馈
    - win_rate: 是否中标（是/否）
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import Base
from app.models.presale_knowledge_case import PresaleKnowledgeCase
from app.models.project import Project
from app.models.customer import Customer


def load_data(file_path: str) -> pd.DataFrame:
    """加载Excel或CSV文件"""
    file_path = Path(file_path)
    
    if file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    return df


def validate_data(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """验证数据完整性"""
    errors = []
    
    # 必填字段检查
    required_fields = ['project_name', 'customer_name']
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"缺少必填字段: {field}")
        elif df[field].isna().any():
            errors.append(f"字段 {field} 存在空值")
    
    return len(errors) == 0, errors


def import_to_database(df: pd.DataFrame, db_session, dry_run: bool = False):
    """导入数据到数据库"""
    stats = {
        'total': len(df),
        'customers_created': 0,
        'projects_created': 0,
        'cases_created': 0,
        'errors': []
    }
    
    for idx, row in df.iterrows():
        try:
            # 1. 创建或获取客户
            customer_name = str(row['customer_name']).strip()
            customer = db_session.query(Customer).filter_by(customer_name=customer_name).first()
            
            if not customer:
                if not dry_run:
                    customer = Customer(
                        customer_name=customer_name,
                        industry=row.get('industry', ''),
                        created_at=datetime.now()
                    )
                    db_session.add(customer)
                    db_session.flush()
                stats['customers_created'] += 1
            
            # 2. 创建项目
            project_name = str(row['project_name']).strip()
            project = db_session.query(Project).filter_by(project_name=project_name).first()
            
            if not project:
                if not dry_run:
                    project = Project(
                        project_name=project_name,
                        customer_id=customer.id if customer else None,
                        industry=row.get('industry', ''),
                        project_amount=float(row.get('project_amount', 0)) * 10000,  # 万元转元
                        project_duration=int(row.get('project_duration', 0)),
                        project_date=row.get('project_date'),
                        project_type=row.get('project_type', ''),
                        project_summary=row.get('project_summary', ''),
                        created_at=datetime.now()
                    )
                    db_session.add(project)
                    db_session.flush()
                stats['projects_created'] += 1
            
            # 3. 创建案例（如果有技术亮点或经验教训）
            technical_highlights = row.get('technical_highlights', '')
            lessons_learned = row.get('lessons_learned', '')
            
            if technical_highlights or lessons_learned:
                case = db_session.query(PresaleKnowledgeCase).filter_by(
                    case_name=project_name
                ).first()
                
                if not case:
                    if not dry_run:
                        case = PresaleKnowledgeCase(
                            case_name=project_name,
                            industry=row.get('industry', ''),
                            equipment_type=row.get('project_type', ''),
                            customer_name=customer_name,
                            project_amount=float(row.get('project_amount', 0)) * 10000,
                            project_summary=row.get('project_summary', ''),
                            technical_highlights=technical_highlights,
                            success_factors=row.get('success_factors', ''),
                            lessons_learned=lessons_learned,
                            quality_score=0.8 if row.get('win_rate') == '是' else 0.5,
                            created_at=datetime.now()
                        )
                        db_session.add(case)
                    stats['cases_created'] += 1
            
        except Exception as e:
            error_msg = f"第 {idx + 1} 行导入失败: {str(e)}"
            stats['errors'].append(error_msg)
            print(f"⚠️  {error_msg}")
    
    if not dry_run:
        db_session.commit()
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='导入真实项目数据')
    parser.add_argument('--input', required=True, help='输入文件路径（Excel或CSV）')
    parser.add_argument('--dry-run', action='store_true', help='试运行，不实际写入数据库')
    parser.add_argument('--database', default='sqlite:///data/app.db', help='数据库连接字符串')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)
    
    print(f"📂 加载文件: {args.input}")
    df = load_data(args.input)
    print(f"✅ 加载成功，共 {len(df)} 条记录")
    
    # 验证数据
    is_valid, errors = validate_data(df)
    if not is_valid:
        print("❌ 数据验证失败:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("✅ 数据验证通过")
    
    # 连接数据库
    engine = create_engine(args.database)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    try:
        # 导入数据
        print(f"\n{'🔍 试运行' if args.dry_run else '💾 开始导入'}...")
        stats = import_to_database(df, db_session, dry_run=args.dry_run)
        
        # 输出统计
        print("\n📊 导入统计:")
        print(f"  总记录数: {stats['total']}")
        print(f"  新建客户: {stats['customers_created']}")
        print(f"  新建项目: {stats['projects_created']}")
        print(f"  新建案例: {stats['cases_created']}")
        
        if stats['errors']:
            print(f"\n⚠️  错误数: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # 只显示前5个错误
                print(f"  - {error}")
            if len(stats['errors']) > 5:
                print(f"  ... 还有 {len(stats['errors']) - 5} 个错误")
        
        if args.dry_run:
            print("\n🔍 这是试运行，数据未实际写入数据库")
        else:
            print("\n✅ 导入完成！")
    
    finally:
        db_session.close()


if __name__ == '__main__':
    main()
