/**
 * 机台管理页面（重构版本）
 * Features: 机台列表、详情、创建、更新、进度管理
 * 
 * 原文件: 1066行
 * 重构后: 模块化结构，主文件约200行
 */
import { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus } from 'lucide-react';
import { PageHeader } from '../../components/layout';
import { Button } from '../../components/ui/button';

// Hooks
import { useMachineData, useMachineDocuments } from './hooks';

// Components
import { MachineFilters, MachineTable, CreateMachineDialog } from './components';

// Constants
import { initialMachineForm } from './constants';

export default function MachineManagement() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    // 使用自定义 Hooks
    const machineData = useMachineData(id);
    const documentData = useMachineDocuments();

    // 对话框状态
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [selectedMachine, setSelectedMachine] = useState(null);

    // 表单状态
    const [newMachine, setNewMachine] = useState(initialMachineForm);

    // 如果 URL 中有 machine_id 参数，自动打开详情对话框
    useEffect(() => {
        const machineId = searchParams.get('machine_id');
        if (
            machineId &&
            !showDetailDialog &&
            machineData.machines.length > 0 &&
            !selectedMachine
        ) {
            const machineIdNum = parseInt(machineId);
            const machine = machineData.machines.find((m) => m.id === machineIdNum);
            if (machine) {
                handleViewDetail(machineIdNum);
            }
        }
    }, [searchParams, machineData.machines, showDetailDialog, selectedMachine]);

    // 过滤后的机台列表
    const filteredMachines = useMemo(() => {
        return machineData.machines.filter((machine) => {
            if (machineData.filters.searchKeyword) {
                const keyword = machineData.filters.searchKeyword.toLowerCase();
                return (
                    machine.machine_code?.toLowerCase().includes(keyword) ||
                    machine.machine_name?.toLowerCase().includes(keyword) ||
                    machine.machine_type?.toLowerCase().includes(keyword)
                );
            }
            return true;
        });
    }, [machineData.machines, machineData.filters.searchKeyword]);

    // 创建机台
    const handleCreateMachine = async () => {
        if (!newMachine.machine_code || !newMachine.machine_name) {
            alert('请填写机台编码和名称');
            return;
        }

        const result = await machineData.createMachine({
            ...newMachine,
            stage: newMachine.status,
        });

        if (result.success) {
            setShowCreateDialog(false);
            setNewMachine(initialMachineForm);
        } else {
            alert('创建机台失败: ' + result.error);
        }
    };

    // 查看机台详情
    const handleViewDetail = async (machineId) => {
        try {
            const machine = await machineData.getMachineDetail(machineId);
            setSelectedMachine(machine);
            setShowDetailDialog(true);
            documentData.fetchDocuments(machineId);
        } catch (error) {
            console.error('Failed to fetch machine detail:', error);
        }
    };

    return (
        <div className="space-y-6 p-6">
            {/* 头部 */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/projects/${id}`)}
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        返回项目
                    </Button>
                    <PageHeader
                        title={`${machineData.project?.project_name || '项目'} - 机台管理`}
                        description="机台列表、详情、创建、进度管理"
                    />
                </div>
                <Button onClick={() => setShowCreateDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    新建机台
                </Button>
            </div>

            {/* 过滤器 */}
            <MachineFilters
                filters={machineData.filters}
                onFiltersChange={machineData.setFilters}
            />

            {/* 机台列表 */}
            <MachineTable
                machines={filteredMachines}
                loading={machineData.loading}
                onViewDetail={handleViewDetail}
            />

            {/* 创建机台对话框 */}
            <CreateMachineDialog
                open={showCreateDialog}
                onOpenChange={setShowCreateDialog}
                formData={newMachine}
                onFormChange={setNewMachine}
                onSubmit={handleCreateMachine}
            />

            {/* TODO: 添加机台详情对话框组件 */}
            {/* 原文件中的详情对话框逻辑较复杂，可以进一步拆分为独立组件 */}
        </div>
    );
}
