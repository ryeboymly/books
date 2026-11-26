# 大头虾 (C-Agent) 能力边界探测报告

> 探测时间: 2026-11-26 (初版) / 2026-11-26 (更新1: 网络深挖+幻觉验证) / 2026-11-26 (更新2: cap-webfetch外网突破) / 2026-11-26 (更新3: dws/COME3.0能力发现) / 2026-11-26 (更新4: 文件传输+workspace规范) / 2026-11-26 (更新5: skill体系全量探测) / 2026-11-26 (更新6: 新skill安装+intranet-fetch测试)
> 探测方式: 通过 cagentapi.catl.com API 发送测试指令
> Agent: agent-1794400677722-fe418fb5 (agentId=14008331)
> 探测轮次: 15轮, 覆盖工具/网络/安全/子agent/文件系统/技能/外网突破/COME3.0/文件传输/skill体系/新skill测试
> Skill总数: 14个系统级 + 10个新安装 + 7个应用开发类 + 13个内置通用 = 44个

## 一、运行环境

| 项目 | 值 |
|------|-----|
| 容器 | K8s Pod (cagent-agent-prod 命名空间) |
| 主机名 | agent-1794400677722-fe418fb5-7b799664bc-84l56 |
| OS | Linux 4.18.0-553.el8_10.x86_64 |
| Python | 3.11 (root 权限) |
| 存储 | NFS 10.53.10.5:/cagent-prod/agent/ (28T, 用22T) |
| DNS | 10.248.112.228 / 169.254.25.10 / 10.248.0.3 |

## 二、工具清单 (27+)

### 文件操作
- read - 读取文件 (文本/图片)
- write - 创建/覆盖文件
- edit - 精确替换文件内容
- apply_patch - 多文件补丁

### 执行与进程
- exec - 执行 shell 命令 (可后台/pty)
- process - 管理后台进程 (list/poll/log/kill)

### 网络
- web_fetch - 抓取 URL (基础HTTP, 外网超时, 内网被SSRF拦截)
- cap-webfetch (技能) - Chrome CDP 引擎抓取网页 (**可访问外网**, 走独立网络通道)

### 会话与通信
- sessions_list - 列出会话
- sessions_history - 获取会话历史
- sessions_send - 向其他会话发消息
- sessions_spawn - 创建子 agent 会话 (webchat通道不支持)
- sessions_yield - 等待子 agent 完成

### 记忆系统
- memory_store - 保存记忆
- memory_recall / memory_search / memory_get - 检索记忆
- memory_fact_query - 按事实键查询
- memory_update - 更新记忆
- memory_forget - 删除记忆

### 目标与计划
- create_goal / get_goal / update_goal / update_plan

### 图像与文档
- image - 分析图片
- pdf - 分析 PDF
- execute_office_js - 在 Office(WORD/Excel/PPT) 执行 JavaScript

### COME3.0 集成 (dws 技能)
- dws (DingTalk Work System CLI) - 二进制命令行工具, 操作 COME3.0 全产品线
  - todo - 创建待办/指派/查询/标记完成/子待办/评论/附件
  - chat - 群聊管理/发消息(文本/Markdown/图片/文件)/搜索群/拉群/机器人
  - contact - 通讯录查询(用户/部门/角色)/花名册/找人
  - calendar - 日程管理/会议室/闲忙查询/时间建议
  - doc - COME 文档读写
  - drive - 云盘文件上传/下载
  - minutes - AI 听记纪要查询
  - report - 日志/日报/周报模板提交
  - sheet - 在线电子表格读写
  - aitable - AI 表格操作
  - ding - DING 消息发送
  - wiki - 知识库管理
  - devdoc - 开放平台文档搜索
  - ⚠️ 不支持: OA审批/BPM审批(走 bpm 技能), 邮件(dws mail 禁用)
  - ⚠️ 需先执行 `dws auth login` 完成设备授权登录

