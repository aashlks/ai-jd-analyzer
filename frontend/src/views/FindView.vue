<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import PageIntro from '../components/PageIntro.vue'
import { api } from '../api.js'
import { addJob, state } from '../store.js'

const tab = ref(state.searchTab)
const keyword = ref(state.searchKeyword)
const city = ref(state.searchCity)
const employment = ref(state.searchEmployment)
const results = ref(state.searchResults)
const error = ref('')
const searching = ref(false)
const resultsScroll = ref(null)
const manual = ref({ title: '', company: '', url: '', jd_text: '' })

watch([tab, keyword, city, employment, results], () => {
  state.searchTab = tab.value
  state.searchKeyword = keyword.value
  state.searchCity = city.value
  state.searchEmployment = employment.value
  state.searchResults = results.value
})

const companiesOnPage = computed(() => new Set(
  (results.value?.items || []).map(job => job.company).filter(name => !['未提及', '未填写'].includes(name)),
).size)

async function runSearch(offset = 0) {
  if (!keyword.value.trim()) { error.value = '请填写岗位关键词。'; return }
  error.value = ''
  searching.value = true
  try {
    const params = new URLSearchParams({
      q: keyword.value.trim(), city: city.value.trim(), employment_type: employment.value, offset: String(offset),
    })
    results.value = await api(`/jobs/search?${params}`)
    await nextTick()
    if (resultsScroll.value) resultsScroll.value.scrollTop = 0
  } catch (cause) {
    error.value = cause.message
    results.value = null
  } finally { searching.value = false }
}

function addCandidate(job) {
  const added = addJob(job)
  message[added ? 'success' : 'info'](added ? '已加入我的岗位，可继续搜索或添加。' : '这条 JD 已在清单中。')
}

function addPage() {
  const count = (results.value?.items || []).reduce((sum, job) => sum + Number(addJob(job)), 0)
  message[count ? 'success' : 'info'](count ? `已加入 ${count} 个岗位，可以继续搜索或翻页。` : '本页岗位都已在清单中。')
}

function addManual() {
  const jd = manual.value.jd_text.trim()
  if (!jd) { message.error('请先填写岗位 JD。'); return }
  const source = manual.value.url.trim()
  if (source) {
    try {
      const parsed = new URL(source)
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('invalid protocol')
    } catch { message.error('来源链接需要是以 http:// 或 https:// 开头的完整网址。'); return }
  }
  const job = {
    id: `manual:${crypto.randomUUID()}`,
    source: '手动添加',
    title: manual.value.title.trim() || '手动添加的岗位',
    company: manual.value.company.trim() || '未填写',
    location: '未提及',
    jd_text: jd,
    url: source,
    original_url: '',
    published_at: '',
  }
  if (addJob(job)) {
    message.success('添加成功！可继续添加，完成后到“我的岗位”查看。')
    manual.value = { title: '', company: '', url: '', jd_text: '' }
  } else message.info('相同内容的 JD 已经在清单里。')
}
</script>

