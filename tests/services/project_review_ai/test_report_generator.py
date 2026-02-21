"""
项目复盘报告生成器测试
测试报告生成、AI总结、数据分析、报告渲染等功能
"""
import pytest
import json
from datetime import datetime, timedelta, date
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from app.services.project_review_ai.report_generator import ProjectReviewReportGenerator
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.project_cost import ProjectCost
from app.models.change_request import ChangeRequest


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock()


@pytest.fixture
def mock_ai_client():
    """模拟AI客户端"""
    client = Mock()
    client.generate_solution.return_value = {
        'content': json.dumps({
            'summary': '项目按时完成，质量良好',
            'success_factors': ['需求明确', '团队协作好', '技术方案合理'],
            'problems': ['测试覆盖不足', '文档更新滞后'],
            'improvements': ['加强测试', '规范文档流程'],
            'best_practices': ['敏捷开发', '持续集成'],
            'conclusion': '整体项目执行良好，有待改进',
            'insights': {'risk_level': 'low'}
        }),
        'token_usage': 1500
    }
    return client


@pytest.fixture
def generator(mock_db, mock_ai_client):
    """创建报告生成器实例"""
    gen = ProjectReviewReportGenerator(mock_db)
    gen.ai_client = mock_ai_client
    return gen


@pytest.fixture
def sample_project():
    """示例项目"""
    project = Mock(spec=Project)
    project.id = 1
    project.code = 'PRJ-001'
    project.name = '测试项目'
    project.description = '项目描述'
    project.status = 'COMPLETED'
    project.project_type = 'CUSTOM'
    project.budget_amount = Decimal('100000.00')
    project.planned_start_date = datetime.now() - timedelta(days=60)
    project.planned_end_date = datetime.now() - timedelta(days=30)
    project.actual_start_date = datetime.now() - timedelta(days=60)
    project.actual_end_date = datetime.now() - timedelta(days=28)
    
    # 模拟客户
    customer = Mock()
    customer.name = '测试客户'
    project.customer = customer
    
    # 模拟团队成员
    member1 = Mock()
    member1.user = Mock()
    member1.user.username = '张三'
    member1.user_id = 1
    member1.role = 'PM'
    
    member2 = Mock()
    member2.user = Mock()
    member2.user.username = '李四'
    member2.user_id = 2
    member2.role = 'DEV'
    
    project.members = [member1, member2]
    
    return project


@pytest.fixture
def sample_timesheets():
    """示例工时记录"""
    ts1 = Mock(spec=Timesheet)
    ts1.project_id = 1
    ts1.user_id = 1
    ts1.work_hours = 40
    
    ts2 = Mock(spec=Timesheet)
    ts2.project_id = 1
    ts2.user_id = 2
    ts2.work_hours = 60
    
    ts3 = Mock(spec=Timesheet)
    ts3.project_id = 1
    ts3.user_id = 1
    ts3.work_hours = 35
    
    return [ts1, ts2, ts3]


@pytest.fixture
def sample_costs():
    """示例成本记录"""
    cost1 = Mock(spec=ProjectCost)
    cost1.project_id = 1
    cost1.amount = Decimal('50000.00')
    
    cost2 = Mock(spec=ProjectCost)
    cost2.project_id = 1
    cost2.amount = Decimal('30000.00')
    
    return [cost1, cost2]


@pytest.fixture
def sample_changes():
    """示例变更记录"""
    change1 = Mock(spec=ChangeRequest)
    change1.title = '需求变更1'
    change1.change_type = 'REQUIREMENT'
    change1.impact_level = 'HIGH'
    change1.status = 'APPROVED'
    
    change2 = Mock(spec=ChangeRequest)
    change2.title = '技术变更'
    change2.change_type = 'TECHNICAL'
    change2.impact_level = 'MEDIUM'
    change2.status = 'COMPLETED'
    
    return [change1, change2]


class TestReportGeneratorInit:
    """测试初始化"""
    
    def test_init_with_db(self, mock_db):
        """测试正常初始化"""
        generator = ProjectReviewReportGenerator(mock_db)
        assert generator.db == mock_db
        assert generator.ai_client is not None
    
    def test_init_creates_ai_client(self, mock_db):
        """测试自动创建AI客户端"""
        generator = ProjectReviewReportGenerator(mock_db)
        assert hasattr(generator, 'ai_client')


