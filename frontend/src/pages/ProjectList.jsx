import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectApi } from '../services/api';
import { Briefcase, ChevronRight } from 'lucide-react';
import ProjectForm from '../components/ProjectForm';

const ProjectList = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const fetchProjects = async () => {
        try {
            const response = await projectApi.list();
            setProjects(response.data);
        } catch (err) {
            console.error('Failed to fetch projects:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProjects();
    }, []);

    const handleCreateProject = async (data) => {
        try {
            await projectApi.create(data);
            setIsModalOpen(false);
            fetchProjects();
        } catch (err) {
            alert('创建项目失败: ' + (err.response?.data?.detail || err.message));
        }
    };

    if (loading) return <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>数据加载中...</div>;

    return (
        <div className="animate-fade">
            <div className="header">
                <h1 className="text-gradient">项目管理</h1>
                <button
                    className="btn-primary"
                    onClick={() => setIsModalOpen(true)}
                >
                    新建项目
                </button>
            </div>

            <ProjectForm
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleCreateProject}
            />

            <div className="glass-panel" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ background: 'rgba(255,255,255,0.03)', textAlign: 'left' }}>
                            <th style={{ padding: '16px 24px', color: 'var(--text-dim)', fontWeight: 500 }}>项目信息</th>
                            <th style={{ padding: '16px 24px', color: 'var(--text-dim)', fontWeight: 500 }}>客户</th>
                            <th style={{ padding: '16px 24px', color: 'var(--text-dim)', fontWeight: 500 }}>阶段/健康度</th>
                            <th style={{ padding: '16px 24px', color: 'var(--text-dim)', fontWeight: 500 }}>进度</th>
                            <th style={{ padding: '16px 24px' }}></th>
                        </tr>
                    </thead>
                    <tbody>
                        {projects.length > 0 ? projects.map(project => (
                            <tr
                                key={project.id}
                                onClick={() => navigate(`/projects/${project.id}`)}
                                style={{ borderBottom: '1px solid var(--border-color)', transition: 'var(--transition-smooth)', cursor: 'pointer' }}
                                className="table-row-hover"
                            >
                                <td style={{ padding: '20px 24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <div style={{ padding: '8px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px' }}>
                                            <Briefcase size={18} color="var(--primary-color)" />
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 600 }}>{project.project_name}</div>
                                            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '2px' }}>{project.project_code}</div>
                                        </div>
                                    </div>
                                </td>
                                <td style={{ padding: '20px 24px' }}>
                                    <div style={{ fontSize: '0.9rem' }}>{project.customer_name || '未指定'}</div>
                                </td>
                                <td style={{ padding: '20px 24px' }}>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <span style={{ fontSize: '0.75rem', padding: '2px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>{project.stage}</span>
                                        <span style={{ fontSize: '0.75rem', padding: '2px 8px', background: project.health === 'H1' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(234, 179, 8, 0.1)', color: project.health === 'H1' ? '#4ade80' : '#fbbf24', borderRadius: '4px' }}>
                                            {project.health}
                                        </span>
                                    </div>
                                </td>
                                <td style={{ padding: '20px 24px' }}>
                                    <div style={{ width: '120px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                                            <span>{project.progress_pct}%</span>
                                        </div>
                                        <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px' }}>
                                            <div style={{ width: `${project.progress_pct}%`, height: '100%', background: 'var(--primary-color)', borderRadius: '10px' }} />
                                        </div>
                                    </div>
                                </td>
                                <td style={{ padding: '20px 24px', textAlign: 'right' }}>
                                    <button className="nav-item" style={{ padding: '8px' }}>
                                        <ChevronRight size={18} />
                                    </button>
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan="5" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
                                    暂无项目数据
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style>{`
        .table-row-hover:hover {
          background: rgba(255, 255, 255, 0.02);
        }
      `}</style>
        </div>
    );
};

export default ProjectList;
