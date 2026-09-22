<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import PageIntro from '../components/PageIntro.vue'
import ResumeInput from '../components/ResumeInput.vue'
import { api, downloadText, post } from '../api.js'
import { selectedJobs, selectedKey, state } from '../store.js'

const router = useRouter()
const mode = computed({ get: () => state.analysisMode, set: value => { state.analysisMode = value } })
const groupConsent = ref(false)
const groupResumeConsent = ref(false)
const singleConsent = ref(false)
const resumeText = ref('')
const groupBusy = ref(false)
const groupResumeBusy = ref(false)
const singleBusy = ref(false)
const error = ref('')
const singleJobId = ref('')
const currentProfile = computed(() => state.profileJobKey === selectedKey() ? state.profile : null)
const singleJob = computed(() => selectedJobs.value.find(job => job.id === singleJobId.value))
const currentGroupFeedback = computed(() => state.groupFeedback && state.groupFeedbackInput === `${selectedKey()}\u241e${resumeText.value.trim()}` ? state.groupFeedback : null)
const currentSingleFeedback = computed(() => state.singleFeedback && state.singleJobId === singleJobId.value && state.singleFeedbackInput === `${singleJob.value?.id || ''}\u241e${singleJob.value?.jd_text || ''}\u241e${resumeText.value.trim()}` ? state.singleFeedback : null)
const knownCompanyCount = computed(() => new Set(selectedJobs.value.map(job => job.company).filter(name => !['未填写', '未提及'].includes(name))).size)
const remaining = computed(() => Math.max(0, state.maxModelRequests - state.usedModelRequests))

watch(selectedJobs, (jobs) => {
  if (!jobs.some(job => job.id === singleJobId.value)) singleJobId.value = jobs[0]?.id || ''
}, { immediate: true })

async function refreshBudget() {
  try {
    const meta = await api('/meta')
    state.usedModelRequests = meta.used_model_requests
    state.maxModelRequests = meta.max_model_requests
  } catch { /* The page remains readable if the local API is not started yet. */ }
}
onMounted(refreshBudget)

function coverage(signal) {
  return new Set(signal.evidence.map(item => item.job_id)).size
}
function percent(signal) {
  return Math.round(coverage(signal) / (currentProfile.value?.job_ids.length || 1) * 100)
}
const frequent = computed(() => (currentProfile.value?.signals || []).filter(signal => coverage(signal) >= 2 && percent(signal) >= 50).sort((a, b) => coverage(b) - coverage(a)))
const other = computed(() => (currentProfile.value?.signals || []).filter(signal => !frequent.value.includes(signal)).sort((a, b) => coverage(b) - coverage(a)))
function jobName(id) {
  const job = selectedJobs.value.find(item => item.id === id)
  return job ? `${job.title} · ${job.company}` : '来源岗位'
}

async function createProfile() {
  if (currentProfile.value) { message.info('相同岗位样本的画像已在下方显示，没有重复调用模型。'); return }
  if (!groupConsent.value) { error.value = '请先确认本次模型请求和可能产生的费用。'; return }
  error.value = ''; groupBusy.value = true
  try {
    const result = await post('/analysis/group', { jobs: selectedJobs.value, consent: true })
    state.profile = result.profile
    state.profileJobKey = selectedKey()
    state.groupFeedback = null
    state.usedModelRequests = result.used_model_requests
    message.success('岗位方向画像已生成。请核对样本与原文依据。')
  } catch (cause) { error.value = cause.message }
  finally { groupBusy.value = false; groupConsent.value = false; await refreshBudget() }
}

