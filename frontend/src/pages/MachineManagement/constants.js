/**
 * 机台管理模块 - 配置常量
 */

// 机台状态配置
export const statusConfigs = {
    DESIGNING: { label: '设计中', color: 'bg-blue-500' },
    PROCURING: { label: '采购中', color: 'bg-amber-500' },
    PRODUCING: { label: '生产中', color: 'bg-purple-500' },
    ASSEMBLING: { label: '装配中', color: 'bg-violet-500' },
    TESTING: { label: '调试中', color: 'bg-cyan-500' },
    COMPLETED: { label: '已完成', color: 'bg-emerald-500' },
};

// 健康度配置
export const healthConfigs = {
    H1: { label: '健康', color: 'bg-emerald-500' },
    H2: { label: '正常', color: 'bg-blue-500' },
    H3: { label: '警告', color: 'bg-amber-500' },
    H4: { label: '危险', color: 'bg-red-500' },
};

// 文档类型配置
export const docTypeConfigs = {
    CIRCUIT_DIAGRAM: { label: '电路图', iconName: 'Zap', color: 'text-yellow-500' },
    PLC_PROGRAM: { label: 'PLC程序', iconName: 'Code', color: 'text-blue-500' },
    LABELWORK_PROGRAM: { label: 'Labelwork程序', iconName: 'FileCode', color: 'text-purple-500' },
    BOM_DOCUMENT: { label: 'BOM文档', iconName: 'Layers', color: 'text-green-500' },
    FAT_DOCUMENT: { label: 'FAT文档', iconName: 'FileCheck', color: 'text-emerald-500' },
    SAT_DOCUMENT: { label: 'SAT文档', iconName: 'FileCheck', color: 'text-teal-500' },
    OTHER: { label: '其他文档', iconName: 'FileText', color: 'text-slate-500' },
};

// 初始表单状态
export const initialMachineForm = {
    machine_code: '',
    machine_name: '',
    machine_type: '',
    stage: 'DESIGNING',
    status: 'DESIGNING',
    health: 'H2',
    description: '',
};

export const initialUploadForm = {
    doc_type: 'OTHER',
    doc_name: '',
    doc_no: '',
    version: '1.0',
    description: '',
    machine_stage: '',
};
