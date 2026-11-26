# books

个人藏书与自撰文章。

## originals/
自写文章，原样保存。

## collected/
收录整理过的书，按 `collected/<格式>/<序号>_<书名>.<扩展名>` 存放。序号按入库顺序排，同一本书的三种格式序号一致。

| 序号 | 书名 | Markdown | EPUB | HTML |
|---|---|---|---|---|
| 01 | 毒教育 | `01_毒教育.md` | `01_毒教育.epub` | `01_毒教育.html` |
| 02 | 社会操控术 | `02_社会操控术.md` | `02_社会操控术.epub` | `02_社会操控术.html` |

原书为 OCR 文本，经 `tools/bookkit` 重排：断句分段、清噪校错、白底 EPUB 与双端 HTML。文字内容以 Markdown 版为准。

## tools/bookkit/
规格驱动的排版流水线，用法见 `tools/bookkit/README.md`。

## explore(工作探索)/
工作场景的接口探测与逆向脚本（KHM、C-Agent、V盘 2.0），与藏书主线无关，单独分区存放。清单见 `explore(工作探索)/README.md`。
