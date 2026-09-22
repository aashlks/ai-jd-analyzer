import { createApp } from 'vue'
import {
  Alert, Button, Card, Checkbox, Collapse, ConfigProvider, Empty, Form,
  Input, Modal, Popconfirm, Progress, Radio, Select, Statistic, Tabs, Tag, Upload,
} from 'ant-design-vue'
import { createRouter, createWebHistory } from 'vue-router'
import 'ant-design-vue/dist/reset.css'
import './style.css'
import App from './App.vue'
import HomeView from './views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView, meta: { title: '欢迎' } },
    { path: '/find', component: () => import('./views/FindView.vue'), meta: { title: '找岗位' } },
    { path: '/saved', component: () => import('./views/SavedView.vue'), meta: { title: '我的岗位' } },
    { path: '/analysis', component: () => import('./views/AnalysisView.vue'), meta: { title: '分析中心' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.afterEach((to) => { document.title = `${to.meta.title}｜求职对照台` })

const app = createApp(App)
for (const component of [
  Alert, Button, Card, Checkbox, Collapse, ConfigProvider, Empty, Form,
  Input, Modal, Popconfirm, Progress, Radio, Select, Statistic, Tabs, Tag, Upload,
]) app.use(component)
app.use(router)
app.mount('#app')
