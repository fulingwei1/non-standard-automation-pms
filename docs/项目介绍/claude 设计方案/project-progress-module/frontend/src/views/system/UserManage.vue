<template>
  <div class="user-manage">
    <!-- 搜索栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="用户名/姓名/工号" clearable style="width: 180px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="部门">
          <el-tree-select v-model="queryParams.dept_id" :data="deptTree" placeholder="选择部门" clearable check-strictly style="width: 180px" 
            :props="{ label: 'dept_name', value: 'dept_id', children: 'children' }" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" value="正常" />
            <el-option label="禁用" value="禁用" />
            <el-option label="锁定" value="锁定" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏和表格 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <div class="header-btns">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>新增用户
            </el-button>
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>导出
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="userList" v-loading="loading" stripe>
        <el-table-column prop="employee_code" label="工号" width="100" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="dept_name" label="部门" width="120" />
        <el-table-column prop="position" label="岗位" width="120" />
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-tag v-for="role in row.roles" :key="role.role_code" size="small" style="margin-right: 4px">
              {{ role.role_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="mobile" label="手机" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleAssignRole(row)">分配角色</el-button>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
              <el-button link type="primary" size="small">更多<el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="resetPwd">重置密码</el-dropdown-item>
                  <el-dropdown-item command="disable" v-if="row.status === '正常'">禁用</el-dropdown-item>
                  <el-dropdown-item command="enable" v-else>启用</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination 
        v-model:current-page="queryParams.page" 
        v-model:page-size="queryParams.page_size" 
        :total="total" 
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper" 
        @change="loadUsers"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="formData.username" placeholder="登录用户名" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工号" prop="employee_code">
              <el-input v-model="formData.employee_code" placeholder="员工工号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="real_name">
              <el-input v-model="formData.real_name" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" prop="dept_id">
              <el-tree-select v-model="formData.dept_id" :data="deptTree" placeholder="选择部门" clearable check-strictly style="width: 100%" 
                :props="{ label: 'dept_name', value: 'dept_id', children: 'children' }" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="岗位">
              <el-input v-model="formData.position" placeholder="岗位名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机" prop="mobile">
              <el-input v-model="formData.mobile" placeholder="手机号码" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="角色" v-if="!isEdit">
          <el-select v-model="formData.role_ids" multiple placeholder="选择角色" style="width: 100%">
            <el-option v-for="role in roleList" :key="role.role_id" :label="role.role_name" :value="role.role_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog v-model="roleDialogVisible" title="分配角色" width="500px">
      <div style="margin-bottom: 10px">
        <span style="color: #666">用户：</span>
        <span style="font-weight: bold">{{ currentUser?.real_name }}</span>
      </div>
      <el-checkbox-group v-model="selectedRoles">
        <el-checkbox v-for="role in roleList" :key="role.role_id" :label="role.role_id" :disabled="role.role_code === 'admin' && currentUser?.user_id !== 1">
          <span>{{ role.role_name }}</span>
          <span style="color: #999; margin-left: 8px; font-size: 12px">{{ role.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRoles">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Download, ArrowDown } from '@element-plus/icons-vue'
import request from '@/utils/request'

// 数据状态
const loading = ref(false)
const submitLoading = ref(false)
const userList = ref([])
const total = ref(0)
const deptTree = ref([])
const roleList = ref([])

const queryParams = reactive({
  keyword: '',
  dept_id: null,
  status: '',
  page: 1,
  page_size: 20
})

// 对话框状态
const dialogVisible = ref(false)
const isEdit = ref(false)
const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')
const formRef = ref(null)
const formData = reactive({
  username: '',
  real_name: '',
  employee_code: '',
  dept_id: null,
  position: '',
  mobile: '',
  email: '',
  role_ids: []
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

// 角色分配对话框
const roleDialogVisible = ref(false)
const currentUser = ref(null)
const selectedRoles = ref([])

// 工具函数
const getStatusType = (status) => {
  const map = { '正常': 'success', '禁用': 'danger', '锁定': 'warning' }
  return map[status] || 'info'
}

// 加载数据
const loadUsers = async () => {
  loading.value = true
  try {
    const res = await request.get('/api/v1/system/users', { params: queryParams })
    userList.value = res.data.list
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const loadDepts = async () => {
  const res = await request.get('/api/v1/system/depts')
  deptTree.value = res.data
}

const loadRoles = async () => {
  const res = await request.get('/api/v1/system/roles', { params: { page_size: 100 } })
  roleList.value = res.data.list
}

// 搜索
const handleSearch = () => {
  queryParams.page = 1
  loadUsers()
}

const handleReset = () => {
  Object.assign(queryParams, { keyword: '', dept_id: null, status: '', page: 1 })
  loadUsers()
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, { username: '', real_name: '', employee_code: '', dept_id: null, position: '', mobile: '', email: '', role_ids: [] })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, { ...row, role_ids: row.roles?.map(r => r.role_id) || [] })
  dialogVisible.value = true
}

// 提交
const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/v1/system/users/${formData.user_id}`, formData)
      ElMessage.success('更新成功')
    } else {
      const res = await request.post('/api/v1/system/users', formData)
      ElMessage.success(`创建成功，初始密码: ${res.data.password}`)
    }
    dialogVisible.value = false
    loadUsers()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 分配角色
const handleAssignRole = (row) => {
  currentUser.value = row
  selectedRoles.value = row.roles?.map(r => r.role_id) || []
  roleDialogVisible.value = true
}

const handleSaveRoles = async () => {
  try {
    await request.put(`/api/v1/system/users/${currentUser.value.user_id}/roles`, { role_ids: selectedRoles.value })
    ElMessage.success('角色分配成功')
    roleDialogVisible.value = false
    loadUsers()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

// 更多操作
const handleCommand = async (cmd, row) => {
  switch (cmd) {
    case 'resetPwd':
      ElMessageBox.confirm(`确定要重置 ${row.real_name} 的密码吗？`, '提示', { type: 'warning' })
        .then(async () => {
          const res = await request.post('/api/v1/auth/reset-password', { user_id: row.user_id })
          ElMessage.success(`密码已重置为: ${res.data.new_password}`)
        }).catch(() => {})
      break
    case 'disable':
    case 'enable':
      const status = cmd === 'disable' ? '禁用' : '正常'
      await request.put(`/api/v1/system/users/${row.user_id}/status?status=${status}`)
      ElMessage.success(`用户已${cmd === 'disable' ? '禁用' : '启用'}`)
      loadUsers()
      break
    case 'delete':
      ElMessageBox.confirm(`确定要删除用户 ${row.real_name} 吗？`, '警告', { type: 'warning' })
        .then(async () => {
          await request.delete(`/api/v1/system/users/${row.user_id}`)
          ElMessage.success('删除成功')
          loadUsers()
        }).catch(() => {})
      break
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

onMounted(() => {
  loadUsers()
  loadDepts()
  loadRoles()
})
</script>

<style scoped>
.user-manage {
  padding: 20px;
}

.search-card {
  margin-bottom: 16px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-btns {
  display: flex;
  gap: 10px;
}

:deep(.el-checkbox) {
  display: flex;
  margin-bottom: 12px;
}
</style>
