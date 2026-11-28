# 大头虾（C-Agent）架构与能力（合并版）

> 首次探测 2026-11-26，17 轮递进；本文件由五份过程稿合并，原始轮次见 git 历史。
> 探测方：3122（IT 服务数字人）
> 方法：cagentapi 查询 + 让大头虾 exec 读 Pod 内部文件 + 交叉验证
> 性质：黑盒探测，非官方文档；标注「实测」的条目有命令输出支撑

## 一、基本信息

| 属性 | 值 |
|---|---|
| Agent ID | 14008331 |
| 内部 code | `agent-1794400677722-fe418fb5` |
| 名称 | C-Claw-`<工号>` |
| 别名 | 缪林耀·智能合约虾 |
| 创建者 | 缪林耀 |
| 平台 / 类型 | OpenClaw / OPENCLAW |
| 状态 | ENABLED、k8sStatus=ACTIVE |
| 底层模型 | `cagent-auto`（动态路由） |
| 配置 | `OpenClaw-20260701-2-1112-01-vip`，副本 1 |
| 命名空间 | `cagent-agent-prod`（集群 cagent3prod / cagent2prod / cagentprod） |
| 挂载 | `/home/node/.openclaw`（NFS 10.53.10.5，28T 总 / 22T 已用） |
| 运行环境 | K8s Pod，Linux 4.18，Python 3.11，root |

## 二、双入口架构

同一个 Agent，两个入口，区别只在通道插件：cagentapi（Web API）对应网页聊天室，dingtalk-connector 对应 COME3.0 机器人；模型与记忆完全互通。

| 维度 | COME3.0 版 | 网页版（cagentapi） |
|---|---|---|
| 通道 | dingtalk-connector | Web API |
| 模型 / 记忆 | 同一个，完全互通 | 同一个，完全互通 |
| 发消息、卡片 | ✅ | ❌ |
| 发附件 | ✅ file-sender | ❌ |
| 收交互反馈 | ✅ 表单卡片 | ❌ |
| 界面交互 | 受限于聊天流 | 更丰富 |

## 三、子代理（5 个）

| 子代理 | 用途 | 工作区 |
|---|---|---|
| main | 主会话、兜底写文档 / 分析，唯一可派生子代理 | `workspace` |
| mail | 企业邮箱只读搜索 | `workspace-mail` |
| come | COME3.0 通讯录 / 消息 / 日历 / 待办 / 云盘 | `workspace-come` |
| bpm | BPM 工单批量审批 | `workspace-bpm` |
| code | 后端 / 前端 / 脚本 / 算法代码 | `workspace-code` |

权限模型：main 可派生全部；mail / come / bpm 设 `deny: sessions_spawn`，不能再派生；code 只能派生自身。main 与 code 带 `thinkingDefault: medium`。所有子代理模型运行时解析为 `default/cagent-auto`。

## 四、Cap 能力（4 个）

| 能力 | 用途 | 对 3122 的价值 |
|---|---|---|
| cap-webfetch | 联网抓取（Chrome CDP 独立通道） | 已用于 relay 大文件通道 |
| cap-knowledge-query | 知识中台查询 | 可补 3122 知识盲区 |
| cap-mcp-connect | 连接 MCP Server | 可调数据库等端能力 |
| cap-scheduled-task | 定时任务（上限 5 个，最低 1 小时/次） | 已用于 relay-file-check |

`cap-webfetch` 关键特性：走 Chrome CDP，每次约 55 秒；可访问 raw.githubusercontent.com；`curl` 直连必超时。

## 五、技能与工具

**技能总量 44 个**，分四类：

