<template>
  <div class="review-detail" v-loading="loading">
    <el-page-header @back="$router.back()" title="返回" content="人工审核" />

    <template v-if="task">
      <!-- 任务基本信息 -->
      <el-card style="margin-top: 16px">
        <template #header><span>基本信息</span></template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ task.task_id }}</el-descriptions-item>
          <el-descriptions-item label="文件名">{{ task.filename }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag type="warning">待人工审核</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="原因">{{ task.verification_result?.fail_reason || '-' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- OCR 提取结果 -->
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
        </el-descriptions>
      </el-card>

      <!-- 官方查询结果 -->
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
          <el-descriptions-item label="来源">{{ task.official_record.source }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 比对结果 -->
      <el-card v-if="task.verification_result?.comparison_detail" style="margin-top: 16px">
        <template #header><span>比对详情</span></template>
        <FieldCompare :details="task.verification_result.comparison_detail.field_details || []" />
      </el-card>

      <!-- 审核操作 -->
      <el-card style="margin-top: 16px">
        <template #header><span>审核操作</span></template>
        <el-form :model="form" label-width="80px">
          <el-form-item label="审核人">
            <el-input v-model="form.reviewer" placeholder="请输入审核人姓名" style="max-width: 300px" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="form.comment" type="textarea" :rows="3" placeholder="审核备注（可选）" style="max-width: 400px" />
          </el-form-item>
          <el-form-item>
            <el-button type="success" :loading="submitting" @click="handleApprove" size="large">
              ✓ 人工审批通过
            </el-button>
            <el-button type="danger" :loading="submitting" @click="handleReject" size="large">
              ✗ 人工驳回
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTaskStatus, approveReview, rejectReview } from '../api/index.js'
import FieldCompare from '../components/FieldCompare.vue'

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId
const resultId = parseInt(route.query.resultId) || 0
const task = ref(null)
const loading = ref(true)
const submitting = ref(false)
const form = ref({ reviewer: '', comment: '' })

async function fetchData() {
  loading.value = true
  try {
    const { data } = await getTaskStatus(taskId)
    task.value = data
  } catch {
    ElMessage.error('加载任务详情失败')
  } finally {
    loading.value = false
  }
}

async function handleApprove() {
  if (!form.value.reviewer) { ElMessage.warning('请输入审核人'); return }
  submitting.value = true
  try {
    await approveReview(resultId, form.value)
    ElMessage.success('审核通过')
    router.push('/admin/reviews')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleReject() {
  if (!form.value.reviewer) { ElMessage.warning('请输入审核人'); return }
  submitting.value = true
  try {
    await rejectReview(resultId, form.value)
    ElMessage.success('已驳回')
    router.push('/admin/reviews')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.review-detail {
  padding: 16px;
}
</style>