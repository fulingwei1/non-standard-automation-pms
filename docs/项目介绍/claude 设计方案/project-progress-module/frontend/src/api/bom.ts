/**
 * BOM管理模块 - API接口
 */
import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface Material {
  material_id: number
  material_code: string
  material_name: string
  specification?: string
  brand?: string
  category: string
  sub_category?: string
  unit: string
  reference_price?: number
  default_supplier_id?: number
  default_supplier_name?: string
  lead_time: number
  min_order_qty: number
  is_standard: number
  status: string
  remark?: string
  created_by: number
  created_time: string
  updated_time?: string
  category_name?: string
}

export interface BomItem {
  item_id: number
  bom_id: number
  project_id: number
  line_no: number
  material_id?: number
  material_code: string
  material_name: string
  specification?: string
  brand?: string
  category: string
  category_name?: string
  unit: string
  quantity: number
  unit_price?: number
  amount?: number
  supplier_id?: number
  supplier_name?: string
  lead_time?: number
  is_long_lead: number
  is_key_part: number
  required_date?: string
  ordered_qty: number
  received_qty: number
  stock_qty: number
  shortage_qty: number
  procurement_status: string
  drawing_no?: string
  position_no?: string
  remark?: string
  version: string
  created_time: string
  updated_time?: string
}

export interface BomHeader {
  bom_id: number
  project_id: number
  project_code: string
  machine_no: string
  machine_name?: string
  bom_type: string
  current_version: string
  status: string
  total_items: number
  total_cost: number
  kit_rate: number
  designer_id: number
  designer_name: string
  reviewer_id?: number
  reviewer_name?: string
  review_time?: string
  publish_time?: string
  remark?: string
  created_by: number
  created_time: string
  updated_time?: string
  items?: BomItem[]
}

export interface BomVersion {
  version_id: number
  bom_id: number
  version: string
  version_type: string
  ecn_id?: number
  ecn_code?: string
  change_summary?: string
  total_items: number
  total_cost: number
  published_by: number
  published_name: string
  published_time: string
  remark?: string
}

export interface BomStatistics {
  total_bom: number
  draft_count: number
  reviewing_count: number
  published_count: number
  frozen_count: number
}

export interface CategoryStatistics {
  category: string
  category_name: string
  count: number
  amount: number
}

export interface ShortageItem {
  item_id: number
  bom_id: number
  machine_no: string
  material_code: string
  material_name: string
  specification?: string
  category: string
  quantity: number
  received_qty: number
  shortage_qty: number
  required_date?: string
  lead_time?: number
  supplier_name?: string
}

// ==================== 物料管理API ====================

export function createMaterial(data: Partial<Material>) {
  return request({
    url: '/bom/materials',
    method: 'post',
    data
  })
}

