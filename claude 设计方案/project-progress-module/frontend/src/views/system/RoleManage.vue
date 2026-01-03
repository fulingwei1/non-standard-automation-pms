<template>
  <div class="role-manage">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="queryParams">
        <el-form-item label="角色名称">
          <el-input v-model="queryParams.keyword" placeholder="角色名称/编码" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" value="正常" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>搜索</el-button>
          <el-button @click="handleReset"><el-icon><Refresh /></el-icon>重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16">
      <!-- 角色列表 -->
      <el-col :span="10">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>角色列表</span>
              <el-button type="primary" size="small" @click="handleAdd"><el-icon><Plus /></el-icon>新增</el-button>
            </div>
          </template>

          <el-table :data="roleList" v-loading="loading" highlight-current-row @current-change="handleSelectRole">
            <el-table-column prop="role_name" label="角色名称" />
            <el-table-column prop="role_code" label="角色编码" width="120" />
            <el-table-column label="数据范围" width="100">
              <template #default="{ row }">
                {{ dataScopeMap[row.data_scope] }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="handleEdit(row)" :disabled="row.is_system">编辑</el-button>
                <el-button link type="danger" size="small" @click.stop="handleDelete(row)" :disabled="row.is_system">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination 
            v-model:current-page="queryParams.page" 
            :total="total" 
            :page-size="20"
            layout="total, prev, pager, next" 
            @change="loadRoles"
            style="margin-top: 16px"
            small
          />
        </el-card>
      </el-col>

      <!-- 权限配置 -->
      <el-col :span="14">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                权限配置
                <el-tag v-if="selectedRole" type="info" size="small" style="margin-left: 8px">{{ selectedRole.role_name }}</el-tag>
              </span>
              <el-button type="primary" size="small" :disabled="!selectedRole || selectedRole.is_system" @click="handleSavePermissions">
                <el-icon><Check /></el-icon>保存配置
              </el-button>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="菜单权限" name="menu">
              <div v-if="selectedRole" class="permission-tree">
                <el-tree
                  ref="menuTreeRef"
                  :data="menuTree"
                  show-checkbox
                  node-key="menu_id"
                  :default-checked-keys="checkedMenus"
                  :props="{ label: 'menu_name', children: 'children' }"
                  @check="handleMenuCheck"
                >
                  <template #default="{ node, data }">
                    <span class="tree-node">
                      <el-icon v-if="data.icon"><component :is="data.icon" /></el-icon>
                      <span>{{ data.menu_name }}</span>
                      <el-tag v-if="data.menu_type === 'directory'" size="small" type="info">目录</el-tag>
                      <el-tag v-else-if="data.menu_type === 'button'" size="small" type="warning">按钮</el-tag>
                    </span>
                  </template>
                </el-tree>
              </div>
              <el-empty v-else description="请选择一个角色" />
            </el-tab-pane>

            <el-tab-pane label="操作权限" name="permission">
              <div v-if="selectedRole" class="permission-tree">
                <el-tree
                  ref="permTreeRef"
                  :data="permissionTree"
                  show-checkbox
                  node-key="permission_id"
                  :default-checked-keys="checkedPerms"
                  :props="{ label: 'permission_name', children: 'children' }"
                  @check="handlePermCheck"
                >
                  <template #default="{ node, data }">
                    <span class="tree-node">
                      <span>{{ data.permission_name }}</span>
                      <span class="perm-code">{{ data.permission_code }}</span>
                    </span>
                  </template>
                </el-tree>
              </div>
              <el-empty v-else description="请选择一个角色" />
            </el-tab-pane>

            <el-tab-pane label="数据权限" name="data">
              <div v-if="selectedRole" class="data-scope-form">
                <el-form label-width="100px">
                  <el-form-item label="数据范围">
                    <el-radio-group v-model="dataScope" :disabled="selectedRole.is_system">
                      <el-radio value="all">全部数据</el-radio>
                      <el-radio value="dept_and_child">本部门及子部门</el-radio>
                      <el-radio value="dept">仅本部门</el-radio>
                      <el-radio value="self">仅本人</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="说明">
                    <div class="scope-desc">
                      <p v-if="dataScope === 'all'">可查看系统所有数据</p>
                      <p v-else-if="dataScope === 'dept_and_child'">可查看本部门及下级部门的数据</p>
                      <p v-else-if="dataScope === 'dept'">只能查看本部门的数据</p>
                      <p v-else>只能查看自己的数据</p>
                    </div>
                  </el-form-item>
                </el-form>
              </div>
              <el-empty v-else description="请选择一个角色" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑角色' : '新增角色'" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="角色编码" prop="role_code">
          <el-input v-model="formData.role_code" placeholder="如：admin, pm, engineer" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="角色名称" prop="role_name">
          <el-input v-model="formData.role_name" placeholder="角色名称" />
        </el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="formData.data_scope" style="width: 100%">
            <el-option label="全部数据" value="all" />
            <el-option label="本部门及子部门" value="dept_and_child" />
            <el-option label="仅本部门" value="dept" />
            <el-option label="仅本人" value="self" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" rows="2" placeholder="角色描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Check } from '@element-plus/icons-vue'
