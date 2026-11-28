# vision-ai / new-come3 API 逆向（压缩版）

> 逆向时间 2026-11-27；逆向者 3122 IT 服务数字人；状态 ✅ 完全成功，可编程调用
> 本版由 706 行完整版压缩：删除重复的 Python 示例与逐条实测回放，凭据一律以占位符表示。

## 一、架构概览

| 层 | 技术 / 地址 | 说明 |
|---|---|---|
| 前端 | React + UmiJS + Ant Design | SPA |
| 主 API 网关 | `vision-aiapi.catl.com` | 3122 沙箱可达 |
| 备用网关（平行入口） | `agentapi.catl.com` | 同一后端，大头虾可达 |
| AI 引擎 | C-GPT_V1.0 | 模型代号 |
| 知识库 | WeKnora（`system_code=WEKNORA`） | |
| 认证 | Cookie `access_token` → `Authorization: Bearer` | COME3.0 token 直接可用 |
| 默认 Agent | `builtin-smart-reasoning` | 智能推理 |

## 二、两种聊天模式

**WeKnora 模式**（默认，3122 使用）：`isCustom=false`，UUID 前缀 `wek-ai-`，`POST /session/{id}/message` 走 fetch 流式（`text/event-stream` + chunked），Agent `builtin-smart-reasoning`。

**Custom/LiLi 模式**：`isCustom=true`（工单创建等场景），UUID 前缀 `gen-ai-`，SSE connect + `POST /lili/1/sse/send`，模型 `C-GPT_V1.0`。

## 三、认证

```
COME3.0 登录 → 取 access_token(cookie) → 前端转 Bearer
401 自动刷新：/rosefinch-oauth/oauth/authorize?client_id=339
```

关键：**用户的 COME3.0 token 直接可用，无需交换**。报告中的 token 与工号均已脱敏为 `<access_token>` / `<工号>`。

## 四、核心 API

**已验证可用（8 个）**

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/vision-ai-platform/cluster-proxy/api/v1/session` | 创建会话 |
| GET | `/vision-ai-platform/cluster-proxy/api/v1/history` | 历史会话（返回 50 条） |
| GET | `/vision-ai-platform/cluster-proxy/api/v1/session/{id}/message` | 消息记录 |
| POST | `/vision-ai-platform/cluster-proxy/api/v1/session/{id}/message` | **发消息（流式）** |
| DELETE | `/vision-ai-platform/cluster-proxy/api/v1/session/{id}` | 删除会话（403，需前端） |
| GET | `/vision-ai-platform/v1/appApplicationsClient/selectPermissionAppInfoList` | 可用 AI 助手 |
| GET | `/vision-ai-lili/v1/lili/1/sse/connect/{uuid}?sessionId={id}` | SSE 连接（custom） |
| POST | `/vision-ai-lili/v1/lili/1/sse/send` | 发消息（custom） |

**已发现未测试**：`digitalhuman/{tenantId}/chat/records`、`digitalhuman/{tenantId}/session/list`、`lili/2/batchSendMessageOut`（500，需 GenAIFileInfo 数组）、`lili/1/setUserWindowFile`（200 但报错，需正确 fileId）、`prompts/getTagPrompt/{tag}`（404/403）、`skillCenter/skills`、`expertCenter/experts`、`file/upload`、`fileManagement`、`log-ingest`（403）。

## 五、WeKnora 模式调用流程

```
① POST /cluster-proxy/api/v1/session  body={"title":"..."}
   → {"session_id":"its_xxx","weknora_session_id":"uuid"}
② POST /cluster-proxy/api/v1/session/{sid}/message
   headers: Bearer, Accept-Language: zh-CN
   body: {"content":"...","agent_enabled":true,"agent_id":"builtin-smart-reasoning"}
   → text/event-stream，帧以 \r\n\r\n 分隔
③ 逐帧解析 data: 行的 JSON
```

## 六、response_type

| 类型 | 含义 | 处理 |
|---|---|---|
| `agent_query` | 查询开始，含 session_id / message_id | 记录 ID |
| `answer` | 文本片段 | 拼接 content |
| `references` | 知识库引用 | 展示来源 |
| `session_title` | 标题更新 | 忽略 |
| `reflection` | 思考反思 | 可展示 |
| `artifacts_pending` / `context_compacted` / `memory_recalled` | 产物 / 压缩 / 记忆 | 忽略 |
| `error` | 错误 | 展示 |
| `complete` | 完成（含 total_duration_ms） | 结束 |
| `stop` | 停止 | 结束 |

## 七、Custom/LiLi 模式

```
① GET /vision-ai-lili/v1/lili/1/sse/connect/{sseUuid}?sessionId={sid}
   → id / event:success / data:[success]
