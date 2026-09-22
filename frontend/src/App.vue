<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import zhCN from 'ant-design-vue/es/locale/zh_CN'

const route = useRoute()
const guideOpen = ref(false)
const privacyOpen = ref(false)
const theme = {
  token: {
    colorPrimary: '#235cb7',
    colorInfo: '#235cb7',
    colorSuccess: '#247b63',
    colorWarning: '#b56b24',
    colorText: '#182b43',
    colorTextSecondary: '#587089',
    colorBorder: '#cfdae8',
    colorBgContainer: '#ffffff',
    borderRadius: 10,
    fontFamily: '"Inter", "Segoe UI", "Noto Sans SC", "Microsoft YaHei", sans-serif',
  },
}
const navigation = [
  { path: '/find', label: '找岗位' },
  { path: '/saved', label: '我的岗位' },
  { path: '/analysis', label: '分析中心' },
]
</script>

<template>
  <a-config-provider :theme="theme" :locale="zhCN">
    <div class="site-shell">
      <header class="site-header">
        <router-link class="brand" to="/" aria-label="求职对照台，返回欢迎页">
          <span class="brand-sigil" aria-hidden="true"></span>
          <span>求职对照台</span>
        </router-link>
        <nav class="main-nav" aria-label="主要页面">
          <router-link v-for="item in navigation" :key="item.path" :to="item.path" :class="{ active: route.path === item.path }">
            {{ item.label }}
          </router-link>
        </nav>
        <div class="header-actions">
          <a-button type="text" @click="guideOpen = true">使用指南</a-button>
          <a-button type="text" @click="privacyOpen = true">隐私与费用</a-button>
        </div>
      </header>

      <main class="main-content"><router-view /></main>

      <footer class="site-footer">
        <span>公开测试版 · 分析结果应回到原 JD 核对，不等于录用判断。</span>
        <span>岗位与勾选仅留在当前浏览会话；没有账号和长期保存。</span>
      </footer>
    </div>

    <a-modal v-model:open="guideOpen" title="三步完成一次岗位方向研究" :footer="null" width="560px">
      <ol class="guide-list">
        <li><strong>找岗位</strong><p>优先搜索 Offer岛；其他行业或 BOSS 岗位可粘贴 JD，添加后仍停留在当前页。</p></li>
        <li><strong>我的岗位</strong><p>勾选多条同类岗位，尽量覆盖不同公司。完全相同的 JD 只计入一次。</p></li>
        <li><strong>分析中心</strong><p>先看共同要求与原文证据，再决定是否上传简历；确定投递目标时也可精读单条岗位。</p></li>
      </ol>
      <a-alert type="info" show-icon message="浏览、搜索、添加和勾选不会调用 DeepSeek；每次模型请求都需单独确认。" />
    </a-modal>
    <a-modal v-model:open="privacyOpen" title="隐私与费用" :footer="null" width="560px">
      <div class="privacy-copy">
        <h3>数据去向</h3>
        <p>搜索词会发送给 Offer岛。只有勾选同意并点击生成后，所选 JD 或简历文字才会发送给 DeepSeek。</p>
        <h3>简历检查</h3>
        <p>PDF / DOCX 在本站服务端提取文字，并遮盖常见邮箱、手机号和证件号码；姓名、地址等剩余信息仍需你检查。扫描 PDF 暂不支持。</p>
        <h3>保存与费用</h3>
        <p>当前没有账号和数据库。岗位清单保存在本浏览标签会话中，服务端模型请求有会话次数限制，但不能代替 API 平台的消费上限。</p>
      </div>
    </a-modal>
  </a-config-provider>
</template>
