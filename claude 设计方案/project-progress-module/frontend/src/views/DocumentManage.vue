<template>
  <div class="document-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-left">
        <h1>文档管理</h1>
        <p class="subtitle">项目文档与图纸版本管理</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="showUploadModal = true">
          <span>📤</span> 上传文档
        </button>
      </div>
    </header>

    <div class="main-content">
      <!-- 左侧文件夹树 -->
      <aside class="folder-sidebar">
        <div class="sidebar-header">
          <h3>文件夹</h3>
        </div>
        <div class="folder-tree">
          <div class="folder-item" :class="{ active: currentFolder === 'all' }" @click="selectFolder('all')">
            <span class="folder-icon">📂</span>
            <span class="folder-name">全部文档</span>
            <span class="folder-count">{{ stats.total }}</span>
          </div>
          <div class="folder-item" :class="{ active: currentFolder === 'recent' }" @click="selectFolder('recent')">
            <span class="folder-icon">🕐</span>
            <span class="folder-name">最近文档</span>
          </div>
          <div class="folder-item" :class="{ active: currentFolder === 'shared' }" @click="selectFolder('shared')">
            <span class="folder-icon">👥</span>
            <span class="folder-name">共享给我</span>
          </div>
          
          <div class="folder-divider"></div>
          <div class="folder-section-title">项目文档</div>
          
          <div class="folder-group" v-for="project in projects" :key="project.id">
            <div class="folder-item project" @click="toggleProject(project)">
              <span class="expand-icon">{{ project.expanded ? '▼' : '▶' }}</span>
              <span class="folder-icon">📁</span>
              <span class="folder-name">{{ project.name }}</span>
            </div>
            <div class="sub-folders" v-if="project.expanded">
              <div class="folder-item sub" 
                   v-for="folder in project.folders" 
                   :key="folder.id"
                   :class="{ active: currentFolder === `${project.id}-${folder.id}` }"
                   @click.stop="selectFolder(`${project.id}-${folder.id}`)">
                <span class="folder-icon">📁</span>
                <span class="folder-name">{{ folder.name }}</span>
                <span class="folder-count">{{ folder.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧文档列表 -->
      <main class="document-main">
        <!-- 工具栏 -->
        <div class="toolbar">
          <div class="search-box">
            <input type="text" v-model="searchKeyword" placeholder="搜索文档..." @keyup.enter="searchDocuments" />
            <span class="search-icon">🔍</span>
          </div>
          <div class="toolbar-filters">
            <select v-model="typeFilter">
              <option value="">全部类型</option>
              <option value="design">设计文档</option>
              <option value="drawing">图纸</option>
              <option value="bom">BOM清单</option>
              <option value="manual">操作手册</option>
              <option value="test_report">测试报告</option>
            </select>
            <select v-model="statusFilter">
              <option value="">全部状态</option>
              <option value="draft">草稿</option>
              <option value="reviewing">审核中</option>
              <option value="approved">已批准</option>
              <option value="released">已发布</option>
            </select>
          </div>
          <div class="toolbar-actions">
            <button class="view-btn" :class="{ active: viewMode === 'grid' }" @click="viewMode = 'grid'">▦</button>
            <button class="view-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">☰</button>
          </div>
        </div>

        <!-- 面包屑 -->
        <div class="breadcrumb">
          <span class="crumb" @click="selectFolder('all')">全部文档</span>
          <span class="separator" v-if="currentFolderPath.length">/</span>
          <span class="crumb" v-for="(crumb, idx) in currentFolderPath" :key="idx">
            {{ crumb }}
            <span class="separator" v-if="idx < currentFolderPath.length - 1">/</span>
          </span>
        </div>

        <!-- 文档统计 -->
        <div class="doc-stats">
          <div class="stat-item">
            <span class="stat-value">{{ filteredDocuments.length }}</span>
            <span class="stat-label">文档</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.totalSize }}</span>
            <span class="stat-label">总大小</span>
          </div>
        </div>

        <!-- 网格视图 -->
        <div class="doc-grid" v-if="viewMode === 'grid'">
          <div class="doc-card" v-for="doc in filteredDocuments" :key="doc.id" @click="viewDocument(doc)">
            <div class="doc-preview">
              <span class="file-icon">{{ getFileIcon(doc.file_type) }}</span>
              <span class="doc-version">{{ doc.current_version }}</span>
            </div>
            <div class="doc-info">
              <h4 class="doc-name" :title="doc.document_name">{{ doc.document_name }}</h4>
              <div class="doc-meta">
                <span class="doc-type">{{ doc.document_type_label }}</span>
                <span class="doc-status" :class="doc.status">{{ doc.status_label }}</span>
              </div>
              <div class="doc-footer">
                <span class="doc-size">{{ doc.file_size }}</span>
                <span class="doc-date">{{ doc.updated_at }}</span>
              </div>
            </div>
            <div class="doc-actions">
              <button class="action-btn" @click.stop="downloadDocument(doc)" title="下载">📥</button>
              <button class="action-btn" @click.stop="shareDocument(doc)" title="分享">🔗</button>
              <button class="action-btn" @click.stop="showMoreActions(doc)" title="更多">⋯</button>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div class="doc-table" v-if="viewMode === 'list'">
          <table>
            <thead>
              <tr>
                <th class="col-name">文档名称</th>
                <th class="col-type">类型</th>
                <th class="col-version">版本</th>
                <th class="col-status">状态</th>
                <th class="col-size">大小</th>
                <th class="col-author">作者</th>
                <th class="col-date">更新时间</th>
                <th class="col-actions">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in filteredDocuments" :key="doc.id" @click="viewDocument(doc)">
                <td class="col-name">
                  <span class="file-icon small">{{ getFileIcon(doc.file_type) }}</span>
                  <span class="name-text">{{ doc.document_name }}</span>
                </td>
                <td class="col-type">{{ doc.document_type_label }}</td>
                <td class="col-version">{{ doc.current_version }}</td>
                <td class="col-status">
                  <span class="status-badge" :class="doc.status">{{ doc.status_label }}</span>
                </td>
                <td class="col-size">{{ doc.file_size }}</td>
                <td class="col-author">{{ doc.author_name }}</td>
                <td class="col-date">{{ doc.updated_at }}</td>
                <td class="col-actions">
                  <button class="action-btn" @click.stop="downloadDocument(doc)">📥</button>
                  <button class="action-btn" @click.stop="shareDocument(doc)">🔗</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>

    <!-- 文档详情弹窗 -->
    <div class="modal-overlay" v-if="showDocDetail" @click.self="showDocDetail = false">
      <div class="modal-content doc-detail-modal">
        <div class="modal-header">
          <div class="doc-title">
            <span class="file-icon large">{{ getFileIcon(currentDoc?.file_type) }}</span>
            <div class="title-info">
              <h3>{{ currentDoc?.document_name }}</h3>
              <span class="doc-no">{{ currentDoc?.document_no }}</span>
            </div>
          </div>
          <button class="close-btn" @click="showDocDetail = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="detail-tabs">
            <button :class="{ active: docTab === 'info' }" @click="docTab = 'info'">基本信息</button>
            <button :class="{ active: docTab === 'versions' }" @click="docTab = 'versions'">版本历史</button>
            <button :class="{ active: docTab === 'review' }" @click="docTab = 'review'">审核记录</button>
            <button :class="{ active: docTab === 'permissions' }" @click="docTab = 'permissions'">权限设置</button>
          </div>

          <!-- 基本信息 -->
          <div class="tab-content" v-if="docTab === 'info'">
            <div class="info-grid">
              <div class="info-item">
                <label>文档类型</label>
                <span>{{ currentDoc?.document_type_label }}</span>
              </div>
              <div class="info-item">
                <label>当前版本</label>
                <span class="version-tag">{{ currentDoc?.current_version }}</span>
              </div>
              <div class="info-item">
                <label>状态</label>
                <span class="status-badge" :class="currentDoc?.status">{{ currentDoc?.status_label }}</span>
              </div>
              <div class="info-item">
                <label>文件大小</label>
                <span>{{ currentDoc?.file_size }}</span>
              </div>
              <div class="info-item">
                <label>所属项目</label>
                <span>{{ currentDoc?.project_name }}</span>
              </div>
              <div class="info-item">
                <label>作者</label>
                <span>{{ currentDoc?.author_name }}</span>
              </div>
              <div class="info-item">
                <label>创建时间</label>
                <span>{{ currentDoc?.created_at }}</span>
              </div>
              <div class="info-item">
                <label>更新时间</label>
                <span>{{ currentDoc?.updated_at }}</span>
              </div>
            </div>
            
            <div class="description-section" v-if="currentDoc?.description">
              <label>文档描述</label>
              <p>{{ currentDoc?.description }}</p>
            </div>

            <div class="tags-section">
              <label>标签</label>
              <div class="tags">
                <span class="tag" v-for="tag in currentDoc?.tags" :key="tag">{{ tag }}</span>
              </div>
            </div>

            <div class="action-buttons">
              <button class="btn-primary" @click="downloadDocument(currentDoc)">
                <span>📥</span> 下载文档
              </button>
              <button class="btn-secondary" @click="showUploadVersion = true">
                <span>📤</span> 上传新版本
              </button>
              <button class="btn-secondary" @click="submitForReview">
                <span>✓</span> 提交审核
              </button>
            </div>
          </div>

          <!-- 版本历史 -->
          <div class="tab-content" v-if="docTab === 'versions'">
            <div class="version-timeline">
              <div class="version-item" v-for="(ver, idx) in versions" :key="ver.id" :class="{ current: ver.is_current }">
                <div class="version-marker">
                  <span class="marker-dot"></span>
                  <span class="marker-line" v-if="idx < versions.length - 1"></span>
                </div>
                <div class="version-content">
                  <div class="version-header">
                    <span class="version-no">{{ ver.version_no }}</span>
                    <span class="version-tag" v-if="ver.is_current">当前版本</span>
                    <span class="version-status" :class="ver.status">{{ ver.status === 'released' ? '已发布' : '已废弃' }}</span>
                  </div>
                  <div class="version-desc">{{ ver.change_description }}</div>
                  <div class="version-meta">
                    <span>{{ ver.author_name }}</span>
                    <span>{{ ver.created_at }}</span>
                    <span>{{ ver.file_size }}</span>
                  </div>
                  <div class="version-actions">
                    <button class="link-btn" @click="downloadVersion(ver)">下载</button>
                    <button class="link-btn" @click="previewVersion(ver)">预览</button>
                    <button class="link-btn" v-if="idx > 0" @click="compareVersions(ver, versions[idx-1])">对比</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 审核记录 -->
          <div class="tab-content" v-if="docTab === 'review'">
            <div class="review-current" v-if="currentReview">
              <h4>当前审核</h4>
              <div class="review-status-bar">
                <span class="review-status" :class="currentReview.status">
                  {{ currentReview.status === 'approved' ? '已通过' : currentReview.status === 'pending' ? '待审核' : '已驳回' }}
                </span>
                <span class="review-time">提交于 {{ currentReview.submitted_at }}</span>
              </div>
              <div class="reviewers-list">
                <div class="reviewer-item" v-for="r in currentReview.reviews" :key="r.id">
                  <span class="reviewer-avatar">{{ r.reviewer_name.charAt(0) }}</span>
                  <div class="reviewer-info">
                    <span class="reviewer-name">{{ r.reviewer_name }}</span>
                    <span class="reviewer-role">{{ r.reviewer_role }}</span>
                  </div>
                  <span class="review-result" :class="r.result">
                    {{ r.result === 'approved' ? '✓ 通过' : r.result === 'rejected' ? '✗ 驳回' : '⏳ 待审核' }}
                  </span>
                  <span class="review-time" v-if="r.review_time">{{ r.review_time }}</span>
                </div>
              </div>
            </div>
            
            <div class="review-history" v-if="reviewHistory.length">
              <h4>历史记录</h4>
              <div class="history-item" v-for="h in reviewHistory" :key="h.id">
                <span class="history-version">{{ h.version }}</span>
                <span class="history-status" :class="h.status">{{ h.status === 'approved' ? '通过' : '驳回' }}</span>
                <span class="history-date">{{ h.completed_at }}</span>
              </div>
            </div>
          </div>

          <!-- 权限设置 -->
          <div class="tab-content" v-if="docTab === 'permissions'">
            <div class="permission-owner">
              <label>所有者</label>
              <div class="owner-info">
                <span class="owner-avatar">{{ currentDoc?.author_name?.charAt(0) }}</span>
                <span class="owner-name">{{ currentDoc?.author_name }}</span>
              </div>
            </div>
            
            <div class="permission-list">
              <label>已授权</label>
              <div class="permission-item" v-for="p in permissions" :key="p.id">
                <span class="perm-avatar">{{ p.name.charAt(0) }}</span>
                <span class="perm-name">{{ p.name }}</span>
                <span class="perm-type">{{ p.type === 'user' ? '用户' : '部门' }}</span>
                <select class="perm-level" v-model="p.permission">
                  <option value="view">查看</option>
                  <option value="download">下载</option>
                  <option value="edit">编辑</option>
                </select>
                <button class="remove-btn" @click="removePermission(p)">×</button>
              </div>
            </div>
            
            <button class="btn-add-permission" @click="showAddPermission = true">
              <span>+</span> 添加权限
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传文档弹窗 -->
    <div class="modal-overlay" v-if="showUploadModal" @click.self="showUploadModal = false">
      <div class="modal-content upload-modal">
        <div class="modal-header">
          <h3>上传文档</h3>
          <button class="close-btn" @click="showUploadModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="upload-zone" 
               :class="{ dragging: isDragging }"
               @dragover.prevent="isDragging = true"
               @dragleave="isDragging = false"
               @drop.prevent="handleDrop">
            <input type="file" ref="fileInput" @change="handleFileSelect" multiple hidden />
            <div class="upload-placeholder" v-if="!uploadFiles.length" @click="$refs.fileInput.click()">
              <span class="upload-icon">📄</span>
              <p>拖拽文件到此处，或点击选择文件</p>
              <span class="upload-hint">支持 PDF, DOC, DWG, XLS 等格式</span>
            </div>
            <div class="upload-files" v-else>
              <div class="upload-file" v-for="(file, idx) in uploadFiles" :key="idx">
                <span class="file-icon">{{ getFileIcon(file.name.split('.').pop()) }}</span>
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
                <button class="remove-file" @click="removeUploadFile(idx)">×</button>
              </div>
              <button class="add-more" @click="$refs.fileInput.click()">+ 添加更多</button>
            </div>
          </div>

          <div class="upload-form" v-if="uploadFiles.length">
            <div class="form-row">
              <label>文档类型</label>
              <select v-model="uploadForm.type">
                <option value="design">设计文档</option>
                <option value="drawing">图纸</option>
                <option value="bom">BOM清单</option>
                <option value="manual">操作手册</option>
                <option value="test_report">测试报告</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="form-row">
              <label>所属项目</label>
              <select v-model="uploadForm.projectId">
                <option value="">请选择项目</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="form-row">
              <label>描述</label>
              <textarea v-model="uploadForm.description" placeholder="请输入文档描述..."></textarea>
            </div>
            <div class="form-row">
              <label>标签</label>
              <input type="text" v-model="uploadForm.tags" placeholder="输入标签，用逗号分隔" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showUploadModal = false">取消</button>
          <button class="btn-confirm" @click="handleUpload" :disabled="!uploadFiles.length || uploading">
            {{ uploading ? '上传中...' : '确认上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

// 状态
const currentFolder = ref('all')
const currentFolderPath = ref([])
const searchKeyword = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const viewMode = ref('grid')
const showDocDetail = ref(false)
const showUploadModal = ref(false)
const showUploadVersion = ref(false)
const showAddPermission = ref(false)
const currentDoc = ref(null)
const docTab = ref('info')
const isDragging = ref(false)
const uploading = ref(false)
const uploadFiles = ref([])
const fileInput = ref(null)

const uploadForm = reactive({
  type: 'design',
  projectId: '',
  description: '',
  tags: ''
})

// 统计
const stats = reactive({
  total: 245,
  totalSize: '2.5GB'
})

// 项目列表
const projects = ref([
  { 
    id: 1, 
    name: 'XX汽车传感器测试设备', 
    expanded: true,
    folders: [
      { id: 1, name: '设计文档', count: 5 },
      { id: 2, name: '图纸', count: 15 },
      { id: 3, name: 'BOM清单', count: 3 },
      { id: 4, name: '测试报告', count: 2 }
    ]
  },
  { 
    id: 2, 
    name: 'YY新能源电池检测线', 
    expanded: false,
    folders: [
      { id: 1, name: '设计文档', count: 8 },
      { id: 2, name: '图纸', count: 25 }
    ]
  }
])

// 文档列表
const documents = ref([
  {
    id: 1,
    document_no: 'DOC-2025-001',
    document_name: 'XX汽车传感器测试设备-总体设计方案',
    document_type: 'design',
    document_type_label: '设计文档',
    current_version: 'V1.2',
    status: 'released',
    status_label: '已发布',
    project_name: 'XX汽车传感器测试设备项目',
    file_type: 'pdf',
    file_size: '2.5MB',
    author_name: '张工',
    created_at: '2024-11-15',
    updated_at: '2024-12-18',
    description: '本文档描述了XX汽车传感器测试设备的总体设计方案',
    tags: ['设计', '方案', '测试设备']
  },
  {
    id: 2,
    document_no: 'DWG-2025-001',
    document_name: '机架装配图',
    document_type: 'drawing',
    document_type_label: '图纸',
    current_version: 'V1.0',
    status: 'approved',
    status_label: '已批准',
    project_name: 'XX汽车传感器测试设备项目',
    file_type: 'dwg',
    file_size: '8.5MB',
    author_name: '李工',
    created_at: '2024-11-25',
    updated_at: '2024-11-28',
    tags: ['图纸', '机械']
  },
  {
    id: 3,
    document_no: 'DWG-2025-002',
    document_name: '电气原理图',
    document_type: 'drawing',
    document_type_label: '图纸',
    current_version: 'V1.1',
    status: 'reviewing',
    status_label: '审核中',
    project_name: 'XX汽车传感器测试设备项目',
    file_type: 'dwg',
    file_size: '5.2MB',
    author_name: '王工',
    created_at: '2024-12-01',
    updated_at: '2024-12-20',
    tags: ['图纸', '电气']
  },
  {
    id: 4,
    document_no: 'BOM-2025-001',
    document_name: 'BOM物料清单',
    document_type: 'bom',
    document_type_label: 'BOM清单',
    current_version: 'V2.0',
    status: 'released',
    status_label: '已发布',
    project_name: 'XX汽车传感器测试设备项目',
    file_type: 'xlsx',
    file_size: '1.2MB',
    author_name: '赵工',
    created_at: '2024-11-20',
    updated_at: '2024-12-15',
    tags: ['BOM', '物料']
  }
])

// 版本历史
const versions = ref([
  { id: 3, version_no: 'V1.2', change_description: '优化了测试流程描述，补充了异常处理章节', file_size: '2.5MB', author_name: '张工', created_at: '2024-12-18 16:45', status: 'released', is_current: true },
  { id: 2, version_no: 'V1.1', change_description: '根据评审意见修改了技术指标部分', file_size: '2.3MB', author_name: '张工', created_at: '2024-12-01 14:20', status: 'obsolete', is_current: false },
  { id: 1, version_no: 'V1.0', change_description: '初始版本', file_size: '2.1MB', author_name: '张工', created_at: '2024-11-15 10:30', status: 'obsolete', is_current: false }
])

// 审核记录
const currentReview = ref({
  status: 'approved',
  submitted_at: '2024-12-16 09:00',
  reviews: [
    { id: 1, reviewer_name: '王主管', reviewer_role: '技术主管', result: 'approved', review_time: '2024-12-17 10:00' }
  ]
})

const reviewHistory = ref([
  { id: 1, version: 'V1.0', status: 'approved', completed_at: '2024-11-17 15:30' }
])

// 权限列表
const permissions = ref([
  { id: 1, type: 'user', name: '李工', permission: 'edit' },
  { id: 2, type: 'user', name: '王工', permission: 'view' },
  { id: 3, type: 'department', name: '技术部', permission: 'view' }
])

// 计算属性
const filteredDocuments = computed(() => {
  let result = documents.value
  if (typeFilter.value) {
    result = result.filter(d => d.document_type === typeFilter.value)
  }
  if (statusFilter.value) {
    result = result.filter(d => d.status === statusFilter.value)
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d => 
      d.document_name.toLowerCase().includes(keyword) ||
      d.document_no.toLowerCase().includes(keyword)
    )
  }
  return result
})

// 方法
const getFileIcon = (type) => {
  const icons = {
    pdf: '📕',
    doc: '📘',
    docx: '📘',
    xls: '📗',
    xlsx: '📗',
    dwg: '📐',
    ppt: '📙',
    pptx: '📙',
    txt: '📄',
    zip: '📦',
    rar: '📦'
  }
  return icons[type?.toLowerCase()] || '📄'
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
}

const selectFolder = (folderId) => {
  currentFolder.value = folderId
  if (folderId === 'all') {
    currentFolderPath.value = []
  }
}

const toggleProject = (project) => {
  project.expanded = !project.expanded
}

const viewDocument = (doc) => {
  currentDoc.value = doc
  docTab.value = 'info'
  showDocDetail.value = true
}

const downloadDocument = (doc) => {
  alert(`下载文档: ${doc.document_name}`)
}

const shareDocument = (doc) => {
  alert(`分享文档: ${doc.document_name}`)
}

const showMoreActions = (doc) => {
  alert(`更多操作: ${doc.document_name}`)
}

const downloadVersion = (ver) => {
  alert(`下载版本: ${ver.version_no}`)
}

const previewVersion = (ver) => {
  alert(`预览版本: ${ver.version_no}`)
}

const compareVersions = (ver1, ver2) => {
  alert(`对比版本: ${ver1.version_no} vs ${ver2.version_no}`)
}

const submitForReview = () => {
  alert('提交审核')
}

const removePermission = (p) => {
  const idx = permissions.value.findIndex(item => item.id === p.id)
  if (idx > -1) permissions.value.splice(idx, 1)
}

const searchDocuments = () => {
  // 搜索逻辑
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files)
  uploadFiles.value.push(...files)
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  uploadFiles.value.push(...files)
}

