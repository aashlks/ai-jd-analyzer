---
name: 求职对照台
description: 以原文证据为中心的蓝白岗位对照工作台
colors:
  primary: "#235cb7"
  primary-deep: "#164a98"
  primary-wash: "#eaf2ff"
  primary-soft: "#f3f7ff"
  ink: "#182b43"
  muted: "#587089"
  line: "#cfdae8"
  line-soft: "#e6edf5"
  surface: "#ffffff"
  canvas: "#f6f9fe"
typography:
  display:
    fontFamily: "Inter, Segoe UI Variable, Segoe UI, Noto Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "clamp(42px, 4.3vw, 64px)"
    fontWeight: 780
    lineHeight: 1.18
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Inter, Segoe UI Variable, Segoe UI, Noto Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "clamp(32px, 3.2vw, 43px)"
    fontWeight: 760
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Inter, Segoe UI Variable, Segoe UI, Noto Sans SC, Microsoft YaHei, sans-serif"
    fontSize: "14px"
    lineHeight: 1.65
  evidence-count:
    fontFamily: "Cascadia Code, SFMono-Regular, Consolas, monospace"
    fontSize: "12px"
    fontWeight: 720
rounded:
  control: "10px"
  card: "12px"
  panel: "13px"
  example: "18px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
  page-top: "44px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.surface}"
  evidence-count:
    backgroundColor: "{colors.primary-wash}"
    textColor: "{colors.primary-deep}"
    typography: "{typography.evidence-count}"
    rounded: "6px"
---

# Design System: 求职对照台

## Overview

**Creative North Star: "岗位证据台"**

页面是一张供人整理和核对招聘信息的工作台，不是招聘平台的替身，也不是模型能力海报。首屏把“多份 JD 的共性”作为主角；收集、筛选、分析按真实使用顺序展开。示例必须写明“示例数据”，真实结论必须能回到样本和原文。

**Key Characteristics:**
- 冷白工作面、深蓝正文和克制的钴蓝行动色。
- 长 JD 保持普通文本阅读节奏；样本次数、来源和确认操作容易辨认。
- 只保留简短的控件状态过渡，不依赖滚动特效。

## Colors

Primary 是行动和样本证据的线索；Neutral 承载长篇文字。规范值以上方 frontmatter 为准。

### Primary
- **钴蓝**：主要按钮、当前导航与重点词。
- **深钴蓝**：蓝色文字与悬停后的操作。
- **证据浅蓝**：选中岗位、样本计数和频率标签。

### Neutral
- **深海军蓝**：正文与标题，不使用纯黑。
- **石板蓝灰**：来源、日期、解释与辅助信息。
- **冷白画布和白色表面**：区分页面工作区与可操作卡片。
- **浅灰蓝分隔线**：帮助扫描长列表和证据行。

**The Evidence Color Rule.** 蓝色只说明“这里可操作、已选择或可核对”，不为模型推测制造假确定性。

## Typography

**Display / Body Font:** Inter 优先处理拉丁字符，中文依次回退到 Noto Sans SC、微软雅黑；不依赖单一远程字体才能阅读。

**Evidence Count Font:** Cascadia Code 等宽回退链用于真实样本的分子／分母和步骤数字，方便纵向比较。

### Hierarchy
- **Display**：欢迎页价值主张，粗而紧凑，桌面约 42–64px，手机缩至 36–48px。
- **Headline**：工作页标题约 32–43px；页面介绍紧凑，让操作尽快进入首屏。
- **Title**：区块 21px、岗位 18px、正文 13–17px，长 JD 保留 1.65 左右行高。
- **Label**：来源、注释和计数约 11–13px；不把英文装饰性 eyebrow 当成信息层级。

**The Count Is Not a Score Rule.** “4 / 5”表示本次样本覆盖，不表达匹配度或录用概率。

## Layout

内容宽度最多 1200px，四条路由共享导航。首页左右分栏呈现价值主张与明确标注的比较示例，下方用有序流程而非三张等宽功能卡。找岗位页在宽屏使用搜索条件／结果双栏；800px 以下改为上下顺序。清单为可扫描的单列岗位卡。分析页先列样本与请求量，再出现用户同意框；结果保留原文证据的展开入口。

页面常用间距为 8、16、24px，页面上缘为 44px；手机压缩为 25px。原生滚动不加视差或监听器，减少长 JD 页面滚动负担。

## Elevation & Depth

默认以白色表面、细边框和浅蓝选中态建立层级。首页示例面板有柔和环境阴影；岗位卡悬停时只略加深边框与阴影，不做大幅移动。

## Shapes

控件使用中等圆角；岗位卡约 12px，搜索面板约 13px，首页示例约 18px。圆角帮助区分可以操作的容器，不把页面做成随意拼贴的胶囊集合。

## Components

### Buttons
- **Primary:** 钴蓝实底、白字，用于搜索、加入和用户确认后的生成；悬停加深。
- **Secondary:** 白底细边框，用于保存列表、批量选项与下载。
- **Focus:** 可见的浅蓝轮廓；不只依靠颜色变化。

### Cards / Containers
- 白色表面、浅灰蓝边框。已选岗位有浅蓝表面与更明确的蓝色边框。
- 搜索结果按单列呈现，便于看标题、公司、简介与来源；完整 JD 可展开。

### Inputs / Fields
- 使用 Ant Design Vue 的表单语义、验证和控件状态；搜索过滤放在结果旁，不让用户来回滚动。

### Navigation
- 四条路由 /、/find、/saved、/analysis 保持可达；当前页用浅蓝底和深蓝字，手机端导航独占第二行。

### Evidence
- 频率旁展示覆盖岗位数，展开后显示对应 JD 的原文。没有来源证据的示例不冒充真实分析。

## Do's and Don'ts

### Do:
- **Do** 在产生模型费用前显示样本、请求量和明确的同意操作。
- **Do** 把数据示例与真实分析结果分开标记。
- **Do** 在窄屏按“条件 → 结果 → 清单 → 分析”的阅读顺序堆叠内容。

### Don't:
- **Don't** 把样本频率画成求职者的匹配分。
- **Don't** 用大面积装饰替代 JD、来源、公司和原文证据。
- **Don't** 使用滚动劫持、循环动画或只在悬停时可发现的关键操作。
