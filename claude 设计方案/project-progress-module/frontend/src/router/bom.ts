/**
 * BOM管理模块 - 路由配置
 */
import type { RouteRecordRaw } from 'vue-router'

const bomRoutes: RouteRecordRaw[] = [
  {
    path: '/bom',
    name: 'BomManagement',
    component: () => import('@/layout/index.vue'),
    redirect: '/bom/list',
    meta: {
      title: 'BOM管理',
      icon: 'Document'
    },
    children: [
      {
        path: 'list',
        name: 'BomList',
        component: () => import('@/views/bom/BomList.vue'),
        meta: {
          title: 'BOM列表',
          icon: 'List'
        }
      },
      {
        path: 'detail/:id',
        name: 'BomDetail',
        component: () => import('@/views/bom/BomDetail.vue'),
        meta: {
          title: 'BOM详情',
          hidden: true
        }
      },
      {
        path: 'materials',
        name: 'MaterialList',
        component: () => import('@/views/bom/MaterialList.vue'),
        meta: {
          title: '物料主数据',
          icon: 'Goods'
        }
      },
      {
        path: 'shortage',
        name: 'ShortageList',
        component: () => import('@/views/bom/ShortageList.vue'),
        meta: {
          title: '缺料预警',
          icon: 'Warning'
        }
      }
    ]
  }
]

export default bomRoutes
