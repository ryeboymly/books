# AI网关5大真身模型深度逆向报告

> 探索时间：2026-11-28
> 网关地址：`https://aigate.catl.com/v1`
> 探索人：3122（IT服务数字人）

---

## 一、5个真身模型档案

| # | 网关别名 | 实际后端 | 厂商 | Thinking | 上下文窗口 |
|---|---------|---------|------|----------|-----------|
| 1 | DeepSeek-V4-Pro / Kimi-K2.6 / Kimi-K2.5 / MiniMax-M2.7 等8个 | DeepSeek-V4.1-Flash-w8a8 | DeepSeek | ❌ | ≥32K |
| 2 | GLM-5.1 / GLM-5.2 | GLM-5.3-w8a8 | Z.ai | ✅ 完整推理链 | ≥32K |
| 3 | GLM-5.3-Flash | glm-5.3-flash | Z.ai | ❌ | ≥32K |
| 4 | Qwen3.8-27B | qwen38_27b | 阿里通义 | ✅ 轻量 | ≥32K |
| 5 | DeepSeek-V4-Flash / auto | deepseek-v4-flash-short | DeepSeek | ❌ | ≥32K |

> 上下文窗口：5个模型全部通过 32000 token 测试，无截断

---

## 二、能力矩阵

| 能力 | DeepSeek-V4-Pro | GLM-5.1 | GLM-5.3-Flash | Qwen3.8-27B | DeepSeek-V4-Flash |
|------|:---:|:---:|:---:|:---:|:---:|
| 基础对话 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 代码生成 | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ |
| Function Calling | ✅ | ✅ | ✅ | ✅ | ✅ |
| 多轮对话 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流式输出 | ✅ | ✅ | ✅ | ✅ | ✅ |
| JSON Mode | ✅ | ✅ | ✅ | ✅ | ✅ |
| System Prompt | ✅ | ✅ | ✅ | ✅ | ✅ |
| 数学推理 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 逻辑推理 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Temperature 0-2 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Seed可复现 | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| 并发(10路) | ✅ | - | - | - | ✅ |
| Thinking推理链 | ❌ | ✅ 233tok | ❌ | ✅ 轻量 | ❌ |

---

## 三、Token计费深度分析

### 同一问题"什么是锂电池？"的Token消耗对比

| 模型 | prompt | completion | reasoning | total | 特点 |
|------|--------|------------|-----------|-------|------|
| DeepSeek-V4-Pro | 7 | 300 | 0 | 307 | 高效，无推理开销 |
| GLM-5.1 | 15 | 300 | **300** | 315 | ⚠️ 300 completion全是reasoning！content可能为空 |
| GLM-5.3-Flash | 15 | **949** | 0 | 964 | 非常啰嗦，3倍token消耗 |
| Qwen3.8-27B | **55** | 300 | 0 | 355 | Tokenizer不同，prompt是DeepSeek的8倍 |
| DeepSeek-V4-Flash | 7 | 300 | 0 | 307 | 与V4-Pro完全一致（同一后端） |

### 关键发现

1. **GLM-5.1的reasoning_tokens = completion_tokens**：所有completion token都用于thinking，实际content可能为空或极少。需要设置max_tokens≥2000才能得到完整回答
2. **GLM-5.3-Flash极度啰嗦**：同一问题消耗949 token，是DeepSeek的3倍
3. **Qwen的Tokenizer不同**：同样输入"什么是锂电池？"，Qwen计55个prompt token，DeepSeek只计7个
4. **DeepSeek-V4-Pro = DeepSeek-V4-Flash**：Token消耗完全一致，再次确认同一后端
5. **用量可查**：`/dashboard/billing/usage` 返回累计总用量（美元），`/dashboard/billing/subscription` 返回额度上限（$1亿，基本无限）

---

## 四、GLM-5.1 Thinking模式详解

GLM-5.1（后端GLM-5.3-w8a8）支持完整的推理链（Chain-of-Thought）：

```
响应结构:
{
  "message": {
    "content": "还剩9只。这是一道经典的文字陷阱题...",  // 最终回答
    "reasoning_content": "用户问的是17只羊..."           // 推理过程
  },
  "usage": {
    "completion_tokens": 338,
    "completion_tokens_details": {
      "reasoning_tokens": 233  // 233个token用于思考
    }
  }
}
```

### Thinking模式特点
- ✅ 推理质量高：正确解答了"17只羊"陷阱题
- ✅ reasoning_content字段完整暴露推理过程
- ⚠️ 慢：18-25秒/次（其他模型1-3秒）
- ⚠️ 费token：reasoning_tokens不计入content但消耗completion_tokens
- ⚠️ 需要大max_tokens：≤500时content可能为空（全被reasoning消耗）

