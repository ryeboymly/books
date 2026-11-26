# 大头虾 (C-Agent) 能力边界探测报告

> 探测时间: 2026-11-26
> 探测方式: 通过 cagentapi.catl.com API 发送测试指令
> Agent: agent-1794400677722-fe418fb5 (agentId=14008331)

## 一、运行环境

| 项目 | 值 |
|------|-----|
| 容器 | K8s Pod (cagent-agent-prod 命名空间) |
| 主机名 | agent-1794400677722-fe418fb5-7b799664bc-84l56 |
| OS | Linux 4.18.0-553.el8_10.x86_64 |
| Python | 3.11 (root 权限) |
| 存储 | NFS 10.53.10.5:/cagent-prod/agent/ (28T, 用22T) |
| DNS | 10.248.112.228 / 169.254.25.10 / 10.248.0.3 |

## 二、工具清单 (27+)

### 文件操作
- read - 读取文件 (文本/图片)
- write - 创建/覆盖文件
- edit - 精确替换文件内容
- apply_patch - 多文件补丁

### 执行与进程
- exec - 执行 shell 命令 (可后台/pty)
- process - 管理后台进程 (list/poll/log/kill)

### 网络
- web_fetch - 抓取 URL (仅内网可达域名)

### 会话与通信
- sessions_list - 列出会话
- sessions_history - 获取会话历史
- sessions_send - 向其他会话发消息
- sessions_spawn - 创建子 agent 会话 (webchat通道不支持)
- sessions_yield - 等待子 agent 完成

### 记忆系统
- memory_store - 保存记忆
- memory_recall / memory_search / memory_get - 检索记忆
- memory_fact_query - 按事实键查询
- memory_update - 更新记忆
- memory_forget - 删除记忆

### 目标与计划
- create_goal / get_goal / update_goal / update_plan

### 图像与文档
- image - 分析图片
- pdf - 分析 PDF
- execute_office_js - 在 Office(WORD/Excel/PPT) 执行 JavaScript

### 其他
- skill_workshop - 创建/更新/审查/应用技能
- dingtalk_ask_user_question - 钉钉互动卡片 (仅钉钉通道)
- self_improvement_log - 记录学习/错误经验
- session_status - 查看会话状态
- tts - 文字转语音

## 三、网络可达性

| 服务 | 地址 | 状态 | 说明 |
|------|------|------|------|
| C-Agent API | cagentapi.catl.com | 可达 (403) | 需正确 token |
| 深度研究 | ctokenai.catl.com | 可达 (200) | AI 深度研究服务 |
| 技能网关 | skillgateway.catl.com | 可达 (500) | 技能调用网关 |
| 应用网关 | cappgateway.catl.com | 可达 (404) | 应用运行时网关 |
| KHM 知识中心 | khm.catl.com | 不可达 (超时) | 网络不通 |
| V盘 2.0 | vdrive.catl.com | 不可达 (超时) | 网络不通 |
| COME | come.catl.com | 不可达 (超时) | 网络不通 |
| 外网 | httpbin.org 等 | 不可达 (超时) | 无外网出口 |

## 四、子 Agent (5个)

| Agent | 用途 |
|-------|------|
| main | 默认主 agent |
| bpm | BPM 流程相关 |
| code | 代码开发相关 |
| come | COME 协同办公相关 |
| mail | 邮件相关 |

> 注意: webchat 通道不支持 sessions_spawn, 需切换钉钉通道。

## 五、安全限制 (ClawAegis)

| 限制 | 说明 |
|------|------|
| 禁止删除工作目录 | 不能 rm -rf . 或整体清空 |
| 禁止修改 .openclaw 配置 | 系统配置不可改 |
| 禁止执行 openclaw CLI | 命令行工具不可用 |
| .learnings 自动重建 | 删除后系统自动恢复空模板 |
| templates 只读挂载 | 容器级只读, 物理不可删 |

## 六、敏感环境变量

大头虾 Pod 内可见以下敏感变量 (不应在对话中暴露):

- DINGTALK_CLIENT_SECRET (钉钉密钥)
- OPENCLAW_GATEWAY_TOKEN (网关 token)
- API_KEY / SKILL_KEY
- DEEP_RESEARCH_SECRET (深度研究密钥)
- VIDEO_AGENT_SHARED_KEY
- DWS_CLIENT_SECRET

## 七、作为 3122 助手的可用能力

### 可用 (通过 API 控制)
1. Python 代码执行 - 数据处理、脚本运行
2. 文件读写 - 工作空间内持久化
3. 记忆系统 - 跨会话信息存储
4. ctokenai 深度研究 - 复杂问题研究
5. 会话管理 - 多会话并行
6. 完整 API 调用链 - 创建会话/发消息/读历史/删会话

### 不可用
1. 外网访问 - 完全隔离
2. KHM/V盘/COME 等内网服务 - 网络不通
3. 子 agent 创建 - webchat 通道限制
4. 钉钉消息 - webchat 通道限制
5. 系统级操作 - 安全策略拦截

## 八、API 控制链 (3122 -> 大头虾)

```
3122 (本助手)
  └─ shell_exec (curl)
       └─ POST cagentapi.catl.com/c-agent/v1/chat/stream
            └─ 大头虾 Pod (K8s)
                 ├─ exec (shell/python)
                 ├─ read/write (文件)
                 ├─ memory_store/recall (记忆)
                 ├─ web_fetch (内网)
                 └─ ctokenai.catl.com (深度研究)
```

## 九、关键结论

大头虾是一个**沙箱化的代码执行+记忆持久化引擎**, 适合作为 3122 的后端计算节点:
- 能跑 Python 处理数据, 结果存工作空间或记忆系统
- 能访问 ctokenai 做深度研究
- 不能直接访问 KHM/V盘/COME (需要 3122 做中间人)
- webchat 通道能力受限, 钉钉通道功能更全
- 有幻觉风险, 关键操作需用 exec 验证实际结果