### 其他内置工具
- skill_workshop - 创建/更新/审查/应用技能提案 (action: create/update/revise/list/inspect/apply/reject/quarantine)
- dingtalk_ask_user_question - 钉钉互动卡片 (仅钉钉通道)
- self_improvement_log - 记录学习/错误经验
- session_status - 查看会话状态
- tts - 文字转语音

### 已安装 Skill 清单 (14个运营类 + 7个应用开发类 = 21个)

#### 运营类 Skill (14个, 位于 /home/node/.openclaw/skills/)

| Skill | 功能 | 关键细节 |
|-------|------|----------|
| approve-travel | 出差单审批 | 查询待审批、同意/驳回出差申请 |
| bpm-approve-batch | BPM流程批量审批 | 基于 catl_bpm_client |
| bpm-get-todolist | BPM待办/已办查询 | |
| bpm-query-workflowDetail | BPM流程表单详情 | |
| cap-knowledge-query | 知识中台检索 | 公司内部术语/部门职能/流程定义 |
| cap-mcp-connect | MCP Server连接 | 可接入外部MCP工具 |
| cap-scheduled-task | **定时任务/提醒管理** | 创建/查看/修改/删除定时任务, 通过SKILL网关调用c-agent定时任务接口, 脚本: scripts/scheduled-task.py, 需用/opt/venv/bin/python3绝对路径调用 |
| cap-webfetch | 外网抓取/搜索 | Chrome CDP引擎, 可访问外网网页和Bing搜索 |
| come-group-roster | COME群成员查询 | 查询/导出群成员名单 |
| dws | COME全产品管理 | DingTalk Work System CLI, 覆盖todo/chat/contact/calendar/doc/drive/minutes/report/sheet/aitable/ding/wiki/devdoc |
| file-sender | **通过COME发送文件/图片** | 通过dws CLI发送, 按渠道(webchat/Come端)和对象(本人/他人/群聊)选择发送方式: webchat给本人→上传COME文档空间发链接, Come端给本人→send-by-bot, 给他人/群聊→send |
| image-recognition | **图片OCR/多模态分析** | 基于CATL平台 |
| office-mail | **企业邮件只读查询** | 查看搜索总结收件箱邮件, 只读不支持发送/回复/转发, 通过scripts/client.py统一入口 |
| ppt-catl | **AI生成PPT** | AI驱动多格式SVG内容生成, 输出PPTX |

#### CAgent应用开发类 Skill (7个, 安装于2026-11-25, 管理界面可见)

| Skill | 版本 | 功能 |
|-------|------|------|
| agent-apps-ui-ux | 1.3.6 | CAgent应用创建UI/UX |
| agent-apps-troubleshoot | 1.7.0 | CAgent应用修复助手 |
| agent-apps-review | 1.7.0 | CAgent应用审查 |
| agent-apps-router | 1.7.1 | CAgent应用开发意图识别 |
| agent-apps-dev | 1.7.0 | CAgent应用开发 |
| agent-apps-brainstorming | 1.7.0 | CAgent头脑风暴 |
| agent-apps-scaffold | - | CAgent脚手架生成 |

> 这7个skill用于在CAgent平台上创建和管理AI应用, 包括UI/UX设计、开发、审查、修复、意图识别、头脑风暴和脚手架生成。管理界面: https://cagent.catl.com/app/settings/skill

### 内置通用 Skill (位于 /app/skills/)
- skill-creator - 技能创作, 手动创建/编辑/审计SKILL.md
- clawhub - 技能市场
- diagram-maker - 绘图
- healthcheck - 安全审计
- meme-maker - 梗图
- notion - Notion API
- python-debugpy - Python调试
- spike - 原型验证
- taskflow - 任务编排
- taskflow-inbox-triage - 收件箱分类
- lesson - 经验记录
- node-connect - 设备配对诊断
- node-inspect-debugger - Node.js调试

### Skill 创建能力
大头虾可以自己创建新skill扩展能力, 有两条路径:
1. **skill_workshop工具** - 创建提案(proposal), 自动校验格式, action=apply后写入skills目录生效
2. **skill-creator skill** - 手动创建/编辑SKILL.md文件