export function getMaterialList(params: {
  keyword?: string
  category?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request({
    url: '/bom/materials',
    method: 'get',
    params
  })
}

export function getMaterial(materialId: number) {
  return request({
    url: `/bom/materials/${materialId}`,
    method: 'get'
  })
}

export function updateMaterial(materialId: number, data: Partial<Material>) {
  return request({
    url: `/bom/materials/${materialId}`,
    method: 'put',
    data
  })
}

export function deleteMaterial(materialId: number) {
  return request({
    url: `/bom/materials/${materialId}`,
    method: 'delete'
  })
}

// ==================== BOM管理API ====================

export function createBom(data: Partial<BomHeader>) {
  return request({
    url: '/bom/headers',
    method: 'post',
    data
  })
}

export function getBomList(params: {
  project_id?: number
  machine_no?: string
  status?: string
  designer_id?: number
  page?: number
  page_size?: number
}) {
  return request({
    url: '/bom/headers',
    method: 'get',
    params
  })
}

export function getBomDetail(bomId: number) {
  return request({
    url: `/bom/headers/${bomId}`,
    method: 'get'
  })
}

export function updateBom(bomId: number, data: Partial<BomHeader>) {
  return request({
    url: `/bom/headers/${bomId}`,
    method: 'put',
    data
  })
}

export function deleteBom(bomId: number) {
  return request({
    url: `/bom/headers/${bomId}`,
    method: 'delete'
  })
}

// ==================== BOM明细API ====================

export function addBomItem(bomId: number, data: Partial<BomItem>) {
  return request({
    url: `/bom/headers/${bomId}/items`,
    method: 'post',
    data
  })
}

export function updateBomItem(itemId: number, data: Partial<BomItem>) {
  return request({
    url: `/bom/items/${itemId}`,
    method: 'put',
    data
  })
}

export function deleteBomItem(itemId: number) {
  return request({
    url: `/bom/items/${itemId}`,
    method: 'delete'
  })
}

export function batchDeleteItems(itemIds: number[]) {
  return request({
    url: '/bom/items/batch-delete',
    method: 'post',
    data: { item_ids: itemIds }
  })
}

export function batchUpdateProcurementStatus(data: {
  item_ids: number[]
  procurement_status: string
  ordered_qty?: number
  received_qty?: number
}) {
  return request({
    url: '/bom/items/batch-update-status',
    method: 'post',
    data
  })
}

// ==================== BOM版本API ====================

export function publishBom(bomId: number, data: {
  version_type: string
  change_summary?: string
}) {
  return request({
    url: `/bom/headers/${bomId}/publish`,
    method: 'post',
    data
  })
}

export function getBomVersions(bomId: number) {
  return request({
    url: `/bom/headers/${bomId}/versions`,
    method: 'get'
  })
}

export function getBomVersion(versionId: number) {
  return request({
    url: `/bom/versions/${versionId}`,
    method: 'get'
  })
}

export function compareVersions(versionId1: number, versionId2: number) {
  return request({
    url: '/bom/versions/compare',
    method: 'post',
    data: {
      version_id_1: versionId1,
      version_id_2: versionId2
    }
  })
}

// ==================== BOM统计API ====================

export function getBomStatistics(projectId?: number) {
  return request({
    url: '/bom/statistics',
    method: 'get',
    params: { project_id: projectId }
  })
}

export function getCategoryStatistics(bomId: number) {
  return request({
    url: `/bom/headers/${bomId}/category-statistics`,
    method: 'get'
  })
}

export function getKitRate(bomId: number) {
  return request({
    url: `/bom/headers/${bomId}/kit-rate`,
    method: 'get'
  })
}

export function getShortageList(params: {
  project_id?: number
  bom_id?: number
  page?: number
  page_size?: number
}) {
  return request({
    url: '/bom/shortage-list',
    method: 'get',
    params
  })
}

// ==================== BOM导入导出API ====================

export function importBomItems(bomId: number, file: File, updateMode: string = 'append') {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: `/bom/headers/${bomId}/import`,
    method: 'post',
    params: { update_mode: updateMode },
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function exportBom(bomId: number, fileType: string = 'excel', includePrice: boolean = false) {
  return request({
    url: `/bom/headers/${bomId}/export`,
    method: 'get',
    params: { file_type: fileType, include_price: includePrice }
  })
}

export function downloadImportTemplate() {
  return request({
    url: '/bom/export-template',
    method: 'get'
  })
}

// ==================== 常量定义 ====================

export const CATEGORY_OPTIONS = [
  { value: 'ME', label: '机械件' },
  { value: 'EL', label: '电气件' },
  { value: 'PN', label: '气动件' },
  { value: 'ST', label: '标准件' },
  { value: 'OT', label: '外协件' },
  { value: 'TR', label: '贸易件' }
]

export const BOM_STATUS_OPTIONS = [
  { value: '草稿', label: '草稿', type: 'info' },
  { value: '评审中', label: '评审中', type: 'warning' },
  { value: '已发布', label: '已发布', type: 'success' },
  { value: '已冻结', label: '已冻结', type: 'danger' }
]

export const PROCUREMENT_STATUS_OPTIONS = [
  { value: '待采购', label: '待采购', type: 'info' },
  { value: '询价中', label: '询价中', type: 'warning' },
  { value: '已下单', label: '已下单', type: 'primary' },
  { value: '部分到货', label: '部分到货', type: 'warning' },
  { value: '已到货', label: '已到货', type: 'success' },
  { value: '已入库', label: '已入库', type: 'success' }
]

export const BOM_TYPE_OPTIONS = [
  { value: '整机', label: '整机BOM' },
  { value: '模块', label: '模块BOM' },
  { value: '备件', label: '备件BOM' }
]