<template>
  <div class="work-page">
    <PageIntro title="找岗位，建立样本" description="搜索和手动添加都在这里完成。先收集多份同类岗位，再到“我的岗位”挑选要比较的样本。" />
    <div class="section-bar page-toolbar"><h2>岗位来源</h2><router-link class="quiet-count" to="/saved">已加入 {{ state.jobs.length }} 条 · 查看清单 →</router-link></div>
    <a-tabs v-model:activeKey="tab" class="source-tabs">
      <a-tab-pane key="search" tab="自动搜索（Offer岛）">
        <div class="search-workbench">
          <aside class="filter-column" aria-label="搜索条件">
            <div class="filter-heading"><h2>搜索条件</h2><p>输入岗位方向，按需缩小范围。</p></div>
            <a-form layout="vertical" @submit.prevent>
              <a-form-item label="岗位关键词" required><a-input v-model:value="keyword" :maxlength="50" placeholder="例如：内容运营" @press-enter="runSearch(0)" /></a-form-item>
              <a-form-item label="城市（可选）"><a-input v-model:value="city" placeholder="例如：上海" @press-enter="runSearch(0)" /></a-form-item>
              <a-form-item label="用工类型"><a-select v-model:value="employment" :options="[{value:'',label:'不限'},{value:'实习',label:'实习'},{value:'正式',label:'正式'}]" /></a-form-item>
              <a-button type="primary" block :loading="searching" @click="runSearch(0)">搜索岗位</a-button>
            </a-form>
            <p class="source-limitation">目前只查询 Offer岛，不抓取 BOSS；该来源偏 AI 方向，不能覆盖所有行业。其他岗位可切换到“手动添加 JD”。</p>
            <p class="small-note">搜索不会调用 DeepSeek。</p>
          </aside>
          <section class="results-column" aria-label="搜索结果">
            <div class="results-head">
              <div><h2>搜索结果</h2><p>{{ results ? `约 ${results.total} 条 · 本页 ${results.items.length} 条 · ${companiesOnPage} 家已知公司` : '输入关键词后，在这里浏览和添加岗位。' }}</p></div>
              <a-button v-if="results" :disabled="!results.items.length" @click="addPage">本页全部加入</a-button>
            </div>
            <a-alert v-if="error" type="error" show-icon :message="error" class="results-error" />
            <div ref="resultsScroll" class="results-scroll" tabindex="0" aria-label="岗位搜索结果列表" :aria-busy="searching">
              <template v-if="results">
              <a-empty v-if="!results.items.length" class="results-empty" description="没有搜到岗位。可换关键词、去掉城市，或手动添加 JD。" />
              <div v-else class="job-grid search-results">
                <a-card v-for="job in results.items" :key="job.id" class="job-card" :bordered="true">
                  <div class="card-overline"><span>{{ job.source }}</span><span>{{ job.published_at ? `发布于 ${job.published_at.slice(0,10)}` : '发布时间未注明' }}</span></div>
                  <h3>{{ job.title }}</h3>
                  <p class="job-meta">{{ job.company }} · {{ job.location }}</p>
                  <p class="job-preview">{{ job.jd_text.slice(0, 180) }}{{ job.jd_text.length > 180 ? '…' : '' }}</p>
                  <a-collapse ghost><a-collapse-panel key="jd" header="查看完整 JD"><p class="jd-body">{{ job.jd_text }}</p></a-collapse-panel></a-collapse>
                  <div class="card-actions"><a-button type="primary" :disabled="state.jobs.some(item => item.id === job.id || item.jd_text === job.jd_text)" @click="addCandidate(job)">{{ state.jobs.some(item => item.id === job.id || item.jd_text === job.jd_text) ? '已加入' : '加入我的岗位' }}</a-button><a v-if="job.url" :href="job.url" target="_blank" rel="noopener noreferrer">查看来源页面 ↗</a></div>
                </a-card>
              </div>
              </template>
              <div v-else class="search-prompt"><div class="prompt-icon" aria-hidden="true"><span class="search-mark"></span></div><h2>从一个岗位关键词开始</h2><p>搜索后在这里浏览结果并连续加入清单。没有结果时，可以改用手动添加。</p></div>
            </div>
            <div v-if="results" class="pager"><a-button :disabled="results.offset === 0 || searching" @click="runSearch(Math.max(0, results.offset - 20))">上一页</a-button><span>第 {{ Math.floor(results.offset / 20) + 1 }} 页</span><a-button :disabled="results.offset + 20 >= results.total || searching" @click="runSearch(results.offset + 20)">下一页</a-button></div>
          </section>
        </div>
      </a-tab-pane>
      <a-tab-pane key="manual" tab="手动添加 JD">
        <div class="manual-intro"><h2>把看到的岗位收进来</h2><p>适用于任何行业。粘贴 BOSS 或其他平台的岗位描述；这里只保存你提供的内容，不会自动访问来源链接。</p></div>
        <a-card class="form-card manual-card" :bordered="false">
          <a-form layout="vertical" @submit.prevent>
            <div class="form-grid manual-grid"><a-form-item label="岗位名称或备注（可选）"><a-input v-model:value="manual.title" placeholder="例如：内容运营专员" /></a-form-item><a-form-item label="公司（可选）"><a-input v-model:value="manual.company" placeholder="例如：某科技公司" /></a-form-item></div>
            <a-form-item label="来源链接（可选）"><a-input v-model:value="manual.url" placeholder="https://..." /></a-form-item>
            <a-form-item label="岗位 JD" required><a-textarea v-model:value="manual.jd_text" :maxlength="20000" :rows="9" show-count placeholder="粘贴岗位职责和任职要求" /></a-form-item>
            <a-button type="primary" @click="addManual">加入我的岗位</a-button>
          </a-form>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>
