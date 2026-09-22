# 岗位 JD 与简历分析器

这是一个适合初学者理解和继续开发的 Python 项目。网页 **不限定技术岗或实习岗**：核心功能是从 2～10 份同类 JD 生成有原文依据的“岗位方向画像”，再按需与简历对照；原有的单岗位精读仍然保留。

**已上线的版本：**[求职对照台（Streamlit）](https://ai-jd-analyzer-aashlks.streamlit.app/)。**这次的 Ant Design Vue 改版目前只在本地完成，尚未替换该线上网址。**

这是公开测试版。首次访问时如果应用处于休眠状态，按页面提示唤醒后等待片刻即可；无需登录 Streamlit。

## 新版：Ant Design Vue 页面（本地预览）

页面面向探索职业方向的学生和初入职场者，**不限定技术岗**。用户最重要的任务是：找多份同类岗位、筛出可比较的样本、看有 JD 原文支撑的高频要求，最后再决定是否用简历对照。因此新版保留四条实际路由：`/` 欢迎页、`/find` 找岗位、`/saved` 我的岗位、`/analysis` 分析中心；“使用指南”只在点击后出现，不占据工作流程。

新版采用蓝白色的岗位对照工作台：冷白背景承载长 JD，深蓝文字保持阅读对比，钴蓝只强调主操作、当前选择和可核对的样本数据。中文与英文统一使用清晰的无衬线字体栈，样本次数使用等宽数字。首页用明确标注的示例说明“多份 JD → 共同要求 → 原文依据”；找岗位页让搜索条件和结果在桌面端相邻、手机端顺序堆叠；岗位清单直接呈现勾选卡片。画像中的频率表示 **本次样本里出现的次数**，并非匹配分或录用概率。动效只用于控件状态变化，页面使用原生滚动，系统设置“减少动态效果”时会关闭过渡。组件使用 Ant Design Vue，业务路由由 Vue Router 管理；原来的搜索、勾选、画像、简历对照和报告下载逻辑继续由 Python 提供。

产品边界与设计规则分别记录在 [PRODUCT.md](PRODUCT.md) 和 [DESIGN.md](DESIGN.md)，后续新增页面可直接沿用同一套蓝白视觉系统。

想在本机打开新版，需要 Python 环境以及 Node.js、pnpm。在项目根目录先安装 Python 依赖；然后分别打开两个终端：

```powershell
# 终端一：在项目根目录启动 Python API
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端二：在项目根目录启动 Vue 开发服务器
cd frontend
pnpm install
pnpm dev
```

浏览器打开开发服务器打印的网址，通常是 `http://127.0.0.1:5173`。第二个终端会把 `/api` 请求转发给第一个终端。若只想用**一个网址**预览，可在 `frontend` 目录运行 `pnpm build`，再只启动上面的 Python API，打开 `http://127.0.0.1:8000`；改了前端文件后需重新 `pnpm build`。两个终端中按 `Ctrl+C` 可停止服务。`pnpm` 不可用时，先检查 Node.js / pnpm 是否安装并能在 VS Code 终端运行。

新版仍是公开测试原型：Key 只放服务端 `.env`，不会交给浏览器。搜索、添加、选择不调用 DeepSeek；模型请求必须单独确认。岗位清单保存在当前浏览标签的会话存储中，没有账号和长期保存。服务端的会话次数限制只是本地/小范围测试保护，**不能单独承担正式公开服务的费用安全**；上线新版前还需要确定适合 Python ASGI 的部署平台、账号或强配额及 API 平台消费上限。

新版文件：`frontend/src/views/` 是四个页面，`frontend/src/style.css` 管理字体、配色、版式、响应式和动效，`frontend/src/store.js` 管理浏览会话中的岗位清单；`api_server.py` 将现有 Python 逻辑接到网页，保持 DeepSeek Key 在服务端。网页对用户展示的是可读的分析和建议，JSON 只在程序内部传递与校验。

## 旧版：怎样试用本地 Streamlit 网页

在项目目录的 VS Code 终端运行。如果已经打开旧网页，先按 `Ctrl+C` 停止服务，再重新启动：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run web_app.py
```

终端会显示一个本地网址，通常是 `http://localhost:8501`。用浏览器打开即可；关闭终端里的服务可按 `Ctrl+C`。

旧版也采用“求职研究手册”的设计：暖纸张承载长篇 JD，深墨色保证阅读，松绿色标记可核对的岗位信号，赭色用于来源与步骤注释。中文衬线标题区分研究结论与操作文字，正文仍用清晰的无衬线字体；欢迎页的画像卡明确写着“界面示意”，不冒充真实分析结果。动效仅帮助理解证据频率和卡片层级，并尊重系统的减少动态效果设置。

目标用户是正在探索不同职业方向的学生和初入职场者，不限行业。核心任务是**收集同类岗位 → 整理样本 → 看共同要求及原文证据 → 按需对照简历**；页面内容包括长 JD、来源、样本频率、隐私和费用提示，因此设计优先考虑可读性、出处和操作状态，而不是装饰。用户第一次进入时会先看到一个**独立的全屏欢迎页**；只有点击“进入求职对照台”后，才会打开真正的工作区。欢迎页不是导航中的一个功能页面。工作区按实际使用顺序分成三个页面，右上方的“使用指南”点开后才显示简短说明：

1. **找岗位**：默认先展示“自动搜索（Offer岛）”，用户输入关键词、可选城市和用工类型即可找岗位；只有没有搜到或岗位来自 BOSS 等未接入来源时，才切换到“手动添加 JD”。Offer岛主要服务 AI 方向求职，所以**自动搜索无法覆盖所有行业**，这里也不爬取 BOSS 直聘。无论手动、逐条还是整页添加，成功后都停留在当前页面，方便连续收集。
2. **我的岗位**：岗位以卡片展示，可以勾选、全选、全不选或移除。完全相同的 JD 不会重复加入，避免把重复内容计入频率。操作区位于卡片列表上方；已选样本会显示岗位数、已知公司数和公司分布。
3. **分析中心**：以“岗位方向画像”为主功能，以“单岗位精读”为辅助功能。两种模式可以切换，但都必须由用户主动确认后才调用 DeepSeek。

岗位方向画像的推荐试用顺序：**开始收集岗位 → 搜索并加入 5～10 条相近岗位 → 在“我的岗位”勾选 → 点击“分析岗位方向” → 核对样本并生成画像**。模型负责归并同义要求并返回原文证据，Python 根据不同岗位 ID 计算 `出现岗位数 / 总岗位数`；页面不会展示内部 JSON，也不会把本次样本冒充整个行业。画像生成后，用户可以停止，也可以上传简历、检查遮盖后的文字，再主动发起第二次请求，获得面向这一岗位方向的准备建议。

画像和简历建议都可以下载为普通 TXT 报告，便于在会话结束前保存。报告保留样本范围、频率和原文证据，不导出内部 JSON，也不会在服务器上新建用户文件。

单岗位精读仍适合已经确定投递目标的情况：从勾选清单中确认一条 JD，上传并检查简历后，生成该岗位的匹配依据、未清楚体现的要求和下一步建议。系统不会默认逐条分析全部岗位，避免重复信息和不必要的模型费用。

**搜索、翻页、添加岗位、勾选、移除、选岗和本地提取简历文字都不会调用 DeepSeek。**每次模型请求前都会说明用途、要求用户勾选确认，并缓存相同输入的成功结果。公开测试保护默认限制每个浏览会话最多主动发起 8 次模型请求，可用 `MAX_MODEL_REQUESTS_PER_SESSION` 调整；刷新会话可以重置它，所以正式公开时仍必须同时在 API 平台设置余额和调用上限。

注意：扫描图片生成的 PDF 暂时无法提取文字；请上传能够选中文字的 PDF 或 DOCX。自动遮盖只能处理常见联系方式，**姓名、地址或特殊格式的敏感信息仍需自己删除**。不要把真实简历复制到项目目录或提交到 Git。岗位、简历文字和反馈目前只保存在当前浏览会话中，**不是永久保存**；公开测试前应先阅读部署说明中的费用与隐私限制。

匹配结果会要求模型给出 JD 与简历中的原文片段，程序会核对这些片段是否真的出现在原文中。这能减少凭空引用，但不能保证模型对经历的理解完全正确；重要建议请自己核对，也不要把“简历未体现”理解成“你不会”。这里不提供虚假的精确匹配分或录用概率。

匹配请求只要求少量最重要的建议，并关闭 DeepSeek 默认的思考模式，以减少内部结构化结果被截断的机会。程序不会因为模型返回不完整结果而自动再次调用 API；如出现错误，先看页面提示，不要连续点击，以免产生额外费用。

如果你之后有 Offer岛个人 API Key，可在本机 `.env` 添加 `OFFERDAO_API_KEY=你的Key`，但不要把它写进代码或提交到 Git。[Offer岛文档](https://offerdao.ai/docs)说明其 API 可用于查询并向用户推荐岗位，同时要求遵守[服务条款](https://offerdao.ai/terms)；本项目只做少量搜索和推荐，不批量抓取、转售内容。

代码分工仍然清楚：`job_sources.py` 查询岗位候选；`group_analyzer.py` 生成多岗位画像并进行方向级简历对照；`resume_reader.py` 在本地读简历；`matcher.py` 负责单岗位精读；`models.py` 校验所有内部结构；旧版由 `web_app.py` 和 `ui_config.py` 负责展示，新版由 `api_server.py` 和 `frontend/` 负责展示。`analyzer.py` 保留命令行单条 JD 结构化学习版。

## 怎样自己调整旧版 Streamlit 样式

以后想改版面时，优先打开 `ui_config.py`，不需要在长篇网页代码中到处寻找数字：

- `COLORS`：文字、背景、边框和主按钮颜色。
- `SIZES`：工作区宽度、上下留白、板块间距、卡片圆角、阴影、按钮高度和页面标题大小。
- `LANDING`：全屏欢迎页的宽度、主标题大小、主卡片内边距、圆角、入口按钮宽度和下方功能卡高度。
- `TYPOGRAPHY`：字体、正文大小与行高。
- `COLUMN_RATIOS`：页头、分页按钮、岗位卡片和操作区各列所占宽度。
- `COMPONENT_HEIGHTS`：JD 与简历文字框的高度。

例如，想让主工作区更宽，可以把 `SIZES["app_max_width"]` 从 `1180px` 改大；想让欢迎页标题更小，可以调低 `LANDING["landing_title_size"]`；想换主色，则修改 `COLORS["signal_dark"]`。保存后 Streamlit 会自动刷新。`ui_config.py` 只负责外观，不处理岗位、简历或 API 逻辑，所以改错样式数值也不会改变分析流程。

## 已上线的旧版

项目已经部署到 [Streamlit Community Cloud](https://ai-jd-analyzer-aashlks.streamlit.app/)：`web_app.py` 是入口，`requirements.txt` 声明依赖，`.streamlit/config.toml` 保存非敏感主题设置；真实密钥通过线上 Secrets 注入。完整的 GitHub 推送、Secrets、上线验收和紧急换 Key 步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。

发布后它仍是**公开测试版**，而不是已经具备账号、数据库和强制消费配额的正式 SaaS。右上方“访客模式 · 登录待开放”是未来账号入口的版面预留；当前每位用户的数据只存在自己的浏览会话中。

---

## 命令行基础版

第一步完成的基础功能是：粘贴一段招聘 JD，程序调用 LLM，最后输出固定字段的 JSON。起初字段偏向 AI 岗位；后来已改为各行业都适用的通用字段。**命令行仍显示 JSON，网页不显示**：网页把模型返回的结构化内容转成人能直接阅读的建议。

这个命令行程序仍保留一个小而完整的闭环：

```text
粘贴 JD → Python 读取文本 → 调用 DeepSeek API
       → 校验结构化结果 → 输出 JSON
```

当初先做这一步，是为了理解 Python、API 和 JSON；网页和简历匹配是在这个基础上逐步加入的。RAG 和数据库目前仍未加入。

## 你会学到什么

- Python 脚本怎样运行，`import`、函数和程序入口分别有什么作用
- API 怎样让本地程序调用云端 LLM
- JSON 为什么适合表达固定结构的数据
- `.env` 为什么适合保存 API Key
- Git 怎样记录版本，以及怎样避免提交密钥

## 项目结构

```text
ai-jd-analyzer/
├── main.py                 # 程序入口：读取 JD、处理错误、打印 JSON
├── analyzer.py             # 调用 LLM，并取得结构化分析结果
├── models.py               # 定义通用 JD 分析和简历反馈的 JSON 结构
├── web_app.py              # 旧版 Streamlit 网页、岗位清单和分析流程
├── api_server.py           # 新版 Vue 使用的 Python API 和静态页面入口
├── frontend/               # Ant Design Vue 页面、样式和 Vue Router
├── ui_config.py             # 可集中调节的颜色、尺寸、间距和列宽
├── job_sources.py          # 从 Offer岛 API 查询岗位候选
├── group_analyzer.py       # 多岗位方向画像与方向级简历对照
├── resume_reader.py        # 在本地读取 PDF/DOCX 简历
├── matcher.py              # 单岗位简历精读
├── report_export.py        # 把三类结果转成可下载的可读 TXT 报告
├── sample_jd.txt           # 可以直接复制使用的虚构示例 JD
├── sample_general_jd.txt   # 虚构的非技术岗位示例 JD
├── requirements.txt        # 项目需要安装的 Python 库
├── .env.example            # 环境变量模板，不含真实 Key
├── .gitignore              # 告诉 Git 不要记录哪些文件
├── .streamlit/
│   ├── config.toml         # 旧版部署和主题的基础设置
│   └── secrets.toml.example # 线上 Secrets 的安全格式示例
├── tests/
│   ├── test_analyzer.py    # API 分析逻辑的离线测试
│   ├── test_main.py        # 命令行输入输出的离线测试
│   ├── test_job_sources.py # 岗位来源的离线测试
│   ├── test_resume_reader.py # PDF/DOCX 文字提取测试
│   ├── test_matcher.py      # 简历匹配和证据核对测试
│   ├── test_group_analyzer.py # 多岗位画像和方向级对照测试
│   ├── test_report_export.py # 可读报告与安全文件名测试
│   ├── test_web_app.py      # 页面顺序、岗位卡片与勾选流程测试
│   ├── test_api_server.py   # 新版 HTTP 接口与费用确认测试
│   └── test_models.py      # 通用字段数据结构的离线测试
├── DEPLOYMENT.md           # 发布为可分享网页的逐步说明
└── README.md               # 你正在看的使用与学习说明
```

命令行的三个核心 Python 文件分工很简单：

- `main.py` 负责“和用户打交道”。
- `analyzer.py` 负责“和 DeepSeek API 打交道”。
- `models.py` 负责“规定结果长什么样”。

## 第 1 步：准备独立的 Python 环境

请先确认已经安装 Python 3.10 或更高版本：

```powershell
python --version
```

下面的命令以 Windows PowerShell 为例。先进入本项目目录，再运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

这三行分别表示：

1. 创建名为 `.venv` 的虚拟环境。
2. 激活它。
3. 在这个环境中安装项目依赖。

虚拟环境可以理解成“只属于当前项目的 Python 工具箱”，它不会把不同项目需要的库混在一起。

如果 PowerShell 不允许激活脚本，可以不激活，直接使用虚拟环境里的 Python：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

后续所有以 `python ...` 开头的命令，都相应改成以 `.\.venv\Scripts\python.exe ...` 开头。例如：

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 第 2 步：配置 API Key

先复制模板：

```powershell
Copy-Item .env.example .env
```

打开新生成的 `.env`，把占位符替换成自己的 Key：

```env
DEEPSEEK_API_KEY=your_real_deepseek_api_key
DEEPSEEK_MODEL=deepseek-flash
```

可以在 [DeepSeek API Key 页面](https://platform.deepseek.com/api_keys)创建 Key。API 调用可能产生费用，创建 Key 也不代表账户已经有可调用余额；可以在 [充值页面](https://platform.deepseek.com/top_up)按需充值。

安全规则：

- 不要把真实 Key 写进 Python 文件。
- 不要把 `.env` 发给别人、截图公开或上传到 GitHub。
- `.env.example` 只有变量名和占位符，可以安全提交。
- `.gitignore` 已经忽略 `.env`，但提交前仍要用 `git status` 再确认一次。
- 如果 Key 泄露，应立即在平台撤销旧 Key 并创建新 Key。

默认模型是 `deepseek-flash`，它支持 JSON Output，适合这类轻量文本提取任务。如果后续要换模型，只需修改 `.env` 中的 `DEEPSEEK_MODEL`。

## 第 3 步：运行程序

```powershell
python main.py
```

程序出现提示后：

1. 粘贴完整 JD，可以包含多行和空行。
2. 粘贴完后另起一行，只输入 `END`。
3. 按回车，等待 JSON 结果。

你可以先复制 `sample_jd.txt` 的内容试运行。

## 输出示例

实际内容由输入的 JD 决定，结构会保持一致：

```json
{
  "job_title": "内容运营专员",
  "company": "示例公司",
  "employment_type": "正式",
  "location": "武汉",
  "responsibilities": ["策划并发布内容", "跟踪内容效果"],
  "required_skills": ["文案写作", "数据复盘"],
  "other_requirements": [],
  "education_requirement": "本科及以上",
  "experience_requirement": "1 年以上相关经验",
  "work_schedule": "未提及",
  "bonus_points": ["有行业账号运营经验"]
}
```

字段名使用 Python 常见的英文 `snake_case` 写法：

| JSON 字段 | 含义 | 数据类型 |
|---|---|---|
| `job_title` | 岗位名称 | 字符串 |
| `company` | 公司 | 字符串 |
| `employment_type` | 实习、正式等用工类型 | 字符串 |
| `location` | 工作地点 | 字符串 |
| `responsibilities` | 工作职责 | 列表 |
| `required_skills` | 要求的专业或通用能力 | 列表 |
| `other_requirements` | 资格、语言、出差等其他要求 | 列表 |
| `education_requirement` | 学历要求 | 字符串 |
| `experience_requirement` | 经验要求 | 字符串 |
| `work_schedule` | 工作安排、出勤和时长 | 字符串 |
| `bonus_points` | 加分项 | 列表 |

提示词要求模型只提取 JD 中明确写出的信息：缺失的字符串字段应返回 `"未提及"`，缺失的列表字段应返回 `[]`。无论是技术、运营、设计还是其他岗位，都用相同结构；有明确出勤或实习时长时，`work_schedule` 应保留全部条件。结构校验能保证字段和数据类型正确，但不能保证模型没有遗漏信息；重要结果仍应人工核对。

## 理解 Python 脚本

可以把 Python 文件想成一份菜谱，Python 解释器按顺序执行其中的步骤。

- `import`：使用别人已经写好的工具。
- 变量：给一份数据取名字，例如 `jd_text`。
- 函数：把一组操作封装成可重复使用的步骤。
- 参数：函数接收的数据。
- 返回值：函数完成后交回的数据。
- `python main.py`：让 Python 解释器执行 `main.py`。
- `if __name__ == "__main__":`：表示只有直接运行这个文件时，才从这里启动程序。

阅读代码时建议按真实运行顺序：

1. `main.py` 的最后一行调用 `main()`。
2. `load_dotenv()` 从 `.env` 加载配置。
3. `read_jd()` 读取你的多行输入。
4. `analyze_jd()` 把输入交给 API。
5. `JobAnalysis` 检查返回结果是否具备全部字段。
6. `json.dumps()` 把 Python 数据格式化成 JSON 并打印。

## 理解 API

API 可以理解成两个程序之间约定好的“点单窗口”：

- API Key：证明调用者有权限。
- 请求：本地 Python 程序发送模型名称、提取规则和 JD。
- 响应：云端 LLM 返回分析结果。
- 错误：网络、Key、额度或服务状态有问题时，请求可能失败。

本项目使用 DeepSeek 的 Chat Completions API 和 JSON Output。`analyzer.py` 通过兼容的 OpenAI Python SDK 把请求发送到 `https://api.deepseek.com`，要求模型返回 JSON，再由 `JobAnalysis` 校验 11 个通用字段和数据类型。内容本身是否准确，仍需结合原 JD 判断。实现方式依据 [DeepSeek API 快速开始](https://api-docs.deepseek.com/)和 [JSON Output 指南](https://api-docs.deepseek.com/guides/json_mode/)。

隐私提醒：不要把带有个人手机号、私人邮箱、未公开公司资料等敏感内容的 JD 直接发送给外部 API。

## 理解 JSON

JSON 是一种人和程序都比较容易阅读的数据格式。

- `{}` 表示一个对象。
- `"job_title"` 是键，表示字段名称。
- `"内容运营专员"` 是字符串值。
- `[]` 表示列表，适合保存多个技能。
- JSON 使用双引号，最后一项后面不能多写逗号。

固定的 JSON 结构很重要：后续做统计、存数据库或接网页界面时，都能直接按字段读取数据，不需要重新理解一整段自然语言。

## 理解 `.env` 和环境变量

可以把代码看作可分享的菜谱，把 API Key 看作家门钥匙。菜谱可以公开，钥匙必须留在本地。

`python-dotenv` 的 `load_dotenv()` 会读取 `.env`，把其中的设置放进当前程序的环境变量。`analyzer.py` 用 `DEEPSEEK_API_KEY` 连接 DeepSeek，并读取 `DEEPSEEK_MODEL` 选择模型。项目继续使用 `openai` Python 库，是因为 DeepSeek 官方提供了与它兼容的接口格式。

三个相关文件的区别：

- `.env`：保存真实配置，只留在本机。
- `.env.example`：告诉别人需要哪些配置，不含秘密。
- `.gitignore`：告诉 Git 不要跟踪 `.env` 和 `.venv`。

## 理解 Git

Git 像项目的存档系统。每完成一个小功能，就可以保存一个带说明的版本。

项目已经初始化为 Git 仓库。第一次练习可以依次执行：

```powershell
git config user.name "你的名字"
git config user.email "you@example.com"
git status
git check-ignore -v .env
git add .
git status
git commit -m "feat: generalize JD and resume analysis"
git log --oneline
```

- 两条 `git config`：只为当前仓库设置提交作者信息，不是 GitHub 密码。把示例内容换成自己的名字和邮箱。
- `git status`：查看哪些文件发生变化。第一次执行时，请确认列表里没有 `.env`。
- `git check-ignore -v .env`：确认 `.env` 确实被忽略，并显示是哪条规则生效。
- `git add .`：选择当前目录里的变化，准备保存。
- 第二次 `git status`：再次核对即将保存的内容。
- `git commit`：创建一次带说明的项目存档。
- `git log --oneline`：查看历史存档。

注意：如果秘密文件已经被 Git 跟踪，后来再把它写进 `.gitignore` 并不能清除历史记录，所以一定要在第一次提交前检查。

## 运行离线测试

测试使用假的 API 客户端，不需要真实 Key，也不会产生 API 费用：

```powershell
python -m unittest discover -s tests -v
```

这些测试确认：

- 多行输入能正确读取，空行不会提前结束。
- 结果模型必须包含全部 11 个通用字段，并拒绝未知字段。
- 空 JD 会在发送 API 请求之前被拒绝。
- 模型配置和 JD 会正确传给分析层。
- 模型输出中断、拒绝或没有结构化结果时会报告可读错误。
- 最终输出能被当作真正的 JSON 读取。
- 缺少 API Key 时会显示清楚的提示。

## 常见问题

### `ModuleNotFoundError`

通常是依赖还没安装，或当前没有使用项目虚拟环境。重新执行：

```powershell
python -m pip install -r requirements.txt
```

### 提示找不到 `DEEPSEEK_API_KEY`

确认文件名是 `.env`，而不是 `.env.txt`；确认它位于 `main.py` 同一目录；确认变量名没有拼错。

### 401 或“API Key 无效”

检查 Key 是否复制完整、是否已经撤销。不要在聊天或公开截图中发送 Key。

### 429 或“额度不足”

检查 API 平台的用量与额度，或稍后重试。

### 无法连接 API

检查网络连接后再试。程序不会在错误信息中打印你的完整 Key 或 JD。

## 命令行验收清单

- [ ] 能创建虚拟环境并安装依赖。
- [ ] 能运行 `python main.py`。
- [ ] 能粘贴一段 JD，并用 `END` 结束输入。
- [ ] 能看到 11 个通用字段的 JSON。
- [ ] 能对照原 JD 人工核查结果，并理解结构校验不等于事实校验。
- [ ] 能运行全部离线测试。
- [ ] `git status` 中没有 `.env`。
- [ ] 能用自己的话解释 Python 脚本、API、JSON、环境变量和 Git。

## 三个小练习

1. 分别输入一份运营 JD 和一份技术 JD，观察 `required_skills` 如何变化。
2. 输入一份没有公司名的 JD，检查 `company` 是否为“未提及”。
3. 尝试在 `models.py` 中新增 `salary` 字段，并思考提示词和输出示例还需要改哪里。

## 面试时可以这样介绍

> 我做了一个面向所有行业的岗位方向分析网页。它以多份同类 JD 为主要输入，把语义相近的要求归并后，再由 Python 按不同岗位计算出现频率，并保留每项结论对应的岗位原文；用户也可以精读某一个岗位，或在确认脱敏文字后把简历与岗位方向对照。网页只展示可读报告，JSON 留在程序内部做结构校验。模型证据还会再次与原文核对，密钥在本地使用 `.env`、线上使用 Streamlit Secrets，均不会提交到 Git。当前是具备部署条件的公开测试版，数据只保留在浏览会话中，登录、数据库和更严格的账户配额是下一阶段能力。