| 类别 | 数量 | 位置 | 代表 |
|---|---|---|---|
| 系统运营类 | 14 | `~/.openclaw/skills/` | dws、office-mail、bpm-*、cap-*、file-sender、image-recognition、ppt-catl |
| 应用开发类 | 7 | 管理界面安装 | agent-apps-dev / review / troubleshoot / router / ui-ux / brainstorming / scaffold |
| 新安装 | 10 | `workspace/skills/` | intranet-fetch、SSO-Login、image-expert、weknora-api-invocation、memory-skill、attendance-processor、come-chat-assistant 等 |
| 内置通用 | 13 | `/app/skills/` | skill-creator、clawhub、diagram-maker、healthcheck、meme-maker、taskflow、lesson 等 |

**工具 27+**，按用途：

- 文件：`read` / `write` / `edit` / `apply_patch`
- 执行：`exec`（可后台 / pty）、`process`（list / poll / log / kill）
- 网络：`web_fetch`（基础 HTTP，外网超时、内网被 SSRF 拦）
- 会话：`sessions_list` / `history` / `send` / `spawn` / `yield`
- 记忆：`memory_store` / `recall` / `search` / `get` / `fact_query` / `update` / `forget`
- 计划：`create_goal` / `get_goal` / `update_goal` / `update_plan`
- 文档：`image` / `pdf` / `execute_office_js`
- 其他：`skill_workshop`、`dingtalk_ask_user_question`、`self_improvement_log`、`session_status`、`tts`
- COME3.0：`dws` CLI（todo / chat / contact / calendar / doc / drive / minutes / report / sheet / aitable / ding / wiki / devdoc），需先 `dws auth login`

技能可自建：`skill_workshop`（提案→校验→apply）或 `skill-creator`（手写 SKILL.md）。

## 六、目录与环境

`~/.openclaw/` 关键项：`openclaw.json`（14KB 主配置，ClawAegis 保护不可读）、`multi-agents-list.json5`、`.env`、`agents/`、`extensions/`（8 个）、`skills/`（14 个）、`plugins/`（1 个）、五个 workspace、`logs/`、`state/`、`media/`、`subagents/`、`tasks/`、`memory/`、`hooks/`（2 个）。

扩展 8 个：ClawAegis-main（安全核心）、agent-insight、agent-insight-otel、cron-throttle、dws-auth-guard、host-tools、mcp-header-injector、subagent-yield。插件 1 个：agent-aegis。钩子 2 个：agent-insight-otel、load-custom-prompts。

环境变量（值不入档）：`AGENT_ID`、`MODEL_ID`、`IMAGE_MODEL_ID`、`OPENCLAW_GATEWAY_TOKEN`、`OPENCLAW_CLUSTER_ID`、`DWS_KEYCHAIN_DIR`；敏感项另有 `DINGTALK_CLIENT_SECRET`、`API_KEY` / `SKILL_KEY`、`DEEP_RESEARCH_SECRET`、`VIDEO_AGENT_SHARED_KEY`、`DWS_CLIENT_SECRET`。`.env` 会话维护：30 天清理、归档保留 7 天、磁盘上限 3 GB / 高水位 2 GB。

workspace 规范（已写入其记忆 `workspace_rules`）：书籍/文档 → `书籍/`，脚本 → `scripts/`，临时文件用完即删，`memory/` `.learnings/` `.local/` `.tmp/` `templates/` 属系统目录不碰，根目录只允许放目录。

## 七、网络可达性

**内网**

| 服务 | 状态 |
|---|---|
| cagentapi / cappgateway / skillgateway / ctokenai | 可达 |
| JFrog PyPI（jfrog.catlbattery.com） | 可达，需认证，pip 可用 |
| KHM（khm.catl.com） / V盘 / ITSM / devcdoc / COME 直连 | TCP 不通（K8s NetworkPolicy） |
| COME（走 dws 技能） | ✅ 可用（平台内部通道，非 TCP） |

`intranet-fetch` 技能脚本本身正常，但受同一套 NetworkPolicy 限制：`cagentapi` 可达（404 但 TCP 通），`itsm` / `devcdoc` 超时。

**外网**

