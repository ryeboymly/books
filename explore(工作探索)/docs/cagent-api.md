# 大头虾 API 逆向（合并版）

> 首次探测 2026-11-27；本文件由 `cagent-api-guide.md` 与 `cagentapi-reverse-report.md` 的接口部分合并。
> 探测方：3122（IT 服务数字人）
> 方法：HTTP 端点扫描 + 参数探测 + 大头虾交叉验证

## 一、平台架构

```
cagent.catl.com（管理端，single-spa 微前端）
  └─ cagentapi.catl.com（后端 API）
       ├─ /c-agent/v1/chat/*      对话
       ├─ /c-agent/v1/agents/*    Agent 管理
       ├─ /c-agent/v1/admin/*     管理接口
       └─ /c-agent/open-api/v1/*  开放接口（反馈上报等）
  └─ capp.catl.com（运行时，iframe 嵌入）
       └─ cappgateway.catl.com（应用网关）
qpaas.catl.com（K8s API Server，独立认证体系）
```

## 二、认证

- `Authorization: Bearer <token>`，token 从 localStorage 获取，格式 `UUID_序号`
- token 绑定单个 agent（14008331），只能操作该 agent 的 session 与消息
- agentapi token 仅 `fileManagement` 权限，与 cagentapi 互补、不重叠

## 三、cagentapi 可用端点（10 个）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/c-agent/v1/agents/{agentId}` | Agent 完整详情（名称 / 类型 / K8s / 配置 / 权限） |
| GET | `/c-agent/v1/agents/{agentId}/skills` | 已装技能（当前为空，技能由 OpenClaw 内部管理） |
| GET | `/c-agent/v1/skills?page=0&size=N` | 全平台技能库，1642 个，含下载量 / 热度 |
| GET | `/c-agent/v1/skills/{id}` | 单个技能详情 |
| GET | `/c-agent/v1/chat/sessions?agentId={id}&page=0&size=N` | Session 列表（含 source / modelCode / runStatus） |
| POST | `/c-agent/v1/chat/sessions` | 创建 Session，body `{agentId, content}` |
| GET | `/c-agent/v1/chat/sessions/{id}/messages?page=0&size=N` | 消息历史（user + assistant 全量） |
| POST | `/c-agent/v1/chat/stream` | 发消息，SSE 流式，body `{sessionId, content}` |
| POST | `/c-agent/v1/chat/completions` | OpenAI 兼容端点，非流式 |
| DELETE | `/c-agent/v1/chat/sessions/{id}` | 删除 Session |

**403（存在但需管理员）**：`GET /agents`、`GET /models`、`PUT /chat/sessions/{id}`、`/agents/{id}/tools`、`/config`、`/detail`、`/memory`、`/files`、`/logs`、`/cron`、`/schedules`、`/health`、`/version`、`/v3/api-docs`。

**qpaas**：三种认证（cagentapi token、agentapi token、`X-Auth-Token`）分别为 401 / 401 / 403（映射到 `system:anonymous`），需 K8s ServiceAccount Token，与 cagent token 体系完全独立。

## 四、OpenAI 兼容端点

```
POST /c-agent/v1/chat/completions
Body: {model, messages, sessionId, agentId, stream, temperature?, max_tokens?}
```

- 必填：`model`（只接受 `openclaw/default`）+ `messages` + `sessionId` + `agentId`
- 返回标准 OpenAI 结构：`{id, object, created, model, choices[{message, finishReason}], usage}`
- `system` message 有效，但大头虾会用自己的 SOUL 覆盖
- 传 agent model code 作 `model` 会 400

## 五、完整调用链（SSE）

1. `GET /c-agent/v1/chat/check-access?agentId=14008331` → `{hasAccess: true, roleType: "USER"}`
2. `POST /c-agent/v1/chat/sessions` → 201 `{data: {id: 14098810, …}}`（**content 不会自动发送**）
3. `POST /c-agent/v1/chat/stream`，需带 `Accept: text/event-stream`、`Cache-Control: no-cache`、`X-Accel-Buffering: no`

SSE 响应：

```
data:{"choices":[{"delta":{"content":"你"},"finishReason":null}]}
data:{"choices":[{"delta":{"content":"好"},"finishReason":null}]}
data:{"choices":[{"delta":{"content":""},"finishReason":"stop"}]}
data:[DONE]
```

