-- 修复审批模板 code 与服务引用不匹配(F1/ECN1/TS1)：孤儿 TPL_* 模板改为服务期望的 code
UPDATE approval_templates SET template_code='SALES_CONTRACT_APPROVAL' WHERE template_code='TPL_CONTRACT';
UPDATE approval_templates SET template_code='ECN_STANDARD' WHERE template_code='TPL_ECN';
UPDATE approval_templates SET template_code='TIMESHEET_APPROVAL' WHERE template_code='TPL_TIMESHEET';