class TestExtractProjectData:
    """测试项目数据提取"""
    
    def test_extract_complete_project_data(
        self, generator, mock_db, sample_project, 
        sample_timesheets, sample_costs, sample_changes
    ):
        """测试提取完整项目数据"""
        # 设置mock查询 - 项目查询
        project_query = Mock()
        project_query.first.return_value = sample_project
        
        # 其他查询 - 使用列表追踪调用顺序
        call_count = [0]
        
        def mock_filter(*args, **kwargs):
            # 第一次调用返回项目查询
            if call_count[0] == 0:
                call_count[0] += 1
                return project_query
            # 后续调用返回带all的查询
            call_count[0] += 1
            query = Mock()
            if call_count[0] == 2:  # Timesheet查询
                query.all.return_value = sample_timesheets
            elif call_count[0] == 3:  # ProjectCost查询
                query.all.return_value = sample_costs
            elif call_count[0] == 4:  # ChangeRequest查询
                query.all.return_value = sample_changes
            else:
                query.all.return_value = []
            return query
        
        mock_db.query.return_value.filter.side_effect = mock_filter
        
        result = generator._extract_project_data(1)
        
        assert result is not None
        assert result['project']['id'] == 1
        assert result['project']['code'] == 'PRJ-001'
        assert result['project']['name'] == '测试项目'
        assert result['project']['customer_name'] == '测试客户'
        assert result['statistics']['total_hours'] == 135
        assert result['statistics']['total_cost'] == 80000.00
        assert result['statistics']['change_count'] == 2
        assert len(result['team_members']) == 2
        assert len(result['changes']) == 2
    
    def test_extract_project_not_found(self, generator, mock_db):
        """测试项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = generator._extract_project_data(999)
        
        assert result is None
    
    def test_extract_project_no_dates(self, generator, mock_db):
        """测试项目无日期数据"""
        project = Mock(spec=Project)
        project.id = 1
        project.code = 'PRJ-002'
        project.name = '无日期项目'
        project.description = None
        project.status = 'PENDING'
        project.project_type = 'STANDARD'
        project.budget_amount = None
        project.planned_start_date = None
        project.planned_end_date = None
        project.actual_start_date = None
        project.actual_end_date = None
        project.customer = Mock()
        project.customer.name = '客户B'
        project.members = []
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator._extract_project_data(1)
        
        assert result is not None
        assert result['project']['planned_start'] is None
        assert result['project']['planned_end'] is None
        assert result['statistics']['plan_duration'] == 0
        assert result['statistics']['actual_duration'] == 0
        assert result['project']['budget'] == 0
    
    def test_extract_with_empty_timesheets(self, generator, mock_db, sample_project):
        """测试空工时记录"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator._extract_project_data(1)
        
        assert result['statistics']['total_hours'] == 0
        assert result['statistics']['total_cost'] == 0
        assert result['statistics']['change_count'] == 0
    
    def test_extract_schedule_variance_delayed(self, generator, mock_db):
        """测试进度延期计算"""
        project = Mock(spec=Project)
        project.id = 1
        project.code = 'PRJ-003'
        project.name = '延期项目'
        project.description = ''
        project.status = 'COMPLETED'
        project.project_type = 'CUSTOM'
        project.budget_amount = Decimal('50000')
        project.planned_start_date = datetime(2024, 1, 1)
        project.planned_end_date = datetime(2024, 2, 1)  # 31天
        project.actual_start_date = datetime(2024, 1, 1)
        project.actual_end_date = datetime(2024, 2, 15)  # 45天
        project.customer = Mock()
        project.customer.name = '客户'
        project.members = []
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator._extract_project_data(1)
        
        assert result['statistics']['plan_duration'] == 31
        assert result['statistics']['actual_duration'] == 45
        assert result['statistics']['schedule_variance'] == 14
    
    def test_extract_schedule_variance_early(self, generator, mock_db):
        """测试进度提前完成"""
        project = Mock(spec=Project)
        project.id = 1
        project.code = 'PRJ-004'
        project.name = '提前完成项目'
        project.description = ''
        project.status = 'COMPLETED'
        project.project_type = 'CUSTOM'
        project.budget_amount = Decimal('50000')
        project.planned_start_date = datetime(2024, 1, 1)
        project.planned_end_date = datetime(2024, 2, 1)  # 31天
        project.actual_start_date = datetime(2024, 1, 1)
        project.actual_end_date = datetime(2024, 1, 25)  # 24天
        project.customer = Mock()
        project.customer.name = '客户'
        project.members = []
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator._extract_project_data(1)
        
        assert result['statistics']['schedule_variance'] == -7
    
    def test_extract_cost_variance_over_budget(self, generator, mock_db, sample_project):
        """测试成本超支"""
        sample_project.budget_amount = Decimal('50000')
        
        costs = [
            Mock(spec=ProjectCost, project_id=1, amount=Decimal('60000'))
        ]
        
        # 设置mock查询
        project_query = Mock()
        project_query.first.return_value = sample_project
        
        call_count = [0]
        
        def mock_filter(*args, **kwargs):
            if call_count[0] == 0:
                call_count[0] += 1
                return project_query
            call_count[0] += 1
            query = Mock()
            if call_count[0] == 2:  # Timesheet
                query.all.return_value = []
            elif call_count[0] == 3:  # ProjectCost
                query.all.return_value = costs
            else:
                query.all.return_value = []
            return query
        
        mock_db.query.return_value.filter.side_effect = mock_filter
        
        result = generator._extract_project_data(1)
        
        assert result['statistics']['cost_variance'] == 10000.00
    
    def test_extract_team_members_hours(
        self, generator, mock_db, sample_project, sample_timesheets
    ):
        """测试团队成员工时统计"""
        # 设置mock查询
        project_query = Mock()
        project_query.first.return_value = sample_project
        
        call_count = [0]
        
        def mock_filter(*args, **kwargs):
            if call_count[0] == 0:
                call_count[0] += 1
                return project_query
            call_count[0] += 1
            query = Mock()
            if call_count[0] == 2:  # Timesheet
                query.all.return_value = sample_timesheets
            else:
                query.all.return_value = []
            return query
        
        mock_db.query.return_value.filter.side_effect = mock_filter
        
        result = generator._extract_project_data(1)
        
        # 张三：40 + 35 = 75小时
        # 李四：60小时
        member_hours = {m['name']: m['hours'] for m in result['team_members']}
        assert member_hours['张三'] == 75
        assert member_hours['李四'] == 60


