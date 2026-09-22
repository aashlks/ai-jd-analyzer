<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import PageIntro from '../components/PageIntro.vue'
import { removeJob, selectAll, selectedJobs, setSelected, state } from '../store.js'

const router = useRouter()
const companyNames = computed(() => [...new Set(selectedJobs.value.map(job => job.company).filter(company => !['未填写', '未提及'].includes(company)))])

function toggle(id, checked) {
  setSelected(checked ? [...state.selectedIds, id] : state.selectedIds.filter(item => item !== id))
}

function begin(mode) {
  state.analysisMode = mode
  router.push('/analysis')
}
</script>

<template>
  <div class="work-page">
    <PageIntro title="整理要比较的岗位" description="加入的岗位会直接列在下面。勾选多个同类岗位生成方向画像，也可以只精读其中一个。" />
    <template v-if="!state.jobs.length">
      <a-empty class="empty-panel" description="这里还没有岗位。先到“找岗位”自动搜索；没有合适结果时再手动添加 JD。">
        <a-button type="primary" @click="router.push('/find')">去找岗位</a-button>
      </a-empty>
    </template>
    <template v-else>
      <section class="selection-panel">
        <div><span class="eyebrow">YOUR SAMPLE</span><h2>选择本次要研究的岗位</h2><p>已勾选 {{ state.selectedIds.length }} / {{ state.jobs.length }} 条 · 已知公司 {{ companyNames.length }} 家</p></div>
        <div class="selection-tools"><a-button @click="selectAll(true)">全选</a-button><a-button @click="selectAll(false)">全不选</a-button></div>
      </section>
      <a-alert v-if="state.selectedIds.length >= 2 && companyNames.length === 1" type="warning" show-icon message="所选岗位目前只来自一家已知公司，方向画像可能反映这家公司的习惯；建议加入其他公司。" />
      <p class="small-note">勾选本身不会调用模型。多个同类岗位用于方向画像；具体投递时可以精读其中一条。</p>
      <div class="selection-actions"><a-button type="primary" :disabled="state.selectedIds.length < 2 || state.selectedIds.length > 10" @click="begin('group')">分析岗位方向（已选 {{ state.selectedIds.length }} 条）</a-button><a-button :disabled="state.selectedIds.length < 1" @click="begin('single')">精读其中一个岗位</a-button></div>
      <div class="section-bar"><div><span class="eyebrow">SAVED POSTINGS</span><h2>已加入的岗位</h2></div><span class="quiet-count">{{ state.jobs.length }} 条 JD</span></div>
      <div class="job-grid">
        <a-card v-for="job in state.jobs" :key="job.id" class="job-card selectable-card" :class="{selected:state.selectedIds.includes(job.id)}">
          <div class="card-overline"><a-checkbox :checked="state.selectedIds.includes(job.id)" :aria-label="`选择${job.title}`" @change="event => toggle(job.id, event.target.checked)">加入本次样本</a-checkbox><span>{{ job.source }}</span></div>
          <h3>{{ job.title }}</h3>
          <p class="job-meta">{{ job.company }} · {{ job.location }}</p>
          <p class="job-preview">{{ job.jd_text.slice(0, 180) }}{{ job.jd_text.length > 180 ? '…' : '' }}</p>
          <a-collapse ghost><a-collapse-panel key="jd" header="查看完整 JD"><p class="jd-body">{{ job.jd_text }}</p></a-collapse-panel></a-collapse>
          <div class="card-actions"><a v-if="job.url" :href="job.url" target="_blank" rel="noopener noreferrer">查看来源页面 ↗</a><a-popconfirm title="移除这条岗位？" ok-text="移除" cancel-text="取消" @confirm="removeJob(job.id)"><a-button danger>移除</a-button></a-popconfirm></div>
        </a-card>
      </div>
      <p class="small-note">清单只保存在当前浏览会话中，关闭或重启后可能消失。</p>
    </template>
  </div>
</template>