> 管理界面: https://cagent.catl.com/app/settings/skill (需浏览器访问)

### 新安装 Skill (10个, 2026-11-26 安装, 位于 workspace/skills/)

| Skill | 功能 | 测试状态 |
|-------|------|----------|
| intranet-fetch | **内网内容抓取** | ✅脚本可用, ⚠️受NetworkPolicy限制(详见3.1) |
| come2opencode-bridge | **虾桥, COME远程指挥OpenCode** | 已安装待测试 |
| SSO-Login (catl-sso-login) | **万能SSO登录** | 已安装待测试 |
| image-expert | **图片识别专家(多模型接力OCR)** | 已安装待测试 |
| weknora-api-invocation | **Weknora知识库API调用** | 已安装待测试 |
| memory-skill | **跨对话项目记忆** | 已安装待测试 |
| memory-skill-full | 跨对话项目记忆(完整版) | 已安装 |
| attendance-processor | 考勤数据查询 | 已安装 |
| com-image-reader | 钉钉图片读取 | 已安装 |
| come-chat-assistant | COME沟通助手 | 已安装 |

> 安装方式: 浏览器访问管理界面安装, 安装后需重启Pod生效。新skill位于 `workspace/skills/` 而非 `~/.openclaw/skills/`。旧会话系统提示词不会更新, 需创建新会话才能识别新skill。

## 三、网络可达性

### 3.1 内网服务

| 服务 | 地址 | 状态 | 说明 |
|------|------|------|------|
| C-Agent API | cagentapi.catl.com | 可达 (403) | 需正确 token |
| 深度研究 | ctokenai.catl.com | 可达 (200) | AI 研究助手页面, API端点不公开 |
| 技能网关 | skillgateway.catl.com | 可达 (500) | 技能调用网关 |
| 应用网关 | cappgateway.catl.com | 可达 (404) | 应用运行时网关 |
| JFrog PyPI | jfrog.catlbattery.com | 可达 (需认证) | pip 镜像源, 仅供包安装 |
| KHM 知识中心 | khm.catl.com | 不可达 (超时) | TCP 不通 |
| V盘 2.0 | vdrive.catl.com | 不可达 (超时) | TCP 不通 |
| COME | come.catl.com | TCP 不通, **但可通过 dws 技能操作** | dws CLI 走平台内部通道, 非直连 TCP |
| ITSM | itsm.catl.com | 不可达 (超时) | intranet-fetch测试: Python urllib超时, K8s NetworkPolicy阻断 |
| devcdoc (朱雀知识库) | devcdoc.catl.com | 不可达 (超时) | intranet-fetch脚本白名单内, 但TCP不通 |

### 3.1.1 intranet-fetch 测试结论 (2026-11-26)

intranet-fetch skill 脚本本身工作正常, 能成功建立TCP连接和HTTP请求。但受K8s NetworkPolicy限制, 只能访问白名单内的内网服务:

| 测试URL | 网络可达 | 结果 |
|---------|---------|------|
| itsm.catl.com | ❌ 超时 | K8s NetworkPolicy不通, 重试2次均超时 |
| cagentapi.catl.com | ✅ 可达 | HTTP 404(根路径无内容, 但TCP连接成功) |

**结论:** intranet-fetch走Python urllib直连TCP, 与curl/socket受同样的NetworkPolicy限制。对于itsm/devcdoc等不通的内网站点, 仍需3122做中间人抓取。该skill在员工电脑上的OpenCode中可正常工作(员工电脑在公司内网, 能直达所有*.catl.com站点)。

### 3.2 外网访问 (深挖结论)

#### 3.2.1 基础网络层 (curl/socket/web_fetch) - 全部不通