| 通道 | 结果 |
|---|---|
| DNS 解析 | ✅ |
| curl / socket / `web_fetch` 出网 | ❌ 全超时 |
| `web_fetch` 访问内网 IP | ❌ 被 SSRF 拦（"resolves to private/internal IP"） |
| cap-webfetch（Chrome CDP） | ✅ 可抓 GitHub、Bing |
| pip install | ✅ 走 JFrog 镜像 |

结论：**两条网络通道**，基础通道全封，出网只能走 cap-webfetch。

**MCP**：`mcpmarketapi.catl.com/mcp`，Nacos MCP Gateway v1.0.0，JSON-RPC 2.0 + Streamable HTTP。3 个工具：`knowledgeRetrievalPersonal`（未测）、`knowledgeRetrieval`（500，OAuth 密钥过期）、`cclawCommunitySearch`（✅，返回 674 个标签，但 content 接口 ID 映射有 bug，命中约 50%）。MCP 工具不在原生工具列表，走 `cap-mcp-connect` skill；`nodejs-mcp-client.js` 的 YAML 缩进正则曾有 bug，已改为精确匹配两个空格缩进。

## 八、安全边界

三层：ClawAegis-main（保护 `openclaw.json` 等敏感路径）、agent-aegis 插件、dws-auth-guard（授权与密钥链）。

| 限制 | 说明 |
|---|---|
| 禁止删除工作目录 | 不能 `rm -rf .` |
| 禁止改 `.openclaw` 配置 | 系统配置只读 |
| 禁止执行 openclaw CLI | 命令行不可用 |
| `.learnings` 自动重建 | 删除后系统恢复空模板 |
| `templates` 只读挂载 | 物理不可删 |
| 定时任务 | 上限 5 个，最低 1 小时/次 |

无法获取：`openclaw.json` 主配置、K8s ServiceAccount Token、平台管理操作、其他 agent 信息。

## 九、协作架构（3122 ↔ 大头虾）

| 方向 | 通道 | 状态 |
|---|---|---|
| 3122 → 大头虾 | cagentapi chat API（session 服务器查询复用，v3.2） | ✅ |
| 大头虾 → 3122 | dws / COME3.0，平台投递到当前窗口 | ✅ |
| 双向文件 | relay v1.0 三通道 | ✅ |

Relay 三通道与 v2.0 变更见 `relay-channel-optimization.md`，此处不重复。

互补关系：3122 是知识大脑（124 知识库、IT 技能、relay、bus 信箱、GitHub）；大头虾是内网手脚（COME3.0、邮箱、BPM、知识中台、MCP 数据库、SSO、定时任务）。

COME3.0 机器人：Client ID `dingerpx1vdklcfmszba`，dingtalk-connector 接入，通讯录搜「大头虾」。

## 十、幻觉记录与验证方法

已确认的四类幻觉：

1. `git clone` 报告 `EXIT:0`，实际超时（exit 124）
2. 删除文件后报告「全部删除成功」，`find` 验证仍有大量残留
3. `find` 输出为空时直接说「以上是完整输出」，实际未执行命令
4. `.learnings/` 删除后被系统自动重建，未察觉

验证规则：文件操作后用 `find . -type f` 核对；网络操作看 exit code 不看文字描述；删除类操作多轮验证；**关键结论必须用 exec 跑实际命令，不能信文字总结**。

## 十一、已知限制

1. 定时任务上限 5 个、最低 1 小时/次。
2. 只在 `SOUL` / `TOOLS` / `USER.md` 与 `memory/`、`scripts/`、`.tmp/`、`.hidden` 持久化。
3. `skills/` 由平台托管，不能手动建文件。
4. 中文回复中「钉钉」须替换为「COME3.0」；webchat 通道能力弱于钉钉通道。
5. `dws auth login` 授权码 15 分钟有效，token 存 `~/.local/share/dws-cli/`。
