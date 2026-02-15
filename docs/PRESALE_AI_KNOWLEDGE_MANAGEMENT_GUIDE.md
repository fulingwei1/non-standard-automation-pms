# 售前AI知识库管理指南

## 📋 目录

1. [管理员职责](#管理员职责)
2. [知识库维护](#知识库维护)
3. [数据质量管理](#数据质量管理)
4. [系统监控与优化](#系统监控与优化)
5. [故障排查](#故障排查)

---

## 管理员职责

### 核心职责

作为AI知识库管理员，您需要：

1. **内容管理**
   - 审核和优化案例质量
   - 删除低质量或过时案例
   - 补充关键信息和标签

2. **数据维护**
   - 定期更新嵌入向量
   - 清理重复或相似案例
   - 维护标签体系

3. **性能监控**
   - 监控搜索性能
   - 分析用户反馈
   - 优化推荐算法

4. **用户支持**
   - 培训新用户
   - 收集功能需求
   - 解答使用问题

---

## 知识库维护

### 1. 案例质量审核

#### 审核标准

**优质案例** (质量评分 ≥ 0.8):
- ✅ 项目摘要完整清晰
- ✅ 技术亮点详细具体
- ✅ 有明确的成功要素或失败教训
- ✅ 标签准确且数量充足（≥3个）
- ✅ 项目金额和客户信息完整

**中等案例** (0.6 ≤ 质量评分 < 0.8):
- ⚠️ 信息基本完整但不够详细
- ⚠️ 缺少部分关键字段
- ⚠️ 标签数量不足

**低质量案例** (质量评分 < 0.6):
- ❌ 信息严重不完整
- ❌ 只有基本字段，无详细描述
- ❌ 标签缺失或不准确

#### 审核流程

1. **每周审核**
   ```sql
   -- 查询新增案例
   SELECT * FROM presale_knowledge_case 
   WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
   ORDER BY quality_score DESC;
   ```

2. **质量评估**
   - 阅读案例内容
   - 检查完整度和准确性
   - 调整质量评分

3. **优化处理**
   - 补充缺失信息
   - 优化标签
   - 更新案例状态

### 2. 案例去重

#### 识别重复案例

重复案例特征：
- 案例名称高度相似
- 客户名称相同
- 项目金额和时间接近
- 技术内容重复

#### 去重步骤

1. **查找疑似重复**
   ```python
   python scripts/find_duplicate_cases.py
   ```

2. **人工确认**
   - 对比案例详情
   - 确认是否为同一项目

3. **合并处理**
   - 保留质量更高的案例
   - 合并两个案例的优质内容
   - 删除重复案例

### 3. 标签体系维护

#### 标签规范

**行业标签**:
- 汽车制造、新能源汽车、消费电子、工业自动化
- 医疗设备、通讯设备、物联网、机器人

**技术标签**:
- ICT测试、功能测试、AOI检测、光学测试
- 电源测试、网络测试、RF测试、显示测试

**特性标签**:
- 高精度、高压测试、车规级、医疗级
- 大型项目、复杂系统、定制化

#### 标签优化

1. **合并同义标签**
   - "汽车" → "汽车制造"
   - "手机测试" → "消费电子"

2. **补充缺失标签**
   - 行业标签：至少1个
   - 技术标签：至少1个
   - 特性标签：根据情况添加

3. **删除无用标签**
   - 过于宽泛的标签（如"项目"）
   - 拼写错误的标签
   - 使用次数<3的冷门标签

### 4. 嵌入向量更新

#### 何时需要更新？

- 案例内容发生重大修改
- 新增大量案例（>20个）
- 搜索准确率下降

#### 更新流程

```bash
# 1. 备份数据库
mysqldump -u user -p database > backup.sql

# 2. 生成嵌入向量
python scripts/generate_embeddings.py

# 3. 验证更新
python scripts/verify_embeddings.py
```

---

## 数据质量管理

### 质量监控指标

#### 1. 案例完整度

```sql
-- 检查案例完整度
SELECT 
    COUNT(*) as total_cases,
    SUM(CASE WHEN project_summary IS NOT NULL THEN 1 ELSE 0 END) as has_summary,
    SUM(CASE WHEN technical_highlights IS NOT NULL THEN 1 ELSE 0 END) as has_highlights,
    SUM(CASE WHEN tags IS NOT NULL AND JSON_LENGTH(tags) >= 3 THEN 1 ELSE 0 END) as has_tags,
    AVG(quality_score) as avg_quality
FROM presale_knowledge_case;
```

**目标值**:
- 案例完整度 > 90%
- 平均质量评分 > 0.75
- 有效标签覆盖 > 95%

#### 2. 搜索性能

监控指标：
- 平均响应时间
- 搜索结果相关性
- 用户满意度（问答反馈）

```sql
-- 问答反馈统计
SELECT 
    AVG(feedback_score) as avg_feedback,
    COUNT(*) as total_qa,
    SUM(CASE WHEN feedback_score >= 4 THEN 1 ELSE 0 END) / COUNT(*) as satisfaction_rate
FROM presale_ai_qa
WHERE feedback_score IS NOT NULL;
```

**目标值**:
- 平均反馈评分 > 4.0
- 满意度（4-5星） > 80%
- 响应时间 < 2秒

#### 3. 知识库活跃度

```sql
-- 案例使用频率
SELECT 
    DATE_FORMAT(created_at, '%Y-%m') as month,
    COUNT(*) as new_cases,
    (SELECT COUNT(*) FROM presale_ai_qa WHERE DATE_FORMAT(created_at, '%Y-%m') = month) as qa_count
FROM presale_knowledge_case
GROUP BY month
ORDER BY month DESC
LIMIT 12;
```

**目标值**:
- 月新增案例 > 10
- 月问答次数 > 100
- 案例使用率 > 60%

### 质量提升措施

1. **定期清理**
   - 每月：删除质量评分<0.5的案例
   - 每季度：归档过时案例（>2年且使用频率低）

2. **内容增强**
   - 补充高价值案例的详细信息
   - 联系项目负责人获取第一手资料
   - 添加实际效果和客户反馈

3. **用户培训**
   - 培训用户正确使用搜索功能
   - 鼓励用户提供反馈
   - 收集改进建议

---

## 系统监控与优化

### 性能监控

#### 1. 日志分析

查看搜索日志：
```bash
tail -f logs/presale_ai_knowledge.log | grep "semantic_search"
```

关注指标：
- 查询响应时间
- 错误率
- 热门搜索词

#### 2. 数据库性能

```sql
-- 慢查询检查
SHOW FULL PROCESSLIST;

-- 索引使用情况
EXPLAIN SELECT * FROM presale_knowledge_case 
WHERE industry = '汽车制造' AND quality_score >= 0.8;
```

优化建议：
- 确保索引有效
- 定期优化表
- 监控查询性能

#### 3. 向量搜索优化

如果搜索变慢：
1. 检查嵌入向量是否完整
2. 考虑增加向量索引（如使用Faiss）
3. 限制搜索范围（添加筛选条件）

### 系统优化

#### 1. 缓存策略

热门查询缓存：
```python
# 在服务层添加缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def semantic_search_cached(query_hash, filters):
    # 缓存搜索结果
    pass
```

#### 2. 数据库优化

```sql
-- 添加复合索引
CREATE INDEX idx_industry_quality ON presale_knowledge_case(industry, quality_score);
CREATE INDEX idx_equipment_quality ON presale_knowledge_case(equipment_type, quality_score);

-- 优化表
OPTIMIZE TABLE presale_knowledge_case;
OPTIMIZE TABLE presale_ai_qa;
```

#### 3. 负载均衡

高并发场景：
- 使用Redis缓存热门查询
- 部署只读副本分担查询压力
- 异步处理嵌入向量生成

---

## 故障排查

### 常见问题

#### 1. 搜索无结果

**可能原因**:
- 嵌入向量缺失
- 筛选条件过于严格
- 案例被误标记为非公开

**排查步骤**:
```sql
-- 检查案例总数和公开数量
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_public = 1 THEN 1 ELSE 0 END) as public_cases,
    SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as has_embedding
FROM presale_knowledge_case;

-- 检查筛选条件匹配的案例数
SELECT COUNT(*) 
FROM presale_knowledge_case 
WHERE industry = '目标行业' AND is_public = 1;
```

**解决方法**:
1. 生成缺失的嵌入向量
2. 放宽筛选条件
3. 检查案例公开状态

#### 2. 搜索速度慢

**可能原因**:
- 案例数量过多
- 嵌入向量计算复杂
- 数据库索引缺失

**排查步骤**:
```sql
-- 检查案例数量
SELECT COUNT(*) FROM presale_knowledge_case;

-- 检查索引使用
SHOW INDEX FROM presale_knowledge_case;
```

**解决方法**:
1. 添加必要的筛选条件
2. 优化嵌入向量计算
3. 添加数据库索引
4. 考虑使用向量数据库（Faiss/Chroma）

#### 3. 智能问答质量差

**可能原因**:
- 相关案例质量低
- 匹配的案例数量少
- 问题描述不清晰

**排查步骤**:
```sql
-- 检查问答置信度分布
SELECT 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'High'
        WHEN confidence_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as confidence_level,
    COUNT(*) as count,
    AVG(feedback_score) as avg_feedback
FROM presale_ai_qa
WHERE feedback_score IS NOT NULL
GROUP BY confidence_level;
```

**解决方法**:
1. 提升案例质量
2. 增加相关领域案例
3. 优化问答算法
4. 引导用户提供更详细的问题描述

#### 4. 嵌入向量生成失败

**可能原因**:
- API密钥失效（如使用OpenAI）
- 网络连接问题
- 文本内容异常

**排查步骤**:
```bash
# 检查API配置
python -c "import openai; print(openai.api_key)"

# 测试嵌入生成
python scripts/test_embedding_generation.py
```

**解决方法**:
1. 更新API密钥
2. 检查网络连接
3. 清理异常文本内容
4. 使用备用嵌入服务

---

## 备份与恢复

### 数据备份

#### 定期备份
```bash
#!/bin/bash
# 每日备份脚本

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/presale_ai_knowledge"

# 备份数据库
mysqldump -u user -p database presale_knowledge_case presale_ai_qa > \
  $BACKUP_DIR/ai_knowledge_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/ai_knowledge_$DATE.sql

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

#### 数据恢复
```bash
# 恢复数据库
gunzip < backup.sql.gz | mysql -u user -p database

# 验证恢复
mysql -u user -p -e "SELECT COUNT(*) FROM presale_knowledge_case"

# 重新生成嵌入向量
python scripts/generate_embeddings.py
```

---

## 最佳实践建议

### 1. 定期维护计划

**每日**:
- 监控系统错误日志
- 检查新增案例质量

**每周**:
- 审核新增案例
- 分析用户反馈
- 优化低质量案例

**每月**:
- 案例质量全面审核
- 更新嵌入向量
- 生成质量报告
- 清理低价值案例

**每季度**:
- 系统性能评估
- 优化标签体系
- 用户培训
- 功能改进计划

### 2. 质量控制流程

1. **新案例审核** (48小时内)
   - 检查完整度
   - 验证准确性
   - 补充标签

2. **质量评分调整**
   - 基于使用频率调整
   - 基于用户反馈调整
   - 定期重新评估

3. **案例归档**
   - 过时案例(>2年)标记归档
   - 归档案例不参与搜索
   - 保留历史记录

### 3. 用户反馈机制

1. **收集反馈**
   - 问答评分
   - 案例有用性投票
   - 功能改进建议

2. **分析反馈**
   - 低评分案例优化
   - 热门需求统计
   - 功能优先级排序

3. **持续改进**
   - 基于反馈优化算法
   - 补充用户需要的案例
   - 改进用户界面

---

## 📞 技术支持

- **系统问题**: tech-support@company.com
- **数据问题**: data-team@company.com
- **紧急故障**: emergency@company.com (24/7)

---

**版本**: v1.0  
**更新日期**: 2026-02-15  
**文档维护**: 技术管理团队
