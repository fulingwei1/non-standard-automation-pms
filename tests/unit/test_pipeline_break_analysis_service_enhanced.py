# -*- coding: utf-8 -*-
"""
增强的全链条断链检测与分析服务单元测试

测试覆盖：
- analyze_pipeline_breaks（多场景）
- _detect_lead_to_opp_breaks（多场景）
- _detect_opp_to_quote_breaks（多场景）
- _detect_quote_to_contract_breaks（多场景）
- _detect_contract_to_project_breaks（多场景）
- _detect_project_to_invoice_breaks（多场景）
- _detect_invoice_to_payment_breaks（多场景）
- get_break_reasons（多场景）
- get_break_patterns（多场景）
- get_break_warnings（多场景）
- 边界条件和异常情况
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService


class TestPipelineBreakAnalysisService(unittest.TestCase):
    """全链条断链检测与分析服务测试基类"""
    
    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = PipelineBreakAnalysisService(self.db)
        self.today = date.today()
    
    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestPipelineBreakAnalysisService):
    """测试初始化"""
    
    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        service = PipelineBreakAnalysisService(self.db)
        self.assertIs(service.db, self.db)
    
    def test_default_break_thresholds_exist(self):
        """测试默认断链阈值配置存在"""
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['LEAD_TO_OPP'], 30)
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['OPP_TO_QUOTE'], 60)
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['QUOTE_TO_CONTRACT'], 90)
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['CONTRACT_TO_PROJECT'], 30)
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['PROJECT_TO_INVOICE'], 30)
        self.assertEqual(self.service.DEFAULT_BREAK_THRESHOLDS['INVOICE_TO_PAYMENT'], 30)


class TestAnalyzePipelineBreaks(TestPipelineBreakAnalysisService):
    """测试 analyze_pipeline_breaks 方法"""
    
    @patch.object(PipelineBreakAnalysisService, '_detect_lead_to_opp_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_opp_to_quote_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_quote_to_contract_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_contract_to_project_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_project_to_invoice_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_invoice_to_payment_breaks')
    def test_analyze_pipeline_breaks_with_default_dates(
        self, mock_invoice, mock_project, mock_contract, mock_quote, mock_opp, mock_lead
    ):
        """测试使用默认日期范围分析断链"""
        # 配置各个检测方法的返回值
        mock_lead.return_value = {'total': 100, 'break_count': 10, 'break_records': []}
        mock_opp.return_value = {'total': 80, 'break_count': 8, 'break_records': []}
        mock_quote.return_value = {'total': 60, 'break_count': 6, 'break_records': []}
        mock_contract.return_value = {'total': 40, 'break_count': 4, 'break_records': []}
        mock_project.return_value = {'total': 30, 'break_count': 3, 'break_records': []}
        mock_invoice.return_value = {'total': 20, 'break_count': 2, 'break_records': []}
        
        result = self.service.analyze_pipeline_breaks()
        
        # 验证返回结构
        self.assertIn('analysis_period', result)
        self.assertIn('breaks', result)
        self.assertIn('break_rates', result)
        self.assertIn('top_break_stages', result)
        
        # 验证日期范围（默认近一年）
        self.assertEqual(result['analysis_period']['end_date'], self.today.isoformat())
        
        # 验证断链率计算
        self.assertEqual(result['break_rates']['LEAD_TO_OPP']['break_rate'], 10.0)
        self.assertEqual(result['break_rates']['OPP_TO_QUOTE']['break_rate'], 10.0)
        
        # 验证所有检测方法被调用
        mock_lead.assert_called_once()
        mock_opp.assert_called_once()
        mock_quote.assert_called_once()
        mock_contract.assert_called_once()
        mock_project.assert_called_once()
        mock_invoice.assert_called_once()
    
    @patch.object(PipelineBreakAnalysisService, '_detect_lead_to_opp_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_opp_to_quote_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_quote_to_contract_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_contract_to_project_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_project_to_invoice_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_invoice_to_payment_breaks')
    def test_analyze_pipeline_breaks_with_custom_dates(
        self, mock_invoice, mock_project, mock_contract, mock_quote, mock_opp, mock_lead
    ):
        """测试使用自定义日期范围分析断链"""
        mock_lead.return_value = {'total': 50, 'break_count': 5, 'break_records': []}
        mock_opp.return_value = {'total': 40, 'break_count': 4, 'break_records': []}
        mock_quote.return_value = {'total': 30, 'break_count': 3, 'break_records': []}
        mock_contract.return_value = {'total': 20, 'break_count': 2, 'break_records': []}
        mock_project.return_value = {'total': 10, 'break_count': 1, 'break_records': []}
        mock_invoice.return_value = {'total': 5, 'break_count': 0, 'break_records': []}
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.service.analyze_pipeline_breaks(start_date, end_date)
        
        self.assertEqual(result['analysis_period']['start_date'], '2024-01-01')
        self.assertEqual(result['analysis_period']['end_date'], '2024-12-31')
    
    @patch.object(PipelineBreakAnalysisService, '_detect_lead_to_opp_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_opp_to_quote_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_quote_to_contract_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_contract_to_project_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_project_to_invoice_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_invoice_to_payment_breaks')
    def test_analyze_pipeline_breaks_top_stages_sorted(
        self, mock_invoice, mock_project, mock_contract, mock_quote, mock_opp, mock_lead
    ):
        """测试最容易断链环节按断链率降序排列"""
        # 设置不同的断链率
        mock_lead.return_value = {'total': 100, 'break_count': 5, 'break_records': []}  # 5%
        mock_opp.return_value = {'total': 100, 'break_count': 25, 'break_records': []}  # 25%
        mock_quote.return_value = {'total': 100, 'break_count': 15, 'break_records': []}  # 15%
        mock_contract.return_value = {'total': 100, 'break_count': 30, 'break_records': []}  # 30%
        mock_project.return_value = {'total': 100, 'break_count': 20, 'break_records': []}  # 20%
        mock_invoice.return_value = {'total': 100, 'break_count': 10, 'break_records': []}  # 10%
        
        result = self.service.analyze_pipeline_breaks()
        
        # 验证前3个断链率最高的环节
        self.assertEqual(len(result['top_break_stages']), 3)
        self.assertEqual(result['top_break_stages'][0]['stage'], 'CONTRACT_TO_PROJECT')
        self.assertEqual(result['top_break_stages'][0]['break_rate'], 30.0)
        self.assertEqual(result['top_break_stages'][1]['stage'], 'OPP_TO_QUOTE')
        self.assertEqual(result['top_break_stages'][1]['break_rate'], 25.0)
        self.assertEqual(result['top_break_stages'][2]['stage'], 'PROJECT_TO_INVOICE')
        self.assertEqual(result['top_break_stages'][2]['break_rate'], 20.0)
    
    @patch.object(PipelineBreakAnalysisService, '_detect_lead_to_opp_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_opp_to_quote_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_quote_to_contract_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_contract_to_project_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_project_to_invoice_breaks')
    @patch.object(PipelineBreakAnalysisService, '_detect_invoice_to_payment_breaks')
    def test_analyze_pipeline_breaks_zero_total_handling(
        self, mock_invoice, mock_project, mock_contract, mock_quote, mock_opp, mock_lead
    ):
        """测试处理总数为0的情况（断链率为0）"""
        mock_lead.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        mock_opp.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        mock_quote.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        mock_contract.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        mock_project.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        mock_invoice.return_value = {'total': 0, 'break_count': 0, 'break_records': []}
        
        result = self.service.analyze_pipeline_breaks()
        
        # 验证所有断链率为0
        for stage, data in result['break_rates'].items():
            self.assertEqual(data['break_rate'], 0)


class TestDetectLeadToOppBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_lead_to_opp_breaks 方法"""
    
    def test_detect_lead_to_opp_breaks_no_leads(self):
        """测试没有线索时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_lead_to_opp_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
        self.assertEqual(result['break_records'], [])
    
    def test_detect_lead_to_opp_breaks_with_opportunity(self):
        """测试有商机的线索不计为断链"""
        mock_lead = MagicMock()
        mock_lead.id = 1
        mock_lead.lead_code = 'LEAD001'
        mock_lead.customer_name = '客户A'
        mock_lead.created_at = datetime.now() - timedelta(days=40)
        mock_lead.owner_id = 10
        mock_lead.owner.real_name = '张三'
        mock_lead.opportunities = [MagicMock()]  # 有商机
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_lead_to_opp_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)  # 有商机，不算断链
    
    def test_detect_lead_to_opp_breaks_without_opportunity_old(self):
        """测试无商机且超过阈值的线索计为断链"""
        mock_owner = MagicMock()
        mock_owner.real_name = '李四'
        
        mock_lead = MagicMock()
        mock_lead.id = 2
        mock_lead.lead_code = 'LEAD002'
        mock_lead.customer_name = '客户B'
        mock_lead.created_at = datetime.now() - timedelta(days=40)  # 超过30天阈值
        mock_lead.owner_id = 20
        mock_lead.owner = mock_owner
        mock_lead.opportunities = []  # 无商机
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_lead_to_opp_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(len(result['break_records']), 1)
        
        break_record = result['break_records'][0]
        self.assertEqual(break_record['pipeline_id'], 2)
        self.assertEqual(break_record['pipeline_code'], 'LEAD002')
        self.assertEqual(break_record['break_stage'], 'LEAD_TO_OPP')
        self.assertEqual(break_record['responsible_person_name'], '李四')
    
    def test_detect_lead_to_opp_breaks_without_opportunity_recent(self):
        """测试无商机但未超过阈值的线索不计为断链"""
        mock_lead = MagicMock()
        mock_lead.id = 3
        mock_lead.lead_code = 'LEAD003'
        mock_lead.created_at = datetime.now() - timedelta(days=20)  # 未超过30天阈值
        mock_lead.opportunities = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_lead_to_opp_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)  # 未超阈值，不算断链
    
    def test_detect_lead_to_opp_breaks_limit_50_records(self):
        """测试断链记录限制在50条"""
        mock_leads = []
        for i in range(60):
            mock_owner = MagicMock()
            mock_owner.real_name = f'用户{i}'
            
            mock_lead = MagicMock()
            mock_lead.id = i
            mock_lead.lead_code = f'LEAD{i:03d}'
            mock_lead.customer_name = f'客户{i}'
            mock_lead.created_at = datetime.now() - timedelta(days=40)
            mock_lead.owner_id = i
            mock_lead.owner = mock_owner
            mock_lead.opportunities = []
            mock_leads.append(mock_lead)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = mock_leads
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_lead_to_opp_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 60)
        self.assertEqual(result['break_count'], 60)
        self.assertEqual(len(result['break_records']), 50)  # 限制50条


class TestDetectOppToQuoteBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_opp_to_quote_breaks 方法"""
    
    def test_detect_opp_to_quote_breaks_no_opportunities(self):
        """测试没有商机时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_opp_to_quote_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_opp_to_quote_breaks_with_quote(self):
        """测试有报价的商机不计为断链"""
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.opp_code = 'OPP001'
        mock_opp.created_at = datetime.now() - timedelta(days=70)
        mock_opp.quotes = [MagicMock()]  # 有报价
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_opp]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_opp_to_quote_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_opp_to_quote_breaks_without_quote_old(self):
        """测试无报价且超过阈值的商机计为断链"""
        mock_owner = MagicMock()
        mock_owner.real_name = '王五'
        
        mock_opp = MagicMock()
        mock_opp.id = 2
        mock_opp.opp_code = 'OPP002'
        mock_opp.opp_name = '商机B'
        mock_opp.created_at = datetime.now() - timedelta(days=70)  # 超过60天阈值
        mock_opp.owner_id = 30
        mock_opp.owner = mock_owner
        mock_opp.quotes = []  # 无报价
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_opp]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_opp_to_quote_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['pipeline_code'], 'OPP002')
        self.assertEqual(result['break_records'][0]['responsible_person_name'], '王五')


class TestDetectQuoteToContractBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_quote_to_contract_breaks 方法"""
    
    def test_detect_quote_to_contract_breaks_no_quotes(self):
        """测试没有报价时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_quote_to_contract_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_quote_to_contract_breaks_with_contract(self):
        """测试有合同的报价不计为断链"""
        mock_opportunity = MagicMock()
        mock_opportunity.contracts = [MagicMock()]  # 有合同
        
        mock_quote = MagicMock()
        mock_quote.id = 1
        mock_quote.created_at = datetime.now() - timedelta(days=100)
        mock_quote.opportunity = mock_opportunity
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_quote]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_quote_to_contract_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_quote_to_contract_breaks_without_contract_old(self):
        """测试无合同且超过阈值的报价计为断链"""
        mock_owner = MagicMock()
        mock_owner.real_name = '赵六'
        
        mock_opportunity = MagicMock()
        mock_opportunity.contracts = []  # 无合同
        mock_opportunity.owner_id = 40
        mock_opportunity.owner = mock_owner
        
        mock_quote = MagicMock()
        mock_quote.id = 2
        mock_quote.quote_code = 'QUOTE002'
        mock_quote.quote_name = '报价B'
        mock_quote.created_at = datetime.now() - timedelta(days=100)  # 超过90天阈值
        mock_quote.opportunity = mock_opportunity
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_quote]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_quote_to_contract_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['pipeline_code'], 'QUOTE002')
        self.assertEqual(result['break_records'][0]['responsible_person_name'], '赵六')
    
    def test_detect_quote_to_contract_breaks_no_opportunity(self):
        """测试报价无关联商机的情况"""
        mock_quote = MagicMock()
        mock_quote.id = 3
        mock_quote.quote_code = 'QUOTE003'
        mock_quote.quote_name = None  # 无名称
        mock_quote.created_at = datetime.now() - timedelta(days=100)
        mock_quote.opportunity = None  # 无商机
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_quote]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_quote_to_contract_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertIn('报价-QUOTE003', result['break_records'][0]['pipeline_name'])


class TestDetectContractToProjectBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_contract_to_project_breaks 方法"""
    
    def test_detect_contract_to_project_breaks_no_contracts(self):
        """测试没有合同时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_contract_to_project_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_contract_to_project_breaks_with_project(self):
        """测试有项目的合同不计为断链"""
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.signing_date = self.today - timedelta(days=40)
        mock_contract.project_id = 100  # 有项目ID
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_contract]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_contract_to_project_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_contract_to_project_breaks_without_project_old(self):
        """测试无项目且超过阈值的合同计为断链"""
        mock_owner = MagicMock()
        mock_owner.real_name = '钱七'
        
        mock_opportunity = MagicMock()
        mock_opportunity.owner_id = 50
        mock_opportunity.owner = mock_owner
        
        mock_contract = MagicMock()
        mock_contract.id = 2
        mock_contract.contract_code = 'CONTRACT002'
        mock_contract.contract_name = '合同B'
        mock_contract.signing_date = self.today - timedelta(days=40)  # 超过30天阈值
        mock_contract.project_id = None  # 无项目
        mock_contract.opportunity = mock_opportunity
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_contract]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_contract_to_project_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['pipeline_code'], 'CONTRACT002')
        self.assertEqual(result['break_records'][0]['responsible_person_name'], '钱七')


class TestDetectProjectToInvoiceBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_project_to_invoice_breaks 方法"""
    
    def test_detect_project_to_invoice_breaks_no_milestones(self):
        """测试没有里程碑时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_project_to_invoice_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_project_to_invoice_breaks_with_invoice(self):
        """测试有发票的项目不计为断链"""
        mock_contract = MagicMock()
        mock_contract.invoices = [MagicMock()]  # 有发票
        
        mock_project = MagicMock()
        mock_project.contract = mock_contract
        
        mock_milestone = MagicMock()
        mock_milestone.actual_date = self.today - timedelta(days=40)
        mock_milestone.project = mock_project
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_milestone]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_project_to_invoice_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_project_to_invoice_breaks_without_invoice_old(self):
        """测试无发票且超过阈值的项目计为断链"""
        mock_manager = MagicMock()
        mock_manager.real_name = '孙八'
        
        mock_contract = MagicMock()
        mock_contract.invoices = []  # 无发票
        
        mock_project = MagicMock()
        mock_project.id = 101
        mock_project.project_code = 'PROJ001'
        mock_project.project_name = '项目A'
        mock_project.pm_id = 60
        mock_project.manager = mock_manager
        mock_project.contract = mock_contract
        
        mock_milestone = MagicMock()
        mock_milestone.milestone_name = '里程碑1'
        mock_milestone.actual_date = self.today - timedelta(days=40)  # 超过30天阈值
        mock_milestone.project = mock_project
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_milestone]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_project_to_invoice_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['pipeline_code'], 'PROJ001')
        self.assertEqual(result['break_records'][0]['responsible_person_name'], '孙八')
        self.assertEqual(result['break_records'][0]['milestone_name'], '里程碑1')
    
    def test_detect_project_to_invoice_breaks_no_project(self):
        """测试里程碑无关联项目的情况"""
        mock_milestone = MagicMock()
        mock_milestone.actual_date = self.today - timedelta(days=40)
        mock_milestone.project = None  # 无项目
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_milestone]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_project_to_invoice_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)  # 无项目则跳过


class TestDetectInvoiceToPaymentBreaks(TestPipelineBreakAnalysisService):
    """测试 _detect_invoice_to_payment_breaks 方法"""
    
    def test_detect_invoice_to_payment_breaks_no_invoices(self):
        """测试没有发票时返回空结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_invoice_to_payment_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_invoice_to_payment_breaks_fully_paid(self):
        """测试已完全回款的发票不计为断链"""
        mock_invoice = MagicMock()
        mock_invoice.id = 1
        mock_invoice.invoice_amount = Decimal('10000')
        mock_invoice.paid_amount = Decimal('10000')  # 已完全回款
        mock_invoice.issue_date = self.today - timedelta(days=40)
        mock_invoice.due_date = self.today - timedelta(days=40)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_invoice]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_invoice_to_payment_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_invoice_to_payment_breaks_partial_paid_old(self):
        """测试部分回款且超过阈值的发票计为断链"""
        mock_owner = MagicMock()
        mock_owner.real_name = '周九'
        
        mock_opportunity = MagicMock()
        mock_opportunity.owner_id = 70
        mock_opportunity.owner = mock_owner
        
        mock_contract = MagicMock()
        mock_contract.opportunity = mock_opportunity
        
        mock_invoice = MagicMock()
        mock_invoice.id = 2
        mock_invoice.invoice_no = 'INV002'
        mock_invoice.customer_name = '客户C'
        mock_invoice.invoice_amount = Decimal('10000')
        mock_invoice.paid_amount = Decimal('5000')  # 部分回款
        mock_invoice.issue_date = self.today - timedelta(days=40)
        mock_invoice.due_date = self.today - timedelta(days=40)  # 超过到期日+阈值
        mock_invoice.contract = mock_contract
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_invoice]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_invoice_to_payment_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['invoice_no'], 'INV002')
        self.assertEqual(result['break_records'][0]['unpaid_amount'], 5000.0)
        self.assertEqual(result['break_records'][0]['responsible_person_name'], '周九')
    
    def test_detect_invoice_to_payment_breaks_unpaid_recent(self):
        """测试未回款但未超过阈值的发票不计为断链"""
        mock_invoice = MagicMock()
        mock_invoice.id = 3
        mock_invoice.invoice_amount = Decimal('10000')
        mock_invoice.paid_amount = Decimal('0')  # 未回款
        mock_invoice.issue_date = self.today - timedelta(days=10)
        mock_invoice.due_date = self.today - timedelta(days=10)  # 未超阈值
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_invoice]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_invoice_to_payment_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 0)
    
    def test_detect_invoice_to_payment_breaks_no_due_date(self):
        """测试发票无到期日时使用发票日期"""
        mock_contract = MagicMock()
        mock_contract.opportunity = None
        
        mock_invoice = MagicMock()
        mock_invoice.id = 4
        mock_invoice.invoice_no = 'INV004'
        mock_invoice.customer_name = None  # 无客户名
        mock_invoice.invoice_amount = Decimal('10000')
        mock_invoice.paid_amount = Decimal('0')
        mock_invoice.issue_date = self.today - timedelta(days=40)
        mock_invoice.due_date = None  # 无到期日
        mock_invoice.contract = mock_contract
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_invoice]
        self.db.query.return_value = mock_query
        
        start_date = self.today - timedelta(days=365)
        end_date = self.today
        
        result = self.service._detect_invoice_to_payment_breaks(start_date, end_date)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['break_count'], 1)
        self.assertEqual(result['break_records'][0]['pipeline_name'], '未知客户')


