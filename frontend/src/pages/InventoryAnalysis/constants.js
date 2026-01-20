export const stockStatusConfigs = {
    normal: { label: '正常', color: 'bg-emerald-500' },
    low: { label: '低库存', color: 'bg-amber-500' },
    out: { label: '缺货', color: 'bg-red-500' },
    over: { label: '过剩', color: 'bg-purple-500' },
};

export const categoryConfigs = {
    mechanical: { label: '机械件', icon: 'Cog' },
    electrical: { label: '电气件', icon: 'Zap' },
    electronic: { label: '电子件', icon: 'Cpu' },
    standard: { label: '标准件', icon: 'Box' },
    consumable: { label: '耗材', icon: 'Package' },
};

export const warehouseConfigs = {
    main: { label: '主仓库', code: 'WH01' },
    spare: { label: '备件库', code: 'WH02' },
    temp: { label: '暂存区', code: 'WH03' },
};
