# GLM-5 vs Kimi vs GPT-4 对比测试方案

**测试目标**: 全面对比三个AI模型在售前AI系统中的表现  
**测试时间**: 2026-02-15  
**测试方法**: 同一任务并行测试，多维度评估  

---

## 📊 对比维度

### 1. 性能对比
- **响应时间** (秒)
- **Token 消耗**
- **并发能力**

### 2. 质量对比
- **方案生成质量** (1-5分)
- **需求理解准确度** (%)
- **成本估算准确度** (%)
- **赢率预测准确度** (%)

### 3. 成本对比
- **单次调用成本** (¥)
- **月度预估成本** (¥)
- **性价比评分** (质量/成本)

### 4. 稳定性对比
- **成功率** (%)
- **错误率** (%)
- **平均可用性** (%)

---

## 🧪 测试用例

### 用例1: 需求理解引擎
**输入**:
```
客户需求：
我们是汽车制造企业，需要一套自动化装配线。
产能要求：100件/小时
自动化程度：95%以上
需要集成视觉检测和机器人装配
```

**评估指标**:
- 关键信息提取完整度
- 需求分类准确性
- 响应时间
- Token消耗

---

### 用例2: 方案生成引擎
**输入**:
```
基于用例1的需求，生成完整技术方案，包括：
- 系统架构
- 设备清单
- 工艺流程
- 技术参数
```

**评估指标**:
- 方案专业度 (1-5分)
- 方案完整度 (1-5分)
- 方案可行性 (1-5分)
- 生成时间
- Token消耗

---

### 用例3: 成本估算模型
**输入**:
```
项目信息：
- 类型: 汽车装配线
- 规模: 中型
- 自动化程度: 95%
- 设备数量: 10台
- 工期: 6个月
```

**评估指标**:
- 成本估算准确度 (与实际成本对比)
- 成本明细完整度
- 响应时间

---

### 用例4: 赢率预测模型
**输入**:
```
项目特征：
- 客户类型: 大型国企
- 竞争对手: 3家
- 报价: ¥500万
- 关系: 有过合作
- 技术难度: 中等
```

**评估指标**:
- 预测准确度 (对比历史数据)
- 影响因素分析质量
- 响应时间

---

### 用例5: 报价单生成
**输入**:
```
生成专业报价单，包括：
- 设备清单及价格
- 工程服务费
- 售后服务
- 付款条件
```

**评估指标**:
- 报价单专业度
- 价格合理性
- 格式规范性
- 生成时间

---

## 🛠️ 测试脚本

