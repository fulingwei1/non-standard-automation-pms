"""
PM介入时机判断服务
基于符哥2026-02-15确认的策略
"""
from typing import Dict, List, Optional
from datetime import datetime


class PMInvolvementService:
    """PM介入时机判断服务"""
    
    # 阈值配置（符哥确认）
    LARGE_PROJECT_THRESHOLD = 100  # 大项目金额阈值（万元）
    SIMILAR_PROJECT_MIN = 3  # 相似项目数量最低要求
    RISK_FACTOR_THRESHOLD = 2  # 风险因素触发数
    
    @classmethod
    def judge_pm_involvement_timing(cls, project_data: Dict) -> Dict:
        """
        判断PM介入时机
        
        Args:
            project_data: 项目数据
                {
                    "项目金额": 150,  # 万元
                    "项目类型": "SMT贴片生产线",
                    "行业": "汽车电子",
                    "是否首次做": False,
                    "历史相似项目数": 2,
                    "失败项目数": 1,
                    "是否有标准方案": False,
                    "技术创新点": ["视觉检测新算法", "多工位协同"]
                }
        
        Returns:
            {
                "建议": "PM提前介入" | "PM签约后介入",
                "介入阶段": "技术评审/需求调研阶段" | "合同签订后",
                "风险等级": "高" | "低",
                "风险因素数": 4,
                "原因": [...],
                "下一步行动": [...]
            }
        """
        high_risk_factors = 0
        reasons = []
        
        # 1. 大项目（≥100万）
        if project_data.get('项目金额', 0) >= cls.LARGE_PROJECT_THRESHOLD:
            high_risk_factors += 1
            reasons.append(f"大型项目（{project_data['项目金额']}万）")
        
        # 2. 技术难度高（以前没做过）
        if project_data.get('是否首次做', False):
            high_risk_factors += 1
            reasons.append("以前没做过该类型项目")
        
        # 3. 技术难度高（有失败经验）
        failed_count = project_data.get('失败项目数', 0)
        if failed_count > 0:
            high_risk_factors += 1
            reasons.append(f"相似项目有失败经验（{failed_count}次）")
        
        # 4. 缺少经验（<3个相似项目）
        similar_count = project_data.get('历史相似项目数', 0)
        if similar_count < cls.SIMILAR_PROJECT_MIN:
            high_risk_factors += 1
            reasons.append(f"相似项目经验不足（仅{similar_count}个）")
        
        # 5. 无标准方案
        if not project_data.get('是否有标准方案', False):
            high_risk_factors += 1
            reasons.append("无标准化方案模板")
        
        # 6. 技术创新
        innovation_points = project_data.get('技术创新点', [])
        if innovation_points and len(innovation_points) > 0:
            high_risk_factors += 1
            reasons.append(f"涉及技术创新（{len(innovation_points)}项）")
        
        # 判断结果（≥2个风险因素就提前介入）
        if high_risk_factors >= cls.RISK_FACTOR_THRESHOLD:
            return {
                "建议": "PM提前介入",
                "介入阶段": "技术评审/需求调研阶段",
                "风险等级": "高",
                "风险因素数": high_risk_factors,
                "原因": reasons,
                "下一步行动": [
                    "1. 立即通知PMO负责人安排PM",
                    "2. 组织技术评审会（邀请PM参加）",
                    "3. PM参与客户需求调研",
                    "4. PM审核成本和工期估算"
                ],
                "需要PM审核": True,
                "紧急程度": "高" if high_risk_factors >= 4 else "中"
            }
        else:
            return {
                "建议": "PM签约后介入",
                "介入阶段": "合同签订后",
                "风险等级": "低",
                "风险因素数": high_risk_factors,
                "原因": reasons if reasons else ["成熟项目，风险可控"],
                "下一步行动": [
                    "1. 售前完成方案设计和报价",
                    "2. 签约后通知PMO安排PM",
                    "3. PM组织项目启动会"
                ],
                "需要PM审核": False,
                "紧急程度": "低"
            }
    
    @classmethod
    def get_similar_project_count(cls, project_type: str, industry: str) -> Dict:
        """
        查询历史相似项目数量和失败数量
        
        Args:
            project_type: 项目类型（如"SMT贴片生产线"）
            industry: 行业（如"汽车电子"）
        
        Returns:
            {
                "总数": 5,
                "成功数": 4,
                "失败数": 1,
                "成功率": 0.8
            }
        """
        # TODO: 从数据库查询历史项目
        # 这里先返回模拟数据
        return {
            "总数": 0,
            "成功数": 0,
            "失败数": 0,
            "成功率": 0.0
        }
    
    @classmethod
    def check_has_standard_solution(cls, project_type: str) -> bool:
        """
        检查是否有标准方案模板
        
        Args:
            project_type: 项目类型
        
        Returns:
            True/False
        """
        # TODO: 从方案模板库查询
        return False
    
    @classmethod
    def auto_judge_from_ticket(cls, ticket_id: int) -> Dict:
        """
        从售前工单自动判断PM介入时机
        
        Args:
            ticket_id: 售前工单ID
        
        Returns:
            判断结果
        """
        # TODO: 从数据库获取工单信息
        # ticket = db.query(PresaleTicket).filter_by(id=ticket_id).first()
        
        # 模拟数据
        project_data = {
            "项目金额": 0,
            "项目类型": "",
            "行业": "",
            "是否首次做": False,
            "历史相似项目数": 0,
            "失败项目数": 0,
            "是否有标准方案": False,
            "技术创新点": []
        }
        
        return cls.judge_pm_involvement_timing(project_data)
    
    @classmethod
    def generate_notification_message(cls, result: Dict, ticket_info: Dict) -> str:
        """
        生成通知消息
        
        Args:
            result: 判断结果
            ticket_info: 工单信息
        
        Returns:
            消息文本
        """
        if result['需要PM审核']:
            return f"""⚠️ 【高风险项目】需PM提前介入

项目：{ticket_info.get('项目名称', 'N/A')}
客户：{ticket_info.get('客户名称', 'N/A')}
金额：{ticket_info.get('预估金额', 0)}万

风险因素（{result['风险因素数']}个）：
{chr(10).join(['✗ ' + r for r in result['原因']])}

建议行动：
{chr(10).join(result['下一步行动'])}

紧急程度：{result['紧急程度']}
请PMO负责人尽快安排PM！
"""
        else:
            return f"""✅ 【常规项目】按正常流程推进

项目：{ticket_info.get('项目名称', 'N/A')}
客户：{ticket_info.get('客户名称', 'N/A')}
金额：{ticket_info.get('预估金额', 0)}万

风险评估：{result['风险等级']}
{chr(10).join(result['原因'])}

{chr(10).join(result['下一步行动'])}
"""