async function compareGroupResume() {
  const inputKey = `${selectedKey()}\u241e${resumeText.value.trim()}`
  if (state.groupFeedback && state.groupFeedbackInput === inputKey) { message.info('相同简历的建议已在下方显示，没有重复调用模型。'); return }
  if (!groupResumeConsent.value) { error.value = '请先检查简历文字并确认本次模型请求。'; return }
  if (!resumeText.value.trim()) { error.value = '请先上传或粘贴简历文字。'; return }
  error.value = ''; groupResumeBusy.value = true
  try {
    const result = await post('/analysis/group-resume', {
      jobs: selectedJobs.value, profile: currentProfile.value, resume_text: resumeText.value, consent: true,
    })
    state.groupFeedback = result.feedback
    state.groupFeedbackInput = inputKey
    state.usedModelRequests = result.used_model_requests
    message.success('简历对照建议已生成。')
  } catch (cause) { error.value = cause.message }
  finally { groupResumeBusy.value = false; groupResumeConsent.value = false; await refreshBudget() }
}

async function compareSingleResume() {
  const inputKey = `${singleJob.value?.id || ''}\u241e${singleJob.value?.jd_text || ''}\u241e${resumeText.value.trim()}`
  if (state.singleFeedback && state.singleFeedbackInput === inputKey) { message.info('相同岗位和简历的建议已在下方显示，没有重复调用模型。'); return }
  if (!singleConsent.value) { error.value = '请先检查简历文字并确认本次模型请求。'; return }
  if (!singleJob.value || !resumeText.value.trim()) { error.value = '请选择岗位并填写简历文字。'; return }
  error.value = ''; singleBusy.value = true
  try {
    const result = await post('/analysis/single', { job: singleJob.value, resume_text: resumeText.value, consent: true })
    state.singleFeedback = result.feedback
    state.singleFeedbackInput = inputKey
    state.singleJobId = singleJob.value.id
    state.usedModelRequests = result.used_model_requests
    message.success('单岗位对照建议已生成。')
  } catch (cause) { error.value = cause.message }
  finally { singleBusy.value = false; singleConsent.value = false; await refreshBudget() }
}

async function saveReport(type) {
  try {
    const value = type === 'profile'
      ? { jobs: selectedJobs.value, profile: currentProfile.value }
      : type === 'group-resume'
        ? { jobs: selectedJobs.value, profile: currentProfile.value, feedback: currentGroupFeedback.value }
        : { job: singleJob.value, feedback: currentSingleFeedback.value }
    const report = await post(`/reports/${type}`, value)
    downloadText(report.text, report.filename)
  } catch (cause) { message.error(cause.message) }
}
</script>

