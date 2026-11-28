# AI 网关 (aigate.catl.com) 能力探索报告

> 探测时间: 2026-11-28
> 探测方: 3122 (IT服务数字人)
> API Key: sk-yQ9...(已存入 mly-secrets)

## 一、端点清单

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/v1/models` | GET | ✅ 可用 | 14个模型 |
| `/v1/chat/completions` | POST | ✅ 可用 | 核心接口，支持多轮对话 |
| `/v1/completions` | POST | ✅ 可用 | 旧版补全接口 |
| `/v1/dashboard/billing/usage` | GET | ✅ 可用 | 用量查询 |
| `/health` | GET | ✅ 可用 | 健康检查 |
| `/v1/embeddings` | POST | ❌ 403 | token无embedding模型权限 |
| `/v1/images/generations` | POST | ❌ 403 | 不支持图片生成 |
| `/v1/audio/transcriptions` | POST | ❌ 403 | 不支持语音转文字 |
| `/v1/audio/speech` | POST | ❌ 403 | 不支持语音合成 |
| `/v1/moderations` | POST | ❌ 403 | 不支持内容审核 |

## 二、核心能力测试

### 2.1 Function Calling ✅
- 模型能理解工具定义并返回结构化 tool_calls
- 测试: 定义 get_weather 函数 → 模型返回 `{"city": "北京"}`
- **意义**: 可用于构建 AI Agent 工具链

### 2.2 流式输出 ✅
- `stream: true` 正常返回 SSE 格式数据
- 逐 token 输出，适合实时交互场景

### 2.3 多轮对话 + System Prompt ✅
- 正确理解 system role
- 跨轮次记忆正常（记住"本杰明"）

### 2.4 旧版 Completions ✅
- `/v1/completions` 可用（非聊天格式）
- 适合补全类任务

## 三、模型能力对比

同一问题："用一句话解释什么是RAG"

| 模型 | 状态 | prompt_tokens | completion_tokens | 回复特点 |
|------|------|---------------|-------------------|----------|
| DeepSeek-V4.1-Flash | ✅ | 15 | 40 | 最简洁，token效率最高 |
| GLM-5.3 | ✅ | 15 | 49 | 最详细，提到"可溯源" |
| Qwen3.8-27B | ✅ | 63 | 60 | prompt_tokens异常高(可能内部处理) |
| Kimi-K2.5 | ✅ | 15 | 45 | 准确，提到"文档" |
| MiniMax-M2.5 | ✅ | 15 | 47 | 提到"实时、专有" |

## 四、可用模型全览（14个）

| 模型 | 类型 | 推荐场景 |
|------|------|----------|
| DeepSeek-V4.1-Flash | 快速推理 | 日常问答、代码生成（快+省） |
| DeepSeek-V4-Pro | 深度推理 | 复杂逻辑、数学、长代码 |
| GLM-5.3 | 中文优化 | 中文长文、内容创作 |
| GLM-5.3-Flash | 快速中文 | 中文快速问答 |
| GLM-5.1/5.2 | 旧版 | 备用 |
| Qwen3.8-27B | 通用 | 多语言、代码 |
| Kimi-K2.5 | 长上下文 | 超长文档分析 |
| Kimi-K2.5-nonthinking | 快速模式 | 简单问答 |
| Kimi-K2.6 | 最新版 | 复杂推理 |
| MiniMax-M2.5 | 创意 | 创意写作、角色扮演 |
| MiniMax-M2.7 | 最新创意 | 高质量创意内容 |
| auto | 自动路由 | 让网关自动选模型 |

## 五、用量

- 当前总用量: $0.539（测试消耗）
- 计费方式: 按 token 计费

## 六、3122 实用场景

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 代码生成/审查 | DeepSeek-V4-Pro | 代码能力最强 |
| 知识库问答增强 | DeepSeek-V4.1-Flash | 快速+省token |
| 长文档摘要 | Kimi-K2.6 | 超长上下文 |
| 中文内容创作 | GLM-5.3 | 中文优化 |
| Function Calling Agent | DeepSeek-V4.1-Flash | 工具调用测试通过 |
| 多方案对比 | auto + 多模型 | 各模型并行回答取最优 |

## 七、限制

1. **无 Embedding** — 不能做向量检索，RAG 需用其他方案
2. **无图片/音频** — 纯文本接口
3. **Key 可能过期** — 与 cagentapi token 同样的生命周期问题
4. **沙箱不持久** — 调用脚本需从 GitHub 仓恢复
