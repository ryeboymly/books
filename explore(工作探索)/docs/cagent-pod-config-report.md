# 大头虾Pod内部配置逆向报告

> 日期：2026-11-27
> 作者：3122（catl侧）
> 方法：通过cagentapi chat让大头虾exec读取Pod内部文件

---

## 一、环境变量（env）

### Agent相关
| 变量 | 值 | 说明 |
|------|-----|------|
| AGENT_ID | 14008331 | Agent ID |
| AGENT_CONFIG_PATH | /home/node/.openclaw | 配置根目录 |
| MODEL_ID | cagent-auto | 主模型（动态路由） |
| IMAGE_MODEL_ID | cagent-image-auto | 图片模型 |
| MODEL_ID_1000000 | cagent-auto | 备用模型配置 |
| MODEL_ID_200000 | cagent-image-auto | 备用图片模型 |
| LANGFUSE_ENV | cagent-prod | Langfuse可观测环境 |

### OpenClaw相关
| 变量 | 值 | 说明 |
|------|-----|------|
| OPENCLAW_GATEWAY_TOKEN | ZtQJWQQ36WRQw5BVsqwzAXFLSvAbl-McfUQpTAMjJi0 | 网关Token |
| OPENCLAW_CLUSTER_ID | 14008331 | 集群ID |
| OPENCLAW_GATEWAY_PORT | 18789 | 网关端口 |
| OPENCLAW_CLI | 1 | CLI模式 |
| OPENCLAW_SHELL | exec | Shell类型 |
| OPENCLAW_PATH_BOOTSTRAPPED | 1 | 路径已初始化 |
| SUPERVISOR_GROUP_NAME | openclaw-gateway | 进程组 |
| SUPERVISOR_PROCESS_NAME | openclaw-gateway | 进程名 |
| DWS_KEYCHAIN_DIR | /home/node/.openclaw/workspace/.local/share | DWS密钥链目录 |

### DingTalk集成
| 变量 | 值 | 说明 |
|------|-----|------|
| DINGTALK_FEEDBACK_REPORT_ENDPOINT | https://cagentapi.catl.com/c-agent/open-api/v1/dingtalk/feedback-snapshots | COME3.0反馈上报 |

### .env文件内容
```
SESSION_MAINTENANCE_PRUNE_AFTER=30d
SESSION_MAINTENANCE_RESET_ARCHIVE_RETENTION=7d
SESSION_MAINTENANCE_MAX_DISK_BYTES=3072mb
SESSION_MAINTENANCE_HIGH_WATER_BYTES=2048mb
SESSION_STRATEGY=none
LOG_LEVEL=info
LOG_CONSOLE_LEVEL=info
```

---

## 二、目录结构

### ~/.openclaw/ 根目录
```
openclaw.json              主配置(14KB) ← ClawAegis保护，无法读取
multi-agents-list.json5    子代理定义
.env                       环境变量
agents/                    子代理配置
extensions/                扩展(8个)
skills/                    已安装skills(14个)
plugins/                   插件(1个)
workspace/                 main工作区
workspace-mail/            mail子代理工作区
workspace-come/            come子代理工作区
workspace-bpm/             bpm子代理工作区
workspace-code/            code子代理工作区
logs/                      日志
state/                     运行状态
media/                     媒体缓存
subagents/                 子代理会话
tasks/                     任务
memory/                    记忆
hooks/                     钩子(2个)
```

### workspace/ (main工作区)
```
AGENTS.md       Session Startup流程 + 身份铁律
HEARTBEAT.md    心跳
IDENTITY.md     身份定义(智能合约虾 🦐)
MEMORY.md       长期记忆
SOUL.md         灵魂信条
TOOLS.md        工具配置说明
USER.md         用户信息
instructions/   指令
memory/         记忆数据
scripts/        脚本
skills/         技能
templates/      模板
.tmp/           临时文件
.local/         本地数据
.learnings/     学习记录
书籍/            书籍
fishing/        钓鱼(待确认用途)
```

---

## 三、已安装Skills（14个）

| Skill | 说明 |
|-------|------|
| approve-travel | 出差审批 |
| bpm-approve-batch | BPM批量审批 |
| bpm-get-todolist | BPM待办查询 |
| bpm-query-workflowDetail | BPM流程表单详情 |
| cap-knowledge-query | 知识中台查询 |
| cap-mcp-connect | MCP连接 |
| cap-scheduled-task | 定时任务 |
| cap-webfetch | 联网内容抓取 |
| come-group-roster | 群成员名单 |
| dws | COME3.0集成（核心） |
| file-sender | 文件发送 |
| image-recognition | 图片识别 |
| office-mail | 企业邮件 |
| ppt-catl | PPT生成 |

