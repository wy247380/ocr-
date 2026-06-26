import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Upload', component: () => import('../views/Upload.vue') },
  { path: '/tasks', name: 'Tasks', component: () => import('../views/Tasks.vue') },
  { path: '/tasks/:taskId', name: 'TaskDetail', component: () => import('../views/TaskDetail.vue') },
  { path: '/admin/reviews', name: 'AdminReview', component: () => import('../views/AdminReview.vue') },
  { path: '/admin/reviews/:taskId', name: 'ReviewDetail', component: () => import('../views/ReviewDetail.vue') },
  { path: '/admin/audit-log', name: 'AuditLog', component: () => import('../views/AuditLog.vue') },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