class TestBuildReviewPrompt:
    """测试AI提示词构建"""
    
    def test_build_basic_prompt(self, generator):
        """测试基本提示词构建"""
        project_data = {
            'project': {
                'name': '测试项目',
                'code': 'PRJ-001',
                'customer_name': '测试客户',
                'type': 'CUSTOM',
                'description': '项目描述',
                'budget': 100000.0
            },
            'statistics': {
                'plan_duration': 30,
                'actual_duration': 28,
                'schedule_variance': -2,
                'total_cost': 95000.0,
                'cost_variance': -5000.0,
                'total_hours': 500,
                'change_count': 3
            },
            'team_members': [
                {'name': '张三', 'role': 'PM', 'hours': 100},
                {'name': '李四', 'role': 'DEV', 'hours': 200}
            ],
            'changes': []
        }
        
        prompt = generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        assert '测试项目' in prompt
        assert 'PRJ-001' in prompt
        assert '测试客户' in prompt
        assert '30天' in prompt
        assert '28天' in prompt
        assert '提前' in prompt
        assert '¥100,000.00' in prompt
        assert '¥95,000.00' in prompt
        assert '结余' in prompt
        assert '500小时' in prompt
        assert '3次' in prompt
        assert '2人' in prompt
    
    def test_build_prompt_with_delay(self, generator):
        """测试延期项目提示词"""
        project_data = {
            'project': {
                'name': '延期项目',
                'code': 'PRJ-002',
                'customer_name': '客户B',
                'type': 'STANDARD',
                'description': '',
                'budget': 50000.0
            },
            'statistics': {
                'plan_duration': 20,
                'actual_duration': 25,
                'schedule_variance': 5,
                'total_cost': 55000.0,
                'cost_variance': 5000.0,
                'total_hours': 300,
                'change_count': 1
            },
            'team_members': [],
            'changes': []
        }
        
        prompt = generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        assert '延期' in prompt
        assert '超支' in prompt
        assert '5天' in prompt
    
    def test_build_prompt_on_schedule(self, generator):
        """测试准时项目提示词"""
        project_data = {
            'project': {
                'name': '准时项目',
                'code': 'PRJ-003',
                'customer_name': '客户C',
                'type': 'CUSTOM',
                'description': '',
                'budget': 80000.0
            },
            'statistics': {
                'plan_duration': 30,
                'actual_duration': 30,
                'schedule_variance': 0,
                'total_cost': 80000.0,
                'cost_variance': 0.0,
                'total_hours': 400,
                'change_count': 0
            },
            'team_members': [],
            'changes': []
        }
        
        prompt = generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        assert '准时' in prompt
        assert '持平' in prompt
    
    def test_build_prompt_with_additional_context(self, generator):
        """测试带额外上下文的提示词"""
        project_data = {
            'project': {
                'name': '项目',
                'code': 'PRJ-004',
                'customer_name': '客户',
                'type': 'CUSTOM',
                'description': '',
                'budget': 50000.0
            },
            'statistics': {
                'plan_duration': 20,
                'actual_duration': 20,
                'schedule_variance': 0,
                'total_cost': 50000.0,
                'cost_variance': 0.0,
                'total_hours': 200,
                'change_count': 0
            },
            'team_members': [],
            'changes': []
        }
        
        additional = "客户非常满意，后续有合作意向"
        prompt = generator._build_review_prompt(project_data, 'POST_MORTEM', additional)
        
        assert '补充信息' in prompt
        assert '客户非常满意' in prompt
    
    def test_build_prompt_with_changes(self, generator):
        """测试带变更的提示词"""
        project_data = {
            'project': {
                'name': '项目',
                'code': 'PRJ-005',
                'customer_name': '客户',
                'type': 'CUSTOM',
                'description': '',
                'budget': 50000.0
            },
            'statistics': {
                'plan_duration': 20,
                'actual_duration': 20,
                'schedule_variance': 0,
                'total_cost': 50000.0,
                'cost_variance': 0.0,
                'total_hours': 200,
                'change_count': 2
            },
            'team_members': [],
            'changes': [
                {
                    'title': '需求变更',
                    'type': 'REQUIREMENT',
                    'impact': 'HIGH',
                    'status': 'APPROVED'
                },
                {
                    'title': '技术调整',
                    'type': 'TECHNICAL',
                    'impact': 'MEDIUM',
                    'status': 'COMPLETED'
                }
            ]
        }
        
        prompt = generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        assert '需求变更' in prompt
        assert '技术调整' in prompt
        assert 'REQUIREMENT' in prompt
        assert 'HIGH' in prompt