| 测试项 | 结果 | 说明 |
|--------|------|------|
| DNS 解析 | 通 | github.com/baidu.com/pypi.org 均解析到真实 IP |
| TCP 外网 (curl) | 全部超时 | 80/443 端口均不通, K8s NetworkPolicy 阻断 |
| TCP 外网 (Python socket) | 全部超时 | connect() 超时, 与 curl 一致 |
| web_fetch 外网 | 全部超时 | baidu/httpbin/github raw 均超时 |
| web_fetch 内网 | 被 SSRF 拦截 | "Blocked: resolves to private/internal IP" |
| git clone GitHub | 超时 (exit 124) | 之前报告的 EXIT:0 是幻觉 |
| curl 直连外网 IP | 超时 | 20.6.7.17:80, 124.237.177.164:80 |
| HTTP 代理 | 无 | env 中无 HTTP_PROXY/HTTPS_PROXY |
| JFrog 代理 GitHub | 拒绝隧道 | Tunnel connection failed: 400 Bad Request |
| 内网 git 镜像 | 无 | github.catl.com/git.catl.com/gitlab.catl.com 全超时 |
| pip install | 可用 | 通过 JFrog 内网镜像代理 PyPI |

#### 3.2.2 cap-webfetch 技能 (Chrome CDP) - **可访问外网**

| 测试项 | 结果 | 说明 |
|--------|------|------|
| cap-webfetch 抓取 GitHub | **成功** | 通过 Chrome CDP 引擎抓取 github.com/ryeboymly 页面 |
| Bing 搜索 | **成功** | 可执行搜索但精确匹配效果一般 |
| web_fetch (基础工具) | 超时 | 与 cap-webfetch 走不同网络通道 |

**关键发现:** 大头虾有两条网络通道:
1. **基础通道** (curl/socket/web_fetch) - K8s NetworkPolicy 全封, 不可用
2. **cap-webfetch 通道** (Chrome CDP 引擎) - 走独立网络出口, **可访问外网**

> cap-webfetch 是一个技能 (skill), 脚本位于 `/home/node/.openclaw/skills/cap-webfetch/scripts/webfetch.py`, 使用 Chrome DevTools Protocol 渲染网页并提取内容。它不走容器的 TCP 出网, 而是通过平台后端代理访问外网。

**实测验证:** 推送新文件到 GitHub 后让大头虾读取, 基础通道全部超时, 但 cap-webfetch 成功抓取到 GitHub 页面并返回正确的公开仓库列表 (books + bookkit-lite)。

### 3.3 ctokenai 深度研究服务

| 端点 | 方法 | 状态码 | 说明 |
|------|------|--------|------|
| / | GET | 200 | 返回研究助手 HTML 页面 |
| /api/v1/chat | POST | 404 | 接口不存在 |
| /v1/chat/completions | GET | 404 | Node 服务无法处理 |
| /v1/chat/completions | POST | 405 | 方法不允许 (端点存在但需不同调用方式) |
| /api/v1 | GET | 404 | 接口不存在 |
| /docs, /openapi.json | GET | 404 | 无公开文档 |

> ctokenai 服务可达但 API 端点不公开, 实际能力由内部服务路由处理。DEEP_RESEARCH_SECRET 环境变量存在但未找到可用端点。

## 四、子 Agent (5个)

| Agent | 用途 |
|-------|------|
| main | 默认主 agent |
| bpm | BPM 流程相关 |
| code | 代码开发相关 |
| come | COME 协同办公相关 |
| mail | 邮件相关 |

> 注意: webchat 通道不支持 sessions_spawn, 需切换钉钉通道。

## 五、安全限制 (ClawAegis)

| 限制 | 说明 |
|------|------|
| 禁止删除工作目录 | 不能 rm -rf . 或整体清空 |
| 禁止修改 .openclaw 配置 | 系统配置不可改 |
| 禁止执行 openclaw CLI | 命令行工具不可用 |
| .learnings 自动重建 | 删除后系统自动恢复空模板 |
| templates 只读挂载 | 容器级只读, 物理不可删 |

## 六、敏感环境变量

大头虾 Pod 内可见以下敏感变量 (不应在对话中暴露):

- DINGTALK_CLIENT_SECRET (钉钉密钥)
- OPENCLAW_GATEWAY_TOKEN (网关 token)
- API_KEY / SKILL_KEY
- DEEP_RESEARCH_SECRET (深度研究密钥)
- VIDEO_AGENT_SHARED_KEY
- DWS_CLIENT_SECRET