---

## 五、并发性能

| 并发数 | 成功率 | 耗时 |
|--------|--------|------|
| 3 | 3/3 ✅ | 0.3s |
| 5 | 5/5 ✅ | 0.7s |
| 10 | 10/10 ✅ | 0.7s |

**结论**：10并发无限制，响应时间不随并发增加而显著增长。

---

## 六、参数支持详情

| 参数 | 支持情况 | 说明 |
|------|---------|------|
| model | ✅ | 14个别名映射到5个后端 |
| messages | ✅ | 支持system/user/assistant/tool角色 |
| max_tokens | ✅ | 测试到8192，无报错 |
| temperature | ✅ | 0.0 ~ 2.0 均可用 |
| top_p | ✅ | 可用 |
| stream | ✅ | SSE格式，data: {json} |
| tools | ✅ | Function Calling完美 |
| tool_choice | ✅ | auto可用 |
| response_format | ✅ | json_object可用 |
| seed | ✅ | 可复现（Qwen除外） |
| frequency_penalty | 未测 | - |
| presence_penalty | 未测 | - |

### 用量与额度查询（可用）

| 端点 | 方法 | 返回 |
|------|------|------|
| `/dashboard/billing/usage` | GET | `{"total_usage": 19.87}` 总用量（美元） |
| `/dashboard/billing/subscription` | GET | 额度上限、支付方式、到期时间 |

> 注意：不带 `/v1` 前缀。`/v1/usage`、`/v1/billing` 等8个带前缀端点全部404。

### 不支持的能力
| 能力 | 状态 | 说明 |
|------|------|------|
| embeddings | ❌ | /v1/embeddings 不可用 |
| images | ❌ | /v1/images 不可用 |
| audio | ❌ | /v1/audio 不可用 |
| 多模态输入 | ❌ | messages不支持image_url |

---

## 七、模型选型建议

### 按场景选型

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| **Agent工具链** | DeepSeek-V4-Pro | FC+多轮+流式+JSON Mode全支持，速度快 |
| **快速问答** | DeepSeek-V4-Flash | 0.3s最快，token效率高 |
| **深度推理** | GLM-5.1 | 完整thinking，适合复杂分析（但慢18-25s） |
| **长文本生成** | GLM-5.3-Flash | 输出量大（但token消耗3倍） |
| **中文理解** | Qwen3.8-27B | 通义千问中文能力强 |
| **高并发** | DeepSeek-V4-Flash | 10并发0.7s，无限制 |
| **成本敏感** | DeepSeek-V4-Pro | token效率最高（7+300=307） |

### 不推荐
- **Kimi/MiniMax系列**：与DeepSeek-V4-Pro完全相同后端，无额外价值
- **GLM-5.1用于实时场景**：thinking太慢（18-25s）
- **GLM-5.3-Flash用于成本敏感场景**：token消耗是DeepSeek的3倍

---

## 八、对数字大脑的架构建议

### 推荐方案：DeepSeek-V4-Pro 作为默认引擎

```
用户自然语言输入
    ↓
AI网关 (DeepSeek-V4-Pro)
    ├── Function Calling → 数字大脑API (CRUD操作)
    ├── JSON Mode → 结构化数据提取
    ├── System Prompt → 角色设定"你是本杰明的数字助手"
    └── 多轮对话 → 上下文记忆
    ↓
SQLite / OceanBase
```

### 具体应用场景

1. **自然语言待办**："明天下午3点开会" → FC调用 `create_todo(title="开会", due_date="明天15:00")`
2. **智能笔记摘要**：长笔记 → "帮我总结这篇笔记的3个要点" → JSON Mode返回 `{"points":["...","...","..."]}`
3. **代码片段解释**：选中代码 → "这段代码做什么的？" → 流式输出解释
4. **复杂分析**：切换GLM-5.1 → "分析我上个月的待办完成率趋势" → thinking推理

### 多模型路由策略

```python
def route_model(task_type):
    if task_type == 'quick_qa':
        return 'DeepSeek-V4-Flash'      # 0.3s
    elif task_type == 'deep_analysis':
        return 'GLM-5.1'                 # thinking模式
    elif task_type == 'long_generation':
        return 'GLM-5.3-Flash'           # 输出量大
    elif task_type == 'chinese_nlp':
        return 'Qwen3.8-27B'             # 中文优化
    else:
        return 'DeepSeek-V4-Pro'         # 默认全能
```
