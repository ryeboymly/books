# explore(工作探索)

工作场景里的接口探测与逆向脚本，跟藏书、排版这条主线无关，单独分区存放，不混进 `tools/`。

| 文件 | 说明 |
|---|---|
| `khm_upload.py` | KHM 知识中心文件上传，逆向自 khm.catl.com 前端 |
| `khm-upload-guide.md` | 上述脚本的接口说明与参数 |
| `cagent_api.py` | C-Agent 对话接口客户端，逆向自 cagent.catl.com |
| `cagent-api-guide.md` | 上述客户端的接口与方法说明 |
| `cagent-capability-report.md` | C-Agent 能力边界实测记录 |
| `vdrive_api.py` | V盘 2.0 接口客户端，逆向自 sdrivesmm.catl.com |
| `vdrive-api-guide.md` | 上述客户端的接口说明（GET 方法、上传表单） |

约定：

- 这里的产出是过程性探索材料，不保证稳定，接口随前端更新会失效。
- 与 `collected/`、`originals/`、`tools/bookkit/` 无依赖关系，删改互不影响。
- 新增同类探索放本目录，不要再往 `tools/` 里加。
