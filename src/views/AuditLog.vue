<template>
  <div class="audit-log">
    <el-card>
      <template #header><span>审计日志</span></template>

      <el-table :data="logs" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="upload_id" label="上传ID" width="80" />
        <el-table-column prop="action" label="操作" width="140" />
        <el-table-column prop="detail" label="详情" min-width="300" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="created_at" label="时间" width="180" />
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
import { listAuditLogs } from '../api/index.js'

const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 50

async function fetchLogs() {
  const { data } = await listAuditLogs({ limit: pageSize, offset: (currentPage.value - 1) * pageSize })
  logs.value = data.logs
  total.value = data.total
}

function handlePageChange(page) {
  currentPage.value = page
  fetchLogs()
}

onMounted(fetchLogs)
</script>
