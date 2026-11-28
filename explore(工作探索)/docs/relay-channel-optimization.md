# 3122 ↔ 大头虾 通信通道 v2.0

> 2026-11-28，3122（IT 服务数字人）；状态：已验证，执行中

## 一、为什么改

v1.0（`relay_protocol.py`）三通道：A GitHub 中转（大文件）、B 聊天 Base64（≤4KB）、C fileManagement 索引。

通道 C 的硬伤：`fileUrl` 恒为 null（API 上传只建记录、不入 OBS）；下载端点全 403（fm_token 只有列表/创建/删除权限）；relay-file-check 每小时才跑，最差等 59 分钟；大头虾只能看到文件名、读不到内容。

通道 B 心跳测试通过，保留为主通道。

## 二、v2.0 架构

```
3122 → 大头虾：cagentapi chat/stream
  ├─ ≤4KB：Base64 编码直接发
  └─ >4KB：gzip → split → GitHub push → 聊天发 FILE_NOTIFY

大头虾 → 3122：dws chat send-by-bot → 本杰明 COME → 本杰明转 3122 → 3122 经 cagentapi 回
```

## 三、能力矩阵

| 能力 | 方向 | 状态 | 说明 |
|---|---|---|---|
| cagentapi chat/stream | 3122→大头虾 | ✅ | relay session 14104349 |
| 聊天 Base64 | 3122→大头虾 | ✅ | SHA256 校验，心跳通过 |
| GitHub 中转 | 3122→大头虾 | ✅ | cap-webfetch 抓取，分块 |
| dws chat send-by-bot | 大头虾→3122 | ✅ | 发 COME 消息给本杰明 |
| sessions_send | 大头虾→3122 | ❌ | 大头虾看不到 3122 建的 session |
| agentapi fileManagement | 双向 | ⚠️ 退役 | fileUrl=null、下载 403 |

## 四、relay-file-check

已禁用（通道 C 退役），替代方案是大头虾有事先用 dws chat 直发。

## 五、Token

| Token | 前缀 | 域 | 用途 | 状态 |
|---|---|---|---|---|
| cagentapi | `<cagentapi_token前缀>` | cagentapi.catl.com | 3122→大头虾聊天 | ✅ |
| fm_token | `<fm_token>` | agentapi.catl.com | fileManagement（退役） | ⚠️ 备用 |
| github_pat | `github_pat` | github.com | 大文件中转 | ✅ |

## 六、变更

- 2026-11-27 v1.0：三通道（`relay_protocol.py` + `relay_send.py` v3.2）
- 2026-11-28 v2.0：通道 C 退役，大头虾→3122 改 dws chat，relay-file-check 禁用
