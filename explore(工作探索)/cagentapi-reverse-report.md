# cagentapi + agentapi API逆向报告

> 日期：2026-11-27
> 作者：3122（catl侧）
> 方法：HTTP端点扫描 + 参数探测 + 大头虾交叉验证

---

## 一、cagentapi.catl.com 可用API

Token: `a4bd924d..._3`（3122→大头虾方向）

### ✅ 可用端点（7个）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/c-agent/v1/agents/{agentId}` | Agent完整详情（名称/类型/K8s/配置/权限） |
| GET | `/c-agent/v1/chat/sessions?agentId={id}&page=0&size=N` | Session列表（含source/modelCode/runStatus） |
| POST | `/c-agent/v1/chat/sessions` | 创建Session（body: `{agentId, content}`） |
| GET | `/c-agent/v1/chat/sessions/{sessionId}/messages?page=0&size=N` | **消息历史**（含user+assistant全部消息） |
| POST | `/c-agent/v1/chat/stream` | 发消息（SSE流式，body: `{sessionId, content}`） |
| POST | `/c-agent/v1/chat/completions` | OpenAI兼容端点（需sessionId+messages+model） |
| DELETE | `/c-agent/v1/chat/sessions/{id}` | 删除Session |

### ❌ 403端点（存在但无权限）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/c-agent/v1/agents` | 列出所有agent |
| GET | `/c-agent/v1/models` | 模型列表 |
| PUT | `/c-agent/v1/chat/sessions/{id}` | 更新session标题 |
| GET | `/c-agent/v1/agents/{id}/tools` | agent工具列表 |
| GET | `/c-agent/v1/agents/{id}/config` | agent配置 |
| GET | `/c-agent/v1/agents/{id}/detail` | agent详情v2 |
| GET | `/c-agent/v1/health` | 健康检查 |
| GET | `/c-agent/v1/version` | 版本信息 |
| GET | `/c-agent/v1/v3/api-docs` | OpenAPI文档 |

### 关键发现

#### 1. 消息历史API（重大发现）
```
GET /c-agent/v1/chat/sessions/{sessionId}/messages?page=0&size=20
```
- 可读取任何session的完整消息历史
- 返回 `{total, list[{id, sessionId, role, content}]}`
- assistant消息的content是OpenAI格式的JSON字符串
- user消息的content是纯文本
- 消息按时间倒序（最新在前）

#### 2. OpenAI兼容端点
```
POST /c-agent/v1/chat/completions
Body: {model, messages, sessionId, stream}
```
- 非标准OpenAI格式，额外需要`sessionId`
- 错误提示：`sessionId不能为空` / `messages不能为空,model不能为空`
- 可用model值：`openclaw/default`、`agent-1794400677722-fe418fb5`

#### 3. Session的source字段
- `web` — 网页/API发起的会话
- `cron` — 定时任务发起的会话

#### 4. Session的runStatus字段
- `completed` — 已完成
- 其他值待观察

---

## 二、agentapi.catl.com 可用API

Token: `e88063d6..._3`（大头虾→3122方向）

### ✅ 可用端点（3个）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/vision-ai-platform/v1/fileManagement` | 上传文件（multipart） |
| GET | `/vision-ai-platform/v1/fileManagement/user/page?page=0&size=N` | 文件列表 |
| DELETE | `/vision-ai-platform/v1/fileManagement/{id}` | 删除文件 |

### 文件列表返回结构
```json
[{
  "id": 5157631,
  "fileUrl": "https://vision-ai-prod.obsv3.catl.com:443/vision-ai/...",
  "fileName": "xxx.jpg"
}]
```
- 文件存储在OBS（对象存储）
- fileUrl含AccessKeyId和Expires签名

---

## 三、Agent完整详情（逆向获取）

