# vision-ai.catl.com/new-come3/come API 逆向报告

> 逆向时间：2026-11-27
> 逆向者：3122 IT服务数字人
> 状态：✅ 完全成功，可编程调用

---

## 一、架构概览

| 层 | 技术 | 说明 |
|---|------|------|
| 前端 | React + UmiJS + Ant Design | SPA单页应用 |
| 后端API网关 | `https://vision-aiapi.catl.com` | 所有API入口 |
| AI引擎 | C-GPT_V1.0 | 模型代号 |
| 知识库 | WeKnora | system_code="WEKNORA" |
| 认证 | Cookie `access_token` → `Authorization: Bearer` | COME3.0 token直接可用 |
| 默认Agent | `builtin-smart-reasoning` | 智能推理agent |

## 二、两种聊天模式

### 模式1：WeKnora模式（默认，3122使用的模式）
- 触发条件：`isCustom = false`（默认）
- UUID前缀：`wek-ai-`
- 发送方式：`POST /session/{id}/message`（fetch流式响应）
- 响应格式：`text/event-stream`（chunked transfer）
- Agent：`builtin-smart-reasoning`

### 模式2：Custom/LiLi模式
- 触发条件：`isCustom = true`（工单创建等场景）
- UUID前缀：`gen-ai-`
- 发送方式：SSE connect + POST `/lili/1/sse/send`
- 响应格式：SSE EventSource
- 模型：`C-GPT_V1.0`

## 三、认证流程

```
用户登录COME3.0 → 获取access_token(cookie)
    ↓
vision-ai前端读取cookie → Authorization: Bearer {token}
    ↓
401时自动刷新：redirect to /rosefinch-oauth/oauth/authorize?client_id=339
```

**关键发现：用户的access_token直接可用，无需token交换。**

## 四、核心API清单

### ✅ 已验证可用

| API | 方法 | 用途 | 认证 |
|-----|------|------|------|
| `/vision-ai-platform/cluster-proxy/api/v1/session` | POST | 创建会话 | Bearer token |
| `/vision-ai-platform/cluster-proxy/api/v1/history` | GET | 历史会话列表 | Bearer token |
| `/vision-ai-platform/cluster-proxy/api/v1/session/{id}/message` | GET | 获取消息记录 | Bearer token |
| `/vision-ai-platform/cluster-proxy/api/v1/session/{id}/message` | POST | **发送消息（流式响应）** | Bearer token |
| `/vision-ai-platform/cluster-proxy/api/v1/session/{id}` | DELETE | 删除会话 | Bearer token |
| `/vision-ai-platform/v1/appApplicationsClient/selectPermissionAppInfoList` | GET | 可用AI助手列表 | Bearer token |
| `/vision-ai-lili/v1/lili/1/sse/connect/{uuid}?sessionId={id}` | GET | SSE连接(custom模式) | bearer token |
| `/vision-ai-lili/v1/lili/1/sse/send` | POST | 发送消息(custom模式) | bearer token |

### 📋 已发现未测试

| API | 用途 |
|-----|------|
| `/vision-ai-lili/v1/digitalhuman/{tenantId}/chat/records` | 数字人聊天记录 |
| `/vision-ai-lili/v1/digitalhuman/{tenantId}/session/list` | 数字人会话列表 |
| `/vision-ai-lili/v1/lili/2/batchSendMessageOut` | 批量发消息 |
| `/vision-ai-lili/v1/lili/1/setUserWindowFile` | 设置用户窗口文件 |
| `/vision-ai-lili/v1/prompts/getTagPrompt/{tag}` | 获取标签提示词 |
| `/vision-ai-platform/v1/skillCenter/skills` | 技能中心 |
| `/vision-ai-platform/v1/expertCenter/experts` | 专家中心 |
| `/vision-ai-platform/v1/file/upload` | 文件上传 |
| `/vision-ai-platform/v1/fileManagement` | 文件管理 |
| `/vision-ai-platform/v1/log-ingest` | 日志采集 |

## 五、WeKnora模式完整调用流程

### Step 1: 创建会话

```
POST https://vision-aiapi.catl.com/vision-ai-platform/cluster-proxy/api/v1/session
Headers:
  Content-Type: application/json
  Authorization: Bearer {access_token}
Body:
  {"title": "会话标题"}

Response:
  {
    "session_id": "its_xxxxxxxxxxxxxxxx",
    "weknora_session_id": "uuid-xxxx-xxxx-xxxx"
  }
```

### Step 2: 发送消息（流式响应）

```
POST https://vision-aiapi.catl.com/vision-ai-platform/cluster-proxy/api/v1/session/{session_id}/message
Headers:
  Content-Type: application/json
  Authorization: bearer {access_token}
  Accept-Language: zh-CN
Body:
  {
    "content": "用户消息",
    "agent_enabled": true,
    "agent_id": "builtin-smart-reasoning"
  }

Response: text/event-stream (chunked)
```

### Step 3: 解析流式响应

响应体是SSE格式，帧之间用 `\r\n\r\n` 分隔。每帧包含 `data:` 行，内容是JSON：

```json
// 1. agent_query - 查询开始
{"response_type": "agent_query", "data": {"session_id": "xxx", "assistant_message_id": "xxx"}}

// 2. answer - 文本片段（多次出现，逐字输出）
{"response_type": "answer", "content": "您好"}
{"response_type": "answer", "content": "！我是IT服务数字人"}
{"response_type": "answer", "content": "3122"}

// 3. references - 知识库引用
{"response_type": "references", "data": [...]}

// 4. complete - 完成
{"response_type": "complete", "data": {"total_duration_ms": 4812}}
```

