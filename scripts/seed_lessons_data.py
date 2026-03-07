#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验教训库种子数据
创建 8-10 条示例经验教训，覆盖不同项目、分类和类型
"""

import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = "data/pms.db"

# 示例数据
LESSONS_DATA = [
    {
        "project_id": 1,
        "title": "需求变更管理流程优化",
        "category": "management",
        "lesson_type": "improvement",
        "description": "在项目执行过程中，客户频繁提出需求变更，导致项目进度严重延误。初期没有建立规范的变更控制流程，所有变更都直接实施。",
        "root_cause": "缺乏正式的变更控制委员会（CCB）和变更评估流程，变更影响分析不到位。",
        "action_taken": "建立了变更控制流程，所有变更需经过 CCB 审批，并评估对进度、成本的影响。实施变更请求单制度。",
        "recommendation": "所有项目应在启动阶段就建立变更控制流程，明确变更审批权限和影响评估机制。建议变更超过 3 次/月时触发项目复盘。",
        "impact_level": "high",
        "applicable_to": "所有软件开发项目",
        "tags": "需求管理，变更控制，流程优化",
        "reviewed": 1,
    },
    {
        "project_id": 2,
        "title": "关键技术选型失误导致返工",
        "category": "technical",
        "lesson_type": "failure",
        "description": "项目初期选择了不成熟的技术框架，后期发现性能无法满足要求，导致核心模块需要重构，延误项目 2 个月。",
        "root_cause": "技术选型时未进行充分的 PoC 验证，过于关注新技术的先进性而忽视了成熟度和团队掌握程度。",
        "action_taken": "组织技术评审会，邀请外部专家参与关键技术选型决策。建立技术选型评估 checklist，包括性能、成熟度、团队能力等维度。",
        "recommendation": "关键技术选型必须进行 PoC 验证，评估维度应包含：性能指标、社区活跃度、团队学习成本、长期维护风险。建议建立公司级技术雷达。",
        "impact_level": "high",
        "applicable_to": "所有研发项目",
        "tags": "技术选型，架构设计，风险评估",
        "reviewed": 1,
    },
    {
        "project_id": 3,
        "title": "跨部门协作沟通机制建立",
        "category": "management",
        "lesson_type": "success",
        "description": "大型项目涉及多个部门协作，通过建立定期沟通机制和明确接口人，有效提升了协作效率，项目按时交付。",
        "root_cause": "NA",
        "action_taken": "建立了周例会制度，各部门指定固定接口人，使用统一的项目管理工具跟踪跨部门任务。",
        "recommendation": "跨部门项目应在启动会就明确沟通机制：周例会时间、参会人员、决策流程。建议使用 RACI 矩阵明确各方职责。",
        "impact_level": "medium",
        "applicable_to": "跨部门协作项目",
        "tags": "沟通管理，协作机制，跨部门",
        "reviewed": 1,
    },
    {
        "project_id": 1,
        "title": "供应商交付延期应对策略",
        "category": "cost",
        "lesson_type": "failure",
        "description": "关键零部件供应商交付延期 3 周，导致整机组装无法按期进行，项目面临违约风险。",
        "root_cause": "单一供应商依赖，未建立备选供应商清单。采购合同中对延期违约责任约定不明确。",
        "action_taken": "紧急启用备选供应商，虽然成本增加 15%，但保证了交付。与主供应商重新谈判，增加延期罚则条款。",
        "recommendation": "关键物料必须建立 AB 供应商机制，保持至少 2 家合格供应商。采购合同应明确延期违约责任和赔偿条款。建议建立供应商绩效评估体系。",
        "impact_level": "high",
        "applicable_to": "采购管理、供应链管理",
        "tags": "供应商管理，采购风险，交付延期",
        "reviewed": 1,
    },
    {
        "project_id": 4,
        "title": "自动化测试覆盖率提升实践",
        "category": "technical",
        "lesson_type": "success",
        "description": "通过建立自动化测试框架，将核心功能的测试覆盖率从 30% 提升至 85%，显著降低了回归测试时间和生产缺陷率。",
        "root_cause": "NA",
        "action_taken": "引入 pytest 测试框架，建立 CI/CD 流水线自动执行测试。制定测试覆盖率目标并纳入代码审查标准。",
        "recommendation": "新项目应从第一天就建立自动化测试，核心业务逻辑覆盖率应达到 80% 以上。建议将测试覆盖率作为代码合并的前置条件。",
        "impact_level": "medium",
        "applicable_to": "软件开发项目",
        "tags": "自动化测试，质量控制，CI/CD",
        "reviewed": 1,
    },
    {
        "project_id": 2,
        "title": "项目进度估算偏差分析",
        "category": "schedule",
        "lesson_type": "failure",
        "description": "项目初期估算 6 个月完成，实际耗时 9 个月，进度偏差达 50%。主要原因是低估了技术难度和需求变更频率。",
        "root_cause": "估算时过于乐观，未考虑技术风险缓冲。采用单一估算方法，缺乏历史数据参考。",
        "action_taken": "引入三点估算法（乐观/悲观/最可能），增加 20% 的风险缓冲时间。建立项目历史数据库，为后续估算提供参考。",
        "recommendation": "项目估算应采用多种方法交叉验证，必须包含风险缓冲（建议 15-25%）。建议建立公司级项目历史数据库，积累估算基准数据。",
        "impact_level": "medium",
        "applicable_to": "项目计划管理",
        "tags": "进度估算，风险管理，项目计划",
        "reviewed": 1,
    },
    {
        "project_id": 5,
        "title": "客户需求管理最佳实践",
        "category": "customer",
        "lesson_type": "success",
        "description": "通过建立客户需求跟踪矩阵和定期确认机制，确保需求理解一致，项目验收一次性通过，客户满意度高。",
        "root_cause": "NA",
        "action_taken": "使用需求跟踪矩阵（RTM）管理所有需求，每个需求都有唯一 ID。每两周与客户确认需求理解，形成书面记录。",
        "recommendation": "所有项目应建立需求跟踪矩阵，确保需求可追溯。建议采用原型或 Demo 方式早期确认需求理解，避免后期返工。",
        "impact_level": "medium",
        "applicable_to": "需求管理、客户沟通",
        "tags": "需求管理，客户沟通，验收管理",
        "reviewed": 1,
    },
    {
        "project_id": 3,
        "title": "代码审查流程优化",
        "category": "quality",
        "lesson_type": "improvement",
        "description": "初期代码审查流于形式，生产环境缺陷率高。优化审查流程后，缺陷率下降 60%。",
        "root_cause": "审查 checklist 不完善，审查人员缺乏培训，审查时间不足。",
        "action_taken": "制定详细的代码审查 checklist，包含安全、性能、可维护性等维度。建立审查人员认证机制，确保审查质量。",
        "recommendation": "代码审查应作为强制流程，核心代码必须经过 2 人以上审查。建议建立审查 checklist 并持续优化，定期组织审查技能培训。",
        "impact_level": "medium",
        "applicable_to": "软件开发项目",
        "tags": "代码审查，质量管理，开发流程",
        "reviewed": 1,
    },
    {
        "project_id": 4,
        "title": "项目文档管理规范化",
        "category": "management",
        "lesson_type": "success",
        "description": "建立统一的项目文档管理体系，所有文档集中存储、版本可控，显著提升知识传承效率和新成员 onboarding 速度。",
        "root_cause": "NA",
        "action_taken": "使用 Confluence 建立项目知识库，定义文档模板和目录结构。制定文档更新流程，确保文档与项目同步。",
        "recommendation": "项目启动时应建立文档目录结构，明确各类文档的责任人和更新频率。建议将文档完整性作为项目结项的前置条件。",
        "impact_level": "low",
        "applicable_to": "所有项目",
        "tags": "文档管理，知识管理，项目规范",
        "reviewed": 1,
    },
    {
        "project_id": 1,
        "title": "性能优化经验总结",
        "category": "technical",
        "lesson_type": "success",
        "description": "通过系统性性能优化，系统响应时间从 2 秒降低至 200ms，用户体验显著提升。",
        "root_cause": "NA",
        "action_taken": "建立性能基线，使用 APM 工具定位瓶颈。优化数据库查询（添加索引、优化 SQL）、引入缓存、异步处理耗时操作。",
        "recommendation": "性能优化应遵循'测量 - 分析 - 优化 - 验证'循环。建议在新项目设计阶段就考虑性能指标，建立性能测试自动化。",
        "impact_level": "high",
        "applicable_to": "系统开发、性能优化",
        "tags": "性能优化，数据库优化，缓存策略",
        "reviewed": 1,
    },
]


def seed_lessons_data():
    """插入经验教训种子数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 检查表是否存在
    cursor.execute(
        """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='lessons_learned'
    """
    )
    if not cursor.fetchone():
        print("❌ lessons_learned 表不存在，请先启动后端创建表")
        conn.close()
        return False

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) as count FROM lessons_learned")
    existing_count = cursor.fetchone()["count"]
    if existing_count > 0:
        print(f"⚠️  已存在 {existing_count} 条经验教训数据，跳过插入")
        conn.close()
        return True

    # 插入数据
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    insert_sql = """
        INSERT INTO lessons_learned (
            project_id, title, category, lesson_type, description,
            root_cause, action_taken, recommendation, impact_level,
            applicable_to, tags, submitted_by, reviewed, created_at, updated_at
        ) VALUES (
            :project_id, :title, :category, :lesson_type, :description,
            :root_cause, :action_taken, :recommendation, :impact_level,
            :applicable_to, :tags, :submitted_by, :reviewed, :now, :now
        )
    """

    inserted_count = 0
    for lesson in LESSONS_DATA:
        try:
            cursor.execute(
                insert_sql,
                {
                    "project_id": lesson["project_id"],
                    "title": lesson["title"],
                    "category": lesson["category"],
                    "lesson_type": lesson["lesson_type"],
                    "description": lesson["description"],
                    "root_cause": lesson["root_cause"],
                    "action_taken": lesson["action_taken"],
                    "recommendation": lesson["recommendation"],
                    "impact_level": lesson["impact_level"],
                    "applicable_to": lesson["applicable_to"],
                    "tags": lesson["tags"],
                    "submitted_by": 1,  # 默认管理员
                    "reviewed": lesson["reviewed"],
                    "now": now,
                },
            )
            inserted_count += 1
        except Exception as e:
            print(f"❌ 插入失败：{lesson['title']} - {e}")

    conn.commit()
    conn.close()

    print(f"✅ 成功插入 {inserted_count} 条经验教训数据")
    return True


if __name__ == "__main__":
    print("📝 开始插入经验教训库种子数据...")
    seed_lessons_data()
    print("\n💡 提示：请访问 /lessons-learned 查看数据")
