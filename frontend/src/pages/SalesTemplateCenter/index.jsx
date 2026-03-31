import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { resolveIcon } from "@/utils/iconMap";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { staggerContainer } from "../../lib/animations";
import { salesTemplateApi } from "../../services/api";

import {
  tabs,
  INITIAL_QUOTE_TEMPLATE,
  INITIAL_CONTRACT_TEMPLATE,
  INITIAL_RULE_SET,
} from "./constants";
import { parseJsonField } from "./utils";

import QuoteTab from "./QuoteTab";
import ContractTab from "./ContractTab";
import CpqTab from "./CpqTab";
import QuoteTemplateDialog from "./QuoteTemplateDialog";
import ContractTemplateDialog from "./ContractTemplateDialog";
import RuleSetDialog from "./RuleSetDialog";
import PreviewDialog from "./PreviewDialog";

export default function SalesTemplateCenter({ embedded = false } = {}) {
  const [activeTab, setActiveTab] = useState("quote");
  const [quoteTemplates, setQuoteTemplates] = useState([]);
  const [contractTemplates, setContractTemplates] = useState([]);
  const [ruleSets, setRuleSets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showQuoteDialog, setShowQuoteDialog] = useState(false);
  const [showContractDialog, setShowContractDialog] = useState(false);
  const [showRuleDialog, setShowRuleDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [previewPayload, setPreviewPayload] = useState(null);
  const [newQuoteTemplate, setNewQuoteTemplate] = useState(INITIAL_QUOTE_TEMPLATE);
  const [newContractTemplate, setNewContractTemplate] = useState(INITIAL_CONTRACT_TEMPLATE);
  const [newRuleSet, setNewRuleSet] = useState(INITIAL_RULE_SET);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [quoteRes, contractRes, ruleRes] = await Promise.allSettled([
        salesTemplateApi.listQuoteTemplates({ page: 1, page_size: 50 }),
        salesTemplateApi.listContractTemplates({ page: 1, page_size: 50 }),
        salesTemplateApi.listRuleSets({ page: 1, page_size: 50 }),
      ]);

      const quoteItems =
        quoteRes.status === "fulfilled"
          ? quoteRes.value?.data?.items || quoteRes.value?.items || []
          : [];
      const contractItems =
        contractRes.status === "fulfilled"
          ? contractRes.value?.data?.items || contractRes.value?.items || []
          : [];
      const ruleItems =
        ruleRes.status === "fulfilled"
          ? ruleRes.value?.data?.items || ruleRes.value?.items || []
          : [];

      setQuoteTemplates(Array.isArray(quoteItems) ? quoteItems : []);
      setContractTemplates(Array.isArray(contractItems) ? contractItems : []);
      setRuleSets(Array.isArray(ruleItems) ? ruleItems : []);
    } catch (error) {
      console.error("加载模板数据失败", error);
    } finally {
      setLoading(false);
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
      alert("创建报价模板失败: " + (error.response?.data?.detail || error.message));
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
      alert("创建合同模板失败: " + (error.response?.data?.detail || error.message));
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
      alert("创建规则集失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handlePublishQuoteVersion = async (template) => {
    if (!template.versions?.length) return;
    const latest = template.versions[0];
    try {
      await salesTemplateApi.publishQuoteVersion(template.id, latest.id);
      loadData();
    } catch (error) {
      alert("发布失败: " + (error.response?.data?.detail || error.message));
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
      alert("获取预测失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handlePublishContractVersion = async (template) => {
    if (!template.versions?.length) return;
    const latest = template.versions[0];
    try {
      await salesTemplateApi.publishContractVersion(template.id, latest.id);
      loadData();
    } catch (error) {
      alert("发布失败: " + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {!embedded && (
        <PageHeader
          title="模板与 CPQ 中心"
          description="管理报价/合同模板与配置化定价资产，提高交付复用与预测准确性。"
        />
      )}

      <div className="flex gap-2">
        {(tabs || []).map((tab) => {
          const Icon = resolveIcon(tab.icon);
          return (
            <Button
              key={tab.key}
              variant={activeTab === tab.key ? "default" : "ghost"}
              onClick={() => setActiveTab(tab.key)}
              className="flex items-center gap-2"
            >
              {Icon && <Icon className="w-4 h-4" />}
              {tab.label}
            </Button>
          );
        })}
      </div>

      {loading ? (
        <div className="py-20 text-center text-muted-foreground">
          数据加载中...
        </div>
      ) : (
        <>
          {activeTab === "quote" && (
            <QuoteTab
              quoteTemplates={quoteTemplates}
              loading={loading}
              onShowDialog={() => setShowQuoteDialog(true)}
              onPublish={handlePublishQuoteVersion}
              onPreview={handlePreviewQuoteTemplate}
            />
          )}
          {activeTab === "contract" && (
            <ContractTab
              contractTemplates={contractTemplates}
              loading={loading}
              onShowDialog={() => setShowContractDialog(true)}
              onPublish={handlePublishContractVersion}
              onReload={loadData}
            />
          )}
          {activeTab === "cpq" && (
            <CpqTab
              ruleSets={ruleSets}
              loading={loading}
              onShowDialog={() => setShowRuleDialog(true)}
            />
          )}
        </>
      )}

      <QuoteTemplateDialog
        open={showQuoteDialog}
        onOpenChange={setShowQuoteDialog}
        formData={newQuoteTemplate}
        setFormData={setNewQuoteTemplate}
        onSubmit={handleCreateQuoteTemplate}
      />

      <ContractTemplateDialog
        open={showContractDialog}
        onOpenChange={setShowContractDialog}
        formData={newContractTemplate}
        setFormData={setNewContractTemplate}
        onSubmit={handleCreateContractTemplate}
      />

      <RuleSetDialog
        open={showRuleDialog}
        onOpenChange={setShowRuleDialog}
        formData={newRuleSet}
        setFormData={setNewRuleSet}
        onSubmit={handleCreateRuleSet}
      />

      <PreviewDialog
        open={showPreviewDialog}
        onOpenChange={setShowPreviewDialog}
        previewPayload={previewPayload}
      />
    </motion.div>
  );
}
