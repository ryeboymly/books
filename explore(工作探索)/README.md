# explore(工作探索)

工作场景里的接口探测与逆向脚本，跟藏书、排版这条主线无关，单独分区存放。

## docs/

| 文件 | 主题 |
|------|------|
| 3122-system-architecture.md | 3122 系统运行机制（压缩版） |
| aigate.md | AI 网关逆向（三合一轮次合并版） |
| cagent-architecture.md | 大头虾架构与能力（五合一轮次合并版） |
| cagent-api.md | 大头虾 API 逆向（合并版） |
| khm-upload-guide.md | KHM 上传指南 |
| vdrive-api-guide.md | V 盘 API 指南 |
| vision-ai-api-reverse-report.md | 视觉 AI 逆向（压缩版） |
| relay-channel-optimization.md | 通信通道优化 v2.0 |

## archive/

一次性存档，只做留痕，不进首轮阅读。

| 文件 | 主题 |
|------|------|
| archive-2026-11-27.md | 11-27 工作存档 |
| books-reorg-comparison-v2.md | 仓库整理三模型对比报告 |

## scripts/

| 脚本 | 用途 |
|------|------|
| cagent_api.py | cagent 对话 API 客户端 |
| khm_upload.py | KHM 文件上传工具 |
| relay_protocol.py | 文件中转协议 v1.0 |
| relay_send.py | 文件中转发送工具 v3.2 |
| vdrive_api.py | V 盘 API CLI 工具 |

## 约定

- 这里的产出是过程性探索材料，不保证稳定，接口随前端更新会失效。
- 与 `collected/`、`originals/`、`tools/bookkit/` 无依赖关系，删改互不影响。
- 新增同类探索放本目录（docs/ 或 scripts/），不要再往 `tools/` 里加。
- 新增文件时在上方表格加一行，不要写"共 N 个"。