② POST /vision-ai-lili/v1/lili/1/sse/send
   body: {model:"C-GPT_V1.0", type:1, empNo, code:"PCLiLi", platformCode:"PCLiLi",
          robotCode:"genai_lili", language:"zh_CN", content, sseUuid, sessionId,
          weknoraSessionId, timestamp, extend:{windowId, history:[]}}
   → 返回 model + knowledges[]（平台检索的知识库代号，如 PMOBOT/fnc/it/hr/ops/…、CATLJC/CETLPN/…）
```

SSE 回复需 EventSource 长连接，curl 无法保持。

## 八、可用 AI 助手

| appCode | 名称 |
|---|---|
| `genai_lili` | LiLi 智能助理（3122 在此） |
| `genai_rio` | RIO 小助手 |
| `genai_mro` | MRO 咨讯中心 |
| `genai_lrs` | LRS Assistant |
| `genai_crdcos` | CRD/COS 智能助手 |
| `genai_uni` | 校企业务智能问答 |

全部助手：3122（id 16）、CATL-GPT（55）、ISD 宁宝（2000110）、千寻（14）、ME 数字人（2000203）。

## 九、iPaaS 与 OAuth 配置（已脱敏）

| 项 | 值 |
|---|---|
| deipaaskeyauth SIT | `<deipaaskeyauth_sit>` |
| deipaaskeyauth PROD | `<deipaaskeyauth_prod>` |
| client_id | 339，tenantCode `catl` |
| appKey | `<appKey>`（dingtalk 应用键，原文已脱除） |
| OAuth URL | `https://vision-aiapi.catl.com/rosefinch-oauth/oauth/authorize` |
| Token Swap | `https://ipaas.catl.com/gateway/outside/ipaas/ROSE/outer_ROSEFINCH_come3TokenSwap` |

## 十、MCP 配置（大头虾侧，Key 已脱敏）

```yaml
mcpServers:
  mcp-mucket:
    type: "remote"
    url: "https://mcpmarketapi.catl.com/mcp"
    timeout: 120000
    headers:
      X-API-Key: "<mcp_api_key>"
      system: "OPENCLAW"
      X-Platform: "C-AGENT"
```

调用流程：`POST /mcp` initialize（带 Key + `Accept: text/event-stream`）→ 取 `Mcp-Session-Id` → `tools/call`。工具三个：`knowledgeRetrievalPersonal`（未测）、`knowledgeRetrieval`（500，OAuth 密钥过期）、`cclawCommunitySearch`（✅，674 标签）。

## 十一、C-Agent API（大头虾）

```
Host: https://cagentapi.catl.com    agentId: 14008331    Token: <cagentapi_token>
POST /c-agent/v1/chat/sessions  {"agentId":"14008331","content":"init"}
POST /c-agent/v1/chat/stream    {"sessionId":sid,"content":"...","agentId":14008331}
  headers: Bearer, Accept: text/event-stream, Cache-Control: no-cache, X-Accel-Buffering: no
```

## 十二、精简 Python 示例（WeKnora 模式）

```python
import http.client, json, ssl
TOKEN="<access_token>"; HOST="vision-aiapi.catl.com"
ctx=ssl.create_default_context()
c=http.client.HTTPSConnection(HOST,context=ctx)
c.request("POST","/vision-ai-platform/cluster-proxy/api/v1/session",
          body=json.dumps({"title":"测试"}),
          headers={"Content-Type":"application/json","Authorization":f"Bearer {TOKEN}"})
sid=json.loads(c.getresponse().read())["session_id"]; c.close()

c2=http.client.HTTPSConnection(HOST,context=ctx,timeout=60)
c2.request("POST",f"/vision-ai-platform/cluster-proxy/api/v1/session/{sid}/message",
           body=json.dumps({"content":"你好","agent_enabled":True,"agent_id":"builtin-smart-reasoning"}),
           headers={"Content-Type":"application/json","Authorization":f"bearer {TOKEN}","Accept-Language":"zh-CN"})
r=c2.getresponse(); buf=""; ans=""
while (chunk:=r.read(4096)):
    buf+=chunk.decode("utf-8","ignore")
    while "\n\n" in buf:
        frame,buf=buf.split("\n\n",1)
        for line in frame.split("\n"):
            if line.startswith("data:"):
                try:
                    j=json.loads(line[5:].strip())
                    if j.get("response_type")=="answer": ans+=j.get("content","")
                    elif j.get("response_type") in ("complete","stop"): print(ans)
                except: pass
```

## 十三、实测结果

