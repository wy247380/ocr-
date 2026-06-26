<template>
  <div class="task-detail" v-loading="loading">
    <el-page-header @back="$router.back()" title="返回" :content="`任务详情: ${taskId}`" />

    <template v-if="task">
      <el-card style="margin-top: 16px">
        <template #header><span>基本信息</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ task.task_id }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ task.filename }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(task.status)">{{ statusLabel(task.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ task.created_at }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="task.extraction" style="margin-top: 16px">
        <template #header><span>OCR 提取结果</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="专利号">{{ task.extraction.patent_no }}</el-descriptions-item>
          <el-descriptions-item label="公开号">{{ task.extraction.publication_no }}</el-descriptions-item>
          <el-descriptions-item label="专利名称">{{ task.extraction.patent_title }}</el-descriptions-item>
          <el-descriptions-item label="专利类型">{{ task.extraction.patent_type }}</el-descriptions-item>
          <el-descriptions-item label="发明人">{{ task.extraction.inventors }}</el-descriptions-item>
          <el-descriptions-item label="专利权人">{{ task.extraction.patentee }}</el-descriptions-item>
          <el-descriptions-item label="申请日">{{ task.extraction.application_date }}</el-descriptions-item>
          <el-descriptions-item label="授权公告日">{{ task.extraction.grant_announcement_date }}</el-descriptions-item>
          <el-descriptions-item label="OCR置信度">{{ task.extraction.avg_confidence }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="task.official_record" style="margin-top: 16px">
        <template #header><span>官方查询结果</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="专利号">{{ task.official_record.patent_no }}</el-descriptions-item>
          <el-descriptions-item label="公开号">{{ task.official_record.publication_no }}</el-descriptions-item>
          <el-descriptions-item label="专利名称">{{ task.official_record.patent_title }}</el-descriptions-item>
          <el-descriptions-item label="专利类型">{{ task.official_record.patent_type }}</el-descriptions-item>
          <el-descriptions-item label="发明人">{{ task.official_record.inventors }}</el-descriptions-item>
          <el-descriptions-item label="专利权人">{{ task.official_record.patentee }}</el-descriptions-item>
          <el-descriptions-item label="申请日">{{ task.official_record.application_date }}</el-descriptions-item>
          <el-descriptions-item label="授权公告日">{{ task.official_record.grant_announcement_date }}</el-descriptions-item>
          <el-descriptions-item label="法律状态">{{ task.official_record.legal_status }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ task.official_record.source }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card v-if="task.verification_result" style="margin-top: 16px">
        <template #header><span>比对结果</span></template>
        <el-alert
          :title="task.verification_result.auto_pass ? '自动通过' : (task.verification_result.fail_reason || '需人工审核')"
          :type="task.verification_result.auto_pass ? 'success' : 'warning'"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        />
        <FieldCompare v-if="task.verification_result.comparison_detail" :details="task.verification_result.comparison_detail.field_details || []" />
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTaskStatus } from '../api/index.js'
import FieldCompare from '../components/FieldCompare.vue'

const route = useRoute()
const taskId = route.params.taskId
const task = ref(null)
const loading = ref(true)

async function fetchTask() {
  loading.value = true
  try {
    const { data } = await getTaskStatus(taskId)
    task.value = data
  } finally {
    loading.value = false
  }
}

function statusType(s) {
  if (s === 'auto_approved' || s === 'approved_manual') return 'success'
  if (s === 'pending_manual_review') return 'warning'
  if (s === 'rejected_manual') return 'danger'
  return 'info'
}

function statusLabel(s) {
  const map = { uploaded: '已上传', processing: '处理中', auto_approved: '自动通过', pending_manual_review: '待人工审核', approved_manual: '人工通过', rejected_manual: '人工驳回' }
  return map[s] || s
}

onMounted(fetchTask)
</script>
