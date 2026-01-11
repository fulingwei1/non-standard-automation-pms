from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.models.project import ProjectStage, ProjectStatus, Project


def generate_project_code(db: Session) -> str:
    """
    生成项目编码：PJyymmddxxx
    
    格式：PJ + 年月日(6位) + 序号(3位)
    示例：PJ250901001
    """
    from app.utils.number_generator import generate_sequential_no
    
    return generate_sequential_no(
        db=db,
        model_class=Project,
        no_field='project_code',
        prefix='PJ',
        date_format='%y%m%d',
        separator='',  # 无分隔符
        seq_length=3
    )


def init_project_stages(db: Session, project_id: int):
    """
    为新项目初始化标准阶段和状态
    """
    stages_config = [
        ("S1", "需求进入", 1, "客户需求初步接收"),
        ("S2", "需求澄清", 2, "深入了解需求细节"),
        ("S3", "立项评审", 3, "技术可行性与商务评审"),
        ("S4", "方案设计", 4, "机械/电气/软件方案设计"),
        ("S5", "采购制造", 5, "物料采购与加工"),
        ("S6", "装配联调", 6, "机械装配与系统联调"),
        ("S7", "出厂验收", 7, "厂内FAT验收"),
        ("S8", "现场交付", 8, "发货、安装、SAT"),
        ("S9", "质保结项", 9, "质保期服务与结项"),
    ]

    statuses_map = {
        "S1": [
            ("ST01", "待补全资料", 1, "客户资料不完整，等待补充"),
            ("ST02", "需求评估中", 2, "初步评估需求可行性"),
        ],
        "S2": [
            ("ST03", "待安排澄清", 1, "等待安排需求澄清会议"),
            ("ST04", "澄清进行中", 2, "需求澄清会议/现场调研中"),
            ("ST05", "待客户确认", 3, "需求规格书待客户确认"),
        ],
        "S3": [
            ("ST06", "待评审", 1, "等待安排立项评审"),
            ("ST07", "评审中", 2, "立项评审进行中"),
            ("ST08", "待签合同", 3, "评审通过，等待签订合同"),
        ],
        "S4": [
            ("ST09", "方案设计中", 1, "机械/电气/软件方案设计"),
            ("ST10", "设计评审中", 2, "方案评审进行中"),
            ("ST11", "BOM发布中", 3, "BOM编制与发布"),
        ],
        "S5": [
            ("ST12", "采购下单中", 1, "物料采购下单"),
            ("ST13", "等待到货", 2, "等待物料到货"),
            ("ST14", "缺料阻塞", 3, "关键物料缺货，影响进度"),
            ("ST15", "外协加工中", 4, "外协件加工中"),
        ],
        "S6": [
            ("ST16", "待排产", 1, "等待排产装配"),
            ("ST17", "装配中", 2, "机械装配进行中"),
            ("ST18", "联调中", 3, "系统联调进行中"),
            ("ST19", "技术阻塞", 4, "技术问题导致阻塞"),
        ],
        "S7": [
            ("ST20", "待FAT", 1, "等待安排FAT验收"),
            ("ST21", "FAT进行中", 2, "FAT验收进行中"),
            ("ST22", "FAT整改中", 3, "FAT不通过，整改中"),
        ],
        "S8": [
            ("ST23", "待发货", 1, "等待安排发货"),
            ("ST24", "运输中", 2, "设备运输中"),
            ("ST25", "SAT进行中", 3, "现场SAT验收中"),
            ("ST26", "SAT整改中", 4, "SAT不通过，整改中"),
            ("ST27", "待终验签字", 5, "等待客户终验签字"),
        ],
        "S9": [
            ("ST28", "质保服务中", 1, "质保期内服务"),
            ("ST29", "待结项", 2, "等待结项审批"),
            ("ST30", "已结项", 3, "项目已结项"),
        ],
    }

    for code, name, order, desc in stages_config:
        stage = ProjectStage(
            project_id=project_id,
            stage_code=code,
            stage_name=name,
            stage_order=order,
            description=desc,
            status="PENDING",
        )
        db.add(stage)
        db.flush()  # 获取 stage.id

        if code in statuses_map:
            for s_code, s_name, s_order, s_desc in statuses_map[code]:
                status = ProjectStatus(
                    stage_id=stage.id,
                    status_code=s_code,
                    status_name=s_name,
                    status_order=s_order,
                    description=s_desc,
                )
                db.add(status)

    db.commit()
