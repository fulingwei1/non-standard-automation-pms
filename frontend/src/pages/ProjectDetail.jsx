import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    projectApi,
    machineApi,
    stageApi,
    milestoneApi,
    memberApi,
    costApi,
    documentApi
} from '../services/api';
import ProjectForm from '../components/ProjectForm';
import MachineForm from '../components/MachineForm';
import {
    ArrowLeft,
    Briefcase,
    Box,
    CheckCircle2,
    Users,
    DollarSign,
    FileText,
    Calendar,
    Clock,
    Plus,
    MoreVertical,
    Activity,
    Edit2
} from 'lucide-react';

const ProjectDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [project, setProject] = useState(null);
    const [stages, setStages] = useState([]);
    const [machines, setMachines] = useState([]);
    const [members, setMembers] = useState([]);
    const [costs, setCosts] = useState([]);
    const [milestones, setMilestones] = useState([]);
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    // Modal states
    const [isProjectFormOpen, setIsProjectFormOpen] = useState(false);
    const [isMachineFormOpen, setIsMachineFormOpen] = useState(false);
    const [editingMachine, setEditingMachine] = useState(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [projRes, stagesRes, machinesRes, membersRes, milestonesRes, costsRes, docsRes] = await Promise.all([
                projectApi.get(id),
                stageApi.list(id),
                machineApi.list({ project_id: id }),
                memberApi.list(id),
                milestoneApi.list(id),
                costApi.list(id),
                documentApi.list(id)
            ]);

            setProject(projRes.data);
            setStages(stagesRes.data);
            setMachines(machinesRes.data);
            setMembers(membersRes.data);
            setMilestones(milestonesRes.data);
            setCosts(costsRes.data);
            setDocuments(docsRes.data);
        } catch (err) {
            console.error('Failed to fetch project details:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [id]);

    const handleUpdateProject = async (data) => {
        try {
            await projectApi.update(id, data);
            setIsProjectFormOpen(false);
            fetchData();
        } catch (err) {
            alert('更新项目失败: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleMachineSubmit = async (data) => {
        try {
            if (editingMachine) {
                await machineApi.update(editingMachine.id, data);
            } else {
                await machineApi.create(data);
            }
            setIsMachineFormOpen(false);
            setEditingMachine(null);
            fetchData();
        } catch (err) {
            alert('提交设备失败: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleEditMachine = (machine) => {
        setEditingMachine(machine);
        setIsMachineFormOpen(true);
    };

    const handleAddMachine = () => {
        setEditingMachine(null);
        setIsMachineFormOpen(true);
    };

    if (loading) return <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>详情加载中...</div>;
    if (!project) return <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>未找到项目</div>;

    const tabs = [
        { id: 'overview', name: '概览', icon: Activity },
        { id: 'stages', name: '进度计划', icon: Clock },
        { id: 'machines', name: '设备列表', icon: Box },
        { id: 'team', name: '项目团队', icon: Users },
        { id: 'finance', name: '财务/成本', icon: DollarSign },
        { id: 'docs', name: '文档中心', icon: FileText },
    ];

    return (
        <div className="animate-fade">
            {/* Header */}
            <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button
                    onClick={() => navigate('/projects')}
                    className="nav-item"
                    style={{ padding: '8px', background: 'rgba(255,255,255,0.05)' }}
                >
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-gradient" style={{ fontSize: '1.8rem', fontWeight: 700 }}>{project.project_name}</h1>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                        <span>{project.project_code}</span>
                        <span>•</span>
                        <span>客户: {project.customer_name}</span>
                        <span>•</span>
                        <span>负责人: {project.pm_name}</span>
                    </div>
                </div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: '12px' }}>
                    <button
                        className="btn-primary"
                        style={{ background: 'rgba(255,255,255,0.05)', color: 'white' }}
                        onClick={() => setIsProjectFormOpen(true)}
                    >
                        编辑详情
                    </button>
                </div>
            </div>

            {/* Quick Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div className="glass-card" style={{ padding: '20px' }}>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>整体进度</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, margin: '8px 0' }}>{project.progress_pct}%</div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' }}>
                        <div style={{ width: `${project.progress_pct}%`, height: '100%', background: 'var(--primary-color)', borderRadius: '10px' }} />
                    </div>
                </div>
                <div className="glass-card" style={{ padding: '20px' }}>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>当前阶段</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, margin: '8px 0' }}>{project.stage}</div>
                    <div style={{ fontSize: '0.8rem', color: '#4ade80' }}>状态正常</div>
                </div>
                <div className="glass-card" style={{ padding: '20px' }}>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>机台总数</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, margin: '8px 0' }}>{machines.length}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>已完成 {machines.filter(m => m.progress_pct === 100).length} 个</div>
                </div>
                <div className="glass-card" style={{ padding: '20px' }}>
                    <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>交付日期</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600, margin: '8px 0' }}>{project.planned_end_date ? new Date(project.planned_end_date).toLocaleDateString() : '未设置'}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>计划结点</div>
                </div>
            </div>

            {/* Tabs */}
            <div className="glass-panel" style={{ padding: '4px', display: 'flex', gap: '4px', marginBottom: '24px', borderRadius: '12px' }}>
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                        style={{ flex: 1, justifyContent: 'center', transition: 'all 0.3s' }}
                    >
                        <tab.icon size={18} />
                        <span>{tab.name}</span>
                    </button>
                ))}
            </div>

            {/* Content Area */}
            <div className="glass-panel" style={{ minHeight: '400px', padding: '24px' }}>
                {activeTab === 'overview' && (
                    <div className="animate-fade">
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
                            <div>
                                <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Activity size={20} color="var(--primary-color)" />
                                    关键里程碑
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                    {milestones.length > 0 ? milestones.map(m => (
                                        <div key={m.id} className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '16px' }}>
                                            <div style={{ color: m.is_completed ? '#4ade80' : 'var(--text-dim)' }}>
                                                <CheckCircle2 size={24} />
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ fontWeight: 600 }}>{m.milestone_name}</div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>计划: {m.planned_date}</div>
                                            </div>
                                            <span style={{ fontSize: '0.75rem', padding: '4px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                                                {m.milestone_type}
                                            </span>
                                        </div>
                                    )) : <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.02)', borderRadius: '12px' }}>暂无里程碑</div>}
                                </div>
                            </div>
                            <div>
                                <h3 style={{ marginBottom: '16px' }}>项目信息</h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                    <div className="glass-card" style={{ padding: '16px' }}>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px' }}>项目经理</div>
                                        <div style={{ fontWeight: 500 }}>{project.pm_name || '未指定'}</div>
                                    </div>
                                    <div className="glass-card" style={{ padding: '16px' }}>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px' }}>交付合同</div>
                                        <div style={{ fontWeight: 500 }}>{project.contract_no || '无编号'}</div>
                                    </div>
                                    <div className="glass-card" style={{ padding: '16px' }}>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px' }}>预算金额</div>
                                        <div style={{ fontWeight: 500, color: 'var(--accent-color)' }}>¥ {project.budget_amount?.toLocaleString()}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'stages' && (
                    <div className="animate-fade">
                        <div style={{ position: 'relative' }}>
                            <div style={{ position: 'absolute', left: '19px', top: '10px', bottom: '10px', width: '2px', background: 'rgba(255,255,255,0.05)' }} />
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                {stages.map((s, idx) => (
                                    <div key={s.id} style={{ display: 'flex', gap: '20px', position: 'relative' }}>
                                        <div style={{
                                            width: '40px', height: '40px', borderRadius: '50%',
                                            background: s.status === 'COMPLETED' ? 'var(--primary-color)' : 'rgba(255,255,255,0.05)',
                                            border: s.id === project.current_stage_id ? '2px solid var(--primary-color)' : 'none',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            zIndex: 1
                                        }}>
                                            {s.status === 'COMPLETED' ? <CheckCircle2 size={20} color="white" /> : <span style={{ fontSize: '0.9rem' }}>{s.stage_code}</span>}
                                        </div>
                                        <div className="glass-card" style={{ flex: 1, padding: '16px', borderLeft: s.id === project.current_stage_id ? '4px solid var(--primary-color)' : 'none' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                                <div style={{ fontWeight: 600 }}>{s.stage_name}</div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                                                    {s.planned_start_date ? new Date(s.planned_start_date).toLocaleDateString() : '-'} ~ {s.planned_end_date ? new Date(s.planned_end_date).toLocaleDateString() : '-'}
                                                </div>
                                            </div>
                                            <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginBottom: '12px' }}>{s.description}</p>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' }}>
                                                    <div style={{ width: `${s.progress_pct}%`, height: '100%', background: 'var(--primary-color)', borderRadius: '10px' }} />
                                                </div>
                                                <span style={{ fontSize: '0.8rem' }}>{s.progress_pct}%</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'machines' && (
                    <div className="animate-fade">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                            <h3>设备明细 ({machines.length})</h3>
                            <button
                                className="btn-primary"
                                style={{ padding: '6px 12px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
                                onClick={handleAddMachine}
                            >
                                <Plus size={16} /> 添加设备
                            </button>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                            {machines.map(m => (
                                <div key={m.id} className="glass-card" style={{ padding: '20px', position: 'relative' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                                        <div style={{ width: '40px', height: '40px', background: 'rgba(99,102,241,0.1)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Box size={20} color="var(--primary-color)" />
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <span style={{ fontSize: '0.75rem', padding: '2px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                                                {m.stage}
                                            </span>
                                            <button
                                                onClick={() => handleEditMachine(m)}
                                                style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer' }}
                                            >
                                                <Edit2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                    <h4 style={{ marginBottom: '4px' }}>{m.machine_name}</h4>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '16px' }}>{m.machine_code}</div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                                        <span>进度</span>
                                        <span>{m.progress_pct}%</span>
                                    </div>
                                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' }}>
                                        <div style={{ width: `${m.progress_pct}%`, height: '100%', background: 'var(--secondary-color)', borderRadius: '10px' }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Other tabs can be implemented similarly */}
                {['team', 'finance', 'docs'].includes(activeTab) && (
                    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
                        <p>该模块数据接口已对接，界面渲染开发中...</p>
                    </div>
                )}
            </div>

            {/* Modals */}
            <ProjectForm
                isOpen={isProjectFormOpen}
                onClose={() => setIsProjectFormOpen(false)}
                onSubmit={handleUpdateProject}
                initialData={project}
            />

            <MachineForm
                isOpen={isMachineFormOpen}
                onClose={() => {
                    setIsMachineFormOpen(false);
                    setEditingMachine(null);
                }}
                onSubmit={handleMachineSubmit}
                initialData={editingMachine || {}}
                projectId={id}
            />

            <style>{`
                .nav-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 10px 16px;
                    color: var(--text-dim);
                    border-radius: 8px;
                    text-decoration: none;
                    transition: all 0.2s;
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 0.95rem;
                }
                .nav-item:hover {
                    color: white;
                    background: rgba(255, 255, 255, 0.05);
                }
                .nav-item.active {
                    color: white;
                    background: var(--primary-color);
                    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
                }
                .glass-card {
                    background: rgba(255, 255, 255, 0.03);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 16px;
                }
                .animate-fade {
                    animation: fadeIn 0.4s ease-out;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default ProjectDetail;