<template>
  <div class="work-page analysis-page">
    <PageIntro title="把岗位信息变成行动建议" description="先看多份同类 JD 的共同要求，或在准备具体投递时精读一个岗位。" />
    <div class="mode-bar"><div><span class="eyebrow">CHOOSE YOUR LENS</span><h2>分析方式</h2></div><a-radio-group v-model:value="mode" button-style="solid"><a-radio-button value="group">岗位方向画像</a-radio-button><a-radio-button value="single">单岗位精读</a-radio-button></a-radio-group></div>
    <p class="small-note">公开测试费用保护：当前浏览会话还可主动发起 {{ remaining }} 次模型请求。失败请求也会计入，避免连续重试。</p>
    <a-alert v-if="error" type="error" show-icon :message="error" class="message-space" />

    <template v-if="mode === 'group'">
      <template v-if="selectedJobs.length < 2 || selectedJobs.length > 10">
        <a-empty class="empty-panel" :description="selectedJobs.length > 10 ? '岗位方向画像最多支持 10 条 JD，请调整选择。' : '岗位方向画像至少需要 2 条 JD；建议选择 5 至 10 条同类岗位。'"><a-button type="primary" @click="router.push('/saved')">去我的岗位</a-button></a-empty>
      </template>
      <template v-else>
        <div class="metric-row"><a-card><a-statistic title="本次样本" :value="selectedJobs.length" suffix="条 JD" /></a-card><a-card><a-statistic title="已知公司" :value="knownCompanyCount" suffix="家" /></a-card><a-card><a-statistic title="本步请求" value="1" suffix="次" /></a-card></div>
        <a-card class="research-card"><span class="eyebrow">BEFORE ANALYSIS</span><h2>先确认样本</h2><p>模型会从所选 JD 中归并同义要求，Python 再按不同岗位 ID 计算出现次数。结论只代表本次样本，不代表整个行业。</p><div class="sample-chips"><a-tag v-for="job in selectedJobs" :key="job.id">{{ job.title }} · {{ job.company }}</a-tag></div><a-checkbox v-model:checked="groupConsent">我已核对以上 JD，同意发送给 DeepSeek 生成方向画像（可能产生费用）</a-checkbox><div class="action-line"><a-button type="primary" size="large" :loading="groupBusy" :disabled="remaining === 0" @click="createProfile">生成岗位方向画像</a-button></div></a-card>

        <section v-if="currentProfile" class="result-section"><div class="section-bar"><div><span class="eyebrow">EVIDENCE PORTRAIT</span><h2>{{ currentProfile.direction_name }}</h2></div><a-button @click="saveReport('profile')">下载画像 TXT</a-button></div><p class="lead-copy">{{ currentProfile.summary }}</p><p class="small-note">{{ currentProfile.consistency_summary }}</p><a-alert v-if="currentProfile.outlier_job_ids.length" type="warning" show-icon :message="`可能混入不同方向的岗位：${currentProfile.outlier_job_ids.map(jobName).join('、')}。建议核对后重新选择。`" />
          <h3>高频岗位信号 <small>至少 2 条且覆盖一半样本</small></h3>
          <a-empty v-if="!frequent.length" description="当前样本没有达到高频条件的要求。" />
          <div v-if="frequent.length" class="signal-grid"><div v-for="signal in frequent" :key="signal.label" class="signal-card"><div class="signal-head"><strong>{{ signal.label }}</strong><span>{{ signal.category }} · {{ coverage(signal) }} / {{ currentProfile.job_ids.length }} 条</span></div><a-progress :percent="percent(signal)" :show-info="false" size="small" /><a-collapse ghost><a-collapse-panel key="evidence" header="查看对应 JD 原文依据"><div v-for="item in signal.evidence" :key="`${item.job_id}-${item.quote}`" class="evidence-quote"><strong>{{ jobName(item.job_id) }}</strong><p>“{{ item.quote }}”</p></div></a-collapse-panel></a-collapse></div></div>
          <template v-if="other.length"><h3>其他明确要求</h3><div class="signal-grid"><div v-for="signal in other" :key="signal.label" class="signal-card"><div class="signal-head"><strong>{{ signal.label }}</strong><span>{{ signal.category }} · {{ coverage(signal) }} / {{ currentProfile.job_ids.length }} 条</span></div><a-progress :percent="percent(signal)" :show-info="false" size="small" /><a-collapse ghost><a-collapse-panel key="evidence" header="查看对应 JD 原文依据"><div v-for="item in signal.evidence" :key="`${item.job_id}-${item.quote}`" class="evidence-quote"><strong>{{ jobName(item.job_id) }}</strong><p>“{{ item.quote }}”</p></div></a-collapse-panel></a-collapse></div></div></template>
          <p class="small-note">频率只表示本次所选样本中出现的次数，不等于重要程度，也不代表整个行业。</p>
          <section class="resume-stage"><div class="section-bar"><div><span class="eyebrow">OPTIONAL NEXT STEP</span><h2>再对照简历</h2></div></div><ResumeInput v-model="resumeText" /><a-checkbox v-model:checked="groupResumeConsent">我已检查上方文字，同意将简历与所选岗位方向发送给 DeepSeek 生成建议（可能产生费用）</a-checkbox><div class="action-line"><a-button type="primary" :loading="groupResumeBusy" :disabled="remaining === 0" @click="compareGroupResume">生成方向匹配建议</a-button></div></section>
        </section>
        <section v-if="currentProfile && currentGroupFeedback" class="result-section feedback-section"><div class="section-bar"><div><span class="eyebrow">YOUR NEXT MOVES</span><h2>简历与岗位方向的对照建议</h2></div><a-button @click="saveReport('group-resume')">下载建议 TXT</a-button></div><p class="lead-copy">{{ currentGroupFeedback.summary }}</p><div class="feedback-grid"><a-card title="简历已有依据"><a-empty v-if="!currentGroupFeedback.matched_capabilities.length" description="暂无可核对依据" /><div v-for="item in currentGroupFeedback.matched_capabilities" :key="item.requirement" class="feedback-point"><strong>{{ item.requirement }}</strong><p>{{ item.explanation }}</p><small>简历原文：“{{ item.resume_quote }}”</small></div></a-card><a-card title="简历还没清楚体现"><a-empty v-if="!currentGroupFeedback.gaps.length" description="暂无明确缺口" /><div v-for="item in currentGroupFeedback.gaps" :key="item.requirement" class="feedback-point"><strong>{{ item.requirement }}</strong><p>{{ item.explanation }}</p></div></a-card></div><div class="feedback-grid"><a-card title="简历表达建议"><ol><li v-for="item in currentGroupFeedback.resume_edits" :key="item">{{ item }}</li></ol></a-card><a-card title="优先准备的事项"><ol><li v-for="item in currentGroupFeedback.action_plan" :key="item">{{ item }}</li></ol></a-card></div><p class="small-note">“未体现”不等于“不会”；只补充真实经历，不要编造项目、技能或数字。</p></section>
      </template>
    </template>

    <template v-else>
      <a-empty v-if="!selectedJobs.length" class="empty-panel" description="先到“我的岗位”勾选至少一条，再精读具体投递目标。"><a-button type="primary" @click="router.push('/saved')">去我的岗位</a-button></a-empty>
      <template v-else><a-card class="research-card"><span class="eyebrow">ONE TARGET, CLOSER LOOK</span><h2>选择具体岗位</h2><a-select v-model:value="singleJobId" class="single-select" :options="selectedJobs.map(job => ({value:job.id,label:`${job.title} · ${job.company}`}))" /><p class="small-note">单岗位精读适合已经确定投递目标的情况；不会自动分析清单中的全部岗位。</p><ResumeInput v-model="resumeText" /><a-checkbox v-model:checked="singleConsent">我已检查上方简历文字，同意将它和选中 JD 发送给 DeepSeek 生成建议（可能产生费用）</a-checkbox><div class="action-line"><a-button type="primary" size="large" :loading="singleBusy" :disabled="remaining === 0" @click="compareSingleResume">生成单岗位建议</a-button></div></a-card>
        <section v-if="currentSingleFeedback" class="result-section feedback-section"><div class="section-bar"><div><span class="eyebrow">EVIDENCE-BASED REVIEW</span><h2>简历与岗位的对照结果</h2></div><a-button @click="saveReport('single')">下载建议 TXT</a-button></div><p class="lead-copy">{{ currentSingleFeedback.summary }}</p><div class="feedback-grid"><a-card title="已体现的匹配点"><div v-for="item in currentSingleFeedback.matched_points" :key="item.requirement" class="feedback-point"><strong>{{ item.requirement }}</strong><small>JD：“{{ item.jd_quote }}”</small><small>简历：“{{ item.resume_quote }}”</small></div></a-card><a-card title="简历未清楚体现的要求"><div v-for="item in currentSingleFeedback.gaps" :key="item.requirement" class="feedback-point"><strong>{{ item.requirement }}</strong><p>{{ item.explanation }}</p><small>JD：“{{ item.jd_quote }}”</small></div></a-card></div><div class="feedback-grid"><a-card title="简历表达建议"><ol><li v-for="item in currentSingleFeedback.resume_edits" :key="item">{{ item }}</li></ol></a-card><a-card title="优先准备的事项"><ol><li v-for="item in currentSingleFeedback.learning_priorities" :key="item">{{ item }}</li></ol></a-card></div><p class="small-note">结论可能遗漏或出错；请核对原文，不要编造经历。</p></section>
      </template>
    </template>
  </div>
</template>
