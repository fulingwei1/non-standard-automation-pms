#!/usr/bin/env python3
"""
AI 模型对比测试（独立版本）
直接测试 GLM-5, Kimi, GPT-4（Mock模式）
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List

# Mock AI 客户端服务
class MockAIClient:
    """Mock AI 客户端（用于演示）"""
    
    def __init__(self):
        self.models_config = {
            'glm-5': {
                'avg_time': 3.5,
                'tokens_multiplier': 1.2,
                'quality_base': 4.0,
                'cost_per_1k': 0.10
            },
            'kimi': {
                'avg_time': 2.8,
                'tokens_multiplier': 0.8,
                'quality_base': 3.7,
                'cost_per_1k': 0.08
            },
            'gpt-4': {
                'avg_time': 4.2,
                'tokens_multiplier': 1.5,
                'quality_base': 4.3,
                'cost_per_1k': 0.30
            }
        }
    
    def generate_solution(self, prompt: str, model: str, **kwargs) -> Dict:
        """模拟生成方案"""
        import random
        
        config = self.models_config.get(model, self.models_config['glm-5'])
        
        # 模拟响应时间
        time.sleep(config['avg_time'] * random.uniform(0.8, 1.2))
        
        # 模拟Token消耗
        prompt_tokens = len(prompt) // 4
        completion_tokens = int(prompt_tokens * config['tokens_multiplier'])
        total_tokens = prompt_tokens + completion_tokens
        
        # 生成Mock内容
        content = self._generate_mock_content(prompt, model)
        
        return {
            'content': content,
            'model': f"{model}-mock",
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens
            }
        }
    
    def _generate_mock_content(self, prompt: str, model: str) -> str:
        """生成Mock内容"""
        if '需求' in prompt or '分析' in prompt:
            return f"""
# 需求分析报告 (由 {model.upper()} 生成)

## 核心需求
- **行业**: 汽车制造
- **产能**: 100件/小时
- **自动化程度**: 95%
- **关键技术**: 视觉检测、机器人装配

## 技术要求
1. 高精度视觉检测系统
2. 六轴机器人装配单元
3. PLC控制系统
4. 数据采集与监控

## 预估规模
- 设备投资: ¥300-400万
- 工期: 4-6个月
- 人员需求: 5-8人

## 风险评估
- 技术难度: 中等
- 时间风险: 低
- 成本风险: 中
"""
        
        elif '方案' in prompt or '架构' in prompt:
            return f"""
# 技术方案 (由 {model.upper()} 生成)

## 系统架构
```
┌─────────────────┐
│   MES系统       │
└────────┬────────┘
         │
┌────────┴────────┐
│  PLC控制系统    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ 视觉  │ │ 机器人│
│ 检测  │ │ 装配  │
└───────┘ └───────┘
```

## 设备清单
1. **视觉检测系统** (2套) - ¥80万
2. **六轴机器人** (3台) - ¥150万
3. **PLC控制柜** (1套) - ¥30万
4. **输送线系统** (1套) - ¥40万

## 工艺流程
1. 上料 → 2. 视觉定位 → 3. 机器人抓取 → 4. 装配 → 5. 检测 → 6. 下料

## 技术参数
- 节拍: 36秒/件
- 精度: ±0.05mm
- 自动化率: 95%
"""
        
        elif '成本' in prompt or '预算' in prompt:
            return f"""
# 成本估算报告 (由 {model.upper()} 生成)

## 设备成本
- 视觉系统: ¥80万
- 机器人: ¥150万
- 控制系统: ¥30万
- 输送系统: ¥40万
- **小计**: ¥300万

## 实施成本
- 系统集成: ¥50万
- 现场安装: ¥20万
- 调试培训: ¥15万
- **小计**: ¥85万

## 其他费用
- 设计费: ¥10万
- 差旅费: ¥5万
- **小计**: ¥15万

## 总计
**¥400万** (含税)
"""
        
        elif '报价' in prompt:
            return f"""
# 商务报价单 (由 {model.upper()} 生成)

项目名称: 汽车零部件装配线
报价日期: 2026-02-15

## 设备明细
| 序号 | 名称 | 规格型号 | 数量 | 单价(万) | 金额(万) |
|------|------|---------|------|---------|---------|
| 1 | 视觉检测系统 | VIS-2000 | 2 | 40 | 80 |
| 2 | 六轴机器人 | ROBOT-600 | 3 | 50 | 150 |
| 3 | PLC控制系统 | S7-1500 | 1 | 30 | 30 |
| 4 | 输送线系统 | CONV-100 | 1 | 40 | 40 |

