<template>
  <div class="admin-review">
    <el-card>
      <template #header><span>待人工审核列表</span></template>

      <el-table :data="reviews" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="task_id" label="任务ID" min-width="200" />
        <el-table-column prop="fail_reason" label="原因" min-width="200" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.task_id"
              type="primary" link size="small"
              @click="$router.push(`/admin/reviews/${row.task_id}?resultId=${row.id}`)"
            >审核</el-button>
            <span v-else class="text-gray">无任务</span>
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
import { listPendingReviews } from '../api/index.js'

const reviews = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20

async function fetchReviews() {
  const { data } = await listPendingReviews({ limit: pageSize, offset: (currentPage.value - 1) * pageSize })
  reviews.value = data.reviews
  total.value = data.total
}

function handlePageChange(page) {
  currentPage.value = page
  fetchReviews()
}

onMounted(fetchReviews)
</script>