class TestGetBreakReasons(TestPipelineBreakAnalysisService):
    """测试 get_break_reasons 方法"""
    
    def test_get_break_reasons_returns_common_reasons(self):
        """测试返回常见断链原因"""
        result = self.service.get_break_reasons()
        
        self.assertIn('break_stage', result)
        self.assertIn('reasons', result)
        self.assertIn('top_reasons', result)
        
        # 验证包含常见原因
        self.assertIn('客户需求变化', result['reasons'])
        self.assertIn('价格不匹配', result['reasons'])
        self.assertIn('技术方案不匹配', result['reasons'])
    
    def test_get_break_reasons_with_stage_filter(self):
        """测试使用环节过滤"""
        result = self.service.get_break_reasons(break_stage='LEAD_TO_OPP')
        
        self.assertEqual(result['break_stage'], 'LEAD_TO_OPP')
    
    def test_get_break_reasons_with_date_range(self):
        """测试使用日期范围"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.service.get_break_reasons(
            break_stage='OPP_TO_QUOTE',
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertIsNotNone(result)


class TestGetBreakPatterns(TestPipelineBreakAnalysisService):
    """测试 get_break_patterns 方法"""
    
    @patch.object(PipelineBreakAnalysisService, 'analyze_pipeline_breaks')
    def test_get_break_patterns_with_top_stages(self, mock_analyze):
        """测试识别最常见的断链环节"""
        mock_analyze.return_value = {
            'top_break_stages': [
                {'stage': 'OPP_TO_QUOTE', 'break_rate': 25.0}
            ]
        }
        
        result = self.service.get_break_patterns()
        
        self.assertIn('most_common_stage', result)
        self.assertEqual(result['most_common_stage']['stage'], 'OPP_TO_QUOTE')
    
    @patch.object(PipelineBreakAnalysisService, 'analyze_pipeline_breaks')
    def test_get_break_patterns_no_top_stages(self, mock_analyze):
        """测试没有断链环节时的模式"""
        mock_analyze.return_value = {
            'top_break_stages': []
        }
        
        result = self.service.get_break_patterns()
        
        self.assertIsNone(result['most_common_stage'])
    
    @patch.object(PipelineBreakAnalysisService, 'analyze_pipeline_breaks')
    def test_get_break_patterns_with_date_range(self, mock_analyze):
        """测试使用日期范围识别模式"""
        mock_analyze.return_value = {
            'top_break_stages': [
                {'stage': 'CONTRACT_TO_PROJECT', 'break_rate': 30.0}
            ]
        }
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = self.service.get_break_patterns(start_date, end_date)
        
        mock_analyze.assert_called_once_with(start_date, end_date)
        self.assertIsNotNone(result)


class TestGetBreakWarnings(TestPipelineBreakAnalysisService):
    """测试 get_break_warnings 方法"""
    
    def test_get_break_warnings_no_leads(self):
        """测试没有即将断链的线索时返回空列表"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.service.get_break_warnings()
        
        self.assertEqual(result, [])
    
    def test_get_break_warnings_with_upcoming_break(self):
        """测试检测即将断链的线索"""
        mock_owner = MagicMock()
        mock_owner.real_name = '吴十'
        
        # 创建一个距离断链还有5天的线索
        days_since_created = 30 - 5  # 30天阈值 - 5天预警期 = 25天前创建
        mock_lead = MagicMock()
        mock_lead.id = 1
        mock_lead.lead_code = 'LEAD001'
        mock_lead.created_at = datetime.now() - timedelta(days=days_since_created)
        mock_lead.owner_id = 80
        mock_lead.owner = mock_owner
        mock_lead.opportunities = []  # 无商机
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        result = self.service.get_break_warnings(days_ahead=7)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['pipeline_code'], 'LEAD001')
        self.assertEqual(result[0]['break_stage'], 'LEAD_TO_OPP')
        self.assertEqual(result[0]['responsible_person_name'], '吴十')
        self.assertGreater(result[0]['days_until_break'], 0)
    
    def test_get_break_warnings_already_converted(self):
        """测试已转商机的线索不会出现在预警中"""
        mock_lead = MagicMock()
        mock_lead.id = 2
        mock_lead.created_at = datetime.now() - timedelta(days=25)
        mock_lead.opportunities = [MagicMock()]  # 有商机
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        result = self.service.get_break_warnings(days_ahead=7)
        
        self.assertEqual(result, [])
    
    def test_get_break_warnings_custom_days_ahead(self):
        """测试自定义预警天数"""
        mock_owner = MagicMock()
        mock_owner.real_name = '郑十一'
        
        # 创建一个距离断链还有12天的线索
        days_since_created = 30 - 12
        mock_lead = MagicMock()
        mock_lead.id = 3
        mock_lead.lead_code = 'LEAD003'
        mock_lead.created_at = datetime.now() - timedelta(days=days_since_created)
        mock_lead.owner_id = 90
        mock_lead.owner = mock_owner
        mock_lead.opportunities = []
        
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [mock_lead]
        self.db.query.return_value = mock_query
        
        # 使用14天预警期
        result = self.service.get_break_warnings(days_ahead=14)
        
        self.assertEqual(len(result), 1)
        
        # 使用7天预警期（不应出现）
        result_short = self.service.get_break_warnings(days_ahead=7)
        
        self.assertEqual(len(result_short), 0)


if __name__ == '__main__':
    unittest.main()
