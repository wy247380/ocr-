<template>
  <div class="field-compare">
    <el-table :data="details" stripe size="small">
      <el-table-column prop="field_label" label="字段" width="120" />
      <el-table-column prop="ocr_value" label="OCR 值" min-width="180">
        <template #default="{ row }">{{ formatValue(row.ocr_value) }}</template>
      </el-table-column>
      <el-table-column prop="official_value" label="官方值" min-width="180">
        <template #default="{ row }">{{ formatValue(row.official_value) }}</template>
      </el-table-column>
      <el-table-column prop="similarity_score" label="相似度" width="90" align="center">
        <template #default="{ row }">{{ row.similarity_score != null ? row.similarity_score : '-' }}</template>
      </el-table-column>
      <el-table-column prop="matched" label="匹配" width="80" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.matched" color="#67c23a"><CircleCheck /></el-icon>
          <el-icon v-else color="#f56c6c"><CircleClose /></el-icon>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'

defineProps({ details: { type: Array, default: () => [] } })

function formatValue(val) {
  if (Array.isArray(val)) return val.join('、')
  return val ?? '-'
}
</script>