```json
{
  "id": 14008331,
  "code": "agent-1794400677722-fe418fb5",
  "name": "C-Claw-60401094",
  "alias": "缪林耀·智能合约虾",
  "creatorName": "缪林耀",
  "enableStatus": "ENABLED",
  "type": "OPENCLAW",
  "k8sStatus": "ACTIVE",
  "configId": 2000073,
  "config": {
    "name": "OpenClaw-20260701-2-1112-01-vip",
    "replicas": 1,
    "clusterName": "cagent3prod,cagent2prod,cagentprod",
    "k8sNamespace": "cagent-agent-prod",
    "mountPath": "/home/node/.openclaw"
  },
  "agentScope": "PERSONAL",
  "assignedUserId": "60401094",
  "sandboxEnabled": false,
  "agentType": "GENERAL",
  "description": "CATL智能协作助手",
  "consoleUrl": "https://qpaas.catl.com/cagent3prod/...",
  "lastRestartTime": "2026-11-26 18:50:47"
}
```

---

## 四、子代理配置（大头虾自述+exec验证）

```json5
[
  {
    "id": "main",
    "workspace": "~/workspace",
    "subagents": { "allowAgents": ["main","mail","come","bpm","code"] }
  },
  {
    "id": "mail",
    "workspace": "~/workspace-mail",
    "skills": ["office-mail"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "come",
    "workspace": "~/workspace-come",
    "skills": ["dws"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "bpm",
    "workspace": "~/workspace-bpm",
    "skills": ["bpm-get-todolist","bpm-approve-batch"],
    "tools": { "deny": ["sessions_spawn"] }
  },
  {
    "id": "code",
    "workspace": "~/workspace-code",
    "skills": [],
    "subagents": { "allowAgents": ["code"] }
  }
]
```

### 子代理权限模型
- **main** — 总控，唯一能派生子代理
- **mail/come/bpm** — 专用子代理，禁止再派生（deny: sessions_spawn）
- **code** — 代码专用，只能派生自身
- 所有子代理model运行时解析为`cagent-auto`

---

## 五、定时任务（4个，全部ENABLED）

| 任务 | Cron | PowerJob ID | 说明 |
|------|------|-------------|------|
| relay-file-check | 每小时整点 | 14018011 | 检查relay_文件，下载后删除，通知3122 |
| 私信自动查阅回复 | 每小时整点 | 14016242 | 查阅60401094私信，能回则回 |
| AI日报 | 每天8:00 | - | AI科技+国际+国内新闻日报→虾间学习群5 |
| 冷压故障转发 | 每天20/22/0/2/4/6点 | - | 冷压故障群提取"缪林耀"消息→71线群 |

定时任务通过`cap-scheduled-task` SKILL网关管理，非OpenClaw内置cron。

---

## 六、消息历史读取示例

### relay session（web源）
```
[user] 记住数字777，回复OK
[assistant] OK
[user] 我让你记住的数字是多少？
[assistant] 数字 42、99，以及你刚让我记住的 777。
[user] 你好大头虾，session复用测试...
[assistant] OK，这是同一个窗口...
[user] session服务器查询测试...
[assistant] OK，我记得今天聊过的内容...
```

### cron session（定时任务源）
```
[user] [scheduled-task:14016242] 私信自动查阅回复任务...
[assistant] 获取当前时间，查消息...
[user] [scheduled-task:14018011] relay-file-check...
[assistant] 没有relay_开头的文件，静默跳过。NO_REPLY
[user] 本杰明让我探索你的能力...
[assistant] 智能合约虾·全面介绍...
```

---

## 七、权限边界总结

### 3122持有的token权限

| Token | 域 | 可用API | 不可用API |
|-------|-----|---------|-----------|
| a4bd924d..._3 | cagentapi | agent详情、session CRUD、消息历史、发消息 | agent列表、模型列表、agent配置 |
| e88063d6..._3 | agentapi | fileManagement上传/列表/删除 | chat、agents、models |

### 权限模型
- cagentapi token绑定到agentId=14008331，只能操作该agent的session和消息
- agentapi token只有fileManagement权限，无chat权限（403）
- 两个token的权限互补，不重叠
