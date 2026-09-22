# 把求职对照台发布为可分享网页

> 本文只适用于已经上线的 **Streamlit 旧版**（入口 `web_app.py`）。新设计的 Ant Design Vue 页面需要 `api_server.py` 提供 Python ASGI 接口，目前只完成本地预览；把仓库推送到 GitHub 不会让 Streamlit Cloud 自动改用 Vue 页面，也不要把新 API 不加配额保护就公开发布。

推荐先用 **Streamlit Community Cloud** 发布测试版。当前项目已经具备入口文件、依赖清单、主题配置和会话隔离；发布后每位访客可以独立收集岗位并生成分析，但刷新或关闭会话后数据可能消失。

## 发布前先知道三件事

1. 访客点击生成画像或简历建议时，会使用站点维护者配置的 DeepSeek Key，费用由该账号承担。
2. 页面里的“每会话请求上限”只能减少误点，刷新浏览器可能重新开始计数，**不能替代 DeepSeek 平台端的余额、限额和用量监控**。
3. 当前版本没有用户账号和数据库，适合小范围公开测试，不适合保存长期求职记录。

## 1. 本地验收

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run web_app.py
```

浏览器里至少走一遍以下流程：

- 首页 → 找岗位 → 添加两条以上同类 JD；
- 我的岗位 → 勾选岗位 → 分析岗位方向；
- 在不点击“生成岗位方向画像”的情况下，确认样本和费用提示正确；
- 如要做真实 API 验收，只调用一次，并检查 DeepSeek 控制台用量。

## 2. 第一次保存到 Git

真实 `.env` 和 `.streamlit/secrets.toml` 都不应进入 Git。先确认忽略规则：

```powershell
git check-ignore -v .env
git check-ignore -v .streamlit/secrets.toml
git status --short
```

如果这是第一次提交，需要先设置当前仓库的作者信息，再提交：

```powershell
git config user.name "你的名字"
git config user.email "你的邮箱"
git add .
git status
git commit -m "feat: build job direction analysis web app"
```

第二次 `git status` 时再次确认没有 `.env`、真实简历或其他私人文件。

## 3. 推送到 GitHub

在 GitHub 新建一个空仓库，不要额外生成 README、`.gitignore` 或 License。然后把页面给出的仓库地址替换到下面命令：

```powershell
git remote add origin https://github.com/你的账号/你的仓库.git
git push -u origin main
```

公开仓库最容易部署；私有仓库也可以，但需要给 Streamlit 相应的 GitHub 访问权限。项目代码可以公开，真实 Key 绝不能公开。

## 4. 在 Streamlit Community Cloud 创建应用

1. 打开 [share.streamlit.io](https://share.streamlit.io/) 并连接 GitHub。
2. 点击 **Create app**，选择刚才的仓库和 `main` 分支。
3. Entrypoint file 填写 `web_app.py`。
4. Python 版本优先选择与本地相同的版本；本项目当前在 Python 3.13 上完成测试。如果平台没有该版本，可选择受支持的较新版本并重新查看构建日志。
5. 打开 **Advanced settings**，在 Secrets 中填写下面内容，把占位符换成真实值：

```toml
DEEPSEEK_API_KEY = "你的真实 DeepSeek Key"
DEEPSEEK_MODEL = "deepseek-flash"
MAX_MODEL_REQUESTS_PER_SESSION = "8"
OFFERDAO_API_KEY = ""
```

不要上传本地 `.env`。Community Cloud 的根级 Secrets 会作为环境变量提供给应用，因此现有代码无需改写。

6. 点击 Deploy。成功后会得到一个 `*.streamlit.app` 地址，可发给测试用户。

官方依据：

- [部署应用](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [文件与依赖组织](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
- [Community Cloud Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Streamlit Secrets 原理](https://docs.streamlit.io/develop/concepts/connections/secrets-management)

## 5. 上线后的冒烟测试

使用一个新的无痕浏览器窗口检查：

- 页面默认进入首页，蓝白样式与四个导航入口正常；
- “隐私与费用”能说明 Offer岛、DeepSeek、保存方式和费用承担；
- 自动搜索失败时仍可切换到手动添加，不会阻断主流程；
- 相同 JD 不会重复加入，移除、全选、全不选和页面切换正常；
- 多岗位画像要求 2～10 条，少于 5 条时出现样本警告；
- 生成前必须勾选确认，生成后展示的是可读报告而不是 JSON；
- 三种分析结果都能下载为可读 TXT，文件名不包含系统非法字符；
- 真实模型请求只做一次，并在 DeepSeek 控制台核对用量；
- 另一台设备看不到上一位用户的会话数据。

## 6. 日常更新与紧急处理

修改代码并通过测试后：

```powershell
git add .
git status
git commit -m "描述这次修改"
git push
```

Community Cloud 会从 GitHub 重新部署。若 Key 疑似泄露，先在 DeepSeek 撤销旧 Key，再到 Streamlit 应用 Settings → Secrets 更新新 Key；不要只删除本地文件，因为已经提交过的 Git 历史仍可能保留秘密。

如果公开测试人数增加，下一阶段应优先补充：真正的登录与数据库、服务端账户级配额、隐私政策与数据删除机制、稳定且覆盖更多行业的授权岗位来源。它们不应伪装成当前版本已经具备的能力。
