<template>
  <div class="settings-page">
    <el-card class="settings-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="form" label-width="160px" label-position="right">
        <el-divider content-position="left">DeepSeek API 配置</el-divider>

        <el-form-item label="API Key">
          <el-input
            v-model="form.deepseek_api_key"
            :type="showKey ? 'text' : 'password'"
            placeholder="请输入 DeepSeek API Key"
            clearable
          >
            <template #suffix>
              <el-icon class="toggle-eye" @click="showKey = !showKey">
                <component :is="showKey ? 'View' : 'Hide'" />
              </el-icon>
            </template>
          </el-input>
          <div class="form-tip">用于 OCR 文本解析和官方页面内容解析</div>
        </el-form-item>

        <el-form-item label="API 地址">
          <el-input v-model="form.deepseek_api_url" placeholder="https://api.deepseek.com/chat/completions" />
        </el-form-item>

        <el-form-item label="快速模型 (OCR解析)">
          <el-input v-model="form.deepseek_model_chat" placeholder="deepseek-v4-flash" />
          <div class="form-tip">用于 OCR 文本提取，普通模式调用，速度快成本低</div>
        </el-form-item>

        <el-form-item label="推理模型 (比对/查询)">
          <el-input v-model="form.deepseek_model_reasoner" placeholder="deepseek-v4-flash" />
          <div class="form-tip">用于官方页面解析和字段比对，启用 thinking 深度推理</div>
        </el-form-item>

        <el-divider content-position="left">Vision 识别</el-divider>

        <el-form-item label="Vision 模型">
          <el-input v-model="form.deepseek_model_vision" placeholder="deepseek-vl2" />
          <div class="form-tip">DeepSeek 多模态模型，直接从图片识别（API 支持后启用）</div>
        </el-form-item>

        <el-divider content-position="left">OCR 引擎</el-divider>

        <el-form-item label="OCR 引擎">
          <el-select v-model="form.ocr_provider" placeholder="选择 OCR 引擎">
            <el-option label="EasyOCR（推荐，本地文字提取）" value="easyocr" />
            <el-option label="PaddleOCR（纯CPU备选）" value="paddle" />
            <el-option label="DeepSeek Vision（云端识图，需API支持）" value="vision_llm" />
          </el-select>
          <div class="form-tip">PDF 优先走文本层+DeepSeek解析，无需 OCR 库；扫描件/图片才走此引擎</div>
        </el-form-item>

        <el-divider content-position="left">功能开关</el-divider>

        <el-form-item label="OCR 智能解析">
          <el-switch v-model="form.use_llm_ocr_parse" active-text="开" inactive-text="关" />
          <div class="form-tip">开启后，OCR 提取不完整时自动调用 DeepSeek 补全</div>
        </el-form-item>

        <el-form-item label="智能比对">
          <el-switch v-model="form.use_llm_compare" active-text="开" inactive-text="关" />
          <div class="form-tip">开启后，字段比对使用 DeepSeek 辅助判断</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving" round>
            保存设置
          </el-button>
          <el-button @click="testConnection" :loading="testing" round>
            测试连接
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="testResult"
        :title="testResult.message"
        :type="testResult.status === 'ok' ? 'success' : 'error'"
        show-icon
        closable
        style="margin-top: 16px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Hide } from '@element-plus/icons-vue'
import api from '../api'

const form = ref({
  deepseek_api_key: '',
  deepseek_api_url: 'https://api.deepseek.com/chat/completions',
  deepseek_model_chat: 'deepseek-v4-flash',
  deepseek_model_reasoner: 'deepseek-v4-flash',
  deepseek_model_vision: 'deepseek-vl2',
  ocr_provider: 'easyocr',
  use_llm_ocr_parse: true,
  use_llm_compare: true,
})

const showKey = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

onMounted(async () => {
  try {
    const res = await api.get('/settings')
    form.value.deepseek_api_url = res.data.deepseek_api_url
    form.value.deepseek_model_chat = res.data.deepseek_model_chat
    form.value.deepseek_model_reasoner = res.data.deepseek_model_reasoner
    form.value.deepseek_model_vision = res.data.deepseek_model_vision || 'deepseek-vl2'
    form.value.ocr_provider = res.data.ocr_provider || 'easyocr'
    form.value.use_llm_ocr_parse = res.data.use_llm_ocr_parse
    form.value.use_llm_compare = res.data.use_llm_compare
    if (res.data.deepseek_api_key_set) {
      form.value.deepseek_api_key = res.data.deepseek_api_key_masked
    }
  } catch (e) {
    console.error('加载设置失败', e)
  }
})

async function saveSettings() {
  saving.value = true
  try {
    await api.post('/settings', form.value)
    ElMessage.success('设置已保存')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await api.post('/settings/test-deepseek')
    testResult.value = res.data
  } catch (e) {
    testResult.value = { status: 'error', message: e.response?.data?.detail || e.message }
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.settings-page {
  padding: 24px;
  max-width: 700px;
  margin: 0 auto;
}

.settings-card {
  border-radius: 16px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
  color: #7c3aed;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.toggle-eye {
  cursor: pointer;
}
</style>
