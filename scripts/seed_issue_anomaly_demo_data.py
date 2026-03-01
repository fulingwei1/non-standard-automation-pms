#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题异常演示数据脚本（任务 3/6）

生成：
- 技术问题 30 条
- 质量问题 20 条
- 交付问题 15 条
- 问题跟进记录 50 条

特点：
- 问题描述具体，贴近非标自动化设备项目场景
- 状态分布可控（OPEN / IN_PROGRESS / RESOLVED）
- 每条问题都有明确负责人
- 时间分布覆盖近 4 个月，且状态流转合理
"""

from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# 兼容从 scripts/ 目录直接执行
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.models.base import get_db_session
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.project import Project
from app.models.user import User

DEMO_TAG = "DEMO_ISSUE_ANOMALY_TASK3"
RANDOM_SEED = 20260301


def _display_name(user: User) -> str:
    return user.real_name or user.username or f"用户{user.id}"


def _priority_to_severity(priority: str) -> str:
    return {"CRITICAL": "CRITICAL", "HIGH": "MAJOR"}.get(priority, "MINOR")


def _priority_to_impact(priority: str) -> str:
    return {"CRITICAL": "CRITICAL", "HIGH": "HIGH"}.get(priority, "MEDIUM")


def _build_issue_blueprints() -> list[dict]:
    """构造 65 条问题蓝图（不含时间和负责人）"""

    blueprints: list[dict] = []

    technical_challenges = [
        ("伺服轴重复定位偏差超标", "A轴重复定位偏差0.18mm，超出规格0.05mm，导致插针工位连续3次NG。"),
        ("视觉定位误判率偏高", "相机在高反光壳体上误判率4.6%，超出<1%要求，影响自动补偿逻辑。"),
        ("PLC扫描周期超限", "主站PLC扫描周期稳定在42ms，超出节拍设计上限20ms，触发连锁延时。"),
        ("激光测高数据抖动", "测高模块同一点连续采样标准差0.12mm，超出工艺容差0.03mm。"),
        ("条码追溯接口丢包", "与MES接口在高并发下出现约2.1%写入失败，造成序列号追溯断点。"),
        ("EtherCAT从站偶发掉线", "8小时老化中出现3次从站掉线，恢复时间超过15秒，影响产线连续性。"),
        ("气动响应时间不稳定", "同一阀组动作时间在280~510ms波动，未达到工艺窗口(<=350ms)。"),
        ("工控机内存占用异常", "上位机运行6小时后内存占用由35%升至92%，触发界面卡顿。"),
        ("数据缓存队列阻塞", "测试结果缓存队列峰值达12k条，延迟超过90秒，实时看板数据滞后。"),
        ("扭矩采集通道漂移", "CH3扭矩零点每班次漂移约0.32N·m，导致拧紧判定边界不稳定。"),
    ]
    technical_design_changes = [
        ("客户新增双工位并行节拍需求", "客户将CT目标由18秒压缩至11秒，现有单工位机构无法满足并行节拍。"),
        ("治具定位基准变更", "客户将产品定位基准由外壳孔位改为电芯边界，现治具定位销需重构。"),
        ("安规门锁方案变更", "客户要求门锁联锁由单回路升级为双回路冗余，原电气图纸不兼容。"),
        ("产品尺寸公差收紧", "客户最新图纸将关键尺寸公差从±0.2mm收紧至±0.08mm，夹具精度不足。"),
        ("扫码规范升级为三码绑定", "客户追溯规则新增SN+PN+LOT三码绑定，现程序仅支持双码校验。"),
        ("通讯协议切换到OPC UA", "原方案为Modbus TCP，客户IT合规要求切换OPC UA并开启证书认证。"),
        ("老化温控区间上调", "客户将老化温控由45±3℃改为55±2℃，现加热功率与风道设计不足。"),
        ("HMI交互流程调整", "客户要求将调试参数权限细分到4级角色，当前HMI仅支持2级权限。"),
        ("防错策略改为强制互锁", "客户审计要求关键工步强制互锁，现流程仍允许人工跳步。"),
        ("测试报告字段新增16项", "客户质量部新增SPC字段与追溯字段，现报表模板缺少16个列项。"),
    ]
    technical_spec_mismatch = [
        ("FAT节拍实测与规格不符", "FAT实测CT均值22.4秒，高于合同规格20秒上限，瓶颈在扫码+写站环节。"),
        ("绝缘耐压项判定阈值错误", "程序使用1.5mA判定阈值，合同技术协议要求1.0mA。"),
        ("上位机日志保留周期不足", "当前仅保留30天日志，客户验收标准明确要求至少180天。"),
        ("多语言界面翻译缺项", "德语界面存在27处未翻译字段，未满足出口项目交付规范。"),
        ("设备噪声指标超标", "满负载运行噪声实测78dB，超出客户协议75dB限制。"),
        ("防护门开关寿命未达标", "型式试验仅通过12万次开合，技术规格要求20万次。"),
        ("产线换型时间偏长", "实测换型耗时26分钟，较投标承诺15分钟偏差过大。"),
        ("测试覆盖率低于承诺", "软件自动测试覆盖率82%，低于客户协议要求90%。"),
        ("报警响应时延超规格", "关键报警到HMI弹窗平均延迟2.4秒，规格要求<=1秒。"),
        ("备份恢复流程不完整", "系统仅支持手动备份，不满足验收条款中的一键恢复要求。"),
    ]

    quality_incoming = [
        ("来料伺服驱动器批次虚焊", "IQC抽检发现驱动器功率板虚焊，48台中检出6台温升异常。"),
        ("气缸密封圈硬度不达标", "供应商来料密封圈邵氏硬度实测48A，图纸要求60±5A。"),
        ("工控网线水晶头压接不良", "入厂网线抽检回波损耗不合格率12%，导致通讯稳定性风险。"),
        ("接近开关触发距离离散", "同批次接近开关触发距离偏差达3.2mm，超出验收标准1.0mm。"),
        ("继电器触点镀层异常", "来料继电器触点氧化，接触电阻上升至180mΩ，规范要求<100mΩ。"),
        ("导轨直线度超差", "导轨抽检直线度0.19mm/m，超过采购规范0.08mm/m。"),
        ("治具铝件表面阳极膜偏薄", "检测阳极膜厚6μm，低于图纸要求10±2μm，存在耐蚀风险。"),
    ]
    quality_process = [
        ("装配扭矩执行偏差", "装配线M6锁付扭矩抽检偏差达18%，存在松脱风险。"),
        ("线束压接不良率抬升", "近3天线束压接不良率由0.8%升至3.6%，集中在夜班工位。"),
        ("焊接工装重复精度异常", "焊接工装重复精度由0.05mm恶化至0.14mm，影响结构同轴度。"),
        ("老化测试中温漂超限", "老化8小时后电流采样温漂达2.8%，超过工艺上限1.5%。"),
        ("喷码附着力不稳定", "喷码百格测试2B，不满足客户要求4B，追溯码存在脱落风险。"),
        ("OQC抽检误判率偏高", "出货前OQC视觉复判不一致率4.1%，超出质量目标1%。"),
        ("ESD防护执行不到位", "巡检发现2个工位腕带接地阻值超标，ESD记录缺失。"),
    ]
    quality_customer = [
        ("客户投诉SAT阶段误报频发", "客户现场连续生产中每小时触发2~3次误报警，影响线体节拍。"),
        ("客户反馈治具磨损过快", "治具在2周内出现定位销磨损，低于合同承诺寿命6个月。"),
        ("客户投诉报表统计口径错误", "日报良率统计未排除返修品，导致管理层数据决策偏差。"),
        ("客户反馈开机自检时间过长", "现场开机自检平均9分钟，客户要求不超过3分钟。"),
        ("客户投诉扫码枪偶发死机", "客户夜班高频扫码场景下，扫码枪2天内出现5次无响应。"),
        ("客户反馈远程诊断连接失败", "VPN隧道在跨厂区访问时成功率仅70%，影响售后效率。"),
    ]

    delivery_delay_risk = [
        ("总装排期存在延期风险", "关键总装工位与电气调试排程冲突，预计影响总交付节点5天。"),
        ("现场联调窗口压缩", "客户通知产线停线窗口缩短为3天，当前联调计划需5天。"),
        ("关键评审节点待确认", "客户设计冻结评审推迟2周，后续采购与装配链路被动顺延。"),
        ("发运前验收准备不足", "FAT资料包尚缺4份校准报告，存在发运前卡点风险。"),
        ("海外项目清关时效不确定", "报关代理反馈目的港抽检概率上升，预计运输周期波动7~10天。"),
    ]
    delivery_material_shortage = [
        ("关键PLC模块交期缺口", "供应商确认PLC CPU交期延后21天，当前库存无法覆盖本项目需求。"),
        ("伺服电机缺料", "17台伺服电机因上游磁钢限产无法按期到货，影响主装进度。"),
        ("工业相机镜头短缺", "高分辨率镜头库存仅余4支，距需求尚差11支，替代料未验证。"),
        ("安全继电器到货不齐", "安全继电器到货率仅58%，导致安规回路装配无法闭环。"),
        ("气动阀岛备件不足", "阀岛主件被临时调拨，当前缺口9套，影响调试与老化计划。"),
    ]
    delivery_capacity_shortage = [
        ("电气装配产能不足", "电气装配班组请假与新项目并发，周产能缺口约32工时。"),
        ("软件调试工程师排班冲突", "两条产线同时进入联调，软件工程师人力仅满足60%。"),
        ("机械加工外协产能吃紧", "外协厂周排产超载，机加工件预计延后7天返厂。"),
        ("OQC检验窗口不足", "月底集中出货导致OQC检验资源排队，平均等待时长达2.5天。"),
        ("现场实施团队人手不足", "华东与华南项目并行上线，现场实施人力缺口3人。"),
    ]

    for title, description in technical_challenges:
        blueprints.append(
            {
                "type_key": "technical",
                "category": "TECHNICAL",
                "issue_type": "QUESTION",
                "subtype": "technical_challenge",
                "title": title,
                "description": description,
                "root_cause": "DESIGN_ERROR",
            }
        )
    for title, description in technical_design_changes:
        blueprints.append(
            {
                "type_key": "technical",
                "category": "TECHNICAL",
                "issue_type": "DEVIATION",
                "subtype": "design_change",
                "title": title,
                "description": description,
                "root_cause": "DESIGN_ERROR",
            }
        )
    for title, description in technical_spec_mismatch:
        blueprints.append(
            {
                "type_key": "technical",
                "category": "TECHNICAL",
                "issue_type": "DEFECT",
                "subtype": "spec_mismatch",
                "title": title,
                "description": description,
                "root_cause": "PROCESS_ERROR",
            }
        )

    for title, description in quality_incoming:
        blueprints.append(
            {
                "type_key": "quality",
                "category": "QUALITY",
                "issue_type": "DEFECT",
                "subtype": "incoming_defect",
                "title": title,
                "description": description,
                "root_cause": "MATERIAL_DEFECT",
            }
        )
    for title, description in quality_process:
        blueprints.append(
            {
                "type_key": "quality",
                "category": "QUALITY",
                "issue_type": "DEVIATION",
                "subtype": "process_abnormal",
                "title": title,
                "description": description,
                "root_cause": "PROCESS_ERROR",
            }
        )
    for title, description in quality_customer:
        blueprints.append(
            {
                "type_key": "quality",
                "category": "QUALITY",
                "issue_type": "QUESTION",
                "subtype": "customer_complaint",
                "title": title,
                "description": description,
                "root_cause": "OTHER",
            }
        )

    for title, description in delivery_delay_risk:
        blueprints.append(
            {
                "type_key": "delivery",
                "category": "SCHEDULE",
                "issue_type": "RISK",
                "subtype": "delay_risk",
                "title": title,
                "description": description,
                "root_cause": "EXTERNAL_FACTOR",
            }
        )
    for title, description in delivery_material_shortage:
        blueprints.append(
            {
                "type_key": "delivery",
                "category": "RESOURCE",
                "issue_type": "BLOCKER",
                "subtype": "material_shortage",
                "title": title,
                "description": description,
                "root_cause": "MATERIAL_DEFECT",
            }
        )
    for title, description in delivery_capacity_shortage:
        blueprints.append(
            {
                "type_key": "delivery",
                "category": "RESOURCE",
                "issue_type": "BLOCKER",
                "subtype": "capacity_shortage",
                "title": title,
                "description": description,
                "root_cause": "EXTERNAL_FACTOR",
            }
        )

    assert len(blueprints) == 65
    return blueprints


def _status_plan() -> list[str]:
    # 技术 30: OPEN 9 / IN_PROGRESS 12 / RESOLVED 9
    technical = ["OPEN"] * 9 + ["IN_PROGRESS"] * 12 + ["RESOLVED"] * 9
    # 质量 20: OPEN 5 / IN_PROGRESS 8 / RESOLVED 7
    quality = ["OPEN"] * 5 + ["IN_PROGRESS"] * 8 + ["RESOLVED"] * 7
    # 交付 15: OPEN 6 / IN_PROGRESS 6 / RESOLVED 3
    delivery = ["OPEN"] * 6 + ["IN_PROGRESS"] * 6 + ["RESOLVED"] * 3
    return technical + quality + delivery


def _priority_plan() -> list[str]:
    # 技术 30: CRITICAL 8 / HIGH 12 / MEDIUM 10
    technical = ["CRITICAL"] * 8 + ["HIGH"] * 12 + ["MEDIUM"] * 10
    # 质量 20: CRITICAL 4 / HIGH 8 / MEDIUM 8
    quality = ["CRITICAL"] * 4 + ["HIGH"] * 8 + ["MEDIUM"] * 8
    # 交付 15: CRITICAL 6 / HIGH 6 / MEDIUM 3
    delivery = ["CRITICAL"] * 6 + ["HIGH"] * 6 + ["MEDIUM"] * 3
    return technical + quality + delivery


def _allocate_issue_times(
    rng: random.Random,
    now: datetime,
    status: str,
    type_key: str,
) -> tuple[datetime, datetime, datetime | None]:
    """按状态分配报出/到期/解决时间"""
    if status == "RESOLVED":
        report_days_ago = rng.randint(45, 120)
        report_at = now - timedelta(days=report_days_ago, hours=rng.randint(1, 18))
        due_at = report_at + timedelta(days=rng.randint(5, 18))
        resolved_at = report_at + timedelta(days=rng.randint(2, 16), hours=rng.randint(1, 8))
        return report_at, due_at, resolved_at

    if status == "IN_PROGRESS":
        report_days_ago = rng.randint(12, 70)
        report_at = now - timedelta(days=report_days_ago, hours=rng.randint(1, 20))
        due_days = rng.randint(4, 16)
        # 交付问题的处理中更容易有延期风险
        if type_key == "delivery" and rng.random() < 0.35:
            due_days = rng.randint(-4, 3)
        due_at = report_at + timedelta(days=due_days)
        return report_at, due_at, None

    # OPEN
    report_days_ago = rng.randint(1, 35)
    report_at = now - timedelta(days=report_days_ago, hours=rng.randint(0, 20))
    due_days = rng.randint(3, 14)
    if type_key == "delivery" and rng.random() < 0.45:
        due_days = rng.randint(-2, 6)
    due_at = report_at + timedelta(days=due_days)
    return report_at, due_at, None


def _purge_old_demo_data(db) -> None:
    old_issues = db.query(Issue).filter(Issue.issue_no.like("IAD26-%")).all()
    if not old_issues:
        return
    old_ids = [item.id for item in old_issues]
    db.query(IssueFollowUpRecord).filter(IssueFollowUpRecord.issue_id.in_(old_ids)).delete(
        synchronize_session=False
    )
    db.query(Issue).filter(Issue.id.in_(old_ids)).delete(synchronize_session=False)
    db.commit()
    print(f"🧹 已清理历史问题异常演示数据: 问题 {len(old_ids)} 条")


def _pick_users_and_projects(db) -> tuple[list[User], list[Project]]:
    users = db.query(User).filter(User.is_active.is_(True)).order_by(User.id.asc()).all()
    users = [u for u in users if (u.real_name or u.username)]
    projects = db.query(Project).order_by(Project.id.asc()).all()
    if len(users) < 4:
        raise RuntimeError("可用用户不足（至少需要4个激活用户）")
    if not projects:
        raise RuntimeError("缺少项目数据，请先准备项目基础数据")
    return users, projects


def seed_issue_anomaly_data() -> None:
    rng = random.Random(RANDOM_SEED)
    now = datetime.now()

    with get_db_session() as db:
        _purge_old_demo_data(db)

        users, projects = _pick_users_and_projects(db)
        blueprints = _build_issue_blueprints()
        status_plan = _status_plan()
        priority_plan = _priority_plan()

        assert len(blueprints) == len(status_plan) == len(priority_plan) == 65

        issues: list[Issue] = []
        type_counters = Counter()
        status_counters = Counter()
        priority_counters = Counter()

        # 固定顺序，保证每次数据可重复
        project_ids = [p.id for p in projects[:24]]
        if len(project_ids) < 8:
            project_ids = [p.id for p in projects]

        for idx, blueprint in enumerate(blueprints, start=1):
            status = status_plan[idx - 1]
            priority = priority_plan[idx - 1]
            report_at, due_at, resolved_at = _allocate_issue_times(
                rng=rng,
                now=now,
                status=status,
                type_key=blueprint["type_key"],
            )

            reporter = users[(idx + 1) % len(users)]
            assignee = users[(idx + 3) % len(users)]
            responsible = users[(idx + 4) % len(users)]
            project_id = project_ids[(idx * 3) % len(project_ids)]

            issue_no = f"IAD26-{idx:03d}"
            issue_title = f"[{blueprint['type_key'].upper()}] {blueprint['title']}"

            solution = None
            resolved_by = None
            resolved_by_name = None
            if status == "RESOLVED":
                solution = (
                    f"已完成根因定位与整改闭环：{blueprint['description']} "
                    f"整改后通过复测，相关SOP与点检表已同步更新。"
                )
                resolved_by = assignee.id
                resolved_by_name = _display_name(assignee)

            issue = Issue(
                issue_no=issue_no,
                category=blueprint["category"],
                project_id=project_id,
                issue_type=blueprint["issue_type"],
                severity=_priority_to_severity(priority),
                priority=priority,
                title=issue_title,
                description=blueprint["description"],
                reporter_id=reporter.id,
                reporter_name=_display_name(reporter),
                report_date=report_at,
                assignee_id=assignee.id,
                assignee_name=_display_name(assignee),
                due_date=due_at.date(),
                status=status,
                solution=solution,
                resolved_at=resolved_at,
                resolved_by=resolved_by,
                resolved_by_name=resolved_by_name,
                impact_scope="影响产线节拍、质量稳定性与交付节点",
                impact_level=_priority_to_impact(priority),
                is_blocking=(priority == "CRITICAL" or blueprint["issue_type"] == "BLOCKER"),
                tags=json.dumps([DEMO_TAG, blueprint["type_key"], blueprint["subtype"]], ensure_ascii=False),
                root_cause=blueprint["root_cause"],
                responsible_engineer_id=responsible.id,
                responsible_engineer_name=_display_name(responsible),
                estimated_inventory_loss=round(rng.uniform(1500, 28000), 2),
                estimated_extra_hours=round(rng.uniform(6, 96), 2),
            )
            db.add(issue)
            issues.append(issue)

            type_counters[blueprint["type_key"]] += 1
            status_counters[status] += 1
            priority_counters[priority] += 1

        db.flush()

        # 生成 50 条跟进记录（覆盖重点问题）
        follow_ups: list[IssueFollowUpRecord] = []
        resolved_issues = [i for i in issues if i.status == "RESOLVED"]
        in_progress_issues = [i for i in issues if i.status == "IN_PROGRESS"]
        open_issues = [i for i in issues if i.status == "OPEN"]

        issue_followup_times: dict[int, list[datetime]] = defaultdict(list)

        # 1) 已解决问题：10条问题，各2条状态流转记录 = 20
        for issue in resolved_issues[:10]:
            owner = users[(issue.id + 2) % len(users)]
            ts1 = issue.report_date + timedelta(days=1, hours=rng.randint(1, 5))
            ts2 = (issue.resolved_at or ts1 + timedelta(days=2)) - timedelta(hours=rng.randint(1, 4))

            f1 = IssueFollowUpRecord(
                issue_id=issue.id,
                follow_up_type="STATUS_CHANGE",
                content="已完成初步定位，问题状态变更为处理中，安排专项攻关。",
                operator_id=owner.id,
                operator_name=_display_name(owner),
                old_status="OPEN",
                new_status="IN_PROGRESS",
                created_at=ts1,
                updated_at=ts1,
            )
            f2 = IssueFollowUpRecord(
                issue_id=issue.id,
                follow_up_type="STATUS_CHANGE",
                content="整改完成并复测通过，状态更新为已解决，待项目经理确认闭环。",
                operator_id=owner.id,
                operator_name=_display_name(owner),
                old_status="IN_PROGRESS",
                new_status="RESOLVED",
                created_at=ts2,
                updated_at=ts2,
            )
            follow_ups.extend([f1, f2])
            issue_followup_times[issue.id].extend([ts1, ts2])

        # 2) 处理中问题：15条问题，各1条状态更新 = 15
        for issue in in_progress_issues[:15]:
            owner = users[(issue.id + 3) % len(users)]
            ts1 = issue.report_date + timedelta(hours=rng.randint(8, 60))
            f1 = IssueFollowUpRecord(
                issue_id=issue.id,
                follow_up_type="STATUS_CHANGE",
                content="已完成责任人分派与排障计划，状态更新为处理中。",
                operator_id=owner.id,
                operator_name=_display_name(owner),
                old_status="OPEN",
                new_status="IN_PROGRESS",
                created_at=ts1,
                updated_at=ts1,
            )
            follow_ups.append(f1)
            issue_followup_times[issue.id].append(ts1)

        # 3) 待处理问题：15条问题，各1条分派记录 = 15
        for issue in open_issues[:15]:
            owner = users[(issue.id + 1) % len(users)]
            ts1 = issue.report_date + timedelta(hours=rng.randint(2, 20))
            f1 = IssueFollowUpRecord(
                issue_id=issue.id,
                follow_up_type="ASSIGNMENT",
                content="已指派责任工程师，要求24小时内提交根因分析与临时遏制措施。",
                operator_id=owner.id,
                operator_name=_display_name(owner),
                old_status=None,
                new_status="OPEN",
                created_at=ts1,
                updated_at=ts1,
            )
            follow_ups.append(f1)
            issue_followup_times[issue.id].append(ts1)

        assert len(follow_ups) == 50
        db.add_all(follow_ups)

        # 回写问题跟进计数和最后跟进时间
        for issue in issues:
            times = issue_followup_times.get(issue.id, [])
            issue.follow_up_count = len(times)
            issue.last_follow_up_at = max(times) if times else None

        db.commit()

        # 统计输出
        status_by_type: dict[str, Counter] = {
            "technical": Counter(),
            "quality": Counter(),
            "delivery": Counter(),
        }
        for issue, blueprint in zip(issues, blueprints):
            status_by_type[blueprint["type_key"]][issue.status] += 1

        print("\n✅ 问题异常演示数据生成完成")
        print("-" * 64)
        print("问题类型数量：")
        print(f"  技术问题: {type_counters['technical']}")
        print(f"  质量问题: {type_counters['quality']}")
        print(f"  交付问题: {type_counters['delivery']}")
        print(f"  问题总数: {len(issues)}")

        print("\n状态分布（整体）：")
        for s in ["OPEN", "IN_PROGRESS", "RESOLVED"]:
            print(f"  {s}: {status_counters[s]}")

        print("\n状态分布（分类型）：")
        for type_key, label in [
            ("technical", "技术问题"),
            ("quality", "质量问题"),
            ("delivery", "交付问题"),
        ]:
            dist = status_by_type[type_key]
            print(
                f"  {label}: OPEN={dist['OPEN']}, "
                f"IN_PROGRESS={dist['IN_PROGRESS']}, RESOLVED={dist['RESOLVED']}"
            )

        print("\n优先级分布：")
        for p in ["CRITICAL", "HIGH", "MEDIUM"]:
            print(f"  {p}: {priority_counters[p]}")

        covered_issue_count = sum(1 for issue in issues if issue.follow_up_count > 0)
        print("\n跟进记录：")
        print(f"  跟进总数: {len(follow_ups)}")
        print(f"  已覆盖问题数: {covered_issue_count}")
        print(f"  覆盖问题平均跟进数: {len(follow_ups) / covered_issue_count:.2f}")
        print(f"  演示标记: {DEMO_TAG}")
        print("-" * 64)


if __name__ == "__main__":
    seed_issue_anomaly_data()