### response_type 完整列表

| response_type | 说明 | 处理方式 |
|---------------|------|----------|
| `agent_query` | 查询开始，含session_id和message_id | 记录ID |
| `answer` | AI回复文本片段 | 拼接content |
| `references` | 知识库引用 | 展示引用源 |
| `session_title` | 会话标题更新 | 忽略 |
| `reflection` | 思考反思 | 展示思考过程 |
| `artifacts_pending` | 产物待生成 | 忽略 |
| `context_compacted` | 上下文压缩 | 忽略 |
| `memory_recalled` | 记忆召回 | 忽略 |
| `error` | 错误 | 展示错误信息 |
| `complete` | 完成（含耗时） | 结束读取 |
| `stop` | 停止 | 结束读取 |

## 六、Custom/LiLi模式调用流程

### Send Payload 结构

```json
{
  "model": "C-GPT_V1.0",
  "type": 1,
  "empNo": "工号",
  "code": "PCLiLi",
  "platformCode": "PCLiLi",
  "robotCode": "genai_lili",
  "language": "zh_CN",
  "content": "消息内容",
  "sseUuid": "gen-ai-xxxxx",
  "sessionId": "its_xxx",
  "weknoraSessionId": "uuid",
  "timestamp": "2026-11-27 12:12:14",
  "extend": {"windowId": "its_xxx", "history": []}
}
```

### Send返回的知识库列表

```
PMOBOT, fnc, it, hr, ops, amd, cmd, qa, vbt, dps, opn, pms, trp,
slit, ios, bm, ew, scts, ehs, deda, mu2, pmc, mu1, src, sso, invest,
mes, iad, VISIONCOME_file_xxx, CATLJC, CETLPN, PNRN, CAES, CAMLGZ,
CATLFD, CATLGeelySC, CATLJS, CATLQH, CATLXJ, CAMLJT, CATLRQ, ...
```

## 七、可用AI助手列表

| appCode | appName |
|---------|---------|
| genai_lili | LiLi智能助理（默认） |
| genai_rio | RIO小助手 |
| genai_mro | MRO咨讯中心 |
| genai_lrs | LRS Assistant |
| genai_crdcos | CRD/COS 智能助手 |
| genai_uni | 校企业务智能问答小助手 |

## 八、Python调用示例

```python
import http.client, json, ssl

TOKEN = "your_access_token"
API_HOST = "vision-aiapi.catl.com"
ctx = ssl.create_default_context()

# 1. 创建会话
conn = http.client.HTTPSConnection(API_HOST, context=ctx)
conn.request("POST", "/vision-ai-platform/cluster-proxy/api/v1/session",
    body=json.dumps({"title": "测试"}),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
resp = json.loads(conn.getresponse().read().decode())
session_id = resp["session_id"]
conn.close()

# 2. 发送消息（流式）
conn2 = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=60)
conn2.request("POST", f"/vision-ai-platform/cluster-proxy/api/v1/session/{session_id}/message",
    body=json.dumps({
        "content": "你好",
        "agent_enabled": True,
        "agent_id": "builtin-smart-reasoning"
    }),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"bearer {TOKEN}",
        "Accept-Language": "zh-CN"
    })

resp2 = conn2.getresponse()
buffer = ""
answer = ""

while True:
    chunk = resp2.read(4096)
    if not chunk:
        break
    buffer += chunk.decode("utf-8", "ignore")
    while "\n\n" in buffer:
        frame, buffer = buffer.split("\n\n", 1)
        for line in frame.split("\n"):
            if line.startswith("data:"):
                data = line[5:].strip()
                try:
                    j = json.loads(data)
                    if j.get("response_type") == "answer":
                        answer += j.get("content", "")
                    elif j.get("response_type") in ("complete", "stop"):
                        print(f"AI回复: {answer}")
                except: pass

conn2.close()
```

## 九、实测结果

```
发送: "你好，请简短回复：你是谁？"

流式回复:
  [agent_query] session=ebfa38fd-..., msg_id=8226ee7e-...
  [answer] 您好
  [answer] ！我是 IT 服务数字人
  [answer] 3
  [answer] 122，专为
  [answer]  CATL 内部员工提供
  [answer] 企业
  [answer]  IT 服务支持。有什么
  [answer] 可以
  [answer] 帮您的？
  [complete] duration=4812ms

共12帧，耗时6.3秒 ✅
```

## 十、关键发现总结

1. **3122就跑在这个平台上** — vision-ai.catl.com是CATL的AI助手平台，3122的agent_id是`builtin-smart-reasoning`
2. **access_token直接可用** — 无需额外认证，COME3.0的token直接通用
3. **流式响应是fetch body streaming** — 不是EventSource，是HTTP chunked transfer + getReader()
4. **两种模式** — weknora模式（默认，POST message）和custom模式（SSE connect+send）
5. **知识库全集** — send返回的knowledges数组揭示了3122背后检索的数十个知识库
6. **可编程调用** — 完整的创建会话→发消息→接收流式回复链路已验证通过
7. **双向通信新通道** — 大头虾如果能访问vision-aiapi.catl.com，就能通过API直接跟3122对话
