<template>
  <div class="tasks-page">
    <el-card>
      <template #header>
        <div class="tasks-header">
          <span>任务列表</span>
          <el-select v-model="filterStatus" placeholder="全部状态" clearable size="small" style="width: 160px" @change="fetchTasks">
            <el-option label="全部" value="" />
            <el-option label="自动通过" value="auto_approved" />
            <el-option label="待人工审核" value="pending_manual_review" />
            <el-option label="人工通过" value="approved_manual" />
            <el-option label="人工驳回" value="rejected_manual" />
          </el-select>
        </div>
      </template>

      <el-table :data="tasks" stripe style="width: 100%">
        <el-table-column prop="task_id" label="任务ID" width="160" />
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="status" label="状态" width="140">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/tasks/${row.task_id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top: 16px; justify-content: center"
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listTasks } from '../api/index.js'

const tasks = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const filterStatus = ref('')

async function fetchTasks() {
  const params = { limit: pageSize, offset: (currentPage.value - 1) * pageSize }
  if (filterStatus.value) params.status = filterStatus.value
  const { data } = await listTasks(params)
  tasks.value = data.tasks
  total.value = data.total
}

function handlePageChange(page) {
  currentPage.value = page
  fetchTasks()
}

function statusType(s) {
  if (s === 'auto_approved') return 'success'
  if (s === 'pending_manual_review') return 'warning'
  if (s === 'rejected_manual') return 'danger'
  if (s === 'approved_manual') return 'success'
  return 'info'
}

function statusLabel(s) {
  const map = { uploaded: '已上传', processing: '处理中', auto_approved: '自动通过', pending_manual_review: '待人工审核', approved_manual: '人工通过', rejected_manual: '人工驳回' }
  return map[s] || s
}

onMounted(fetchTasks)
</script>

<style scoped>
.tasks-header { display: flex; justify-content: space-between; align-items: center; }
</style>