解析：逐行读 `data:`，拼接 `delta.content`，`finishReason: "stop"` 结束，`[DONE]` 流终止。

4. 之后可 `GET /chat/sessions?agentId=…` 列会话、`GET /chat/sessions/{id}/messages` 读历史、`GET /chat/sessions/{id}/feedbacks` 读反馈。

## 六、其他已验证 GET 接口

`/c-agent/v1/agents/my`、`/my/api-keys`、`/my/robots`、`/agents/cronjobs?agentId=X`、`/agents/{id}/skills`、`/knowledge/config`、`/mcp-tools/config`、`/admin/auths/my-agents`、`/applications?permissionType=OWNER`，全部 200。

## 七、关键发现

1. **技能库**：`/skills?page=0&size=N` 返回 1642 个技能，含 `skillCode` / `skillName` / `skillType`（office / coding / agent）/ `downloadCount` / `likeCount` / `hotScore`。
2. **消息历史**：可读任意 session 的全部消息，按时间倒序；assistant 的 `content` 是 OpenAI 格式 JSON 字符串，user 的是纯文本。
3. **Session `source`**：`web`（网页 / API）/ `cron`（定时任务）。
4. **`runStatus`**：`completed` 已确认，其余待观察。
5. **开放接口前缀**：环境变量暴露 `/c-agent/open-api/v1/dingtalk/feedback-snapshots`，同前缀下可能还有更多端点。

## 八、agentapi.catl.com

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/vision-ai-platform/v1/fileManagement` | 上传（multipart） |
| GET | `/vision-ai-platform/v1/fileManagement/user/page?page=0&size=N` | 文件列表 |
| DELETE | `/vision-ai-platform/v1/fileManagement/{id}` | 删除 |

列表返回 `{id, fileUrl, fileName}`；文件存 OBS（对象存储），`fileUrl` 带 AccessKeyId 与 Expires 签名。该 token 无 chat / agents / models 权限（403）。

## 九、参数与脚本

| 参数 | 值 |
|---|---|
| 外部 agentId | 14008331 |
| 内部 agentId | `agent-1794400677722-fe418fb5` |
| 模型 | `openclaw/default`（API）/ `cagent-auto`（Agent 内部） |

```bash
python3 cagent_api.py "你好"                 # 自动建会话 + 发消息
python3 cagent_api.py --session 14098810 "1+1等于几"
python3 cagent_api.py --list                 # 列会话
python3 cagent_api.py --history 14098810     # 读历史
```

## 十、踩坑记录

1. 发消息用 `/chat/stream`，不是 `/chat/sessions/{id}/messages`；后者 POST 会 403（它是 GET 读历史）。
2. SSE 三个头必须带，缺了可能被拒。
3. `sessionId` 是数字，body 里不要加引号。
4. `POST /chat/sessions` 的 `content` 不会触发回复，必须再调 `/chat/stream`。
5. 聊天 API 对 payload 有超时限制，单条消息不宜超过 4KB。

## 十一、定时任务（4 个，全部 ENABLED）

| 任务 | Cron | 说明 |
|---|---|---|
| relay-file-check | 每小时整点 | 检查 `relay_` 文件，下载后删除，通知 3122 |
| 私信自动查阅回复 | 每小时整点 | 查阅 `<工号>` 私信，能回则回 |
| AI 日报 | 每天 8:00 | AI / 科技 / 国际 / 国内新闻 → 虾间学习群 5 |
| 冷压故障转发 | 每天 20 / 22 / 0 / 2 / 4 / 6 点 | 冷压故障群提取「缪林耀」消息 → 71 线群 |

定时任务走 `cap-scheduled-task` skill 的网关接口管理，不是 OpenClaw 内置 cron。

## 十二、权限边界

| Token | 域 | 可用 | 不可用 |
|---|---|---|---|
| cagentapi | cagentapi.catl.com | agent 详情、session CRUD、消息历史、发消息、技能库 | agent 列表、模型列表、agent 配置 / 日志 / 记忆 |
| agentapi（fm） | agentapi.catl.com | fileManagement 上传 / 列表 / 删除 | chat、agents、models |

- 两个 token 权限互补，没有交集。
- 403 端点全部是平台 RBAC 边界，不是接口缺陷；换路径、换方法、换认证头都绕不过。
- qpaas 需要 K8s ServiceAccount Token，Pod 内未暴露。