class TestFormatChanges:
    """测试变更格式化"""
    
    def test_format_empty_changes(self, generator):
        """测试空变更列表"""
        result = generator._format_changes([])
        assert result == "无变更记录"
    
    def test_format_single_change(self, generator):
        """测试单个变更"""
        changes = [
            {
                'title': '需求变更',
                'type': 'REQUIREMENT',
                'impact': 'HIGH',
                'status': 'APPROVED'
            }
        ]
        
        result = generator._format_changes(changes)
        
        assert '1. 需求变更' in result
        assert 'REQUIREMENT' in result
        assert 'HIGH' in result
        assert 'APPROVED' in result
    
    def test_format_multiple_changes(self, generator):
        """测试多个变更"""
        changes = [
            {'title': f'变更{i}', 'type': 'REQUIREMENT', 'impact': 'LOW', 'status': 'APPROVED'}
            for i in range(3)
        ]
        
        result = generator._format_changes(changes)
        
        assert '1. 变更0' in result
        assert '2. 变更1' in result
        assert '3. 变更2' in result
    
    def test_format_more_than_five_changes(self, generator):
        """测试超过5个变更（应该截断）"""
        changes = [
            {'title': f'变更{i}', 'type': 'REQUIREMENT', 'impact': 'LOW', 'status': 'APPROVED'}
            for i in range(10)
        ]
        
        result = generator._format_changes(changes)
        
        assert '1. 变更0' in result
        assert '5. 变更4' in result
        assert '... 共10条变更' in result
        assert '变更9' not in result


