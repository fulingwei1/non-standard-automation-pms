#!/usr/bin/env python3
"""
AI 模型对比测试脚本
对比 GLM-5 vs Kimi vs GPT-4 在售前AI系统中的表现
"""

import os
import sys
import time
import json
from typing import Dict, List
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_client_service import AIClientService


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ModelComparison:
    """AI模型对比测试"""
    
    def __init__(self):
        # 检测可用模型
        self.available_models = self.detect_available_models()
        self.test_cases = self.load_test_cases()
        self.results = []
        
        print(f"{Colors.BOLD}可用模型: {', '.join(self.available_models)}{Colors.RESET}\n")
    
    def detect_available_models(self) -> List[str]:
        """检测哪些模型可用"""
        models = []
        
        if os.getenv("ZHIPU_API_KEY") and os.getenv("ZHIPU_API_KEY") != "your_zhipu_api_key_here":
            models.append("glm-5")
        if os.getenv("OPENAI_API_KEY"):
            models.append("gpt-4")
        if os.getenv("KIMI_API_KEY"):
            models.append("kimi")
        
        # 如果没有配置任何API Key，使用Mock模式
        if not models:
            models = ["glm-5", "kimi", "gpt-4"]  # Mock模式全部可用
        
        return models
    
    def run_comparison(self):
        """运行完整对比测试"""
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}AI 模型对比测试{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for case_id, test_case in enumerate(self.test_cases, 1):
            print(f"\n{Colors.BLUE}{Colors.BOLD}📝 测试用例 {case_id}: {test_case['name']}{Colors.RESET}")
            print(f"{Colors.BOLD}{'-' * 60}{Colors.RESET}\n")
            
            case_results = {
                'case_id': case_id,
                'case_name': test_case['name'],
                'models': {}
            }
            
            for model in self.available_models:
                print(f"{Colors.MAGENTA}🤖 测试模型: {model.upper()}{Colors.RESET}")
                result = self.test_single_model(model, test_case)
                case_results['models'][model] = result
                
                # 打印结果
                self.print_result(model, result)
                print()  # 空行分隔
            
            self.results.append(case_results)
            
            # 对比分析
            self.compare_results(case_results)
        
        # 生成总体报告
        self.generate_report()
    
    def test_single_model(self, model: str, test_case: Dict) -> Dict:
        """测试单个模型"""
        client = AIClientService()
        
        start_time = time.time()
        error = None
        response = None
        
        try:
            response = client.generate_solution(
                prompt=test_case['prompt'],
                model=model,
                temperature=test_case.get('temperature', 0.7),
                max_tokens=test_case.get('max_tokens', 2000)
            )
            success = True
        except Exception as e:
            error = str(e)
            success = False
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        result = {
            'success': success,
            'response_time': round(elapsed, 2),
            'error': error
        }
        
        if success and response:
            result['content'] = response.get('content', '')
            result['tokens'] = response.get('usage', {}).get('total_tokens', 0)
            result['model'] = response.get('model', model)
            
            # 质量评估
            result['quality_score'] = self.evaluate_quality(
                response.get('content', ''),
                test_case
            )
            
            # 成本估算
            result['estimated_cost'] = self.estimate_cost(
                model,
                result['tokens']
            )
        
        return result
    
    def evaluate_quality(self, content: str, test_case: Dict) -> float:
        """评估回复质量 (1-5分)"""
        score = 3.0  # 基础分
        
        # 检查关键词
        keywords = test_case.get('keywords', [])
        if keywords:
            matched = sum(1 for kw in keywords if kw.lower() in content.lower())
            keyword_ratio = matched / len(keywords)
            score += keyword_ratio * 1.0
        
        # 检查长度
        min_length = test_case.get('min_length', 500)
        if len(content) >= min_length:
            score += 0.5
        else:
            score -= 0.5
        
        # 检查结构化
        has_structure = any(marker in content for marker in ['```json', '```', '1.', '2.', '•', '-'])
        if has_structure:
            score += 0.5
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def estimate_cost(self, model: str, tokens: int) -> float:
        """估算成本（人民币）"""
        # 价格参考（每1K tokens）
        prices = {
            'glm-5': 0.10,      # 输入0.05+输出0.15 平均
            'kimi': 0.08,       # Kimi 价格
            'gpt-4': 0.30,      # GPT-4 价格
        }
        
        price_per_1k = prices.get(model, 0.10)
        return round(tokens / 1000 * price_per_1k, 4)
    
    def print_result(self, model: str, result: Dict):
        """打印单次测试结果"""
        if result['success']:
            print(f"  {Colors.GREEN}✅ 成功{Colors.RESET}")
            print(f"  ⏱️  响应时间: {Colors.YELLOW}{result['response_time']}秒{Colors.RESET}")
            print(f"  📊 Token消耗: {Colors.CYAN}{result.get('tokens', 'N/A')}{Colors.RESET}")
            print(f"  ⭐ 质量评分: {Colors.GREEN}{result.get('quality_score', 'N/A')}/5{Colors.RESET}")
            print(f"  💰 预估成本: {Colors.YELLOW}¥{result.get('estimated_cost', 0)}{Colors.RESET}")
            content_preview = result.get('content', '')[:150].replace('\n', ' ')
            print(f"  📝 内容预览: {content_preview}...")
        else:
            print(f"  {Colors.RED}❌ 失败: {result['error']}{Colors.RESET}")
    
    def compare_results(self, case_results: Dict):
        """对比分析单个用例的结果"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}📊 对比分析 - {case_results['case_name']}{Colors.RESET}")
        print(f"{Colors.BOLD}{'-' * 60}{Colors.RESET}")
        
        # 收集数据
        models_data = []
        for model, result in case_results['models'].items():
            if result['success']:
                models_data.append({
                    'model': model,
                    'time': result['response_time'],
                    'tokens': result.get('tokens', 0),
                    'quality': result.get('quality_score', 0),
                    'cost': result.get('estimated_cost', 0)
                })
        
        if not models_data:
            print(f"  {Colors.RED}⚠️  所有模型测试失败{Colors.RESET}")
            return
        
        # 找出最优
        fastest = min(models_data, key=lambda x: x['time'])
        most_efficient = min(models_data, key=lambda x: x['tokens'])
        best_quality = max(models_data, key=lambda x: x['quality'])
        cheapest = min(models_data, key=lambda x: x['cost'])
        
        # 计算性价比（质量/成本）
        for data in models_data:
            if data['cost'] > 0:
                data['value_score'] = data['quality'] / data['cost'] * 100
            else:
                data['value_score'] = data['quality'] * 100
        best_value = max(models_data, key=lambda x: x['value_score'])
        
        print(f"  {Colors.GREEN}🏆 最快: {fastest['model'].upper()} ({fastest['time']}秒){Colors.RESET}")
        print(f"  {Colors.CYAN}💰 最省Token: {most_efficient['model'].upper()} ({most_efficient['tokens']} tokens){Colors.RESET}")
        print(f"  {Colors.YELLOW}⭐ 最高质量: {best_quality['model'].upper()} ({best_quality['quality']}/5){Colors.RESET}")
        print(f"  {Colors.MAGENTA}💵 最低成本: {cheapest['model'].upper()} (¥{cheapest['cost']}){Colors.RESET}")
        print(f"  {Colors.BOLD}🎯 最佳性价比: {best_value['model'].upper()} (得分: {best_value['value_score']:.1f}){Colors.RESET}")
    
    def generate_report(self):
        """生成完整对比报告"""
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}📊 完整对比报告{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
        
        # 统计每个模型的表现
        model_stats = {model: {
            'success_count': 0,
            'fail_count': 0,
            'total_time': 0,
            'total_tokens': 0,
            'total_quality': 0,
            'total_cost': 0,
            'test_count': 0
        } for model in self.available_models}
        
        for case_result in self.results:
            for model, result in case_result['models'].items():
                stats = model_stats[model]
                stats['test_count'] += 1
                
                if result['success']:
                    stats['success_count'] += 1
                    stats['total_time'] += result['response_time']
                    stats['total_tokens'] += result.get('tokens', 0)
                    stats['total_quality'] += result.get('quality_score', 0)
                    stats['total_cost'] += result.get('estimated_cost', 0)
                else:
                    stats['fail_count'] += 1
        
        # 打印统计
        comparison_table = []
        
        for model, stats in model_stats.items():
            print(f"{Colors.MAGENTA}{Colors.BOLD}🤖 {model.upper()}{Colors.RESET}")
            print(f"{Colors.BOLD}{'-' * 60}{Colors.RESET}")
            
            if stats['test_count'] == 0:
                print(f"  {Colors.RED}未测试{Colors.RESET}\n")
                continue
            
            success_rate = (stats['success_count'] / stats['test_count'] * 100) if stats['test_count'] > 0 else 0
            avg_time = stats['total_time'] / stats['success_count'] if stats['success_count'] > 0 else 0
            avg_tokens = stats['total_tokens'] / stats['success_count'] if stats['success_count'] > 0 else 0
            avg_quality = stats['total_quality'] / stats['success_count'] if stats['success_count'] > 0 else 0
            avg_cost = stats['total_cost'] / stats['success_count'] if stats['success_count'] > 0 else 0
            
            # 计算综合得分
            quality_score = (avg_quality / 5) * 100
            speed_score = (2.0 / avg_time * 100) if avg_time > 0 else 0  # 假设2秒是理想时间
            cost_score = (0.10 / avg_cost * 100) if avg_cost > 0 else 100  # 假设¥0.10是理想成本
            stability_score = success_rate
            
            comprehensive_score = (
                quality_score * 0.4 +
                min(speed_score, 100) * 0.3 +
                min(cost_score, 100) * 0.2 +
                stability_score * 0.1
            )
            
            print(f"  成功率: {Colors.GREEN if success_rate >= 90 else Colors.YELLOW}{success_rate:.1f}%{Colors.RESET}")
            print(f"  平均响应时间: {Colors.YELLOW}{avg_time:.2f}秒{Colors.RESET}")
            print(f"  平均Token消耗: {Colors.CYAN}{avg_tokens:.0f}{Colors.RESET}")
            print(f"  平均质量评分: {Colors.GREEN}{avg_quality:.1f}/5{Colors.RESET}")
            print(f"  平均单次成本: {Colors.YELLOW}¥{avg_cost:.4f}{Colors.RESET}")
            print(f"  {Colors.BOLD}综合得分: {Colors.GREEN if comprehensive_score >= 80 else Colors.YELLOW}{comprehensive_score:.1f}/100{Colors.RESET}\n")
            
            comparison_table.append({
                'model': model,
                'success_rate': success_rate,
                'avg_time': avg_time,
                'avg_tokens': avg_tokens,
                'avg_quality': avg_quality,
                'avg_cost': avg_cost,
                'comprehensive_score': comprehensive_score
            })
        
        # 推荐
        if comparison_table:
            best_model = max(comparison_table, key=lambda x: x['comprehensive_score'])
            print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
            print(f"{Colors.GREEN}{Colors.BOLD}🏆 推荐模型: {best_model['model'].upper()}{Colors.RESET}")
            print(f"{Colors.GREEN}综合得分: {best_model['comprehensive_score']:.1f}/100{Colors.RESET}")
            print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
        
        # 保存详细结果
        report_file = f"ai_model_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': datetime.now().isoformat(),
                'test_cases': len(self.test_cases),
                'models_tested': self.available_models,
                'detailed_results': self.results,
                'summary': comparison_table,
                'recommendation': best_model if comparison_table else None
            }, f, ensure_ascii=False, indent=2)
        
        print(f"{Colors.GREEN}✅ 详细结果已保存到: {report_file}{Colors.RESET}\n")
    
    def load_test_cases(self) -> List[Dict]:
        """加载测试用例"""
        return [
            {
                'name': '需求理解引擎',
                'prompt': '''
客户需求：
我们是汽车制造企业，需要一套自动化装配线。
产能要求：100件/小时
自动化程度：95%以上
需要集成视觉检测和机器人装配

请分析并提取关键需求信息，以JSON格式返回。
''',
                'keywords': ['汽车', '装配线', '100', '95', '视觉检测', '机器人'],
                'min_length': 300,
                'temperature': 0.3,
                'max_tokens': 1000
            },
            {
                'name': '方案生成引擎',
                'prompt': '''
基于以下需求生成完整技术方案：
- 行业: 汽车制造
- 产能: 100件/小时
- 自动化程度: 95%
- 关键技术: 视觉检测、机器人装配

请包含：系统架构、设备清单、工艺流程、技术参数
''',
                'keywords': ['架构', '设备', '工艺', '参数', '机器人', '视觉'],
                'min_length': 800,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            {
                'name': '成本估算模型',
                'prompt': '''
预估项目成本：
- 项目类型: 汽车装配线
- 规模: 中型
- 自动化程度: 95%
- 设备数量: 10台
- 工期: 6个月

请提供详细成本估算（设备、人工、实施、调试等）
''',
                'keywords': ['成本', '设备费', '人工', '实施', '调试', '总计'],
                'min_length': 400,
                'temperature': 0.5,
                'max_tokens': 1500
            },
            {
                'name': '报价单生成',
                'prompt': '''
生成专业报价单：
- 项目: 汽车零部件装配线
- 预算范围: ¥500万

包括：设备清单、工程服务、售后服务、付款条件
''',
                'keywords': ['报价', '设备', '服务', '付款', '总计'],
                'min_length': 500,
                'temperature': 0.5,
                'max_tokens': 1500
            }
        ]


def main():
    """主函数"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}")
    print("AI 模型对比测试工具")
    print(f"{'=' * 60}{Colors.RESET}\n")
    
    # 检查环境变量
    print(f"{Colors.YELLOW}📌 环境检查:{Colors.RESET}")
    print(f"  ZHIPU_API_KEY: {'✅ 已配置' if os.getenv('ZHIPU_API_KEY') and os.getenv('ZHIPU_API_KEY') != 'your_zhipu_api_key_here' else '❌ 未配置'}")
    print(f"  OPENAI_API_KEY: {'✅ 已配置' if os.getenv('OPENAI_API_KEY') else '❌ 未配置'}")
    print(f"  KIMI_API_KEY: {'✅ 已配置' if os.getenv('KIMI_API_KEY') else '❌ 未配置'}")
    
    if not any([
        os.getenv('ZHIPU_API_KEY') and os.getenv('ZHIPU_API_KEY') != 'your_zhipu_api_key_here',
        os.getenv('OPENAI_API_KEY'),
        os.getenv('KIMI_API_KEY')
    ]):
        print(f"\n{Colors.YELLOW}⚠️  未配置任何API Key，将使用Mock模式测试{Colors.RESET}")
    
    print()
    
    # 运行对比测试
    comparison = ModelComparison()
    comparison.run_comparison()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
