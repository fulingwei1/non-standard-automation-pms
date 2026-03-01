#!/usr/bin/env python3
"""
历史成本数据导入脚本

用于导入历史项目的成本数据,供AI模型学习
"""
import sys
import csv
import json
from decimal import Decimal
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.sales.presale_ai_cost import PresaleCostHistory


def import_from_csv(csv_file_path: str):
    """
    从CSV文件导入历史成本数据
    
    CSV格式:
    project_id,project_name,project_type,estimated_cost,actual_cost,hardware_cost,software_cost,installation_cost,service_cost
    """
    db = SessionLocal()
    imported_count = 0
    error_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # 解析数据
                    project_id = int(row['project_id']) if row.get('project_id') else None
                    project_name = row['project_name']
                    estimated_cost = Decimal(row['estimated_cost'])
                    actual_cost = Decimal(row['actual_cost'])
                    
                    # 计算偏差率
                    variance = actual_cost - estimated_cost
                    variance_rate = (variance / estimated_cost * Decimal("100")) if estimated_cost > 0 else Decimal("0")
                    
                    # 构建成本分解
                    cost_breakdown = {}
                    if row.get('hardware_cost'):
                        cost_breakdown['hardware_cost'] = float(Decimal(row['hardware_cost']))
                    if row.get('software_cost'):
                        cost_breakdown['software_cost'] = float(Decimal(row['software_cost']))
                    if row.get('installation_cost'):
                        cost_breakdown['installation_cost'] = float(Decimal(row['installation_cost']))
                    if row.get('service_cost'):
                        cost_breakdown['service_cost'] = float(Decimal(row['service_cost']))
                    
                    # 构建项目特征
                    project_features = {}
                    if row.get('project_type'):
                        project_features['project_type'] = row['project_type']
                    if row.get('industry'):
                        project_features['industry'] = row['industry']
                    if row.get('complexity_level'):
                        project_features['complexity_level'] = row['complexity_level']
                    
                    # 创建历史记录
                    history = PresaleCostHistory(
                        project_id=project_id,
                        project_name=project_name,
                        estimated_cost=estimated_cost,
                        actual_cost=actual_cost,
                        variance_rate=variance_rate,
                        cost_breakdown=cost_breakdown if cost_breakdown else None,
                        variance_analysis={
                            'total_variance': float(variance),
                            'variance_rate': float(variance_rate),
                            'import_source': 'csv_import',
                            'import_date': datetime.now().isoformat()
                        },
                        project_features=project_features if project_features else None
                    )
                    
                    db.add(history)
                    imported_count += 1
                    
                    if imported_count % 50 == 0:
                        db.commit()
                        print(f"✅ 已导入 {imported_count} 条记录...")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ 第{row_num}行导入失败: {str(e)}")
                    print(f"   数据: {row}")
                    continue
        
        # 最后提交
        db.commit()
        print(f"\n{'='*60}")
        print(f"✅ 导入完成!")
        print(f"   成功: {imported_count} 条")
        print(f"   失败: {error_count} 条")
        print(f"{'='*60}")
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {csv_file_path}")
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


def import_from_json(json_file_path: str):
    """
    从JSON文件导入历史成本数据
    
    JSON格式:
    [
        {
            "project_id": 1,
            "project_name": "XX项目",
            "estimated_cost": 100000,
            "actual_cost": 110000,
            "cost_breakdown": {...},
            "project_features": {...}
        },
        ...
    ]
    """
    db = SessionLocal()
    imported_count = 0
    error_count = 0
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for idx, record in enumerate(data):
            try:
                estimated_cost = Decimal(str(record['estimated_cost']))
                actual_cost = Decimal(str(record['actual_cost']))
                
                variance = actual_cost - estimated_cost
                variance_rate = (variance / estimated_cost * Decimal("100")) if estimated_cost > 0 else Decimal("0")
                
                history = PresaleCostHistory(
                    project_id=record.get('project_id'),
                    project_name=record.get('project_name'),
                    estimated_cost=estimated_cost,
                    actual_cost=actual_cost,
                    variance_rate=variance_rate,
                    cost_breakdown=record.get('cost_breakdown'),
                    variance_analysis={
                        'total_variance': float(variance),
                        'variance_rate': float(variance_rate),
                        'import_source': 'json_import',
                        'import_date': datetime.now().isoformat()
                    },
                    project_features=record.get('project_features')
                )
                
                db.add(history)
                imported_count += 1
                
                if imported_count % 50 == 0:
                    db.commit()
                    print(f"✅ 已导入 {imported_count} 条记录...")
            
            except Exception as e:
                error_count += 1
                print(f"❌ 第{idx+1}条记录导入失败: {str(e)}")
                continue
        
        db.commit()
        print(f"\n{'='*60}")
        print(f"✅ 导入完成!")
        print(f"   成功: {imported_count} 条")
        print(f"   失败: {error_count} 条")
        print(f"{'='*60}")
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {json_file_path}")
    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        db.rollback()
    finally:
        db.close()


