# books

个人藏书与自撰文章仓库，兼存放工作探索脚本与电子书排版工具。

## 目录结构

| 路径 | 内容 |
|------|------|
| `originals/` | 自撰文章 |
| `collected/` | 藏书成品，一书三格式同名：`<NN_书名>.md/.html/.epub` |
| `explore(工作探索)/docs/` | 工作报告与技术文档 |
| `explore(工作探索)/scripts/` | 探索脚本（cagent / khm / relay / vdrive） |
| `tools/bookkit/` | 排版工具：md → html/epub |

## 藏书

| 书 | 文件 |
|----|------|
| 01 毒教育 | `collected/01_毒教育/01_毒教育.{md,html,epub}` |
| 02 社会操控术 | `collected/02_社会操控术/02_社会操控术.{md,html,epub}` |

原书为 OCR 文本，经 `tools/bookkit` 重排：断句分段、清噪校错、白底 EPUB 与双端 HTML。文字内容以 Markdown 版为准。

## bookkit

```bash
python tools/bookkit/bookkit.py <spec.yml>
```

用法见 `tools/bookkit/README.md`。

## 约定

1. 报告进 `explore(工作探索)/docs/`，脚本进 `explore(工作探索)/scripts/`，根目录只留 README/.gitignore
2. 中间产物（`chunks_b64/`、`*.b64`）与测试大文件不入库
3. 新增文档/脚本时在 `explore(工作探索)/README.md` 索引表加一行——只增行，不写"共 N 个"
