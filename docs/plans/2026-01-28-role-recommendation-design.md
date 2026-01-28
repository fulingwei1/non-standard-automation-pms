# AI 角色推荐功能设计文档

## 概述

根据用户的工作岗位和职级，AI 自动推荐匹配的系统角色。所有推荐均需管理员确认后生效。

## 使用场景

| 场景 | 触发方式 | 交互流程 |
|-----|---------|---------|
| 新用户创建 | 用户管理→创建用户 | 自动显示推荐角色，可修改后保存 |
| 员工调岗/晋升 | 员工详情→岗位变更 | 弹窗提示"检测到岗位变更，是否更新角色？" |
| 批量角色检查 | 系统管理→角色推荐 | 定期或手动触发全量扫描，显示差异列表 |

## 推荐规则

### 匹配逻辑

采用**岗位+职级组合匹配**：
- 岗位决定基础角色类型（如项目经理→项目管理角色）
- 职级决定角色等级（如 M1-M2→基础角色，M3+→高级角色）
- 职级序列（P/M/T）可作为附加筛选条件

### 规则优先级

当一个用户匹配多条规则时，取优先级（priority）最高的规则。

---

## 数据模型

### 扩展 `position_roles` 表

现有表仅支持"岗位→角色"映射，需扩展支持职级条件：

```sql
-- 新增字段到 position_roles 表
ALTER TABLE position_roles ADD COLUMN min_level_rank INTEGER DEFAULT 0 COMMENT '最低职级rank（含）';
ALTER TABLE position_roles ADD COLUMN max_level_rank INTEGER DEFAULT 99 COMMENT '最高职级rank（含）';
ALTER TABLE position_roles ADD COLUMN level_category VARCHAR(10) COMMENT '职级序列（P/M/T，可选）';
ALTER TABLE position_roles ADD COLUMN priority INTEGER DEFAULT 0 COMMENT '优先级（数值越大优先级越高）';
ALTER TABLE position_roles ADD COLUMN description TEXT COMMENT '规则说明';

-- 添加索引
CREATE INDEX idx_pr_level_rank ON position_roles(min_level_rank, max_level_rank);
CREATE INDEX idx_pr_priority ON position_roles(priority);
```

### 规则配置示例

| 岗位 | 职级序列 | 最低职级 | 最高职级 | 推荐角色 | 优先级 |
|------|---------|---------|---------|---------|-------|
| 项目经理 | M | 1 | 2 | 项目管理-基础 | 10 |
| 项目经理 | M | 3 | 5 | 项目管理-高级 | 10 |
| 软件工程师 | P | 1 | 4 | 研发-基础 | 10 |
| 软件工程师 | P | 5 | 10 | 研发-高级 | 10 |
| 销售专员 | - | 0 | 99 | 销售-基础 | 5 |

---

## 后端设计

### 服务层：`RoleRecommendationService`

```python
class RoleRecommendationService:
    """角色推荐服务"""

    def get_recommended_roles(self, db: Session, user_id: int) -> List[Role]:
        """
        根据用户的岗位+职级，返回推荐的角色列表

        匹配逻辑：
        1. 获取用户的岗位和职级信息
        2. 查询匹配的推荐规则（岗位匹配 + 职级范围匹配）
        3. 按优先级排序，返回推荐角色
        """
        pass

    def get_recommendation_diff(self, db: Session, user_id: int) -> Dict:
        """
        返回当前角色与推荐角色的差异

        Returns:
            {
                "user_id": 1,
                "user_name": "张三",
                "position": "项目经理",
                "job_level": "M3",
                "current_roles": [{"id": 1, "name": "项目-基础"}],
                "recommended_roles": [{"id": 2, "name": "项目-高级"}],
                "to_add": [{"id": 2, "name": "项目-高级"}],
                "to_remove": [{"id": 1, "name": "项目-基础"}],
                "has_diff": True
            }
        """
        pass

    def batch_get_diffs(
        self, db: Session,
        only_with_diff: bool = True,
        department_id: int = None,
        position_id: int = None
    ) -> List[Dict]:
        """
        批量获取用户的角色差异

        Args:
            only_with_diff: 仅返回有差异的用户
            department_id: 按部门筛选
            position_id: 按岗位筛选
        """
        pass

    def apply_recommendation(
        self, db: Session,
        user_id: int,
        role_ids: List[int],
        operator_id: int
    ) -> None:
        """
        确认并应用角色分配（支持手动调整）

        Args:
            role_ids: 最终确认的角色ID列表（可能与推荐不同）
        """
        pass

    def batch_apply(
        self, db: Session,
        user_ids: List[int],
        operator_id: int
    ) -> Dict:
        """
        批量应用推荐（使用AI推荐的角色）

        Returns:
            {"success": 10, "failed": 0, "details": [...]}
        """
        pass
```

### API 端点

