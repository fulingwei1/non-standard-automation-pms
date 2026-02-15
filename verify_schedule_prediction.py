#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度偏差预警系统验证脚本

验证内容:
1. 数据库模型导入
2. AI服务基础功能
3. 预测算法
4. 方案生成
5. 预警创建

运行: python verify_schedule_prediction.py
"""

import sys
import os
from datetime import datetime, date, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_test_header(title: str):
    """打印测试标题"""
    print(f"\n{'='*70}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{'='*70}\n")


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """打印信息"""
    print(f"   {message}")


def test_model_import():
    """测试1: 数据库模型导入"""
    print_test_header("测试 1: 数据库模型导入")
    
    try:
        from app.models.project.schedule_prediction import (
            ProjectSchedulePrediction,
            CatchUpSolution,
            ScheduleAlert,
        )
        print_success("所有模型导入成功")
        print_info(f"   ProjectSchedulePrediction: {ProjectSchedulePrediction}")
        print_info(f"   CatchUpSolution: {CatchUpSolution}")
        print_info(f"   ScheduleAlert: {ScheduleAlert}")
        
        # 验证表名
        assert ProjectSchedulePrediction.__tablename__ == "project_schedule_prediction"
        assert CatchUpSolution.__tablename__ == "catch_up_solutions"
        assert ScheduleAlert.__tablename__ == "schedule_alerts"
        print_success("表名验证通过")
        
        return True
    except ImportError as e:
        print_error(f"模型导入失败: {e}")
        return False
    except AssertionError as e:
        print_error(f"表名验证失败: {e}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def test_service_import():
    """测试2: AI服务导入"""
    print_test_header("测试 2: AI服务导入")
    
    try:
        from app.services.schedule_prediction_service import SchedulePredictionService
        print_success("SchedulePredictionService 导入成功")
        print_info(f"   类定义: {SchedulePredictionService}")
        
        # 验证方法存在
        assert hasattr(SchedulePredictionService, 'predict_completion_date')
        assert hasattr(SchedulePredictionService, 'generate_catch_up_solutions')
        assert hasattr(SchedulePredictionService, 'create_alert')
        assert hasattr(SchedulePredictionService, 'check_and_create_alerts')
        assert hasattr(SchedulePredictionService, 'get_risk_overview')
        print_success("核心方法验证通过")
        
        return True
    except ImportError as e:
        print_error(f"服务导入失败: {e}")
        return False
    except AssertionError as e:
        print_error(f"方法验证失败: {e}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def test_feature_extraction():
    """测试3: 特征提取"""
    print_test_header("测试 3: 特征提取算法")
    
    try:
        from unittest.mock import MagicMock
        from app.services.schedule_prediction_service import SchedulePredictionService
        
        # 创建Mock DB
        mock_db = MagicMock()
        service = SchedulePredictionService(mock_db)
        
        # 测试特征提取
        features = service._extract_features(
            project_id=1,
            current_progress=45.5,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5,
            project_data={"days_elapsed": 40, "complexity": "high"}
        )
        
        print_success("特征提取成功")
        print_info(f"   特征数量: {len(features)}")
        print_info(f"   当前进度: {features['current_progress']}%")
        print_info(f"   进度偏差: {features['progress_deviation']}%")
        print_info(f"   速度比率: {features['velocity_ratio']}")
        
        # 验证关键特征
        assert 'current_progress' in features
        assert 'progress_deviation' in features
        assert 'velocity_ratio' in features
        assert features['progress_deviation'] == -14.5
        print_success("特征验证通过")
        
        return True
    except Exception as e:
        print_error(f"特征提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linear_prediction():
    """测试4: 线性预测算法"""
    print_test_header("测试 4: 线性预测算法")
    
    try:
        from unittest.mock import MagicMock
        from app.services.schedule_prediction_service import SchedulePredictionService
        
        mock_db = MagicMock()
        service = SchedulePredictionService(mock_db)
        
        # 测试场景1: 速度正常
        print_info("场景1: 速度正常（按时完成）")
        features_on_track = {
            "velocity_ratio": 1.2,
            "remaining_days": 30,
        }
        prediction1 = service._predict_linear(features_on_track)
        print_success(f"   预测延期: {prediction1['delay_days']}天")
        print_info(f"   置信度: {prediction1['confidence']}")
        assert prediction1['delay_days'] == 0
        
        # 测试场景2: 速度慢
        print_info("\n场景2: 速度慢（会延期）")
        features_delayed = {
            "velocity_ratio": 0.6,
            "remaining_days": 30,
        }
        prediction2 = service._predict_linear(features_delayed)
        print_success(f"   预测延期: {prediction2['delay_days']}天")
        print_info(f"   置信度: {prediction2['confidence']}")
        assert prediction2['delay_days'] > 0
        
        print_success("线性预测算法验证通过")
        return True
    except Exception as e:
        print_error(f"线性预测失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_assessment():
    """测试5: 风险评估"""
    print_test_header("测试 5: 风险评估算法")
    
    try:
        from unittest.mock import MagicMock
        from app.services.schedule_prediction_service import SchedulePredictionService
        
        mock_db = MagicMock()
        service = SchedulePredictionService(mock_db)
        
        test_cases = [
            (-5, "low", "提前完成"),
            (0, "low", "按时完成"),
            (3, "low", "轻微延期"),
            (7, "medium", "中等延期"),
            (14, "high", "严重延期"),
            (20, "critical", "极度延期"),
        ]
        
        for delay_days, expected_risk, description in test_cases:
            risk = service._assess_risk_level(delay_days)
            status = "✅" if risk == expected_risk else "❌"
            print(f"{status} {description}: {delay_days}天 -> {risk}")
            assert risk == expected_risk, f"预期 {expected_risk}，实际 {risk}"
        
        print_success("风险评估算法验证通过")
        return True
    except Exception as e:
        print_error(f"风险评估失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_default_solutions():
    """测试6: 默认赶工方案生成"""
    print_test_header("测试 6: 默认赶工方案生成")
    
    try:
        from unittest.mock import MagicMock
        from app.services.schedule_prediction_service import SchedulePredictionService
        
        mock_db = MagicMock()
        service = SchedulePredictionService(mock_db)
        
        # 生成方案
        solutions = service._generate_default_solutions(
            delay_days=15,
            project_data=None
        )
        
        print_success(f"生成了 {len(solutions)} 个方案")
        
        for idx, sol in enumerate(solutions, 1):
            print_info(f"\n方案 {idx}: {sol['name']}")
            print_info(f"   类型: {sol['type']}")
            print_info(f"   追回天数: {sol['estimated_catch_up']}天")
            print_info(f"   额外成本: ¥{sol['additional_cost']:,}")
            print_info(f"   风险等级: {sol['risk']}")
            print_info(f"   成功率: {sol['success_rate']*100:.0f}%")
        
        # 验证方案
        assert len(solutions) >= 3, "应至少生成3个方案"
        
        types = [sol['type'] for sol in solutions]
        assert 'overtime' in types, "应包含加班方案"
        assert 'process' in types, "应包含流程优化方案"
        assert 'manpower' in types, "应包含人力方案"
        
        print_success("方案生成验证通过")
        return True
    except Exception as e:
        print_error(f"方案生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint_import():
    """测试7: API端点导入"""
    print_test_header("测试 7: API端点导入")
    
    try:
        from app.api.v1.endpoints.projects import schedule_prediction
        print_success("API端点模块导入成功")
        
        # 验证router存在
        assert hasattr(schedule_prediction, 'router')
        print_success("Router验证通过")
        
        # 获取路由列表
        router = schedule_prediction.router
        routes = [route.path for route in router.routes]
        print_info(f"\n已注册路由 ({len(routes)}个):")
        for route_path in routes:
            print_info(f"   {route_path}")
        
        # 验证关键路由
        assert any("predict" in r for r in routes), "应包含预测路由"
        assert any("alerts" in r for r in routes), "应包含预警路由"
        assert any("solutions" in r for r in routes), "应包含方案路由"
        
        print_success("API路由验证通过")
        return True
    except ImportError as e:
        print_error(f"API端点导入失败: {e}")
        return False
    except Exception as e:
        print_error(f"API端点验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_migration_file():
    """测试8: 迁移文件检查"""
    print_test_header("测试 8: 数据库迁移文件")
    
    try:
        migration_path = "migrations/versions/20260215_schedule_prediction_system.py"
        
        if os.path.exists(migration_path):
            print_success(f"迁移文件存在: {migration_path}")
            
            # 读取文件检查关键内容
            with open(migration_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证表创建
            tables = [
                'project_schedule_prediction',
                'catch_up_solutions',
                'schedule_alerts'
            ]
            
            for table in tables:
                if table in content:
                    print_success(f"   包含表: {table}")
                else:
                    print_error(f"   缺少表: {table}")
                    return False
            
            print_success("迁移文件验证通过")
            return True
        else:
            print_error(f"迁移文件不存在: {migration_path}")
            return False
    except Exception as e:
        print_error(f"迁移文件检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print(f"\n{Colors.BLUE}{'='*70}")
    print("进度偏差预警系统 - 验证脚本")
    print(f"{'='*70}{Colors.RESET}\n")
    
    tests = [
        ("数据库模型导入", test_model_import),
        ("AI服务导入", test_service_import),
        ("特征提取", test_feature_extraction),
        ("线性预测", test_linear_prediction),
        ("风险评估", test_risk_assessment),
        ("方案生成", test_default_solutions),
        ("API端点", test_api_endpoint_import),
        ("迁移文件", test_migration_file),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"测试 '{test_name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 打印汇总
    print_test_header("测试汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print(f"{Colors.GREEN}🎉 所有测试通过！系统准备就绪！{Colors.RESET}")
        print(f"{'='*70}{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  部分测试失败，请检查上述错误{Colors.RESET}")
        print(f"{'='*70}{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
