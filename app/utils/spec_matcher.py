# -*- coding: utf-8 -*-
"""
规格匹配器
"""

import re
from decimal import Decimal
from difflib import SequenceMatcher
from typing import Any, Dict, Optional

from app.models.technical_spec import TechnicalSpecRequirement
from app.utils.spec_extractor import SpecExtractor


def _extract_numeric(value: Any) -> Optional[float]:
    """从带单位后缀的字符串中提取数值部分，如 '24V' -> 24.0"""
    s = str(value).strip()
    m = re.match(r'^([+-]?\d+\.?\d*)', s)
    if m:
        return float(m.group(1))
    return None


def _get_attr(obj: Any, name: str) -> Any:
    """获取属性值，兼容 callable（方法）和普通属性"""
    val = getattr(obj, name, None)
    if callable(val):
        return val()
    return val


class SpecMatchResult:
    """规格匹配结果"""
    def __init__(
        self,
        match_status: str,
        match_score: Optional[Decimal] = None,
        differences: Optional[Dict[str, Any]] = None
    ):
        self.match_status = match_status
        self.match_score = match_score
        self.differences = differences


class SpecMatcher:
    """规格匹配器"""

    def __init__(self):
        self.extractor = SpecExtractor()
        self.match_threshold = Decimal('80.0')  # 匹配度阈值（80%）

    def match_specification(
        self,
        requirement: TechnicalSpecRequirement,
        actual_spec: str,
        actual_brand: Optional[str] = None,
        actual_model: Optional[str] = None
    ) -> SpecMatchResult:
        """
        智能匹配规格要求与实际规格

        Args:
            requirement: 规格要求
            actual_spec: 实际规格
            actual_brand: 实际品牌
            actual_model: 实际型号

        Returns:
            匹配结果
        """
        differences = {}
        scores = []

        # 兼容属性和方法访问
        req_specification = _get_attr(requirement, 'specification') or ''
        req_brand = _get_attr(requirement, 'brand')
        req_model = _get_attr(requirement, 'model')
        req_key_parameters = _get_attr(requirement, 'key_parameters')
        # 兼容 requirement_level 和 requirementment_level（部分调用方拼写不同）
        req_requirement_level = _get_attr(requirement, 'requirement_level') or _get_attr(requirement, 'requirementment_level')

        # 1. 文本相似度匹配（规格型号）
        spec_similarity = self._text_similarity(
            req_specification.lower(),
            actual_spec.lower()
        )
        scores.append(('specification', spec_similarity * 100))

        if spec_similarity < 0.8:
            differences['specification'] = {
                'required': req_specification,
                'actual': actual_spec,
                'similarity': spec_similarity
            }

        # 2. 品牌匹配检查
        if req_brand:
            if actual_brand:
                brand_match = req_brand.lower() == actual_brand.lower()
                if not brand_match:
                    differences['brand'] = {
                        'required': req_brand,
                        'actual': actual_brand
                    }
                scores.append(('brand', 100 if brand_match else 0))
            else:
                differences['brand'] = {
                    'required': req_brand,
                    'actual': None,
                    'missing': True
                }
                scores.append(('brand', 0))

        # 3. 型号匹配检查
        if req_model:
            if actual_model:
                model_match = req_model.lower() == actual_model.lower()
                if not model_match:
                    differences['model'] = {
                        'required': req_model,
                        'actual': actual_model
                    }
                scores.append(('model', 100 if model_match else 0))
            else:
                differences['model'] = {
                    'required': req_model,
                    'actual': None,
                    'missing': True
                }
                scores.append(('model', 0))

        # 4. 关键参数提取和对比
        required_params = req_key_parameters or {}
        actual_params = self.extractor.extract_key_parameters(actual_spec)

        # 仅在实际参数可提取时进行参数对比和评分
        if required_params and actual_params:
            param_differences = self._compare_parameters(required_params, actual_params)
            if param_differences:
                differences['parameters'] = param_differences

            param_score = self._calculate_param_score(required_params, actual_params)
            scores.append(('parameters', param_score))

        # 5. 计算总体匹配度（加权平均）
        if scores:
            # 规格型号权重50%，品牌20%，型号20%，参数10%
            weights = {
                'specification': 0.5,
                'brand': 0.2,
                'model': 0.2,
                'parameters': 0.1
            }

            total_score = Decimal('0')
            total_weight = Decimal('0')

            for key, score in scores:
                weight = weights.get(key, 0.1)
                total_score += Decimal(str(score)) * Decimal(str(weight))
                total_weight += Decimal(str(weight))

            match_score = (total_score / total_weight) if total_weight > 0 else Decimal('0')
        else:
            match_score = Decimal('0')

        # 6. 确定匹配状态
        if match_score >= self.match_threshold and not differences:
            match_status = 'MATCHED'
        elif match_score >= self.match_threshold and differences:
            # 有差异但匹配度足够高，可能是非关键差异
            match_status = 'MATCHED' if req_requirement_level != 'STRICT' else 'MISMATCHED'
        elif match_score < Decimal('50.0'):
            match_status = 'UNKNOWN'
        else:
            match_status = 'MISMATCHED'

        return SpecMatchResult(
            match_status=match_status,
            match_score=match_score,
            differences=differences if differences else None
        )

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（使用SequenceMatcher，大小写不敏感）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1）
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _compare_parameters(
        self,
        required: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比关键参数，返回差异

        Args:
            required: 要求的参数
            actual: 实际的参数

        Returns:
            差异字典
        """
        differences = {}

        for key, required_value in required.items():
            actual_value = actual.get(key)

            if actual_value is None:
                differences[key] = {
                    'required': required_value,
                    'actual': None,
                    'missing': True
                }
            else:
                # 数值比较（支持带单位后缀的值如 '24V', '100W'）
                req_num = _extract_numeric(required_value)
                act_num = _extract_numeric(actual_value)

                if req_num is not None and act_num is not None:
                    # 允许5%的相对误差（与 _calculate_param_score 一��）
                    if abs(req_num - act_num) / max(abs(req_num), 0.01) > 0.05:
                        differences[key] = {
                            'required': required_value,
                            'actual': actual_value,
                            'deviation': abs(req_num - act_num)
                        }
                else:
                    # 非数值，直接比较字符串
                    if str(required_value).lower() != str(actual_value).lower():
                        differences[key] = {
                            'required': required_value,
                            'actual': actual_value
                        }

        return differences

    def _calculate_param_score(
        self,
        required: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """
        计算参数匹配度

        Args:
            required: 要求的参数
            actual: 实际的参数

        Returns:
            匹配度（0-100）
        """
        if not required:
            return 100.0

        matched_count = 0
        total_count = len(required)

        for key, required_value in required.items():
            actual_value = actual.get(key)

            if actual_value is not None:
                # 数值比较（支持带单位后缀的值如 '24V', '100W'）
                req_num = _extract_numeric(required_value)
                act_num = _extract_numeric(actual_value)

                if req_num is not None and act_num is not None:
                    # 允许5%的误差
                    if abs(req_num - act_num) / max(abs(req_num), 0.01) <= 0.05:
                        matched_count += 1
                else:
                    if str(required_value).lower() == str(actual_value).lower():
                        matched_count += 1

        return (matched_count / total_count) * 100 if total_count > 0 else 0.0




