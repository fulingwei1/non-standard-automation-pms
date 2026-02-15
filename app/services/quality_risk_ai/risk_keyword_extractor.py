# -*- coding: utf-8 -*-
"""
质量风险关键词提取器
从工作日志中提取质量风险信号关键词
"""

import re
from typing import List, Dict, Any
from datetime import datetime


class RiskKeywordExtractor:
    """质量风险关键词提取器"""
    
    # 质量风险关键词库
    RISK_KEYWORDS = {
        'BUG': [
            'bug', 'Bug', 'BUG', 'defect', '缺陷', '错误', 
            '问题', '故障', '异常', '失败', '报错', '崩溃',
            'crash', 'error', 'fail', '不稳定', '闪退'
        ],
        'PERFORMANCE': [
            '性能', '慢', '卡顿', '延迟', '超时', 'timeout',
            'slow', '响应慢', '加载慢', '卡', '占用', '内存',
            'memory', 'cpu', '资源', 'lag', '掉帧'
        ],
        'STABILITY': [
            '不稳定', '偶现', '随机', '概率性', '时而', 
            '稳定性', 'unstable', 'random', '间歇', '重现',
            '复现', '难复现', '必现', '经常', '频繁'
        ],
        'COMPATIBILITY': [
            '兼容', '适配', '版本', '环境', '系统', '浏览器',
            'compatible', 'compatibility', '不支持', '无法运行',
            '平台', 'iOS', 'Android', 'Windows', 'Mac'
        ],
        'CRITICAL': [
            '严重', '紧急', 'critical', 'urgent', '致命',
            '阻塞', 'block', 'blocker', '无法使用', '不可用',
            '数据丢失', '数据错误', '安全', 'security'
        ],
        'REWORK': [
            '返工', '重做', '重写', '改', '修改', '调整',
            'refactor', '优化', '改进', '重构', '再次',
            '又', '还是', '依然', '仍然'
        ],
        'DELAY': [
            '延期', '推迟', '延后', 'delay', '滞后',
            '进度慢', '落后', '超期', '逾期', '晚了'
        ]
    }
    
    # 异常模式（正则表达式）
    ABNORMAL_PATTERNS = [
        {
            'name': '频繁修复',
            'pattern': r'(修复|fix|解决).{0,20}(bug|问题|错误)',
            'severity': 'MEDIUM'
        },
        {
            'name': '多次返工',
            'pattern': r'(再次|又|重新|又一次).{0,20}(修改|调整|返工)',
            'severity': 'HIGH'
        },
        {
            'name': '阻塞问题',
            'pattern': r'(阻塞|block|无法|不能).{0,30}(继续|进行|推进)',
            'severity': 'CRITICAL'
        },
        {
            'name': '性能问题',
            'pattern': r'(性能|卡|慢|延迟).{0,20}(问题|严重|明显)',
            'severity': 'HIGH'
        },
        {
            'name': '不稳定',
            'pattern': r'(偶现|随机|概率|时而|不稳定)',
            'severity': 'MEDIUM'
        }
    ]
    
    def extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        从文本中提取风险关键词
        
        Args:
            text: 工作日志文本
            
        Returns:
            按类别分组的关键词列表
        """
        found_keywords = {}
        
        for category, keywords in self.RISK_KEYWORDS.items():
            found = []
            for keyword in keywords:
                if keyword in text:
                    found.append(keyword)
            if found:
                found_keywords[category] = list(set(found))  # 去重
        
        return found_keywords
    
    def detect_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        检测文本中的异常模式
        
        Args:
            text: 工作日志文本
            
        Returns:
            检测到的异常模式列表
        """
        detected_patterns = []
        
        for pattern_def in self.ABNORMAL_PATTERNS:
            matches = re.findall(pattern_def['pattern'], text, re.IGNORECASE)
            if matches:
                detected_patterns.append({
                    'name': pattern_def['name'],
                    'severity': pattern_def['severity'],
                    'matches': matches,
                    'count': len(matches)
                })
        
        return detected_patterns
    
    def calculate_risk_score(
        self, 
        keywords: Dict[str, List[str]], 
        patterns: List[Dict[str, Any]]
    ) -> float:
        """
        基于关键词和模式计算风险评分
        
        Args:
            keywords: 提取的关键词
            patterns: 检测到的异常模式
            
        Returns:
            风险评分 (0-100)
        """
        score = 0.0
        
        # 关键词评分
        category_weights = {
            'CRITICAL': 20,
            'BUG': 15,
            'REWORK': 12,
            'DELAY': 10,
            'PERFORMANCE': 8,
            'STABILITY': 8,
            'COMPATIBILITY': 5
        }
        
        for category, kw_list in keywords.items():
            weight = category_weights.get(category, 5)
            score += len(kw_list) * weight
        
        # 异常模式评分
        pattern_weights = {
            'CRITICAL': 25,
            'HIGH': 15,
            'MEDIUM': 10,
            'LOW': 5
        }
        
        for pattern in patterns:
            weight = pattern_weights.get(pattern['severity'], 5)
            score += pattern['count'] * weight
        
        # 归一化到0-100
        return min(100.0, score)
    
    def determine_risk_level(self, score: float) -> str:
        """
        根据评分确定风险等级
        
        Args:
            score: 风险评分
            
        Returns:
            风险等级: LOW/MEDIUM/HIGH/CRITICAL
        """
        if score >= 75:
            return 'CRITICAL'
        elif score >= 50:
            return 'HIGH'
        elif score >= 25:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        综合分析文本的质量风险
        
        Args:
            text: 工作日志文本
            
        Returns:
            分析结果字典
        """
        keywords = self.extract_keywords(text)
        patterns = self.detect_patterns(text)
        score = self.calculate_risk_score(keywords, patterns)
        level = self.determine_risk_level(score)
        
        return {
            'risk_keywords': keywords,
            'abnormal_patterns': patterns,
            'risk_score': round(score, 2),
            'risk_level': level,
            'keyword_count': sum(len(v) for v in keywords.values()),
            'pattern_count': len(patterns),
            'analyzed_at': datetime.now().isoformat()
        }