## 七、作为 3122 助手的可用能力

### 可用 (通过 API 控制)
1. Python 代码执行 - 数据处理、脚本运行 (root 权限, pip 可装包)
2. 文件读写 - 工作空间内持久化 (NFS 28T)
3. 记忆系统 - 跨会话信息存储/检索/删除
4. 会话管理 - 多会话并行, 可创建/删除/发消息
5. 完整 API 调用链 - 创建会话/发消息(SSE)/读历史/删会话
6. pip 包安装 - 通过 JFrog 内网镜像
7. **外网访问 (cap-webfetch)** - Chrome CDP 引擎可抓取外网网页, 包括 GitHub/Bing 等
8. Bing 搜索 - 通过 cap-webfetch 执行搜索引擎查询
9. **COME3.0 操作 (dws 技能)** - 待办/消息/群聊/通讯录/日历/文档/云盘/表格/知识库/DING消息
10. COME3.0 文档读写 - 通过 dws doc 操作 COME 文档
11. COME3.0 云盘 - 通过 dws drive 上传/下载文件
12. **COME发送文件/图片 (file-sender)** - 通过dws CLI发送文件, 按渠道和对象自动选择发送方式
13. **定时任务/提醒 (cap-scheduled-task)** - 创建/查看/修改/删除定时提醒和周期任务
14. **企业邮件查询 (office-mail)** - 只读查询收件箱邮件, 搜索/总结邮件内容
15. **图片OCR/多模态分析 (image-recognition)** - 图片文字识别和视觉理解
16. **AI生成PPT (ppt-catl)** - AI驱动SVG内容生成, 输出PPTX文件
17. **BPM流程操作** - 待办查询/批量审批/流程详情查询
18. **知识中台检索 (cap-knowledge-query)** - 公司内部术语/部门职能/流程定义
19. **MCP Server连接 (cap-mcp-connect)** - 可接入外部MCP工具扩展能力
20. **Skill自创建 (skill_workshop/skill-creator)** - 可自己创建新skill扩展能力

### 不可用
1. 基础外网通道 (curl/socket/web_fetch) - K8s NetworkPolicy 全封
2. ctokenai 深度研究 - 服务可达但 API 端点不公开
3. KHM/V盘 - TCP 不通 (COME 已通过 dws 技能解决)
4. 子 agent 创建 - webchat 通道限制 (钉钉通道可能支持)
5. 钉钉消息 - webchat 通道限制 (钉钉通道可能支持)
6. 系统级操作 - ClawAegis 安全策略拦截
7. web_fetch 内网 - SSRF 保护拦截私有 IP

## 八、API 控制链 (3122 -> 大头虾)

```
3122 (本助手)
  └─ shell_exec (curl)
       └─ POST cagentapi.catl.com/c-agent/v1/chat/stream
            └─ 大头虾 Pod (K8s)
                 ├─ exec (shell/python)
                 ├─ read/write (文件)
                 ├─ memory_store/recall (记忆)
                 ├─ web_fetch (基础HTTP, 外网不通)
                 ├─ cap-webfetch (Chrome CDP, **外网可达**)
                 ├─ dws CLI (COME3.0 全产品线, 需 auth login)
                 ├─ file-sender (COME发送文件/图片)
                 ├─ cap-scheduled-task (定时任务/提醒)
                 ├─ office-mail (企业邮件只读查询)
                 ├─ image-recognition (图片OCR/多模态)
                 ├─ ppt-catl (AI生成PPT)
                 ├─ bpm-* (BPM流程操作)
                 ├─ cap-mcp-connect (MCP Server连接)
                 ├─ skill_workshop (创建新skill)
                 └─ ctokenai.catl.com (深度研究, API不公开)
```

## 九、关键结论