# 测试代码
if __name__ == "__main__":
    # 测试案例1：高风险项目
    test_data_high_risk = {
        "项目金额": 150,
        "项目类型": "SMT贴片生产线",
        "行业": "汽车电子",
        "是否首次做": False,
        "历史相似项目数": 2,
        "失败项目数": 1,
        "是否有标准方案": False,
        "技术创新点": ["视觉检测新算法", "多工位协同"]
    }
    
    print("=" * 60)
    print("测试案例1：高风险项目")
    print("=" * 60)
    result1 = PMInvolvementService.judge_pm_involvement_timing(test_data_high_risk)
    print(f"建议：{result1['建议']}")
    print(f"介入阶段：{result1['介入阶段']}")
    print(f"风险等级：{result1['风险等级']}")
    print(f"风险因素数：{result1['风险因素数']}")
    print(f"原因：")
    for reason in result1['原因']:
        print(f"  - {reason}")
    print(f"下一步行动：")
    for action in result1['下一步行动']:
        print(f"  {action}")
    
    # 测试案例2：低风险项目
    test_data_low_risk = {
        "项目金额": 50,
        "项目类型": "视觉检测系统",
        "行业": "消费电子",
        "是否首次做": False,
        "历史相似项目数": 5,
        "失败项目数": 0,
        "是否有标准方案": True,
        "技术创新点": []
    }
    
    print("\n" + "=" * 60)
    print("测试案例2：低风险项目")
    print("=" * 60)
    result2 = PMInvolvementService.judge_pm_involvement_timing(test_data_low_risk)
    print(f"建议：{result2['建议']}")
    print(f"介入阶段：{result2['介入阶段']}")
    print(f"风险等级：{result2['风险等级']}")
    print(f"风险因素数：{result2['风险因素数']}")
    print(f"原因：")
    for reason in result2['原因']:
        print(f"  - {reason}")
    print(f"下一步行动：")
    for action in result2['下一步行动']:
        print(f"  {action}")
    
    # 测试通知消息生成
    print("\n" + "=" * 60)
    print("测试通知消息生成")
    print("=" * 60)
    ticket_info = {
        "项目名称": "SMT贴片生产线自动化改造",
        "客户名称": "某汽车电子公司",
        "预估金额": 150
    }
    msg = PMInvolvementService.generate_notification_message(result1, ticket_info)
    print(msg)
