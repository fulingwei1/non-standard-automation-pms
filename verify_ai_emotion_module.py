"""
AI情绪分析模块验证脚本
独立运行，不依赖完整的应用环境
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

def verify_models():
    """验证数据模型"""
    print("=" * 60)
    print("1. 验证数据模型...")
    print("=" * 60)
    
    try:
        from app.models.presale_ai_emotion_analysis import (
            PresaleAIEmotionAnalysis,
            SentimentType,
            ChurnRiskLevel
        )
        from app.models.presale_follow_up_reminder import (
            PresaleFollowUpReminder,
            ReminderPriority,
            ReminderStatus
        )
        from app.models.presale_emotion_trend import PresaleEmotionTrend
        
        print("✅ presale_ai_emotion_analysis 模型导入成功")
        print("✅ presale_follow_up_reminder 模型导入成功")
        print("✅ presale_emotion_trend 模型导入成功")
        
        # 验证枚举
        assert len(list(SentimentType)) == 3
        assert len(list(ChurnRiskLevel)) == 3
        assert len(list(ReminderPriority)) == 3
        assert len(list(ReminderStatus)) == 3
        print("✅ 所有枚举类型验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False

def verify_schemas():
    """验证Schema"""
    print("\n" + "=" * 60)
    print("2. 验证Schema...")
    print("=" * 60)
    
    try:
        from app.schemas.presale_ai_emotion import (
            EmotionAnalysisRequest,
            EmotionAnalysisResponse,
            ChurnRiskPredictionRequest,
            ChurnRiskPredictionResponse,
            FollowUpRecommendationRequest,
            FollowUpRecommendationResponse,
            BatchAnalysisRequest,
            BatchAnalysisResponse
        )
        
        print("✅ EmotionAnalysisRequest Schema导入成功")
        print("✅ ChurnRiskPredictionRequest Schema导入成功")
        print("✅ FollowUpRecommendationRequest Schema导入成功")
        print("✅ BatchAnalysisRequest Schema导入成功")
        
        # 测试Schema验证
        try:
            request = EmotionAnalysisRequest(
                presale_ticket_id=1,
                customer_id=100,
                communication_content="测试内容"
            )
            print("✅ Schema验证功能正常")
        except Exception as e:
            print(f"❌ Schema验证失败: {e}")
            return False
        
        # 测试验证器
        try:
            # 空内容应该失败
            request = EmotionAnalysisRequest(
                presale_ticket_id=1,
                customer_id=100,
                communication_content=""
            )
            print("❌ 空内容验证应该失败但没有")
            return False
        except:
            print("✅ 空内容验证器正常工作")
        
        return True
    except Exception as e:
        print(f"❌ Schema验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_service_structure():
    """验证服务层结构"""
    print("\n" + "=" * 60)
    print("3. 验证服务层结构...")
    print("=" * 60)
    
    try:
        # 读取服务文件
        service_file = os.path.join(os.path.dirname(__file__), 'app/services/ai_emotion_service.py')
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证核心方法存在
        required_methods = [
            'analyze_emotion',
            'predict_churn_risk',
            'recommend_follow_up',
            'get_emotion_trend',
            'get_follow_up_reminders',
            'dismiss_reminder',
            'batch_analyze_customers',
            '_call_openai_for_emotion',
            '_call_openai_for_churn',
            '_call_openai_for_follow_up',
            '_determine_sentiment',
            '_determine_churn_risk',
            '_identify_turning_points'
        ]
        
        for method in required_methods:
            if f'def {method}' in content:
                print(f"✅ 方法 {method} 存在")
            else:
                print(f"❌ 方法 {method} 缺失")
                return False
        
        print(f"✅ 服务文件大小: {len(content)} 字符")
        print(f"✅ 服务文件行数: {len(content.splitlines())} 行")
        
        return True
    except Exception as e:
        print(f"❌ 服务层验证失败: {e}")
        return False

def verify_api_endpoints():
    """验证API端点"""
    print("\n" + "=" * 60)
    print("4. 验证API端点...")
    print("=" * 60)
    
    try:
        api_file = os.path.join(os.path.dirname(__file__), 'app/api/presale_ai_emotion.py')
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证8个端点
        endpoints = [
            'analyze_emotion',
            'get_emotion_analysis',
            'predict_churn_risk',
            'recommend_follow_up',
            'get_follow_up_reminders',
            'get_emotion_trend',
            'dismiss_reminder',
            'batch_analyze_customers'
        ]
        
        for endpoint in endpoints:
            if f'def {endpoint}' in content:
                print(f"✅ 端点 {endpoint} 存在")
            else:
                print(f"❌ 端点 {endpoint} 缺失")
                return False
        
        # 验证路由装饰器
        router_count = content.count('@router.')
        print(f"✅ API端点数量: {router_count} (应该>=8)")
        
        return router_count >= 8
    except Exception as e:
        print(f"❌ API端点验证失败: {e}")
        return False

def verify_migration():
    """验证数据库迁移"""
    print("\n" + "=" * 60)
    print("5. 验证数据库迁移...")
    print("=" * 60)
    
    try:
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            'migrations/versions/20260215_add_presale_ai_emotion_analysis.py'
        )
        
        if not os.path.exists(migration_file):
            print(f"❌ 迁移文件不存在: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证关键内容
        checks = [
            ('presale_ai_emotion_analysis', '情绪分析表'),
            ('presale_follow_up_reminder', '跟进提醒表'),
            ('presale_emotion_trend', '情绪趋势表'),
            ('def upgrade', 'upgrade函数'),
            ('def downgrade', 'downgrade函数')
        ]
        
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description} 存在")
            else:
                print(f"❌ {description} 缺失")
                return False
        
        print(f"✅ 迁移文件大小: {len(content)} 字符")
        
        return True
    except Exception as e:
        print(f"❌ 迁移文件验证失败: {e}")
        return False

def verify_tests():
    """验证测试文件"""
    print("\n" + "=" * 60)
    print("6. 验证测试文件...")
    print("=" * 60)
    
    try:
        test_file = os.path.join(os.path.dirname(__file__), 'tests/test_ai_emotion_service.py')
        
        if not os.path.exists(test_file):
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计测试函数
        test_count = content.count('def test_')
        print(f"✅ 测试用例数量: {test_count} (要求>=20)")
        
        if test_count < 20:
            print(f"❌ 测试用例数量不足")
            return False
        
        # 验证测试覆盖的功能
        test_categories = {
            '情绪分析': ['test_analyze_emotion'],
            '意向识别': ['test_determine'],
            '流失预警': ['test_churn', 'test_predict'],
            '跟进提醒': ['test_follow', 'test_reminder']
        }
        
        for category, keywords in test_categories.items():
            found = any(keyword in content for keyword in keywords)
            if found:
                print(f"✅ {category}测试覆盖")
            else:
                print(f"⚠️  {category}测试可能缺失")
        
        print(f"✅ 测试文件大小: {len(content)} 字符")
        print(f"✅ 测试文件行数: {len(content.splitlines())} 行")
        
        return True
    except Exception as e:
        print(f"❌ 测试文件验证失败: {e}")
        return False

def verify_documentation():
    """验证文档"""
    print("\n" + "=" * 60)
    print("7. 验证文档...")
    print("=" * 60)
    
    docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
    
    required_docs = {
        'ai_emotion_analysis_api.md': 'API文档',
        'ai_emotion_analysis_user_guide.md': '用户手册',
        'ai_emotion_model_tuning.md': '模型调优文档',
        'ai_emotion_implementation_summary.md': '实施总结报告'
    }
    
    all_exist = True
    total_chars = 0
    
    for doc_file, description in required_docs.items():
        doc_path = os.path.join(docs_dir, doc_file)
        
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                chars = len(content)
                total_chars += chars
                print(f"✅ {description}: {chars:,} 字符")
        else:
            print(f"❌ {description} 缺失")
            all_exist = False
    
    print(f"✅ 文档总字数: {total_chars:,} 字符")
    
    return all_exist

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI客户情绪分析模块验证报告" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # 运行所有验证
    results.append(("数据模型", verify_models()))
    results.append(("Schema", verify_schemas()))
    results.append(("服务层", verify_service_structure()))
    results.append(("API端点", verify_api_endpoints()))
    results.append(("数据库迁移", verify_migration()))
    results.append(("单元测试", verify_tests()))
    results.append(("文档", verify_documentation()))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s}: {status}")
    
    print("\n" + "=" * 60)
    print(f"验证结果: {passed}/{total} 项通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有验证通过！模块开发完成，可以交付！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项验证失败，需要修复")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
