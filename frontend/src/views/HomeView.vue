<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { state } from '../store.js'

const router = useRouter()
const hasJobs = computed(() => state.jobs.length > 0)
const demoSignals = [
  { name: '跨团队协作', count: '4 / 5', quote: '“与设计、产品同事沟通需求”' },
  { name: '数据整理', count: '3 / 5', quote: '“定期复盘内容效果和数据”' },
  { name: '项目推进', count: '3 / 5', quote: '“跟进活动执行和上线节奏”' },
]
</script>

<template>
  <div class="home-page">
    <section class="hero-paper" aria-labelledby="hero-title">
      <div class="hero-copy">
        <h1 id="hero-title">从多份 JD，<br />看清<span>岗位方向。</span></h1>
        <p>收集同类岗位，找出反复出现的要求，逐条核对招聘原文。看清岗位方向后，再决定简历该怎么准备。</p>
        <div class="hero-actions">
          <a-button type="primary" size="large" class="hero-cta" @click="router.push('/find')">开始找岗位 <span aria-hidden="true">→</span></a-button>
          <a-button v-if="hasJobs" size="large" @click="router.push('/saved')">查看已存的 {{ state.jobs.length }} 条岗位</a-button>
        </div>
        <p class="hero-assurance">先收集，再分析。搜索与添加不会调用 DeepSeek。</p>
      </div>
      <div class="sample-sheet" aria-label="岗位画像示例，不是真实分析结果">
        <div class="sheet-top"><span>岗位方向画像</span><span class="demo-badge">示例数据</span></div>
        <div class="sheet-summary"><strong>内容运营方向</strong><span>基于 5 份同类 JD 的示例</span></div>
        <div class="demo-table-head"><span>反复出现的要求</span><span>覆盖岗位</span></div>
        <div v-for="signal in demoSignals" :key="signal.name" class="demo-signal">
          <div class="demo-signal-line"><strong>{{ signal.name }}</strong><span>{{ signal.count }}</span></div>
          <small>原文例子：{{ signal.quote }}</small>
        </div>
        <p class="demo-caption">实际画像会列出来源岗位、覆盖次数和对应 JD 原文，不把样本频率当作行业结论。</p>
      </div>
    </section>
    <section class="home-flow" aria-labelledby="flow-title">
      <div class="flow-intro"><h2 id="flow-title">从岗位信息到准备方向</h2><p>主要看多份 JD 的共性；单岗位精读留给已经确定投递目标时使用。</p></div>
      <ol class="flow-steps">
        <li><span>01</span><div><h3>收集岗位</h3><p>自动搜索，或粘贴其他平台的 JD，连续加入清单。</p></div></li>
        <li><span>02</span><div><h3>对照要求</h3><p>选择 2–10 份同类岗位，看出现次数与原文依据。</p></div></li>
        <li><span>03</span><div><h3>决定行动</h3><p>按需上传简历获取建议；模型请求前会再次确认。</p></div></li>
      </ol>
    </section>
  </div>
</template>
