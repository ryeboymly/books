# AI网关深度逆向报告（第二轮·端点+参数+基础设施）

> 探测时间：2026-11-28
> 探测方：3122 (工号<工号>)
> 网关地址：https://aigate.catl.com
> API Key：<略>(已存入密钥库)

---

## 一、基础设施逆向（新发现）

### 响应头暴露的完整技术栈

| 响应头 | 值 | 含义 |
|--------|-----|------|
| `x-new-api-version` | `0.11.2-plus.2` | 网关用 **New API**（One API 增强分支），版本 0.11.2-plus.2 |
| `x-oneapi-request-id` | `20261128114651...` | 确认 One API 系列后端 |
| `x-envoy-decorator-operation` | `kubesphere-router-...svc.cluster.local:80/*` | 运行在 **KubeSphere**（K8s），用 **Envoy** 代理 |
| `x-envoy-upstream-service-time` | `1147` | 上游服务耗时(ms) |
| `system_fingerprint` | `vllm-0.30.0-tp2-dp8-ep-66995d43` | 推理引擎 **vLLM 0.30.0**，TP=2(张量并行) DP=8(数据并行) EP(专家并行) |

**架构推断**：
```
用户 → Envoy(KubeSphere Ingress) → New API v0.11.2(路由/计费/限流) → vLLM 0.30.0(GPU推理)
```

---

## 二、端点清单（完整扫描）

### 可用端点

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/v1/chat/completions` | POST | ✅ 200 | 核心对话端点，支持流式/非流式 |
| `/v1/models` | GET | ✅ 200 | 返回14个模型，全 owned_by=custom |
| `/dashboard/billing/usage` | GET | ✅ 200 | 总用量($26.46) |
| `/dashboard/billing/subscription` | GET | ✅ 200 | 额度($1亿) |

### 端点存在但无权限

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/v1/audio/transcriptions` | POST | ⚠️ 403 | 端点存在！需要 whisper-1 模型权限 |
| `/v1/moderations` | POST | ⚠️ 403 | 端点存在！需要 text-moderation-stable 权限 |
| `/v1/files` | GET | ⚠️ 403 | 端点存在，token无模型权限 |