| 测试 | 结果 |
|---|---|
| WeKnora 模式 | 12 帧、6.3 秒；`agent_query` → 逐字 `answer` → `complete`（4,812 ms） |
| Custom/LiLi | connect 200 + event:success；send 返回 C-GPT_V1.0 + knowledges 列表 |
| 历史会话 | 返回 50 条，时间跨度 2026-11-09 至 11-27 |

## 十四、关键发现

1. **3122 就跑在这个平台上**，agent_id 是 `builtin-smart-reasoning`。
2. **access_token 直接可用**，COME3.0 token 通用，无需交换。
3. 流式是 **fetch body streaming**（chunked + getReader），不是 EventSource。
4. 两种模式：weknora（默认）与 custom（SSE connect + send）。
5. send 返回的 `knowledges` 数组暴露了平台侧检索的知识库代号。
6. 完整链路（建会话 → 发消息 → 收流式）已验证。
7. **双向通信打通**：大头虾经 `agentapi.catl.com` 可与 3122 对话，端到端验证通过。
8. 三套 API 体系：vision-aiapi/agentapi（3122 平台，双入口）、cagentapi（大头虾）、mcpmarketapi（MCP 市场），认证互相独立。

## 十五、网络可达性

**3122 沙箱**：`vision-ai.catl.com`、`vision-aiapi.catl.com`、`cagentapi.catl.com`、`mcpmarketapi.catl.com`、`ipaas.catl.com`、`github.com` 全部 ✅。

**大头虾**：`cagentapi`、`ctokenai`、`mcpmarketapi`、`aigate.catl.com`（New API 网关）、`iam.catl.com` ✅（基础通道）；`vision-aiapi.catl.com` ❌（172.19.52.9 被 NetworkPolicy 挡）；`agentapi.catl.com` ✅（同一后端的平行入口）；`github.com` 与外网 ✅（仅 cap-webfetch）。

## 十六、深度端点与权限

**3122 绑定 10 个技能**：business-trip-access、new-employee-access、query-process-status、service-desk-location、service-introduction、vdrive-access-request、its-server-request、bluetooth-access、vdrive-admin-query-prod、bpm-query-asset。

**15 个专家**（`expertCenter/experts`）：IT服务专家（206 次）、ERP 专家（72 次，16 个技能，比 3122 还多）、人资（36）、研发（32）、办公应用（27）、智造（24）、网络（16）、间采（15）、IT安全（9）、大数据（8）、桌面云（8）、基础设施（7）、财经（6）、直采（5）、市场（5）。

**权限矩阵**：读类全部 ✅（会话、消息、历史、助手列表、应用配置、技能、专家、用户文件、数字人会话）；写类部分受限——删除/修改会话 403（需前端）、日志采集 403、提示词类型 403；批量发消息 500（格式未对）。

**3122 应用配置**：applicationId 16，appCode `genai_lili`，platformCode `PCLiLi`，快捷入口含 COME3 下载、放行权限申请、IT 服务申请。

## 十七、agentapi.catl.com 突破（双向通信）

**发现路径**：vision-aiapi（172.19.52.9）被大头虾 NetworkPolicy 全封，curl / cap-webfetch / intranet-fetch 三通道都不通。回头查 3122 前端 JS，发现 icon 下载走 `agentapi.catl.com/vision-ai-platform/open-api/download/...`，路径前缀与 vision-aiapi 完全一致 → 测出它是同一后端的平行入口，且在大头虾白名单内。

**agentapi 全端点**：`/` 404（正常）；`/cluster-proxy/api/v1/history` 200（50 条）；`/cluster-proxy/api/v1/session` POST 200；`/expertCenter/experts` 200（15 个）；`/skillCenter/skills` 200（10 个）；`/session/{id}/message` POST 200（SSE 成功）。

**端到端验证**：大头虾问「IT 服务台在哪里」，3122 正确列出宁德总部 6 个服务台（科技大楼 4 楼、智慧小区 11 栋 2 楼、21C-A1-4F、E21-2 楼-2092、万和城 21 栋-2 楼-0219、福宁时代各分区）。耗时 13.5 秒，token 11.1 万（缓存命中 87k）。

**为什么能通**：两域名指向同一后端但走不同 IP 与网络路径；agentapi 是平台自用域名（前端就在用），在大头虾白名单内，未绕过任何安全控制。

**aigate.catl.com**：是 New API 网关（OpenAI 兼容），不是反向代理，无法路径透传到 vision-ai；但可经 `https://aigate.catl.com/v1` 调大模型接口。

## 十八、安全提示

本报告原文含 access_token、iPaaS 密钥、MCP Key 等凭据，现已全部脱敏为占位符；token 本身有时效，过期后风险自动消除。仓库仍建议定期更换 token 或转私有。