| 方法 | 路径 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/api/v1/role-recommendations/user/{user_id}` | 获取单用户推荐差异 | `ROLE_VIEW` |
| GET | `/api/v1/role-recommendations/batch` | 批量获取推荐差异列表 | `ROLE_VIEW` |
| POST | `/api/v1/role-recommendations/apply/{user_id}` | 确认单用户角色（可手动调整） | `USER_UPDATE` |
| POST | `/api/v1/role-recommendations/batch-apply` | 批量确认角色 | `USER_UPDATE` |
| GET | `/api/v1/role-recommendations/rules` | 获取推荐规则列表 | `ROLE_VIEW` |
| POST | `/api/v1/role-recommendations/rules` | 创建推荐规则 | `ROLE_CREATE` |
| PUT | `/api/v1/role-recommendations/rules/{id}` | 修改推荐规则 | `ROLE_UPDATE` |
| DELETE | `/api/v1/role-recommendations/rules/{id}` | 删除推荐规则 | `ROLE_DELETE` |

---

## 前端设计

### 1. 角色推荐主界面

**路径**：系统管理 → 角色推荐

**功能**：
- 显示所有用户的当前角色与推荐角色对比
- 支持筛选：仅显示有差异、按部门、按岗位、按职级
- 支持批量确认操作
- 差异可视化：⬆升级 ⬇降级 ➕新增 ➖移除 ✓已匹配

**界面布局**：
```
┌─────────────────────────────────────────────────────────────────┐
│  角色推荐管理                                    [刷新] [批量确认] │
├─────────────────────────────────────────────────────────────────┤
│  筛选：[仅显示有差异 ✓] [部门▼] [岗位▼] [职级▼]    共 12 人有差异  │
├─────────────────────────────────────────────────────────────────┤
│ □ │ 姓名     │ 岗位       │ 职级 │ 当前角色      │ 推荐角色      │ 操作     │
├───┼──────────┼───────────┼──────┼──────────────┼──────────────┼─────────┤
│ □ │ 张三     │ 项目经理   │ M3   │ 项目-基础    │ 项目-高级 ⬆  │ [确认]  │
│ □ │ 李四     │ 软件工程师 │ P5   │ 研发-基础    │ 研发-高级 ⬆  │ [确认]  │
│ □ │ 王五     │ 销售专员   │ P2   │ (无)         │ 销售-基础 ➕  │ [确认]  │
│ ─ │ 赵六     │ 产品经理   │ P4   │ 产品-基础    │ 产品-基础 ✓  │ 已匹配  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 单用户确认弹窗

**功能**：
- 显示用户岗位、职级信息
- 显示当前角色和AI推荐角色
- 支持手动增删角色
- 确认后应用

**界面布局**：
```
┌─────────────────────────────────────────┐
│  确认角色分配 - 张三                     │
├─────────────────────────────────────────┤
│  岗位：项目经理    职级：M3              │
│                                         │
│  当前角色：[项目-基础]                   │
│  推荐角色：[项目-高级] (AI推荐)          │
│                                         │
│  最终角色：[项目-高级 ×] [+ 添加角色]    │
│                                         │
│           [取消]    [确认分配]           │
└─────────────────────────────────────────┘
```

### 3. 推荐规则配置界面

**路径**：系统管理 → 角色推荐 → 规则配置（Tab页）

**功能**：
- 查看所有推荐规则
- 新建、编辑、删除规则
- 规则预览测试

**界面布局**：
```
┌──────────────────────────────────────────────────────────────────────┐
│  角色推荐规则配置                                        [+ 新建规则] │
├──────────────────────────────────────────────────────────────────────┤
│ 岗位         │ 职级序列 │ 职级范围  │ 推荐角色     │ 优先级 │ 操作    │
├──────────────┼─────────┼──────────┼─────────────┼───────┼────────┤
│ 项目经理     │ M       │ M1 - M2  │ 项目-基础    │ 10    │ [编辑] │
│ 项目经理     │ M       │ M3 - M5  │ 项目-高级    │ 10    │ [编辑] │
│ 软件工程师   │ P       │ P1 - P4  │ 研发-基础    │ 10    │ [编辑] │
│ 软件工程师   │ P       │ P5 - P10 │ 研发-高级    │ 10    │ [编辑] │
└─────────────────────────────────────────────────��────────────────────┘
```

### 4. 集成触发点

#### 4.1 用户创建流程集成

在"创建用户"表单中：
- 当选择员工后，自动查询推荐角色
- 在角色选择区域显示"AI推荐"标签
- 用户可修改后保存

#### 4.2 岗位变更流程集成

在员工岗位变更保存时：
- 检测岗位或职级是否变化
- 若变化，弹窗提示"检测到岗位/职级变更，是否更新系统角色？"
- 用户可选择"更新"或"保持不变"

---

## 文件清单

### 后端

| 文件路径 | 说明 |
|---------|------|
| `migrations/2026XXXX_role_recommendation_sqlite.sql` | 数据库迁移脚本 |
| `app/services/role_recommendation_service.py` | 角色推荐服务 |
| `app/api/v1/endpoints/role_recommendations.py` | API端点 |
| `app/schemas/role_recommendation.py` | 请求/响应模型 |

### 前端

| 文件路径 | 说明 |
|---------|------|
| `frontend/src/pages/RoleRecommendation/index.jsx` | 主界面 |
| `frontend/src/pages/RoleRecommendation/components/DiffTable.jsx` | 差异对比表格 |
| `frontend/src/pages/RoleRecommendation/components/ConfirmDialog.jsx` | 确认弹窗 |
| `frontend/src/pages/RoleRecommendation/components/RuleConfig.jsx` | 规则配置Tab |
| `frontend/src/pages/RoleRecommendation/components/RuleEditDialog.jsx` | 规则编辑弹窗 |
| `frontend/src/services/api/roleRecommendation.js` | API服务 |

---

## 实现优先级

1. **P0 - 核心功能**
   - 数据库扩展
   - 推荐服务核心逻辑
   - 批量差异查询API
   - 角色推荐主界面

2. **P1 - 确认流程**
   - 单用户确认（支持手动调整）
   - 批量确认

3. **P2 - 规则配置**
   - 规则CRUD API
   - 规则配置界面

4. **P3 - 流程集成**
   - 用户创建流程集成
   - 岗位变更流程集成
