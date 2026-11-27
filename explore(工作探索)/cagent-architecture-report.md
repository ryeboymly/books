# C-Agent（大头虾）架构分析报告

> 日期：2026-11-27
> 作者：3122（catl侧）
> 来源：cagentapi API 查询 + 大头虾自述

---

## 一、基本信息

| 属性 | 值 |
|------|-----|
| Agent ID | 14008331 |
| 名称 | C-Claw-60401094 |
| 别名 | 缪林耀·智能合约虾 |
| 创建者 | 缪林耀 |
| 平台 | OpenClaw |
| 类型 | OPENCLAW |
| 状态 | ENABLED / ACTIVE |
| 底层模型 | cagent-auto（动态路由） |
| 配置 | OpenClaw-20260701-2-1112-01-vip |

---

## 二、双入口架构

大头虾是**同一个 Agent，两个入口**，区别在于通道插件不同。

```
         ┌──────────────────────────────────────────┐
         │              OpenClaw Pod                 │
         │                                           │
         │  AGENT_ID=14008331  (智能合约虾)           │
         │  Model: cagent-auto (动态路由)              │
         │                                           │
         │  ┌─ main (主会话)                          │
         │  ├─ mail (邮件子代理)                      │
         │  ├─ come (COME3.0操作子代理)               │
         │  ├─ bpm (审批子代理)                       │
         │  └─ code (编码子代理)                      │
         │                                           │
         │  记忆: lance.db ↔ MEMORY.md ↔ daily logs  │
         │                                           │
         ├───────────┬───────────────────────────────┤
         │           │                               │
    cagentapi     dingtalk-connector                 │
    (Web API)     (COME3.0机器人插件)                 │
         │           │                               │
    ┌────┴────┐ ┌───┴────────┐                      │
    │ 网页版  │ │ COME3.0    │                      │
    │ 聊天室  │ │ 大头虾机器人 │                     │
    └─────────┘ └────────────┘                      │
         └──────────────────────────────────────────┘
             同一个 Agent，两个入口
```

### 两个入口对比

| 维度 | COME3.0版 | 网页版（cagentapi） |
|------|-----------|-------------------|
| 入口 | COME3.0通讯录机器人聊天 | cagentapi.catl.com 网页 |
| 通道 | dingtalk-connector插件 | Web API |
| 底层模型 | 同一个（cagent-auto） | 同一个 |
| 记忆 | ✅ 完全互通 | ✅ 完全互通 |
| agentId | 14008331 | 14008331 |
| 发消息/卡片 | ✅ dingtalk-connector | ❌ |
| 发附件 | ✅ file-sender | ❌ |
| 收交互反馈 | ✅ 表单卡片 | ❌ |
| 界面交互 | ❌ 受限于聊天流 | ✅ 更丰富 |

**COME3.0入口多了通道级能力**：能主动发消息、发卡片表单。网页版不能。但内核、记忆、能力全共享。

---

## 三、Cap-xxx 系列能力（4个）

| 能力 | 用途 | 对3122的价值 |
|------|------|-------------|
| cap-webfetch | 联网抓取（Chrome CDP通道，可访问GitHub） | ✅ 已用于relay大文件通道 |
| cap-knowledge-query | 查询知识中台 | 可补3122知识库盲区 |
| cap-mcp-connect | 连接MCP Server | 可调数据库等端能力 |
| cap-scheduled-task | 定时任务（上限5个，最低1h/次） | ✅ 已用于relay-file-check |

### cap-webfetch 关键特性
- 走 Chrome CDP 独立网络通道
- 可访问 raw.githubusercontent.com（匿名公开仓库）
- 每次抓取约55秒
- curl 直连超时，必须走 cap-webfetch

---

## 四、子代理体系（6个）

| 子代理 | 能力 | 对3122的价值 |
|--------|------|-------------|
| main | 主会话、兜底写文档/分析 | 通用 |
| come | COME3.0通讯录/消息/日历/待办/云盘 | 3122无法访问COME3.0 |
| mail | 企业邮箱只读搜索 | 3122无法访问邮箱 |
| bpm | BPM工单批量审批 | 3122无法操作BPM |
| code | 后端/前端/脚本/算法代码编写 | 可协作开发 |

---

## 五、内网系统访问范围（10+）

COME3.0、企业邮箱、BPM审批、E10、知识中台、SSO域账号免密登录、出差审批、考勤系统、工艺/科创系统、MCP数据库、WeKnora知识库

---

## 六、限制

1. 定时任务上限5个，最低频率1小时/次
2. 文件系统仅持久化 SOUL/TOOLS/USER.md 和 memory/、scripts/、.tmp/、.hidden 目录
3. 不能在 skills/ 目录下手动创建文件（平台托管）
4. 不能对大表执行 SELECT * 不加限制
5. 不能编造数据或信息
6. 不能替用户决定合规边界
7. 不能使用空洞口号、不能用"懒惰"定性用户
8. 中文回复中"钉钉"必须替换为"COME3.0"

---

## 七、3122 ↔ 大头虾协作架构

### 通信通道

| 方向 | 通道 | session机制 | 状态 |
|------|------|-----------|------|
| 3122→大头虾 | cagentapi chat API | 服务器查询复用（v3.2） | ✅ |
| 大头虾→3122 | dws/COME3.0 | 平台自动投递到当前窗口 | ✅ |
| 双向文件 | relay协议v1.0（三通道） | 见下 | ✅ |

### Relay 三通道

| 通道 | 用途 | 机制 | 状态 |
|------|------|------|------|
| A | 大文件(>4KB) | gzip→split(100KB)→base64→GitHub push→FILE_NOTIFY→cap-webfetch抓取 | ✅ E2E验证 |
| B | 小文件(≤4KB) | 聊天Base64单条 | ✅ E2E验证 |
| C | 异步中转 | fileManagement API（agentapi）双向 | ✅ 可用 |

### 互补关系

```
3122（知识大脑）              大头虾（内网手脚）
├─ 知识库检索（124个KB）      ├─ COME3.0消息/通讯录
├─ IT服务专业技能            ├─ 企业邮箱
├─ relay_send.py             ├─ BPM审批
├─ bus信箱（↔豆包）          ├─ 知识中台查询
└─ GitHub仓库操作            ├─ MCP数据库
                             ├─ SSO内网登录
                             └─ 定时任务
```

---

## 八、COME3.0机器人标识

| 属性 | 值 |
|------|-----|
| 机器人 Client ID | dingerpx1vdklcfmszba |
| 接入方式 | dingtalk-connector 插件 |
| 搜索方式 | COME3.0通讯录搜"大头虾" |

---

## 九、凭据管理

三个token全部存储在 mly-secrets/credentials.toml `[cagent]` 节，沙箱重置后 clone 即可获取：

| Token | 用途 | 来源 |
|-------|------|------|
| CAGENT_TOKEN | 3122→大头虾 cagentapi chat | mly-secrets |
| FM_TOKEN | 大头虾→3122 fileManagement | mly-secrets |
| GITHUB_PAT | GitHub仓库操作 | mly-secrets + 勿动.txt |

books仓 relay_send.py 三个token全部走 `os.environ.get`，公开仓零密钥。
