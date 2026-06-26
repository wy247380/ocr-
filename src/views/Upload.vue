<template>
  <div class="upload-page">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">上传专利证书核验</span>
          <el-switch v-model="batchMode" active-text="批量" inactive-text="单个" style="margin-left: auto" />
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :multiple="batchMode"
        :limit="batchMode ? 50 : 1"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :on-exceed="handleExceed"
        :file-list="fileList"
        accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
      >
        <el-icon class="el-icon--upload" :size="48"><Upload /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击选择</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            {{ batchMode ? '支持批量上传，最多 50 个文件' : '单个专利证书文件' }}，格式: PDF / PNG / JPG / TIFF
          </div>
        </template>
      </el-upload>

      <el-button
        type="primary"
        size="large"
        :loading="uploading"
        :disabled="selectedFiles.length === 0"
        style="margin-top: 20px; width: 100%"
        @click="submitUpload"
      >
        {{ uploading ? '核验中...' : `开始核验 (${selectedFiles.length} 个文件)` }}
      </el-button>
    </el-card>

    <!-- 单个结果 -->
    <el-card v-if="!batchMode && singleResult" class="result-card" style="margin-top: 20px">
      <template #header><span>核验结果</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="文件名">{{ singleResult.filename }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(singleResult.status)">{{ statusLabel(singleResult.status) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <div v-if="singleResult.verification_result && !singleResult.verification_result.auto_pass" class="mismatch-section">
        <p class="mismatch-title">不合格字段:</p>
        <MismatchList :details="singleResult.verification_result.comparison_detail" />
      </div>
      <el-button type="primary" link style="margin-top: 12px" @click="$router.push(`/tasks/${singleResult.task_id}`)">
        查看完整详情
      </el-button>
    </el-card>

    <!-- 批量结果 -->
    <el-card v-if="batchMode && batchResult" class="result-card" style="margin-top: 20px">
      <template #header>
        <div class="batch-header">
          <span>批量核验结果</span>
          <div class="batch-stats">
            <el-tag type="success" size="small">通过 {{ batchResult.passed }}</el-tag>
            <el-tag type="warning" size="small">待审 {{ batchResult.pending_review }}</el-tag>
            <el-tag type="danger" size="small">不合格 {{ batchResult.failed }}</el-tag>
          </div>
        </div>
      </template>

      <el-table :data="batchResult.items" stripe style="width: 100%" size="small">
        <el-table-column prop="filename" label="文件名" min-width="180" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="不合格字段" min-width="260">
          <template #default="{ row }">
            <template v-if="row.mismatch_fields && row.mismatch_fields.length > 0">
              <el-tag
                v-for="(f, idx) in row.mismatch_fields"
                :key="idx"
                type="danger"
                size="small"
                effect="plain"
                style="margin: 2px 4px 2px 0"
              >
                {{ f.field }}
              </el-tag>
            </template>
            <span v-else-if="row.status === 'auto_approved'" style="color: #67c23a">全部合格</span>
            <span v-else-if="row.fail_reason" style="color: #909399; font-size: 12px">{{ row.fail_reason }}</span>
            <span v-else style="color: #909399">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/tasks/${row.task_id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 展开的不合格详情 -->
      <div v-for="item in batchMismatchItems" :key="item.task_id" class="batch-mismatch-detail">
        <p class="mismatch-file-name">{{ item.filename }}</p>
        <div class="mismatch-field-list">
          <div v-for="(f, idx) in item.mismatch_fields" :key="idx" class="mismatch-field-item">
            <span class="field-label">{{ f.field }}:</span>
            <span class="field-ocr">证书值「{{ f.ocr_value }}」</span>
            <span class="field-vs">vs</span>
            <span class="field-official">官方值「{{ f.official_value }}」</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadPatentFile, uploadPatentFilesBatch, getTaskStatus, getBatchStatus } from '../api/index.js'
import MismatchList from '../components/MismatchList.vue'

