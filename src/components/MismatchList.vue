<template>
  <div class="mismatch-list" v-if="fields.length > 0">
    <div v-for="(f, idx) in fields" :key="idx" class="mismatch-item">
      <span class="item-field">{{ f.field }}</span>
      <div class="item-values">
        <span class="val-ocr">证书: {{ formatVal(f.ocr_value) }}</span>
        <span class="val-official">官方: {{ formatVal(f.official_value) }}</span>
      </div>
    </div>
  </div>
  <div v-else class="no-mismatch">所有字段均一致</div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ details: { type: Object, default: null } })

const fields = computed(() => {
  if (!props.details) return []
  const list = props.details.field_details || []
  return list
    .filter(d => !d.matched && d.ocr_value && d.official_value)
    .map(d => ({
      field: d.field_label || d.field_key,
      ocr_value: d.ocr_value,
      official_value: d.official_value,
    }))
})

function formatVal(v) {
  if (Array.isArray(v)) return v.join('、')
  return v ?? '—'
}
</script>

<style scoped>
.mismatch-list { display: flex; flex-direction: column; gap: 8px; }
.mismatch-item { display: flex; align-items: flex-start; gap: 10px; padding: 6px 0; border-bottom: 1px dashed #fde2e2; }
.item-field { font-weight: 600; color: #c0392b; min-width: 80px; font-size: 13px; }
.item-values { display: flex; flex-direction: column; gap: 2px; font-size: 12px; }
.val-ocr { color: #e74c3c; }
.val-official { color: #27ae60; }
.no-mismatch { color: #67c23a; font-size: 13px; }
</style>