def generate_sample_data():
    """生成样例数据文件"""
    # 生成CSV样例
    csv_sample = """project_id,project_name,project_type,estimated_cost,actual_cost,hardware_cost,software_cost,installation_cost,service_cost,industry,complexity_level
1,A公司自动化产线,自动化产线,200000,218000,80000,90000,15000,20000,制造业,medium
2,B公司AGV调度系统,AGV调度系统,350000,365000,120000,180000,25000,30000,物流,high
3,C公司视觉检测系统,视觉检测,150000,142000,60000,55000,10000,12000,电子,low
4,D公司机器人集成,机器人集成,450000,480000,200000,180000,35000,45000,汽车,high
5,E公司MES系统,MES系统,280000,275000,50000,170000,20000,25000,制造业,medium
"""
    
    csv_path = Path(__file__).parent.parent / 'data' / 'sample_cost_history.csv'
    csv_path.parent.mkdir(exist_ok=True)
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_sample)
    
    print(f"✅ 已生成CSV样例文件: {csv_path}")
    
    # 生成JSON样例
    json_sample = [
        {
            "project_id": 101,
            "project_name": "F公司仓储管理系统",
            "estimated_cost": 180000,
            "actual_cost": 195000,
            "cost_breakdown": {
                "hardware_cost": 40000,
                "software_cost": 100000,
                "installation_cost": 15000,
                "service_cost": 25000
            },
            "project_features": {
                "project_type": "仓储管理",
                "industry": "物流",
                "complexity_level": "medium"
            }
        },
        {
            "project_id": 102,
            "project_name": "G公司生产追溯系统",
            "estimated_cost": 220000,
            "actual_cost": 210000,
            "cost_breakdown": {
                "hardware_cost": 70000,
                "software_cost": 95000,
                "installation_cost": 18000,
                "service_cost": 22000
            },
            "project_features": {
                "project_type": "追溯系统",
                "industry": "食品",
                "complexity_level": "medium"
            }
        }
    ]
    
    json_path = Path(__file__).parent.parent / 'data' / 'sample_cost_history.json'
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_sample, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成JSON样例文件: {json_path}")
    
    return csv_path, json_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导入历史成本数据')
    parser.add_argument('--csv', help='CSV文件路径')
    parser.add_argument('--json', help='JSON文件路径')
    parser.add_argument('--generate-sample', action='store_true', help='生成样例数据文件')
    
    args = parser.parse_args()
    
    if args.generate_sample:
        csv_path, json_path = generate_sample_data()
        print(f"\n{'='*60}")
        print("📝 样例数据已生成,可以使用以下命令导入:")
        print(f"   python {__file__} --csv {csv_path}")
        print(f"   python {__file__} --json {json_path}")
        print(f"{'='*60}")
        return
    
    if args.csv:
        print(f"开始从CSV文件导入: {args.csv}")
        import_from_csv(args.csv)
    elif args.json:
        print(f"开始从JSON文件导入: {args.json}")
        import_from_json(args.json)
    else:
        print("请指定导入文件:")
        print(f"  python {__file__} --csv <csv文件路径>")
        print(f"  python {__file__} --json <json文件路径>")
        print(f"  python {__file__} --generate-sample  (生成样例数据)")


if __name__ == '__main__':
    main()