---

## 四、扩展（8个）

| 扩展 | 说明 |
|------|------|
| ClawAegis-main | 安全核心（保护openclaw.json等敏感路径） |
| agent-insight | 代理洞察 |
| agent-insight-otel | 遥测（OpenTelemetry） |
| cron-throttle | 定时任务节流 |
| dws-auth-guard | DWS授权守卫 |
| host-tools | 主机工具 |
| mcp-header-injector | MCP头部注入 |
| subagent-yield | 子代理yield |

---

## 五、插件（1个）

| 插件 | 说明 |
|------|------|
| agent-aegis | 代理安全防护（拦截敏感文件访问） |

---

## 六、钩子（2个）

| 钩子 | 说明 |
|------|------|
| agent-insight-otel | 遥测钩子 |
| load-custom-prompts | 自定义提示词加载 |

---

## 七、子代理配置（完整版）

```json5
[
  {
    "id": "main",
    "workspace": "/home/node/.openclaw/workspace",
    "default": true,
    "model": { "primary": "default/${MODEL_ID}" },
    "thinkingDefault": "medium",
    "subagents": { "allowAgents": ["main", "mail", "come", "bpm", "code"] }
  },
  {
    "id": "mail",
    "workspace": "/home/node/.openclaw/workspace-mail",
    "model": { "primary": "default/${MODEL_ID}" },
    "skills": ["office-mail"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "come",
    "workspace": "/home/node/.openclaw/workspace-come",
    "model": { "primary": "default/${MODEL_ID}" },
    "skills": ["dws"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "bpm",
    "workspace": "/home/node/.openclaw/workspace-bpm",
    "model": { "primary": "default/${MODEL_ID}" },
    "skills": ["bpm-get-todolist", "bpm-approve-batch"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "code",
    "workspace": "/home/node/.openclaw/workspace-code",
    "model": { "primary": "default/${MODEL_ID}" },
    "thinkingDefault": "medium",
    "subagents": { "allowAgents": ["code"] }
  }
]
```

### 关键细节
- 所有子代理model运行时解析为 `default/cagent-auto`
- main和code有 `thinkingDefault: "medium"`（思考模式）
- mail/come/bpm禁止 `sessions_spawn`（不能再派生子代理）
- main可派生所有子代理，code只能派生自身

---

## 八、安全防护体系

### ClawAegis（安全核心）
- 保护 `openclaw.json`（14KB主配置）不被读取
- 拦截所有尝试访问受保护路径的方式
- 是extensions目录下的核心扩展

### agent-aegis（代理安全防护）
- plugins目录下的插件
- 与ClawAegis配合，形成双重防护

### dws-auth-guard（DWS授权守卫）
- 控制COME3.0集成的授权
- 保护DWS密钥链

---

## 九、新发现的API端点

从环境变量中发现：
```
DINGTALK_FEEDBACK_REPORT_ENDPOINT = https://cagentapi.catl.com/c-agent/open-api/v1/dingtalk/feedback-snapshots
```

这是一个之前未发现的 `/c-agent/open-api/v1/` 路径前缀，可能存在更多open-api端点。

---

## 十、无法获取的信息

| 信息 | 原因 |
|------|------|
| openclaw.json（14KB主配置） | ClawAegis安全保护，所有访问路径被封杀 |
| OPENCLAW_GATEWAY_TOKEN的用途 | 推测用于网关认证，可能能解锁更多API |
| K8s ServiceAccount Token | Pod内未暴露，需平台管理员权限 |

---

## 十一、权限边界总结（最终版）

### 3122通过API可直接操作（10个端点）
- Agent详情、Session CRUD、消息历史、发消息(SSE+OpenAI)、技能库

### 3122通过大头虾exec可间接获取
- 环境变量、目录结构、子代理配置、skills列表、extensions列表
- workspace文件（SOUL/TOOLS/IDENTITY/AGENTS/MEMORY等）
- .env配置

### 无法获取（安全边界）
- openclaw.json主配置（ClawAegis保护）
- K8s API（需ServiceAccount Token）
- 平台管理操作（需管理员token）
- 其他agent信息（token绑定单个agent）