设备小计: ¥300万

## 工程服务
- 系统集成: ¥50万
- 安装调试: ¥35万
- 培训服务: ¥15万

服务小计: ¥100万

## 商务条款
- 合同总价: ¥400万 (含税)
- 付款方式: 3-3-3-1
- 交货期: 120天
- 质保: 12个月

有效期: 30天
"""
        else:
            return f"Mock response from {model.upper()}: " + prompt[:200]


class ModelComparison:
    """模型对比测试"""
    
    def __init__(self):
        self.client = MockAIClient()
        self.models = ['glm-5', 'kimi', 'gpt-4']
        self.results = []
    
    def run_comparison(self):
        """运行对比测试"""
        print("=" * 70)
        print("🔬 AI 模型对比测试 (Mock 演示版)")
        print("=" * 70)
        print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("📌 说明: 这是演示版本，使用Mock数据模拟真实API响应\n")
        
        test_cases = self.load_test_cases()
        
        for idx, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*70}")
            print(f"📝 测试用例 {idx}: {test_case['name']}")
            print("=" * 70)
            
            case_result = {
                'case_id': idx,
                'case_name': test_case['name'],
                'models': {}
            }
            
            for model in self.models:
                print(f"\n🤖 测试模型: {model.upper()}")
                print("-" * 70)
                
                result = self.test_model(model, test_case)
                case_result['models'][model] = result
                self.print_result(result)
            
            self.results.append(case_result)
            self.compare_case_results(case_result)
        
        self.generate_final_report()
    
    def test_model(self, model: str, test_case: Dict) -> Dict:
        """测试单个模型"""
        start_time = time.time()
        
        try:
            response = self.client.generate_solution(
                prompt=test_case['prompt'],
                model=model
            )
            
            elapsed = time.time() - start_time
            tokens = response['usage']['total_tokens']
            
            # 计算成本
            cost_per_1k = self.client.models_config[model]['cost_per_1k']
            cost = tokens / 1000 * cost_per_1k
            
            # 质量评分
            quality = self.evaluate_quality(
                response['content'],
                test_case
            )
            
            return {
                'success': True,
                'response_time': round(elapsed, 2),
                'tokens': tokens,
                'cost': round(cost, 4),
                'quality': quality,
                'content': response['content']
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def evaluate_quality(self, content: str, test_case: Dict) -> float:
        """评估质量"""
        score = 3.0
        
        keywords = test_case.get('keywords', [])
        if keywords:
            matched = sum(1 for kw in keywords if kw in content)
            score += (matched / len(keywords)) * 1.5
        
        if len(content) >= test_case.get('min_length', 500):
            score += 0.5
        
        return min(5.0, round(score, 1))
    
    def print_result(self, result: Dict):
        """打印结果"""
        if result['success']:
            print(f"  ✅ 成功")
            print(f"  ⏱️  响应时间: {result['response_time']}秒")
            print(f"  📊 Token消耗: {result['tokens']}")
            print(f"  💰 预估成本: ¥{result['cost']}")
            print(f"  ⭐ 质量评分: {result['quality']}/5.0")
            print(f"  📝 内容长度: {len(result['content'])} 字符")
        else:
            print(f"  ❌ 失败: {result.get('error', '未知错误')}")
    
    def compare_case_results(self, case_result: Dict):
        """对比单个用例结果"""
        print(f"\n{'='*70}")
        print(f"📊 对比分析: {case_result['case_name']}")
        print("=" * 70)
        
        models_data = []
        for model, result in case_result['models'].items():
            if result['success']:
                models_data.append({
                    'model': model,
                    'time': result['response_time'],
                    'tokens': result['tokens'],
                    'cost': result['cost'],
                    'quality': result['quality']
                })
        
        if not models_data:
            print("⚠️  所有模型测试失败")
            return
        
        # 找出最优
        fastest = min(models_data, key=lambda x: x['time'])
        cheapest = min(models_data, key=lambda x: x['cost'])
        best_quality = max(models_data, key=lambda x: x['quality'])
        
        # 计算性价比
        for data in models_data:
            data['value'] = data['quality'] / data['cost'] if data['cost'] > 0 else 0
        best_value = max(models_data, key=lambda x: x['value'])
        
        print(f"\n🏆 最快: {fastest['model'].upper()} ({fastest['time']}秒)")
        print(f"💵 最便宜: {cheapest['model'].upper()} (¥{cheapest['cost']})")
        print(f"⭐ 最高质量: {best_quality['model'].upper()} ({best_quality['quality']}/5)")
        print(f"🎯 最佳性价比: {best_value['model'].upper()} ({best_value['value']:.1f})")
    
    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*70}")
        print("📊 最终对比报告")
        print("=" * 70)
        
        # 统计
        stats = {model: {
            'total_time': 0,
            'total_tokens': 0,
            'total_cost': 0,
            'total_quality': 0,
            'count': 0
        } for model in self.models}
        
        for case_result in self.results:
            for model, result in case_result['models'].items():
                if result['success']:
                    stats[model]['total_time'] += result['response_time']
                    stats[model]['total_tokens'] += result['tokens']
                    stats[model]['total_cost'] += result['cost']
                    stats[model]['total_quality'] += result['quality']
                    stats[model]['count'] += 1
        
        # 打印对比表
        print(f"\n{'模型':<10} {'平均时间':<12} {'平均Token':<12} {'平均成本':<12} {'平均质量':<12} {'综合得分':<12}")
        print("-" * 70)
        
        scores = []
        for model, stat in stats.items():
            if stat['count'] > 0:
                avg_time = stat['total_time'] / stat['count']
                avg_tokens = stat['total_tokens'] / stat['count']
                avg_cost = stat['total_cost'] / stat['count']
                avg_quality = stat['total_quality'] / stat['count']
                
                # 综合得分
                quality_score = (avg_quality / 5) * 100
                speed_score = min((2.0 / avg_time * 100), 100) if avg_time > 0 else 0
                cost_score = min((0.10 / avg_cost * 100), 100) if avg_cost > 0 else 0
                
                comprehensive = (
                    quality_score * 0.4 +
                    speed_score * 0.3 +
                    cost_score * 0.3
                )
                
                scores.append({
                    'model': model,
                    'score': comprehensive
                })
                
                print(f"{model.upper():<10} {avg_time:.2f}秒{'':<6} {avg_tokens:.0f}{'':<7} ¥{avg_cost:.4f}{'':<6} {avg_quality:.1f}/5{'':<7} {comprehensive:.1f}/100")
        
        # 推荐
        if scores:
            best = max(scores, key=lambda x: x['score'])
            print(f"\n{'='*70}")
            print(f"🏆 推荐模型: {best['model'].upper()}")
            print(f"📊 综合得分: {best['score']:.1f}/100")
            print("=" * 70)
        
        # 保存报告
        report_file = f"ai_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': datetime.now().isoformat(),
                'results': self.results,
                'summary': stats,
                'recommendation': best if scores else None
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 详细报告已保存: {report_file}\n")
    
    def load_test_cases(self) -> List[Dict]:
        """加载测试用例"""
        return [
            {
                'name': '需求理解引擎',
                'prompt': '客户需求：汽车制造企业，需要自动化装配线，产能100件/小时，自动化程度95%以上，集成视觉检测和机器人装配。请分析并提取关键需求。',
                'keywords': ['汽车', '装配线', '100', '95', '视觉', '机器人'],
                'min_length': 300
            },
            {
                'name': '方案生成引擎',
                'prompt': '基于汽车制造行业，产能100件/小时，自动化程度95%，包含视觉检测和机器人装配的需求，生成完整技术方案（系统架构、设备清单、工艺流程）。',
                'keywords': ['架构', '设备', '工艺', '参数'],
                'min_length': 800
            },
            {
                'name': '成本估算模型',
                'prompt': '项目类型：汽车装配线，规模中型，自动化程度95%，设备10台，工期6个月。请提供详细成本估算。',
                'keywords': ['成本', '设备费', '人工', '实施'],
                'min_length': 400
            },
            {
                'name': '报价单生成',
                'prompt': '生成汽车零部件装配线的专业报价单，预算¥500万，包括设备清单、工程服务、售后服务、付款条件。',
                'keywords': ['报价', '设备', '服务', '付款'],
                'min_length': 500
            }
        ]


if __name__ == '__main__':
    comparison = ModelComparison()
    comparison.run_comparison()