### 端点存在但后端未配置

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/v1/embeddings` | POST | ❌ 404 | 网关转发但后端返回 bad_response_status_code |
| `/v1/images/generations` | POST | ❌ 404 | 同上 |
| `/v1/audio/speech` | POST | ❌ 404 | 同上 |

### 完全不支持

| 端点 | 状态 |
|------|------|
| `/v1/assistants` | ❌ Invalid URL |
| `/v1/threads` | ❌ Invalid URL |
| `/v1/batches` | ❌ Invalid URL |
| `/v1/fine_tuning/jobs` | ❌ Invalid URL |
| `/v1/vector_stores` | ❌ Invalid URL |

### Dashboard端点

| 端点 | 返回类型 | 说明 |
|------|----------|------|
| `/dashboard/billing/usage` | JSON | ✅ 唯一返回JSON的用量端点 |
| `/dashboard/billing/subscription` | JSON | ✅ 唯一返回JSON的额度端点 |
| `/dashboard/billing/usage_by_model` | HTML | 返回Web页面，非API |
| `/dashboard/models` | HTML | 同上 |
| `/dashboard/keys` | HTML | 同上 |
| `/dashboard/organizations` | HTML | 同上 |
| `/dashboard/users` | HTML | 同上 |
| `/dashboard/rate_limits` | HTML | 同上 |

---

## 三、隐藏模型发现

### `auto` 模型路由

`/v1/models` 列出14个模型，但还有一个 **未列出的第15个模型**：

| 模型名 | 是否在/v1/models中 | 说明 |
|--------|-------------------|------|
| `deepseek-v4-flash-short` | ❌ 未列出 | `auto`模型实际路由目标 |

**测试**：5个不同问题（你好/写诗/量子力学/1+1=/翻译）全部路由到 `deepseek-v4-flash-short`，说明 auto 是固定路由而非智能选择。

### 完整模型清单（15个）

| # | 模型别名 | 真身后端(已知) | 备注 |
|---|---------|---------------|------|
| 1 | DeepSeek-V4-Pro | DeepSeek-V4.1-Flash-w8a8 | 主力模型 |
| 2 | DeepSeek-V4-Flash | DeepSeek-V4.1-Flash-w8a8 | |
| 3 | DeepSeek-V4.1-Flash | DeepSeek-V4.1-Flash-w8a8 | |
| 4 | GLM-5.1 | GLM-5.1 | 有thinking模式 |
| 5 | GLM-5.2 | GLM-5.1 | |
| 6 | GLM-5.3 | GLM-5.1 | |
| 7 | GLM-5.3-Flash | GLM-5.1 | |
| 8 | Kimi-K2.5 | ? | |
| 9 | Kimi-K2.5-nonthinking | ? | |
| 10 | Kimi-K2.6 | ? | |
| 11 | MiniMax-M2.5 | ? | |
| 12 | MiniMax-M2.7 | ? | |
| 13 | Qwen3.8-27B | ? | |
| 14 | auto | deepseek-v4-flash-short | 隐藏路由 |
| 15 | deepseek-v4-flash-short | ? | **隐藏模型，未列出** |

---

## 四、高级参数支持矩阵

| 参数 | 支持 | 验证方式 | 说明 |
|------|:----:|----------|------|
| `temperature` | ✅ | 已知 | 采样温度 |
| `max_tokens` | ✅ | 已知 | 最大生成token |
| `top_p` | ✅ | 本轮测试 | 核采样 |
| `top_k` | ✅ | **新发现** | Top-K采样，vLLM原生支持 |
| `presence_penalty` | ✅ | **新发现** | 存在惩罚 |
| `frequency_penalty` | ✅ | **新发现** | 频率惩罚 |
| `seed` | ✅ | **新发现** | 可复现输出，3次同seed结果完全一致 |
| `n` | ✅ | **新发现** | 多候选生成，n=3返回3个候选 |
| `stop` | ✅ | **新发现** | 停止序列，命中后finish_reason=stop |
| `logprobs` | ✅ | **新发现** | 返回对数概率 |
| `top_logprobs` | ✅ | **新发现** | 返回Top-N对数概率 |
| `response_format` (json_object) | ✅ | **新发现** | JSON模式 |
| `response_format` (json_schema) | ✅ | **新发现** | 结构化输出，按schema生成JSON |
| `stream` | ✅ | 已知 | SSE流式 |
| `tools` (FC) | ✅ | 已知 | 函数调用 |
| `multimodal` (image_url) | ✅ | **新发现** | 支持base64图片输入 |

---

## 五、关键能力验证

### 1. seed可复现性 ✅
```
seed=999, temperature=0, 连续3次请求
→ 结果完全一致，system_fingerprint一致
→ vLLM 0.30.0 原生支持确定性输出
```

### 2. 多模态图片输入 ✅
```
data:image/png;base64,... → HTTP 200
→ 网关接受base64图片，不依赖外部URL
→ 注意：外部URL会超时（网关可能无法访问外网）
```

### 3. 结构化输出 ✅
```
response_format: json_schema → HTTP 200
→ 支持按JSON Schema约束输出
→ 可用于数字大脑的自然语言操作层
```

### 4. 上下文窗口 ✅
```
42,000字符输入 → prompt_tokens=24,017 → 成功
→ 至少支持24K+ prompt tokens
→ 之前已验证32K上下文
```

### 5. 并发无限制 ✅
```
20并发请求 → 全部成功，总耗时0.4s
→ 无x-ratelimit-*响应头
→ 网关层面不限速（限制可能在vLLM侧）
```

---

## 六、与第一轮逆向的增量对比

| 维度 | 第一轮已知 | 本轮新增 |
|------|-----------|---------|
| 模型数 | 14个别名→5个真身 | +1隐藏模型(deepseek-v4-flash-short) |
| 端点 | chat/models/billing | +audio/moderations/files(存在但无权限) |
| 参数 | temperature/max_tokens/stream/FC | +seed/n/stop/logprobs/top_k/json_schema/多模态 |
| 基础设施 | 未知 | New API v0.11.2 + KubeSphere + vLLM 0.30.0 |
| 速率限制 | 10并发通过 | 20并发0.4s全通过，无限制 |
| 上下文 | 32K通过 | 24K prompt tokens精确计量 |

---

## 七、对数字大脑的可用价值

| 能力 | 数字大脑应用场景 |
|------|----------------|
| `response_format: json_schema` | 自然语言→结构化指令，用户说"记一笔账"→自动生成{type:"expense",amount:?,category:?} |
| `seed` + `temperature:0` | 需要确定性输出的场景（分类、提取） |
| `multimodal` | 用户上传图片→AI识别内容→存入数字大脑 |
| `n` 多候选 | 重要决策生成多个方案供选择 |
| `logprobs` | 置信度评估，低置信度时提示用户确认 |
| `auto`模型 | 简单问答自动路由到最快模型，省token |
| 无限并发 | 批量处理任务不受限 |