### 自动化测试流程
```python
# test_ai_model_comparison.py

import time
import json
from typing import Dict, List
from app.services.ai_client_service import AIClientService

class ModelComparison:
    """AI模型对比测试"""
    
    def __init__(self):
        self.models = ["glm-5", "kimi", "gpt-4"]
        self.test_cases = self.load_test_cases()
        self.results = []
    
    def run_comparison(self):
        """运行完整对比测试"""
        print("=" * 60)
        print("AI 模型对比测试开始")
        print("=" * 60)
        
        for case_id, test_case in enumerate(self.test_cases, 1):
            print(f"\n📝 测试用例 {case_id}: {test_case['name']}")
            print("-" * 60)
            
            case_results = {
                'case_id': case_id,
                'case_name': test_case['name'],
                'models': {}
            }
            
            for model in self.models:
                print(f"\n🤖 测试模型: {model}")
                result = self.test_single_model(model, test_case)
                case_results['models'][model] = result
                
                # 打印结果
                self.print_result(model, result)
            
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
        
        return result
    
    def evaluate_quality(self, content: str, test_case: Dict) -> float:
        """评估回复质量 (1-5分)"""
        score = 3.0  # 基础分
        
        # 检查关键词
        keywords = test_case.get('keywords', [])
        matched = sum(1 for kw in keywords if kw in content)
        keyword_ratio = matched / len(keywords) if keywords else 0.5
        
        # 检查长度
        min_length = test_case.get('min_length', 500)
        length_ok = len(content) >= min_length
        
        # 检查结构化
        has_structure = any(marker in content for marker in ['```json', '```', '1.', '2.'])
        
        # 综合评分
        score += keyword_ratio * 1.0
        score += 0.5 if length_ok else -0.5
        score += 0.5 if has_structure else 0
        
        return min(5.0, max(1.0, round(score, 1)))
    
    def print_result(self, model: str, result: Dict):
        """打印单次测试结果"""
        if result['success']:
            print(f"  ✅ 成功")
            print(f"  ⏱️  响应时间: {result['response_time']}秒")
            print(f"  📊 Token消耗: {result.get('tokens', 'N/A')}")
            print(f"  ⭐ 质量评分: {result.get('quality_score', 'N/A')}/5")
            print(f"  📝 内容预览: {result.get('content', '')[:100]}...")
        else:
            print(f"  ❌ 失败: {result['error']}")
    
    def compare_results(self, case_results: Dict):
        """对比分析单个用例的结果"""
        print(f"\n📊 对比分析 - {case_results['case_name']}")
        print("-" * 60)
        
        # 收集数据
        models_data = []
        for model, result in case_results['models'].items():
            if result['success']:
                models_data.append({
                    'model': model,
                    'time': result['response_time'],
                    'tokens': result.get('tokens', 0),
                    'quality': result.get('quality_score', 0)
                })
        
        if not models_data:
            print("  ⚠️  所有模型测试失败")
            return
        
        # 找出最优
        fastest = min(models_data, key=lambda x: x['time'])
        most_efficient = min(models_data, key=lambda x: x['tokens'])
        best_quality = max(models_data, key=lambda x: x['quality'])
        
        print(f"  🏆 最快: {fastest['model']} ({fastest['time']}秒)")
        print(f"  💰 最省Token: {most_efficient['model']} ({most_efficient['tokens']} tokens)")
        print(f"  ⭐ 最高质量: {best_quality['model']} ({best_quality['quality']}/5)")
    
    def generate_report(self):
        """生成完整对比报告"""
        print("\n" + "=" * 60)
        print("📊 完整对比报告")
        print("=" * 60)
        
        # 统计每个模型的表现
        model_stats = {model: {
            'success_count': 0,
            'fail_count': 0,
            'total_time': 0,
            'total_tokens': 0,
            'total_quality': 0,
            'test_count': 0
        } for model in self.models}
        
        for case_result in self.results:
            for model, result in case_result['models'].items():
                stats = model_stats[model]
                stats['test_count'] += 1
                
                if result['success']:
                    stats['success_count'] += 1
                    stats['total_time'] += result['response_time']
                    stats['total_tokens'] += result.get('tokens', 0)
                    stats['total_quality'] += result.get('quality_score', 0)
                else:
                    stats['fail_count'] += 1
        
        # 打印统计
        for model, stats in model_stats.items():
            print(f"\n🤖 {model.upper()}")
            print("-" * 60)
            
            success_rate = (stats['success_count'] / stats['test_count'] * 100) if stats['test_count'] > 0 else 0
            avg_time = stats['total_time'] / stats['success_count'] if stats['success_count'] > 0 else 0
            avg_tokens = stats['total_tokens'] / stats['success_count'] if stats['success_count'] > 0 else 0
            avg_quality = stats['total_quality'] / stats['success_count'] if stats['success_count'] > 0 else 0
            
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  平均响应时间: {avg_time:.2f}秒")
            print(f"  平均Token消耗: {avg_tokens:.0f}")
            print(f"  平均质量评分: {avg_quality:.1f}/5")
        
        # 保存详细结果到文件
        with open('ai_model_comparison_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print("\n✅ 详细结果已保存到: ai_model_comparison_results.json")
    
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
                'keywords': ['汽车', '装配线', '100件/小时', '95%', '视觉检测', '机器人'],
                'min_length': 300
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
                'min_length': 800
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
                'keywords': ['成本', '设备费', '人工', '实施', '调试'],
                'min_length': 400
            },
            {
                'name': '报价单生成',
                'prompt': '''
                生成专业报价单：
                - 项目: 汽车零部件装配线
                - 总金额: ¥500万
                
                包括：设备清单、工程服务、售后服务、付款条件
                ''',
                'keywords': ['报价', '设备', '服务', '付款', '总计'],
                'min_length': 500
            }
        ]


if __name__ == '__main__':
    comparison = ModelComparison()
    comparison.run_comparison()
```

---

## 📈 评估矩阵

### 综合评分公式
```
综合得分 = (质量分×40%) + (性能分×30%) + (成本分×20%) + (稳定性分×10%)

其中：
- 质量分 = 平均质量评分 / 5 × 100
- 性能分 = (最慢响应时间 / 当前模型响应时间) × 100
- 成本分 = (最贵成本 / 当前模型成本) × 100
- 稳定性分 = 成功率
```

---

## 📊 预期对比结果

| 维度 | GLM-5 | Kimi | GPT-4 |
|------|-------|------|-------|
| **响应时间** | 3-5秒 | 2-4秒 | 4-6秒 |
| **质量评分** | 4.2/5 | 3.8/5 | 4.5/5 |
| **Token消耗** | 1500 | 800 | 2000 |
| **单次成本** | ¥0.25 | ¥0.20 | ¥0.75 |
| **成功率** | 95% | 90% | 98% |
| **综合得分** | 85 | 78 | 88 |

**预测结论**:
- **GLM-5**: 性价比之王 ⭐⭐⭐⭐⭐
- **Kimi**: 速度快但质量略低 ⭐⭐⭐
- **GPT-4**: 质量最高但成本高 ⭐⭐⭐⭐

---

## 🎯 测试执行计划

### 阶段1: 基础对比（立即）
- [x] 创建测试脚本
- [ ] 配置API Keys（GLM-5, Kimi, GPT-4）
- [ ] 运行5个基础用例
- [ ] 生成初步报告

### 阶段2: 深度测试（1天内）
- [ ] 运行售前AI 10个模块完整测试
- [ ] 长时间稳定性测试
- [ ] 并发压力测试
- [ ] 生成完整报告

### 阶段3: 生产验证（1周内）
- [ ] 小规模灰度测试
- [ ] 收集真实用户反馈
- [ ] 成本数据统计
- [ ] 最终决策

---

## ✅ 决策标准

### 如果 GLM-5 胜出
- 全面切换到 GLM-5
- Kimi/GPT-4 作为备用

### 如果 Kimi 胜出
- 保持 Kimi 为主
- GLM-5 作为备用

### 如果 GPT-4 胜出
- 评估成本接受度
- 可能混合使用（复杂任务用GPT-4，简单任务用GLM-5）

---

**测试方案准备完毕！准备执行对比测试** 🚀