class TestParseAIResponse:
    """测试AI响应解析"""
    
    def test_parse_valid_json(self, generator):
        """测试解析有效JSON"""
        ai_response = {
            'content': json.dumps({
                'summary': '项目成功完成',
                'success_factors': ['因素1', '因素2'],
                'problems': ['问题1'],
                'improvements': ['改进1', '改进2'],
                'best_practices': ['实践1'],
                'conclusion': '总结',
                'insights': {'key': 'value'}
            })
        }
        
        project_data = {
            'project': {
                'id': 1,
                'code': 'PRJ-001',
                'budget': 100000.0
            },
            'statistics': {
                'plan_duration': 30,
                'actual_duration': 28,
                'schedule_variance': -2,
                'total_cost': 95000.0,
                'cost_variance': -5000.0,
                'change_count': 2
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        assert result['project_id'] == 1
        assert result['project_code'] == 'PRJ-001'
        assert '因素1' in result['success_factors']
        assert '因素2' in result['success_factors']
        assert '问题1' in result['problems']
        assert '改进1' in result['improvements']
        assert '实践1' in result['best_practices']
        assert result['conclusion'] == '总结'
        assert result['ai_summary'] == '项目成功完成'
        assert result['ai_insights'] == {'key': 'value'}
    
    def test_parse_json_with_code_block(self, generator):
        """测试解析带```json代码块的响应"""
        ai_response = {
            'content': '''
            这是一些前置说明
            ```json
            {
                "summary": "项目总结",
                "success_factors": ["成功1"],
                "problems": [],
                "improvements": [],
                "best_practices": [],
                "conclusion": "结论",
                "insights": {}
            }
            ```
            这是一些后续说明
            '''
        }
        
        project_data = {
            'project': {'id': 1, 'code': 'PRJ-001', 'budget': 50000.0},
            'statistics': {
                'plan_duration': 20, 'actual_duration': 20, 'schedule_variance': 0,
                'total_cost': 50000.0, 'cost_variance': 0.0, 'change_count': 0
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        assert result['ai_summary'] == '项目总结'
        assert '成功1' in result['success_factors']
        assert result['conclusion'] == '结论'
    
    def test_parse_json_with_generic_code_block(self, generator):
        """测试解析带```普通代码块的响应"""
        ai_response = {
            'content': '''
            ```
            {
                "summary": "另一个总结",
                "success_factors": [],
                "problems": ["问题A"],
                "improvements": [],
                "best_practices": [],
                "conclusion": "另一个结论",
                "insights": {}
            }
            ```
            '''
        }
        
        project_data = {
            'project': {'id': 2, 'code': 'PRJ-002', 'budget': 30000.0},
            'statistics': {
                'plan_duration': 15, 'actual_duration': 15, 'schedule_variance': 0,
                'total_cost': 30000.0, 'cost_variance': 0.0, 'change_count': 0
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        assert result['ai_summary'] == '另一个总结'
        assert '问题A' in result['problems']
    
    def test_parse_invalid_json(self, generator):
        """测试解析无效JSON（降级为纯文本）"""
        ai_response = {
            'content': '这是一段普通文本，不是JSON格式'
        }
        
        project_data = {
            'project': {'id': 3, 'code': 'PRJ-003', 'budget': 20000.0},
            'statistics': {
                'plan_duration': 10, 'actual_duration': 10, 'schedule_variance': 0,
                'total_cost': 20000.0, 'cost_variance': 0.0, 'change_count': 0
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        # 应该降级为纯文本处理
        assert '这是一段普通文本' in result['ai_summary']
        assert isinstance(result['success_factors'], str)
        assert isinstance(result['problems'], str)
    
    def test_parse_includes_project_metrics(self, generator):
        """测试解析结果包含项目指标"""
        ai_response = {
            'content': json.dumps({
                'summary': '总结',
                'success_factors': [],
                'problems': [],
                'improvements': [],
                'best_practices': [],
                'conclusion': '结论',
                'insights': {}
            })
        }
        
        project_data = {
            'project': {'id': 4, 'code': 'PRJ-004', 'budget': 150000.0},
            'statistics': {
                'plan_duration': 45,
                'actual_duration': 50,
                'schedule_variance': 5,
                'total_cost': 160000.0,
                'cost_variance': 10000.0,
                'change_count': 3
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        assert result['plan_duration'] == 45
        assert result['actual_duration'] == 50
        assert result['schedule_variance'] == 5
        assert result['budget_amount'] == 150000.0
        assert result['actual_cost'] == 160000.0
        assert result['cost_variance'] == 10000.0
        assert result['change_count'] == 3
    
    def test_parse_sets_ai_flags(self, generator):
        """测试设置AI标记"""
        ai_response = {
            'content': json.dumps({
                'summary': '', 'success_factors': [], 'problems': [],
                'improvements': [], 'best_practices': [], 'conclusion': '', 'insights': {}
            })
        }
        
        project_data = {
            'project': {'id': 5, 'code': 'PRJ-005', 'budget': 50000.0},
            'statistics': {
                'plan_duration': 20, 'actual_duration': 20, 'schedule_variance': 0,
                'total_cost': 50000.0, 'cost_variance': 0.0, 'change_count': 0
            }
        }
        
        result = generator._parse_ai_response(ai_response, project_data)
        
        assert result['ai_generated'] is True
        assert 'ai_generated_at' in result
        assert result['review_type'] == 'POST_MORTEM'
        assert 'review_date' in result


class TestGenerateReport:
    """测试完整报告生成流程"""
    
    def test_generate_report_success(
        self, generator, mock_db, sample_project, 
        sample_timesheets, sample_costs, sample_changes, mock_ai_client
    ):
        """测试成功生成报告"""
        # 设置mock
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        
        def mock_all(*args):
            if 'Timesheet' in str(args):
                return sample_timesheets
            elif 'ProjectCost' in str(args):
                return sample_costs
            elif 'ChangeRequest' in str(args):
                return sample_changes
            return []
        
        mock_db.query.return_value.filter.return_value.all.side_effect = mock_all
        
        result = generator.generate_report(1, 'POST_MORTEM', '额外上下文')
        
        # 验证调用AI
        mock_ai_client.generate_solution.assert_called_once()
        call_args = mock_ai_client.generate_solution.call_args
        assert call_args[1]['model'] == 'glm-5'
        assert call_args[1]['temperature'] == 0.7
        assert call_args[1]['max_tokens'] == 3000
        assert '额外上下文' in call_args[1]['prompt']
        
        # 验证结果
        assert result['project_id'] == 1
        assert result['project_code'] == 'PRJ-001'
        assert 'ai_metadata' in result
        assert result['ai_metadata']['model'] == 'glm-5'
        assert 'processing_time_ms' in result['ai_metadata']
        assert result['ai_metadata']['token_usage'] == 1500
    
    def test_generate_report_project_not_found(self, generator, mock_db):
        """测试项目不存在时抛出异常"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="项目 999 不存在或数据不完整"):
            generator.generate_report(999)
    
    def test_generate_report_without_additional_context(
        self, generator, mock_db, sample_project, mock_ai_client
    ):
        """测试不带额外上下文生成报告"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator.generate_report(1)
        
        assert result is not None
        call_args = mock_ai_client.generate_solution.call_args
        assert '补充信息' not in call_args[1]['prompt']
    
    def test_generate_report_processing_time_recorded(
        self, generator, mock_db, sample_project, mock_ai_client
    ):
        """测试记录处理时间"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = generator.generate_report(1)
        
        assert 'ai_metadata' in result
        assert 'processing_time_ms' in result['ai_metadata']
        assert result['ai_metadata']['processing_time_ms'] >= 0
        assert 'generated_at' in result['ai_metadata']
    
    def test_generate_report_different_review_types(
        self, generator, mock_db, sample_project, mock_ai_client
    ):
        """测试不同复盘类型"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        for review_type in ['POST_MORTEM', 'MID_TERM', 'QUARTERLY']:
            result = generator.generate_report(1, review_type=review_type)
            assert result is not None
