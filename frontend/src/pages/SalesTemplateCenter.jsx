import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Layers,
  ClipboardList,
  PenTool,
  FileText,
  Sparkles,
  CheckCircle2,
  UploadCloud,
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { fadeIn, staggerContainer } from '../lib/animations';
import { cn, formatDate } from '../lib/utils';
import { salesTemplateApi } from '../services/api';

const tabs = [
  { key: 'quote', label: '报价模板', icon: Layers },
  { key: 'contract', label: '合同模板', icon: ClipboardList },
  { key: 'cpq', label: 'CPQ规则', icon: Sparkles },
];

export default function SalesTemplateCenter() {
  const [activeTab, setActiveTab] = useState('quote');
  const [quoteTemplates, setQuoteTemplates] = useState([]);
  const [contractTemplates, setContractTemplates] = useState([]);
  const [ruleSets, setRuleSets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showQuoteDialog, setShowQuoteDialog] = useState(false);
  const [showContractDialog, setShowContractDialog] = useState(false);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [previewPayload, setPreviewPayload] = useState(null);
  const [newQuoteTemplate, setNewQuoteTemplate] = useState({
    template_code: '',
    template_name: '',
    category: '',
    visibility_scope: 'TEAM',
    version_no: 'v1',
    sections: '{"sections":[]}',
    pricing_rules: '{"base_price":0}',
  });
  const [newContractTemplate, setNewContractTemplate] = useState({
    template_code: '',
    template_name: '',
    contract_type: '',
    visibility_scope: 'TEAM',
    version_no: 'v1',
    clause_sections: '{"sections":[]}',
  });
  const [newRuleSet, setNewRuleSet] = useState({
    rule_code: '',
    rule_name: '',
    base_price: 0,
    config_schema: '{"options":[]}',
    pricing_matrix: '{"items":{}}',
    approval_threshold: '{"max_discount_pct":10}',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [quoteRes, contractRes, ruleRes] = await Promise.all([
        salesTemplateApi.listQuoteTemplates({ page: 1, page_size: 50 }),
        salesTemplateApi.listContractTemplates({ page: 1, page_size: 50 }),
        salesTemplateApi.listRuleSets({ page: 1, page_size: 50 }),
      ]);
      setQuoteTemplates(quoteRes.data?.items || quoteRes.items || []);
      setContractTemplates(contractRes.data?.items || contractRes.items || []);
      setRuleSets(ruleRes.data?.items || ruleRes.items || []);
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };

  const parseJsonField = (value, fallback = {}) => {
    try {
      return JSON.parse(value || '{}');
    } catch (error) {
      throw new Error('JSON 字段格式不正确');
    }
  };

  const handleCreateQuoteTemplate = async () => {
    try {
      const payload = {
        template_code: newQuoteTemplate.template_code,
        template_name: newQuoteTemplate.template_name,
        category: newQuoteTemplate.category,
        visibility_scope: newQuoteTemplate.visibility_scope,
        initial_version: {
          version_no: newQuoteTemplate.version_no,
          sections: parseJsonField(newQuoteTemplate.sections),
          pricing_rules: parseJsonField(newQuoteTemplate.pricing_rules),
        },
      };
      await salesTemplateApi.createQuoteTemplate(payload);
      setShowQuoteDialog(false);
      loadData();
    } catch (error) {
      alert('创建报价模板失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateContractTemplate = async () => {
    try {
      const payload = {
        template_code: newContractTemplate.template_code,
        template_name: newContractTemplate.template_name,
        contract_type: newContractTemplate.contract_type,
        visibility_scope: newContractTemplate.visibility_scope,
        initial_version: {
          version_no: newContractTemplate.version_no,
          clause_sections: parseJsonField(newContractTemplate.clause_sections),
        },
      };
      await salesTemplateApi.createContractTemplate(payload);
      setShowContractDialog(false);
      loadData();
    } catch (error) {
      alert('创建合同模板失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateRuleSet = async () => {
    try {
      const payload = {
        rule_code: newRuleSet.rule_code,
        rule_name: newRuleSet.rule_name,
        base_price: Number(newRuleSet.base_price) || 0,
        config_schema: parseJsonField(newRuleSet.config_schema),
        pricing_matrix: parseJsonField(newRuleSet.pricing_matrix),
        approval_threshold: parseJsonField(newRuleSet.approval_threshold),
      };
      await salesTemplateApi.createRuleSet(payload);
      setShowRuleDialog(false);
      loadData();
    } catch (error) {
      alert('创建规则集失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePublishQuoteVersion = async (template) => {
    if (!template.versions?.length) return;
    const latest = template.versions[0];
    try {
      await salesTemplateApi.publishQuoteVersion(template.id, latest.id);
      loadData();
    } catch (error) {
      alert('发布失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePreviewQuoteTemplate = async (template) => {
    try {
      const res = await salesTemplateApi.applyQuoteTemplate(template.id, {
        selections: {},
      });
      setPreviewPayload(res.data || res);
      setShowPreviewDialog(true);
    } catch (error) {
      alert('获取预测失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderQuoteTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">标准报价模板库</h3>
          <p className="text-sm text-muted-foreground">
            可复用的报价骨架与 CPQ 规则，支持多版本、审批与预测。
          </p>
        </div>
        <Button onClick={() => setShowQuoteDialog(true)}>新增模板</Button>
      </div>
      {quoteTemplates.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          暂无模板，点击「新增模板」开始配置。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {quoteTemplates.map(template => (
          <Card key={template.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-base">{template.template_name}</CardTitle>
              <Badge variant="outline">{template.status}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center text-sm text-muted-foreground justify-between">
                <span>编码: {template.template_code}</span>
                <span>可见范围: {template.visibility_scope}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                当前版本: {template.current_version_id || '未发布'}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handlePublishQuoteVersion(template)}>
                  <CheckCircle2 className="w-4 h-4 mr-1" /> 发布最新
                </Button>
                <Button size="sm" onClick={() => handlePreviewQuoteTemplate(template)}>
                  <PenTool className="w-4 h-4 mr-1" /> 应用/预测
                </Button>
              </div>
              <div className="space-y-2">
                {(template.versions || []).slice(0, 3).map(version => (
                  <div key={version.id} className="border rounded-md p-2 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium">{version.version_no}</div>
                      <div className="text-muted-foreground">
                        {version.release_notes || '未填写说明'}
                      </div>
                    </div>
                    <Badge variant="secondary">{version.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const handlePublishContractVersion = async (template) => {
    if (!template.versions?.length) return;
    const latest = template.versions[0];
    try {
      await salesTemplateApi.publishContractVersion(template.id, latest.id);
      loadData();
    } catch (error) {
      alert('发布失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderContractTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">合同条款模板</h3>
          <p className="text-sm text-muted-foreground">
            快速复用标准条款、审批流与附件清单，保障 G4 交付质量。
          </p>
        </div>
        <Button onClick={() => setShowContractDialog(true)}>新增合同模板</Button>
      </div>
      {contractTemplates.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          尚未配置合同模板。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {contractTemplates.map(template => (
          <Card key={template.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span>{template.template_name}</span>
                <Badge variant="outline">{template.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center justify-between text-muted-foreground">
                <span>类型: {template.contract_type || '-'}</span>
                <span>范围: {template.visibility_scope}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                最新版本: {template.current_version_id || '未发布'}
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => handlePublishContractVersion(template)}>
                  <UploadCloud className="w-4 h-4 mr-1" /> 发布
                </Button>
                <Button size="sm" onClick={loadData}>
                  <FileText className="w-4 h-4 mr-1" /> 同步条款
                </Button>
              </div>
              <div className="space-y-2">
                {(template.versions || []).slice(0, 3).map(version => (
                  <div key={version.id} className="border rounded-md p-2 text-xs flex items-center justify-between">
                    <div>
                      <div className="font-medium">{version.version_no}</div>
                      <div className="text-muted-foreground">{version.release_notes || '暂无说明'}</div>
                    </div>
                    <Badge variant="secondary">{version.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderCpqTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">CPQ 定价规则</h3>
          <p className="text-sm text-muted-foreground">
            配置参数选项、定价矩阵与审批阈值，驱动智能预测。
          </p>
        </div>
        <Button onClick={() => setShowRuleDialog(true)}>新增规则集</Button>
      </div>
      {ruleSets.length === 0 && !loading && (
        <div className="text-center text-muted-foreground py-8 border rounded-md">
          规则集为空，先创建一个基础规则集。
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {ruleSets.map(rule => (
          <Card key={rule.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span>{rule.rule_name}</span>
                <Badge variant="outline">{rule.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="text-xs text-muted-foreground">
                编码: {rule.rule_code} · 基准价 {rule.base_price}
              </div>
              <div className="text-xs text-muted-foreground">
                审批阈值: {JSON.stringify(rule.approval_threshold || {})}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="模板与 CPQ 中心"
        description="管理报价/合同模板与配置化定价资产，提高交付复用与预测准确性。"
      />
      <div className="flex gap-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? 'default' : 'ghost'}
              onClick={() => setActiveTab(tab.key)}
              className="flex items-center gap-2"
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </Button>
          );
        })}
      </div>
      {loading ? (
        <div className="py-20 text-center text-muted-foreground">数据加载中...</div>
      ) : (
        <>
          {activeTab === 'quote' && renderQuoteTab()}
          {activeTab === 'contract' && renderContractTab()}
          {activeTab === 'cpq' && renderCpqTab()}
        </>
      )}

      {/* Quote Template Dialog */}
      <Dialog open={showQuoteDialog} onOpenChange={setShowQuoteDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建报价模板</DialogTitle>
            <DialogDescription>定义基础信息与版本骨架，后续可继续扩展。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>模板编码</Label>
              <Input
                className="col-span-3"
                value={newQuoteTemplate.template_code}
                onChange={(e) => setNewQuoteTemplate(prev => ({ ...prev, template_code: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>模板名称</Label>
              <Input
                className="col-span-3"
                value={newQuoteTemplate.template_name}
                onChange={(e) => setNewQuoteTemplate(prev => ({ ...prev, template_name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>版本号</Label>
              <Input
                className="col-span-3"
                value={newQuoteTemplate.version_no}
                onChange={(e) => setNewQuoteTemplate(prev => ({ ...prev, version_no: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>模板结构 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newQuoteTemplate.sections}
                onChange={(e) => setNewQuoteTemplate(prev => ({ ...prev, sections: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>定价规则 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newQuoteTemplate.pricing_rules}
                onChange={(e) => setNewQuoteTemplate(prev => ({ ...prev, pricing_rules: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowQuoteDialog(false)}>取消</Button>
            <Button onClick={handleCreateQuoteTemplate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Contract Template Dialog */}
      <Dialog open={showContractDialog} onOpenChange={setShowContractDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建合同模板</DialogTitle>
            <DialogDescription>配置条款章节与审批指引，提升 G4 自检效率。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>模板编码</Label>
              <Input
                className="col-span-3"
                value={newContractTemplate.template_code}
                onChange={(e) => setNewContractTemplate(prev => ({ ...prev, template_code: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>模板名称</Label>
              <Input
                className="col-span-3"
                value={newContractTemplate.template_name}
                onChange={(e) => setNewContractTemplate(prev => ({ ...prev, template_name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>合同类型</Label>
              <Input
                className="col-span-3"
                value={newContractTemplate.contract_type}
                onChange={(e) => setNewContractTemplate(prev => ({ ...prev, contract_type: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>版本号</Label>
              <Input
                className="col-span-3"
                value={newContractTemplate.version_no}
                onChange={(e) => setNewContractTemplate(prev => ({ ...prev, version_no: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>条款结构 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newContractTemplate.clause_sections}
                onChange={(e) => setNewContractTemplate(prev => ({ ...prev, clause_sections: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowContractDialog(false)}>取消</Button>
            <Button onClick={handleCreateContractTemplate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rule Set Dialog */}
      <Dialog open={showRuleDialog} onOpenChange={setShowRuleDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新增 CPQ 规则集</DialogTitle>
            <DialogDescription>定义资源负载、价格矩阵与审批阈值。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>规则编码</Label>
              <Input
                className="col-span-3"
                value={newRuleSet.rule_code}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, rule_code: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>规则名称</Label>
              <Input
                className="col-span-3"
                value={newRuleSet.rule_name}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, rule_name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-center">
              <Label>基准价格</Label>
              <Input
                type="number"
                className="col-span-3"
                value={newRuleSet.base_price}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, base_price: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>配置项 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newRuleSet.config_schema}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, config_schema: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>定价矩阵 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newRuleSet.pricing_matrix}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, pricing_matrix: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-4 gap-2 items-start">
              <Label>审批阈值 JSON</Label>
              <Textarea
                className="col-span-3 min-h-[120px]"
                value={newRuleSet.approval_threshold}
                onChange={(e) => setNewRuleSet(prev => ({ ...prev, approval_threshold: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRuleDialog(false)}>取消</Button>
            <Button onClick={handleCreateRuleSet}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>模板应用与 CPQ 预测</DialogTitle>
            <DialogDescription>自动计算的完工价格、折扣与调价轨迹。</DialogDescription>
          </DialogHeader>
          {previewPayload ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>价格预估</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                  <div>
                    <div className="text-xs text-muted-foreground">基础价格</div>
                    <div className="text-lg font-semibold">{previewPayload.cpq_preview?.base_price || 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">调价合计</div>
                    <div className="text-lg font-semibold text-blue-600">
                      {previewPayload.cpq_preview?.adjustment_total || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">最终报价</div>
                    <div className="text-lg font-semibold text-emerald-600">
                      {previewPayload.cpq_preview?.final_price || 0}
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>调价因子</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {(previewPayload.cpq_preview?.adjustments || []).map(adj => (
                    <div key={adj.key} className="border rounded-md p-2 flex items-center justify-between">
                      <div>
                        <div className="font-medium">{adj.label}</div>
                        <div className="text-xs text-muted-foreground">{adj.reason}</div>
                      </div>
                      <div className={cn('font-semibold', adj.value >= 0 ? 'text-emerald-600' : 'text-red-500')}>
                        {adj.value}
                      </div>
                    </div>
                  ))}
                  {(previewPayload.cpq_preview?.adjustments || []).length === 0 && (
                    <div className="text-muted-foreground text-sm">暂无调价轨迹</div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="py-10 text-center text-muted-foreground">暂无预览数据</div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowPreviewDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
