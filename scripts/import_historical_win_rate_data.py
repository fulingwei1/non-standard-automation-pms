#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
历史赢率数据导入脚本
Team 4 - AI智能赢率预测模型

功能：
1. 从历史数据（CSV/Excel）导入赢率记录
2. 清洗和验证数据
3. 生成特征快照
4. 导入数据库

使用方法：
    python scripts/import_historical_win_rate_data.py --file data/historical_win_rate.csv
"""

import argparse
import logging
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.models.sales.presale_ai_win_rate import (
    PresaleWinRateHistory,
    WinRateResultEnum,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalDataImporter:
    """历史数据导入器"""
    
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def import_from_csv(self, file_path: str) -> int:
        """从CSV文件导入"""
        
        logger.info(f"开始从CSV导入数据: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"读取到 {len(df)} 条记录")
            
            # 数据验证和清洗
            df = self._clean_data(df)
            
            # 导入数据库
            count = self._import_to_db(df)
            
            logger.info(f"成功导入 {count} 条记录")
            return count
            
        except Exception as e:
            logger.error(f"导入失败: {e}")
            raise
    
    def import_from_excel(self, file_path: str, sheet_name: str = 'Sheet1') -> int:
        """从Excel文件导入"""
        
        logger.info(f"开始从Excel导入数据: {file_path}, Sheet: {sheet_name}")
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"读取到 {len(df)} 条记录")
            
            # 数据验证和清洗
            df = self._clean_data(df)
            
            # 导入数据库
            count = self._import_to_db(df)
            
            logger.info(f"成功导入 {count} 条记录")
            return count
            
        except Exception as e:
            logger.error(f"导入失败: {e}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗和验证数据"""
        
        logger.info("开始数据清洗...")
        
        # 必需字段
        required_fields = [
            'presale_ticket_id',
            'predicted_win_rate',
            'actual_result'
        ]
        
        # 检查必需字段
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必需字段: {missing_fields}")
        
        # 删除空行
        df = df.dropna(subset=required_fields)
        
        # 数据类型转换
        df['presale_ticket_id'] = df['presale_ticket_id'].astype(int)
        df['predicted_win_rate'] = df['predicted_win_rate'].astype(float)
        
        # 验证赢率范围
        df = df[(df['predicted_win_rate'] >= 0) & (df['predicted_win_rate'] <= 100)]
        
        # 验证实际结果枚举值
        valid_results = ['won', 'lost', 'pending']
        df = df[df['actual_result'].isin(valid_results)]
        
        # 处理日期字段
        if 'actual_win_date' in df.columns:
            df['actual_win_date'] = pd.to_datetime(df['actual_win_date'], errors='coerce')
        
        if 'actual_lost_date' in df.columns:
            df['actual_lost_date'] = pd.to_datetime(df['actual_lost_date'], errors='coerce')
        
        logger.info(f"数据清洗完成，剩余 {len(df)} 条有效记录")
        
        return df
    
    def _import_to_db(self, df: pd.DataFrame) -> int:
        """导入到数据库"""
        
        logger.info("开始导入数据库...")
        
        session = self.SessionLocal()
        count = 0
        
        try:
            for _, row in df.iterrows():
                # 构建特征快照
                features = self._build_features(row)
                
                # 计算预测误差和准确性
                prediction_error = None
                is_correct = None
                
                if row['actual_result'] != 'pending':
                    actual_score = 100.0 if row['actual_result'] == 'won' else 0.0
                    predicted_score = float(row['predicted_win_rate'])
                    
                    prediction_error = abs(actual_score - predicted_score)
                    
                    # 判断预测是否正确（阈值50%）
                    if (predicted_score >= 50 and row['actual_result'] == 'won') or \
                       (predicted_score < 50 and row['actual_result'] == 'lost'):
                        is_correct = 1
                    else:
                        is_correct = 0
                
                # 创建记录
                history = PresaleWinRateHistory(
                    presale_ticket_id=int(row['presale_ticket_id']),
                    predicted_win_rate=Decimal(str(row['predicted_win_rate'])),
                    prediction_id=int(row.get('prediction_id')) if pd.notna(row.get('prediction_id')) else None,
                    actual_result=WinRateResultEnum(row['actual_result']),
                    actual_win_date=row.get('actual_win_date'),
                    actual_lost_date=row.get('actual_lost_date'),
                    features=features,
                    prediction_error=Decimal(str(prediction_error)) if prediction_error else None,
                    is_correct_prediction=is_correct,
                    result_updated_at=datetime.now(),
                    updated_by=int(row.get('updated_by', 1))
                )
                
                session.add(history)
                count += 1
                
                # 每100条提交一次
                if count % 100 == 0:
                    session.commit()
                    logger.info(f"已导入 {count} 条记录...")
            
            # 提交剩余记录
            session.commit()
            logger.info(f"数据库导入完成")
            
        except Exception as e:
            session.rollback()
            logger.error(f"数据库导入失败: {e}")
            raise
        finally:
            session.close()
        
        return count
    
    def _build_features(self, row: pd.Series) -> Dict[str, Any]:
        """构建特征快照"""
        
        features = {}
        
        # 基本信息
        if 'ticket_no' in row and pd.notna(row['ticket_no']):
            features['ticket_no'] = str(row['ticket_no'])
        
        if 'customer_name' in row and pd.notna(row['customer_name']):
            features['customer_name'] = str(row['customer_name'])
        
        if 'estimated_amount' in row and pd.notna(row['estimated_amount']):
            features['estimated_amount'] = float(row['estimated_amount'])
        
        # 客户信息
        if 'is_repeat_customer' in row:
            features['is_repeat_customer'] = bool(row['is_repeat_customer'])
        
        if 'cooperation_count' in row and pd.notna(row['cooperation_count']):
            features['cooperation_count'] = int(row['cooperation_count'])
        
        if 'success_count' in row and pd.notna(row['success_count']):
            features['success_count'] = int(row['success_count'])
        
        # 竞争态势
        if 'competitor_count' in row and pd.notna(row['competitor_count']):
            features['competitor_count'] = int(row['competitor_count'])
        
        # 技术评估
        for field in ['requirement_maturity', 'technical_feasibility', 
                     'business_feasibility', 'delivery_risk', 'customer_relationship']:
            if field in row and pd.notna(row[field]):
                features[field] = int(row[field])
        
        # 销售人员
        if 'salesperson_win_rate' in row and pd.notna(row['salesperson_win_rate']):
            features['salesperson_win_rate'] = float(row['salesperson_win_rate'])
        
        return features
    
    def generate_sample_data(self, output_file: str, num_records: int = 100):
        """生成样例数据文件"""
        
        logger.info(f"生成样例数据文件: {output_file}, 记录数: {num_records}")
        
        import random
        
        data = []
        for i in range(1, num_records + 1):
            # 随机生成数据
            is_repeat = random.choice([True, False])
            cooperation_count = random.randint(0, 10) if is_repeat else 0
            success_count = random.randint(0, cooperation_count) if cooperation_count > 0 else 0
            competitor_count = random.randint(1, 6)
            
            # 生成赢率（基于简单规则）
            base_rate = 50
            if is_repeat:
                base_rate += 15
            if competitor_count <= 2:
                base_rate += 10
            if competitor_count >= 5:
                base_rate -= 15
            
            predicted_rate = max(10, min(90, base_rate + random.randint(-20, 20)))
            
            # 生成实际结果（有一定概率与预测一致）
            if random.random() < 0.75:  # 75%概率预测正确
                actual_result = 'won' if predicted_rate >= 50 else 'lost'
            else:
                actual_result = 'lost' if predicted_rate >= 50 else 'won'
            
            record = {
                'presale_ticket_id': i,
                'ticket_no': f'PS-2025-{i:04d}',
                'customer_name': f'客户{i}',
                'estimated_amount': random.randint(50000, 5000000),
                'predicted_win_rate': predicted_rate,
                'actual_result': actual_result,
                'is_repeat_customer': is_repeat,
                'cooperation_count': cooperation_count,
                'success_count': success_count,
                'competitor_count': competitor_count,
                'requirement_maturity': random.randint(40, 90),
                'technical_feasibility': random.randint(40, 90),
                'business_feasibility': random.randint(40, 90),
                'delivery_risk': random.randint(10, 60),
                'customer_relationship': random.randint(40, 90),
                'salesperson_win_rate': random.uniform(0.3, 0.8),
                'actual_win_date': datetime.now().strftime('%Y-%m-%d') if actual_result == 'won' else '',
                'actual_lost_date': datetime.now().strftime('%Y-%m-%d') if actual_result == 'lost' else '',
                'updated_by': 1
            }
            
            data.append(record)
        
        # 保存为CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"样例数据已生成: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='历史赢率数据导入工具')
    parser.add_argument('--file', type=str, help='数据文件路径（CSV或Excel）')
    parser.add_argument('--sheet', type=str, default='Sheet1', help='Excel工作表名称（仅Excel）')
    parser.add_argument('--generate-sample', type=str, help='生成样例数据文件路径')
    parser.add_argument('--num-records', type=int, default=100, help='样例数据记录数')
    parser.add_argument('--db-url', type=str, help='数据库URL（可选，默认从配置读取）')
    
    args = parser.parse_args()
    
    # 获取数据库URL
    if args.db_url:
        db_url = args.db_url
    else:
        settings = get_settings()
        db_url = settings.ASYNC_DATABASE_URL.replace('+asyncmy', '')
    
    importer = HistoricalDataImporter(db_url)
    
    # 生成样例数据
    if args.generate_sample:
        importer.generate_sample_data(args.generate_sample, args.num_records)
        return
    
    # 导入数据
    if not args.file:
        logger.error("请指定数据文件路径（--file）或生成样例数据（--generate-sample）")
        return
    
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return
    
    # 根据文件扩展名选择导入方法
    if file_path.suffix.lower() == '.csv':
        count = importer.import_from_csv(str(file_path))
    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
        count = importer.import_from_excel(str(file_path), args.sheet)
    else:
        logger.error(f"不支持的文件格式: {file_path.suffix}")
        return
    
    logger.info(f"✅ 导入完成！共导入 {count} 条记录")


if __name__ == '__main__':
    main()
