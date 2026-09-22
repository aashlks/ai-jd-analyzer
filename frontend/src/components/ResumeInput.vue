<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { api } from '../api.js'

defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue'])
const extracting = ref(false)

function chooseFile(file) {
  const suffix = file.name.toLowerCase().split('.').pop()
  if (!['pdf', 'docx'].includes(suffix)) { message.error('目前只支持 PDF 和 DOCX 简历。'); return false }
  if (file.size > 5 * 1024 * 1024) { message.error('简历文件不能超过 5 MB。'); return false }
  extract(file)
  return false // 阻止 Upload 自动提交，由下面的 API 请求完成本地提取。
}

async function extract(file) {
  extracting.value = true
  const form = new FormData()
  form.append('file', file)
  try {
    const result = await api('/resume/extract', { method: 'POST', body: form })
    emit('update:modelValue', result.text)
    message.success('已提取简历文字。请先检查遮盖结果，再决定是否发送给模型。')
  } catch (error) { message.error(error.message) }
  finally { extracting.value = false }
}
</script>

<template>
  <div class="resume-input">
    <div class="resume-top"><div><span class="eyebrow">RESUME REVIEW</span><h3>先检查简历文字</h3></div><a-upload accept=".pdf,.docx" :show-upload-list="false" :before-upload="chooseFile"><a-button :loading="extracting">上传 PDF / DOCX</a-button></a-upload></div>
    <a-alert type="info" show-icon message="上传文件只会由本站服务端提取文字，不会立即调用 DeepSeek。邮箱、常见手机号和证件号码会尝试遮盖；姓名和地址仍需你检查。扫描版 PDF 暂不支持。" />
    <a-textarea :value="modelValue" :rows="11" :maxlength="16000" show-count placeholder="也可以直接粘贴简历文字。请删去不愿交给第三方模型处理的信息。" @update:value="value => emit('update:modelValue', value)" />
  </div>
</template>
