# -*- coding: utf-8 -*-
"""
知识提取服务
从已解决工单自动提取知识，生成知识库文章和解决方案模板
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.issue import SolutionTemplate
from app.models.service import KnowledgeBase, ServiceTicket
from app.utils.number_generator import generate_sequential_no
from app.utils.db_helpers import save_obj


def auto_extract_knowledge_from_ticket(
    db: Session,
    ticket: ServiceTicket,
    auto_publish: bool = True
) -> Optional[KnowledgeBase]:
    """
    从工单自动提取知识

    Args:
        db: 数据库会话
        ticket: 服务工单
        auto_publish: 是否自动发布

    Returns:
        创建的知识库文章，如果提取失败则返回None
    """
    # 检查工单是否已关闭且有解决方案
    if ticket.status != "CLOSED" or not ticket.solution:
        return None

    # 必须有处理人才能提取知识（避免使用硬编码用户ID）
    if not ticket.assigned_to_id:
        return None

    # 检查是否已经提取过知识（通过标题或内容匹配）
    existing = None
    if ticket.ticket_no:
        existing_query = db.query(KnowledgeBase)
        existing_query = apply_keyword_filter(
            existing_query,
            KnowledgeBase,
            ticket.ticket_no,
            "title",
            use_ilike=False,
        )
        existing = existing_query.first()
    if existing:
        return existing

    # 生成文章编号
    article_no = generate_sequential_no(
        db=db,
        model_class=KnowledgeBase,
        no_field='article_no',
        prefix='KB',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )

    # 构建知识库文章
    title = f"问题解决方案：{ticket.problem_type} - {ticket.ticket_no}"

    content_parts = []
    content_parts.append(f"## 问题描述\n\n{ticket.problem_desc}\n\n")

    if ticket.root_cause:
        content_parts.append(f"## 根本原因\n\n{ticket.root_cause}\n\n")

    if ticket.solution:
        content_parts.append(f"## 解决方案\n\n{ticket.solution}\n\n")

    if ticket.preventive_action:
        content_parts.append(f"## 预防措施\n\n{ticket.preventive_action}\n\n")

    content_parts.append("## 相关信息\n\n")
    content_parts.append(f"- 工单号：{ticket.ticket_no}\n")
    content_parts.append(f"- 问题类型：{ticket.problem_type}\n")
    content_parts.append(f"- 紧急程度：{ticket.urgency}\n")
    if ticket.project:
        content_parts.append(f"- 项目：{ticket.project.project_name}\n")
    if ticket.resolved_time:
        content_parts.append(f"- 解决时间：{ticket.resolved_time.strftime('%Y-%m-%d %H:%M')}\n")

    content = "".join(content_parts)

    # 确定分类
    category_map = {
        "SOFTWARE": "软件问题",
        "MECHANICAL": "机械问题",
        "ELECTRICAL": "电气问题",
        "OPERATION": "操作问题",
        "OTHER": "其他问题"
    }
    category = category_map.get(ticket.problem_type, "其他问题")

    # 构建标签（JSON格式）
    tags = [ticket.problem_type, ticket.urgency]
    if ticket.project:
        tags.append(f"项目:{ticket.project.project_code}")

    # 创建知识库文章
    article = KnowledgeBase(
        article_no=article_no,
        title=title,
        category=category,
        content=content,
        tags=tags,  # JSON字段会自动序列化
        is_faq=False,
        is_featured=False,
        status="PUBLISHED" if auto_publish else "DRAFT",
        author_id=ticket.assigned_to_id,
        author_name=ticket.assigned_to_name or "系统",
    )

    save_obj(db, article)

    # 同时创建解决方案模板
    create_solution_template_from_ticket(db, ticket, article)

    return article


def create_solution_template_from_ticket(
    db: Session,
    ticket: ServiceTicket,
    knowledge_article: Optional[KnowledgeBase] = None
) -> Optional[SolutionTemplate]:
    """
    从工单创建解决方案模板
    """
    if not ticket.solution:
        return None

    # 检查是否已存在模板
    existing = None
    if ticket.ticket_no:
        existing_query = db.query(SolutionTemplate)
        existing_query = apply_keyword_filter(
            existing_query,
            SolutionTemplate,
            ticket.ticket_no,
            "template_code",
            use_ilike=False,
        )
        existing = existing_query.first()
    if existing:
        return existing

    # 生成模板编码
    template_code = f"SOL-{ticket.ticket_no}"

    # 构建解决方案步骤（简单拆分）
    solution_steps = []
    solution_lines = ticket.solution.split('\n')
    step_num = 1
    for line in solution_lines:
        line = line.strip()
        if line and not line.startswith('#'):
            solution_steps.append({
                "step": step_num,
                "description": line,
                "expected_result": "问题解决"
            })
            step_num += 1

    # 创建解决方案模板
    template = SolutionTemplate(
        template_name=f"解决方案模板：{ticket.problem_type}",
        template_code=template_code,
        issue_type="DEFECT",  # 默认类型
        category="CUSTOMER",
        severity=ticket.urgency.upper() if ticket.urgency else "MEDIUM",
        solution=ticket.solution,
        solution_steps=solution_steps if solution_steps else None,
        applicable_scenarios=f"适用于{ticket.problem_type}类型的问题",
        prerequisites="需要确认问题描述准确",
        precautions=ticket.preventive_action or "注意预防措施",
        tags=[ticket.problem_type, ticket.urgency] if ticket.problem_type and ticket.urgency else [],
        keywords=[ticket.problem_type, ticket.urgency] if ticket.problem_type and ticket.urgency else [],
        source_issue_id=None,  # 如果有关联问题可以设置
        created_by=ticket.assigned_to_id,
        created_by_name=ticket.assigned_to_name or "系统",
        is_active=True,
        is_public=True,
    )

    save_obj(db, template)

    return template


def recommend_knowledge_for_ticket(
    db: Session,
    ticket: ServiceTicket,
    limit: int = 5
) -> list:
    """
    为工单推荐相关知识库文章
    """
    # 基于问题类型和紧急程度推荐
    recommendations = db.query(KnowledgeBase).filter(
        KnowledgeBase.status == "PUBLISHED"
    )

    # 优先匹配问题类型
    if ticket.problem_type:
        recommendations = recommendations.filter(
            KnowledgeBase.tags.contains([ticket.problem_type])
        )

    # 限制数量并排序
    recommendations = recommendations.order_by(
        KnowledgeBase.view_count.desc(),
        KnowledgeBase.created_at.desc()
    ).limit(limit).all()

    result = []
    for article in recommendations:
        result.append({
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "category": article.category,
            "view_count": article.view_count,
            "like_count": article.like_count,
        })

    return result