const removeUploadFile = (idx) => {
  uploadFiles.value.splice(idx, 1)
}

const handleUpload = async () => {
  uploading.value = true
  await new Promise(resolve => setTimeout(resolve, 2000))
  uploading.value = false
  showUploadModal.value = false
  uploadFiles.value = []
  alert('上传成功！')
}
</script>

<style scoped>
.document-page { min-height: 100vh; background: #0f172a; color: white; }
.page-header { display: flex; justify-content: space-between; align-items: center; padding: 24px 32px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { font-size: 14px; color: #94A3B8; margin-top: 4px; }
.header-actions { display: flex; gap: 12px; }
.btn-primary, .btn-secondary { padding: 10px 20px; border: none; border-radius: 10px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px; }
.btn-primary { background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white; }
.btn-secondary { background: rgba(255,255,255,0.1); color: white; }

.main-content { display: flex; height: calc(100vh - 90px); }

/* 左侧文件夹 */
.folder-sidebar { width: 280px; background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.1); padding: 20px 0; overflow-y: auto; }
.sidebar-header { padding: 0 20px 16px; }
.sidebar-header h3 { font-size: 14px; color: #94A3B8; font-weight: 500; }
.folder-tree { display: flex; flex-direction: column; }
.folder-item { display: flex; align-items: center; gap: 10px; padding: 10px 20px; cursor: pointer; transition: background 0.2s; }
.folder-item:hover { background: rgba(255,255,255,0.05); }
.folder-item.active { background: rgba(99,102,241,0.2); border-right: 3px solid #6366F1; }
.folder-item.project { font-weight: 500; }
.folder-item.sub { padding-left: 48px; }
.expand-icon { width: 16px; font-size: 10px; color: #64748B; }
.folder-icon { font-size: 16px; }
.folder-name { flex: 1; font-size: 14px; }
.folder-count { font-size: 12px; color: #64748B; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 10px; }
.folder-divider { height: 1px; background: rgba(255,255,255,0.1); margin: 12px 20px; }
.folder-section-title { padding: 8px 20px; font-size: 12px; color: #64748B; text-transform: uppercase; }

/* 右侧文档区 */
.document-main { flex: 1; padding: 20px 24px; overflow-y: auto; }
.toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.search-box { position: relative; flex: 1; max-width: 400px; }
.search-box input { width: 100%; padding: 10px 16px 10px 40px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: white; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); }
.toolbar-filters { display: flex; gap: 12px; }
.toolbar-filters select { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; }
.toolbar-actions { display: flex; gap: 4px; }
.view-btn { width: 36px; height: 36px; border: none; background: rgba(255,255,255,0.05); border-radius: 6px; color: #94A3B8; cursor: pointer; font-size: 16px; }
.view-btn.active { background: rgba(99,102,241,0.2); color: white; }

.breadcrumb { font-size: 14px; color: #64748B; margin-bottom: 16px; }
.crumb { cursor: pointer; }
.crumb:hover { color: white; }
.separator { margin: 0 8px; }

.doc-stats { display: flex; gap: 24px; margin-bottom: 20px; }
.stat-item { display: flex; align-items: baseline; gap: 6px; }
.stat-value { font-size: 20px; font-weight: 600; }
.stat-label { font-size: 13px; color: #64748B; }

/* 网格视图 */
.doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.doc-card { background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); overflow: hidden; cursor: pointer; transition: all 0.2s; }
.doc-card:hover { border-color: rgba(99,102,241,0.5); transform: translateY(-2px); }
.doc-preview { height: 100px; background: rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center; position: relative; }
.file-icon { font-size: 40px; }
.file-icon.small { font-size: 20px; }
.file-icon.large { font-size: 48px; }
.doc-version { position: absolute; top: 8px; right: 8px; padding: 4px 8px; background: rgba(99,102,241,0.8); border-radius: 4px; font-size: 11px; }
.doc-info { padding: 16px; }
.doc-name { font-size: 14px; font-weight: 500; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-meta { display: flex; gap: 8px; margin-bottom: 8px; }
.doc-type { font-size: 12px; color: #64748B; }
.doc-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; }
.doc-status.released, .status-badge.released { background: rgba(16,185,129,0.2); color: #10B981; }
.doc-status.approved, .status-badge.approved { background: rgba(99,102,241,0.2); color: #A5B4FC; }
.doc-status.reviewing, .status-badge.reviewing { background: rgba(245,158,11,0.2); color: #F59E0B; }
.doc-status.draft, .status-badge.draft { background: rgba(100,116,139,0.2); color: #94A3B8; }
.doc-footer { display: flex; justify-content: space-between; font-size: 12px; color: #64748B; }
.doc-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 0 16px 16px; }
.action-btn { width: 32px; height: 32px; border: none; background: rgba(255,255,255,0.05); border-radius: 6px; cursor: pointer; font-size: 14px; }
.action-btn:hover { background: rgba(255,255,255,0.1); }

/* 列表视图 */
.doc-table { background: rgba(255,255,255,0.02); border-radius: 12px; overflow: hidden; }
.doc-table table { width: 100%; border-collapse: collapse; }
.doc-table th, .doc-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.05); }
.doc-table th { background: rgba(0,0,0,0.2); font-size: 12px; color: #94A3B8; font-weight: 500; }
.doc-table tr:hover { background: rgba(255,255,255,0.02); cursor: pointer; }
.col-name { display: flex; align-items: center; gap: 10px; }
.name-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #1E293B; border-radius: 16px; overflow: hidden; max-height: 90vh; overflow-y: auto; }
.doc-detail-modal { width: 800px; }
.upload-modal { width: 600px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.modal-header h3 { font-size: 18px; }
.doc-title { display: flex; align-items: center; gap: 16px; }
.title-info h3 { font-size: 18px; margin-bottom: 4px; }
.doc-no { font-size: 13px; color: #64748B; }
.close-btn { width: 32px; height: 32px; border: none; background: rgba(255,255,255,0.1); border-radius: 8px; color: #94A3B8; font-size: 20px; cursor: pointer; }
.modal-body { padding: 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 20px 24px; border-top: 1px solid rgba(255,255,255,0.1); }
.btn-cancel { padding: 10px 24px; background: rgba(255,255,255,0.1); border: none; border-radius: 8px; color: #94A3B8; cursor: pointer; }
.btn-confirm { padding: 10px 24px; background: linear-gradient(135deg, #6366F1, #8B5CF6); border: none; border-radius: 8px; color: white; cursor: pointer; }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

/* Tabs */
.detail-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; }
.detail-tabs button { padding: 8px 16px; background: transparent; border: none; color: #94A3B8; cursor: pointer; border-radius: 6px; }
.detail-tabs button.active { background: rgba(99,102,241,0.2); color: white; }

/* Info grid */
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item label { font-size: 12px; color: #64748B; }
.info-item span { font-size: 14px; }
.version-tag { padding: 4px 10px; background: rgba(99,102,241,0.2); border-radius: 6px; color: #A5B4FC; display: inline-block; }
.description-section, .tags-section { margin-bottom: 20px; }
.description-section label, .tags-section label { display: block; font-size: 12px; color: #64748B; margin-bottom: 8px; }
.description-section p { font-size: 14px; line-height: 1.6; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; }
.tag { padding: 4px 12px; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 13px; }
.action-buttons { display: flex; gap: 12px; margin-top: 24px; }

/* Version timeline */
.version-timeline { position: relative; }
.version-item { display: flex; gap: 16px; margin-bottom: 24px; }
.version-marker { display: flex; flex-direction: column; align-items: center; width: 20px; }
.marker-dot { width: 12px; height: 12px; border-radius: 50%; background: #64748B; }
.version-item.current .marker-dot { background: #6366F1; }
.marker-line { flex: 1; width: 2px; background: rgba(255,255,255,0.1); margin-top: 4px; }
.version-content { flex: 1; background: rgba(255,255,255,0.02); border-radius: 12px; padding: 16px; }
.version-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.version-no { font-size: 16px; font-weight: 600; }
.version-tag { padding: 2px 8px; background: rgba(99,102,241,0.2); border-radius: 4px; font-size: 11px; color: #A5B4FC; }
.version-status { font-size: 12px; color: #64748B; }
.version-desc { font-size: 14px; margin-bottom: 8px; }
.version-meta { display: flex; gap: 16px; font-size: 12px; color: #64748B; margin-bottom: 12px; }
.version-actions { display: flex; gap: 12px; }
.link-btn { background: none; border: none; color: #6366F1; cursor: pointer; font-size: 13px; }
.link-btn:hover { text-decoration: underline; }

/* Review */
.review-current { margin-bottom: 24px; }
.review-current h4, .review-history h4 { font-size: 14px; color: #94A3B8; margin-bottom: 12px; }
.review-status-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.review-status { padding: 4px 12px; border-radius: 6px; font-size: 13px; }
.review-status.approved { background: rgba(16,185,129,0.2); color: #10B981; }
.review-status.pending { background: rgba(245,158,11,0.2); color: #F59E0B; }
.review-time { font-size: 13px; color: #64748B; }
.reviewers-list { display: flex; flex-direction: column; gap: 12px; }
.reviewer-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; }
.reviewer-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #8B5CF6); display: flex; align-items: center; justify-content: center; font-size: 14px; }
.reviewer-info { flex: 1; }
.reviewer-name { display: block; font-size: 14px; }
.reviewer-role { font-size: 12px; color: #64748B; }
.review-result { font-size: 13px; }
.review-result.approved { color: #10B981; }
.review-result.rejected { color: #EF4444; }
.history-item { display: flex; align-items: center; gap: 16px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
.history-version { font-weight: 500; }
.history-status { padding: 2px 8px; border-radius: 4px; }
.history-status.approved { background: rgba(16,185,129,0.2); color: #10B981; }
.history-date { color: #64748B; }

/* Permissions */
.permission-owner { margin-bottom: 20px; }
.permission-owner label, .permission-list label { display: block; font-size: 12px; color: #64748B; margin-bottom: 8px; }
.owner-info { display: flex; align-items: center; gap: 12px; }
.owner-avatar, .perm-avatar { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #8B5CF6); display: flex; align-items: center; justify-content: center; font-size: 13px; }
.permission-list { margin-bottom: 16px; }
.permission-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.perm-name { flex: 1; font-size: 14px; }
.perm-type { font-size: 12px; color: #64748B; }
.perm-level { padding: 4px 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; color: white; font-size: 13px; }
.remove-btn { width: 24px; height: 24px; border: none; background: rgba(239,68,68,0.2); border-radius: 4px; color: #EF4444; cursor: pointer; }
.btn-add-permission { padding: 10px 16px; background: rgba(255,255,255,0.05); border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px; color: #94A3B8; cursor: pointer; width: 100%; }

/* Upload */
.upload-zone { border: 2px dashed rgba(255,255,255,0.2); border-radius: 12px; padding: 40px 20px; text-align: center; transition: all 0.2s; margin-bottom: 20px; }
.upload-zone.dragging { border-color: #6366F1; background: rgba(99,102,241,0.1); }
.upload-placeholder { cursor: pointer; }
.upload-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.upload-placeholder p { font-size: 14px; margin-bottom: 8px; }
.upload-hint { font-size: 12px; color: #64748B; }
.upload-files { text-align: left; }
.upload-file { display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; margin-bottom: 8px; }
.upload-file .file-info { flex: 1; }
.upload-file .file-name { display: block; font-size: 14px; margin-bottom: 2px; }
.upload-file .file-size { font-size: 12px; color: #64748B; }
.remove-file { width: 24px; height: 24px; border: none; background: rgba(255,255,255,0.1); border-radius: 4px; color: #94A3B8; cursor: pointer; }
.add-more { padding: 8px 16px; background: rgba(255,255,255,0.05); border: 1px dashed rgba(255,255,255,0.2); border-radius: 6px; color: #94A3B8; cursor: pointer; font-size: 13px; }
.upload-form .form-row { margin-bottom: 16px; }
.upload-form label { display: block; font-size: 13px; color: #94A3B8; margin-bottom: 6px; }
.upload-form select, .upload-form input, .upload-form textarea { width: 100%; padding: 10px 14px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; font-size: 14px; }
.upload-form textarea { min-height: 80px; resize: vertical; }
</style>
