import { useState, useCallback, useEffect } from 'react';
import { costApi } from '../../../services/api/projects.js';

export function useCostAccounting() {
    const [costs, setCosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ project_id: '', range: 'month' });

    const loadCosts = useCallback(async () => {
        try {
            setLoading(true);
            const { project_id, ...otherParams } = filters;
            
            // 使用项目中心路由：如果指定了项目ID，使用 /projects/{project_id}/costs
            // 否则提示需要选择项目（跨项目查询功能可能需要通过 analytics 模块实现）
            if (project_id) {
                const response = await costApi.list(project_id, otherParams);
                setCosts(response.data?.items || response.data?.items || response.data || []);
            } else {
                // 未选择项目时保持空态，不在页面初始化阶段刷 console。
                setCosts([]);
            }
        } catch (err) { 
            console.error('加载成本数据失败:', err);
            setCosts([]);
        }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadCosts(); }, [loadCosts]);
    return { costs, loading, filters, setFilters, loadCosts };
}