const uploadRef = ref(null)
const batchMode = ref(false)
const selectedFiles = ref([])
const fileList = ref([])
const uploading = ref(false)
const singleResult = ref(null)
const batchResult = ref(null)

const batchMismatchItems = computed(() => {
  if (!batchResult.value) return []
  return batchResult.value.items.filter(i => i.mismatch_fields && i.mismatch_fields.length > 0)
})

function handleFileChange(file, list) {
  selectedFiles.value = list.map(f => f.raw)
  fileList.value = list
}

function handleFileRemove(file, list) {
  selectedFiles.value = list.map(f => f.raw)
  fileList.value = list
}

function handleExceed() {
  ElMessage.warning(batchMode.value ? '最多上传 50 个文件' : '单次只能上传 1 个文件')
}

async function submitUpload() {
  if (selectedFiles.value.length === 0) return
  uploading.value = true
  singleResult.value = null
  batchResult.value = null

  try {
    if (!batchMode.value || selectedFiles.value.length === 1) {
      const { data } = await uploadPatentFile(selectedFiles.value[0])
      await pollSingleTask(data.task_id)
    } else {
      const { data } = await uploadPatentFilesBatch(selectedFiles.value)
      await pollBatchStatus(data.batch_id)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function pollSingleTask(taskId) {
  for (let i = 0; i < 90; i++) {
    await new Promise(r => setTimeout(r, 2000))
    try {
      const { data } = await getTaskStatus(taskId)
      if (data.status !== 'processing' && data.status !== 'uploaded') {
        singleResult.value = data
        return
      }
    } catch { /* continue */ }
  }
  ElMessage.warning('核验超时，请到任务列表查看')
}

async function pollBatchStatus(batchId) {
  for (let i = 0; i < 120; i++) {
    await new Promise(r => setTimeout(r, 3000))
    try {
      const { data } = await getBatchStatus(batchId)
      const pending = data.items.filter(it => it.status === 'processing' || it.status === 'uploaded')
      if (pending.length === 0) {
        batchResult.value = data
        return
      }
      batchResult.value = data
    } catch { /* continue */ }
  }
  ElMessage.warning('部分文件仍在处理中，请到任务列表查看')
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
</script>

<style scoped>
.upload-page { max-width: 800px; margin: 30px auto; }
.upload-card { border-radius: 20px; overflow: hidden; }
.card-header { display: flex; align-items: center; }
.card-title { font-size: 17px; font-weight: 600; color: #4a5568; }
.result-card { border-radius: 20px; }
.batch-header { display: flex; align-items: center; justify-content: space-between; }
.batch-stats { display: flex; gap: 8px; }
.mismatch-section { margin-top: 16px; padding: 12px; background: #fff5f5; border-radius: 12px; }
.mismatch-title { font-size: 14px; font-weight: 600; color: #e53e3e; margin: 0 0 8px 0; }
.batch-mismatch-detail { margin-top: 16px; padding: 12px 16px; background: #fff9f0; border-radius: 12px; border-left: 3px solid #e67e22; }
.mismatch-file-name { font-weight: 600; color: #4a5568; margin: 0 0 8px 0; font-size: 13px; }
.mismatch-field-list { display: flex; flex-direction: column; gap: 6px; }
.mismatch-field-item { font-size: 12px; color: #555; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.field-label { font-weight: 600; color: #e53e3e; min-width: 70px; }
.field-ocr { color: #c0392b; }
.field-vs { color: #aaa; font-size: 11px; }
.field-official { color: #27ae60; }
:deep(.el-upload-dragger) {
  border-radius: 16px;
  border: 2px dashed #c3d0f5;
  background: linear-gradient(180deg, #f8faff 0%, #fff 100%);
  transition: all 0.3s;
}
:deep(.el-upload-dragger:hover) {
  border-color: #667eea;
  background: linear-gradient(180deg, #f0f4ff 0%, #fff 100%);
}
</style>