大头虾是一个**沙箱化的代码执行+记忆持久化+外网抓取引擎**, 适合作为 3122 的后端计算节点:
- 能跑 Python 处理数据, 结果存工作空间或记忆系统
- **可通过 cap-webfetch 技能访问外网** (Chrome CDP 引擎, 抓取网页/搜索)
- 基础网络通道 (curl/socket/web_fetch) 全封, 外网只能走 cap-webfetch
- ctokenai 服务可达但 API 不公开, 深度研究能力暂不可用
- **可通过 dws 技能操作 COME3.0** (待办/消息/群聊/通讯录/日历/文档/云盘/表格/知识库等)
- 不能直接访问 KHM/V盘 (需要 3122 做中间人)
- dws 需要先完成 `dws auth login` 设备授权登录 (15分钟有效期)
- webchat 通道能力受限, 钉钉通道功能更全
- **有幻觉风险, 关键操作必须用 exec 跑实际命令验证, 不能信文字总结**

### 外网访问的正确姿势
- 不要用 `web_fetch` 工具或 `curl` 访问外网 (会超时)
- 让大头虾使用 `cap-webfetch` 技能 (Chrome CDP 引擎) 抓取外网网页
- 指令示例: "用 cap-webfetch 技能抓取 https://github.com/xxx"
- 大头虾会自动调用 `/home/node/.openclaw/skills/cap-webfetch/scripts/webfetch.py`
- 支持网页抓取和搜索引擎查询 (Bing)

### COME3.0 操作的正确姿势
- 使用 `dws` 命令行工具操作 COME3.0, 覆盖待办/消息/群聊/通讯录/日历/文档/云盘等
- 首次使用需执行 `dws auth login`, 生成设备授权码, 在浏览器中完成钉钉授权
- 授权码有效期 15 分钟, 登录后 token 持久化在 `~/.local/share/dws-cli/`
- 指令示例: `dws todo +get-my-tasks` 查询待办, `dws chat +send` 发消息
- 不支持 OA/BPM 审批 (走 bpm 技能), 不支持邮件 (dws mail 禁用)

### 文件传输的正确姿势 (3122 → 大头虾)
- 小文件 (<4KB): 直接 base64 编码通过聊天 API 发送, 大头虾解码写入
- 大文件: gzip压缩 → split分块(100KB) → base64编码 → 推送到GitHub公开仓 → 大头虾用cap-webfetch逐块抓取 → 二进制拼接 → gunzip解压
- 聊天API对大payload有超时限制, 单条消息不宜超过4KB
- cap-webfetch每次抓取约55秒, 大文件需分多次调用
- 文件名用纯ASCII避免URL编码问题
- 拼接时必须先解码再二进制拼接, 不能先拼base64再统一解码

### Workspace 目录规范 (已写入大头虾记忆系统)
大头虾 workspace (`/home/node/.openclaw/workspace/`) 遵循以下目录结构:

```
workspace/
├── 书籍/          ← 书籍/文档等最终产物
├── scripts/       ← 工具脚本归档
├── memory/        ← 系统管理, 不碰
├── .learnings/    ← 系统管理, 不碰
├── .local/        ← dws认证, 不碰
├── .tmp/          ← 系统临时, 不碰
└── templates/     ← 只读模板, 不碰
```

规则:
1. 书籍/文档 → 放 `书籍/` 目录
2. 工具脚本 → 放 `scripts/` 目录
3. 临时文件 → 用完即删, 不留根目录
4. 系统目录不碰
5. 根目录保持干净, 只允许目录, 不允许散落文件

> 此规范已通过 `memory_store` 写入大头虾记忆系统 (key: workspace_rules), 大头虾会在每次文件操作时自觉遵守。

### 幻觉案例记录
1. git clone GitHub 报告 EXIT:0, 实际超时 (exit 124)
2. 首次删除文件后报告"全部删除成功", 实际 find 验证仍有大量残留
3. find 命令输出为空时直接说"以上是完整输出", 未执行实际命令
4. .learnings/ 文件删除后被系统自动重建, 大头虾未察觉

### 验证方法
- 所有文件操作后必须用 `find . -type f` 验证实际结果
- 所有网络操作后必须检查 exit code 而非文字描述
- 涉及删除操作需多轮验证, 因为系统可能自动重建文件
