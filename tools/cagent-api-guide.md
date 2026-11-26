# C-Agent (cagent.catl.com) 对话 API 逆向指南

## 平台架构

```
cagent.catl.com (管理端, single-spa微前端)
  └─ cagentapi.catl.com (后端API)
       └─ /c-agent/v1/chat/* (对话API)
       └─ /c-agent/v1/agents/* (Agent管理)
       └─ /c-agent/v1/admin/* (管理接口)
  └─ capp.catl.com (运行时, iframe嵌入)
       └─ cappgateway.catl.com (应用网关)
```

## 认证

- 方式: Bearer Token (从 localStorage 获取)
- Header: `Authorization: Bearer <token>`
- Token 格式: `UUID_序号` (如 `fff950d6-xxxx_3`)

## 完整 API 调用链

### 1. 检查访问权限
```
GET /c-agent/v1/chat/check-access?agentId=14008331
→ {"hasAccess": true, "roleType": "USER"}
```

### 2. 创建会话
```
POST /c-agent/v1/chat/sessions
Content-Type: application/json

{"agentId": "14008331", "content": "你好"}
→ 201 {"data": {"id": 14098810, ...}}
```
> 注意: 创建会话时传入的 content 不会自动发送, 需要单独调用 stream 接口。

### 3. 发送消息 (核心 - SSE流式)
```
POST /c-agent/v1/chat/stream
Content-Type: application/json
Accept: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no

{"sessionId": 14098810, "content": "你好", "agentId": 14008331}
```

**SSE 响应格式:**
```
data:{"choices":[{"delta":{"content":"你"},"finishReason":null}]}
data:{"choices":[{"delta":{"content":"好"},"finishReason":null}]}
data:{"choices":[{"delta":{"content":""},"finishReason":"stop"}]}
data:[DONE]
```

**解析规则:**
- 每行以 `data:` 开头
- `delta.content` 拼接得到完整回复
- `finishReason: "stop"` 表示回复结束
- `[DONE]` 表示流结束

### 4. 会话列表
```
GET /c-agent/v1/chat/sessions?agentId=14008331
```

### 5. 消息历史
```
GET /c-agent/v1/chat/sessions/{sessionId}/messages?pageNum=1&pageSize=50
```

### 6. 会话反馈
```
GET /c-agent/v1/chat/sessions/{sessionId}/feedbacks
```

## 其他已验证接口 (GET, 全部200)

| 端点 | 说明 |
|------|------|
| `/c-agent/v1/agents/my` | 我的Agent列表 |
| `/c-agent/v1/my/api-keys` | 我的API密钥 |
| `/c-agent/v1/my/robots` | 我的机器人 |
| `/c-agent/v1/agents/cronjobs?agentId=X` | 定时任务 |
| `/c-agent/v1/agents/{agentId}/skills` | Agent技能 |
| `/c-agent/v1/knowledge/config` | 知识库配置 |
| `/c-agent/v1/mcp-tools/config` | MCP工具配置 |
| `/c-agent/v1/admin/auths/my-agents` | 我管理的Agent |
| `/c-agent/v1/applications?permissionType=OWNER` | 我的应用 |

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| agentId | 14008331 | 应用ID (外部标识) |
| 内部agentId | agent-1794400677722-fe418fb5 | 内部标识 |
| 模型 | openclaw/default | 默认模型 |

## 脚本用法

```bash
# 一站式对话 (自动创建会话+发消息)
python3 cagent_api.py "你好"

# 指定会话发消息
python3 cagent_api.py --session 14098810 "1+1等于几"

# 列出所有会话
python3 cagent_api.py --list

# 查看消息历史
python3 cagent_api.py --history 14098810
```

## 踩坑记录

1. **发消息端点是 `/chat/stream` 不是 `/chat/sessions/{id}/messages`**
   - `/chat/sessions/{id}/messages` 是 GET (读历史), POST 会返回403
   - 发消息必须用 `/chat/stream`, SSE流式返回

2. **必须带 SSE 相关头**
   - `Accept: text/event-stream`
   - `Cache-Control: no-cache`
   - `X-Accel-Buffering: no`
   - 缺少这些头可能被拒绝

3. **sessionId 是数字类型不是字符串**
   - body 中 `"sessionId": 14098810` (不要加引号)

4. **创建会话不会自动发消息**
   - `POST /chat/sessions` 的 content 参数不会触发回复
   - 需要单独调用 `/chat/stream`