import request from '@/utils/request'

// 数据状态
const loading = ref(false)
const roleList = ref([])
const total = ref(0)
const menuTree = ref([])
const permissionTree = ref([])
const selectedRole = ref(null)
const activeTab = ref('menu')

const queryParams = reactive({ keyword: '', status: '', page: 1 })

const dataScopeMap = {
  'all': '全部',
  'dept_and_child': '部门及子部门',
  'dept': '本部门',
  'self': '仅本人'
}

// 权限配置
const menuTreeRef = ref(null)
const permTreeRef = ref(null)
const checkedMenus = ref([])
const checkedPerms = ref([])
const dataScope = ref('self')

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const formData = reactive({
  role_code: '',
  role_name: '',
  data_scope: 'self',
  sort_order: 0,
  description: ''
})
const formRules = {
  role_code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
  role_name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

// 加载角色列表
const loadRoles = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/v1/system/roles', { params: queryParams })
    roleList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

// 加载菜单树
const loadMenus = async () => {
  const res = await request.get('/api/v1/system/menus')
  menuTree.value = res.data
}

// 加载权限树
const loadPermissions = async () => {
  const res = await request.get('/api/v1/system/permissions')
  permissionTree.value = res.data
}

// 选择角色
const handleSelectRole = async (row) => {
  if (!row) return
  selectedRole.value = row
  
  // 加载角色详情（包含已分配的权限）
  const res = await request.get(`/api/v1/system/roles/${row.role_id}`)
  checkedMenus.value = res.data.menus || []
  checkedPerms.value = res.data.permissions || []
  dataScope.value = res.data.data_scope || 'self'
  
  // 更新树选中状态
  await nextTick()
  if (menuTreeRef.value) {
    menuTreeRef.value.setCheckedKeys(checkedMenus.value)
  }
  if (permTreeRef.value) {
    permTreeRef.value.setCheckedKeys(checkedPerms.value)
  }
}

// 菜单勾选
const handleMenuCheck = (data, { checkedKeys }) => {
  checkedMenus.value = checkedKeys
}

// 权限勾选
const handlePermCheck = (data, { checkedKeys }) => {
  checkedPerms.value = checkedKeys
}

// 保存权限配置
const handleSavePermissions = async () => {
  try {
    // 保存菜单权限
    await request.put(`/api/v1/system/roles/${selectedRole.value.role_id}/menus`, {
      menu_ids: menuTreeRef.value?.getCheckedKeys() || []
    })
    // 保存操作权限
    await request.put(`/api/v1/system/roles/${selectedRole.value.role_id}/permissions`, {
      permission_ids: permTreeRef.value?.getCheckedKeys() || []
    })
    // 更新数据范围
    await request.put(`/api/v1/system/roles/${selectedRole.value.role_id}`, {
      data_scope: dataScope.value
    })
    ElMessage.success('权限配置保存成功')
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  }
}

// 搜索
const handleSearch = () => {
  queryParams.page = 1
  loadRoles()
}

const handleReset = () => {
  Object.assign(queryParams, { keyword: '', status: '', page: 1 })
  loadRoles()
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, { role_code: '', role_name: '', data_scope: 'self', sort_order: 0, description: '' })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除角色"${row.role_name}"吗？`, '警告', { type: 'warning' })
    .then(async () => {
      await request.delete(`/api/v1/system/roles/${row.role_id}`)
      ElMessage.success('删除成功')
      loadRoles()
      if (selectedRole.value?.role_id === row.role_id) {
        selectedRole.value = null
      }
    }).catch(() => {})
}

// 提交
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  try {
    if (isEdit.value) {
      await request.put(`/api/v1/system/roles/${formData.role_id}`, formData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/api/v1/system/roles', formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadRoles()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => {
  loadRoles()
  loadMenus()
  loadPermissions()
})
</script>

<style scoped>
.role-manage {
  padding: 20px;
}

.search-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.permission-tree {
  max-height: 500px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

.perm-code {
  color: #999;
  font-size: 12px;
  margin-left: 8px;
}

.data-scope-form {
  padding: 20px;
}

.scope-desc {
  color: #999;
  font-size: 13px;
}

.scope-desc p {
  margin: 0;
}

:deep(.el-radio) {
  display: block;
  margin-bottom: 10px;
}
</style>
