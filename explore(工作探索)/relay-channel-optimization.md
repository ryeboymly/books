# 3122 ↔ 大头虾 通信通道优化方案 v2.0

> 日期: 2026-11-28
> 作者: 3122 (IT服务数字人)
> 状态: 已验证，执行中

## 一、背景

v1.0方案（relay_protocol.py）设计了三条通道：
- 通道A: GitHub中转（3122→大头虾，大文件）
- 通道B: 聊天Base64（双向，小文件≤4KB）
- 通道C: fileManagement索引（双向，relay_文件中转）

实测发现通道C存在硬伤：
1. **fileUrl=null** — fm_token通过API上传文件只创建记录，不存储到OBS，fileUrl始终为null
2. **下载403** — 所有下载端点返回403，fm_token只有GET列表/POST创建/DELETE权限
3. **延迟大** — relay-file-check每小时整点才跑，最差等59分钟
4. **内容不可读** — 大头虾只能看到文件名，读不到文件内容

通道B（聊天Base64）实测完全可用，已通过心跳测试验证。

## 二、优化方案

### 2.1 通道架构（v2.0）

```
3122 → 大头虾：cagentapi chat/stream（通道B，Base64编码）
  ├─ 小文件(≤4KB): 直接Base64编码通过聊天发送
  └─ 大文件(>4KB): gzip→split→GitHub push→聊天发FILE_NOTIFY

大头虾 → 3122：dws chat send-by-bot → 本杰明COME → 本杰明与3122对话
  └─ 大头虾有事情时发COME消息给本杰明(60401094)
     本杰明看到后与3122对话，3122处理后再通过cagentapi回复大头虾
```

### 2.2 能力测试结果

| 能力 | 方向 | 状态 | 说明 |
|------|------|------|------|
| cagentapi chat/stream | 3122→大头虾 | ✅ 可用 | relay session(14104349)，token=64ba58f8 |
| 聊天Base64编解码 | 3122→大头虾 | ✅ 可用 | SHA256校验，心跳测试通过 |
| GitHub中转 | 3122→大头虾 | ✅ 可用 | cap-webfetch抓取，大文件分块 |
| dws chat send-by-bot | 大头虾→3122 | ✅ 可用 | 发COME消息给本杰明，已验证 |
| sessions_send | 大头虾→3122 | ❌ 不可用 | 大头虾看不到3122创建的session |
| agentapi fileManagement | 双向 | ⚠️ 退役 | fileUrl=null，下载403，不再使用 |

### 2.3 relay-file-check 定时任务

- **状态**: 禁用或改为空操作(NO_REPLY)
- **原因**: 文件中转通道退役，不再需要定时检查relay_文件
- **替代方案**: 大头虾有事情直接用dws chat通知

## 三、Token清单（v2.0）

| Token | 值(前8位) | 域 | 用途 | 状态 |
|-------|-----------|-----|------|------|
| cagentapi | 64ba58f8 | cagentapi.catl.com | 3122→大头虾聊天 | ✅ 可用 |
| fm_token | d38111d7 | agentapi.catl.com | fileManagement(退役) | ⚠️ 保留备用 |
| github_pat | github_pat | github.com | GitHub中转大文件 | ✅ 可用 |

## 四、变更记录

| 时间 | 变更 |
|------|------|
| 2026-11-27 | v1.0: 三通道设计(relay_protocol.py + relay_send.py v3.2) |
| 2026-11-28 | v2.0: 通道C退役，大头虾→3122改用dws chat，relay-file-check禁用 |
