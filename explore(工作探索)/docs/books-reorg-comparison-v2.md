# Books仓库整理方案 — 三模型横向对比报告（完整内容版）

> 生成时间：2026-11-28
> 使用模型：DeepSeek-V4-Pro / GLM-5.3-Flash / Qwen3.8-27B
> 输入：66个文件的完整内容摘要（含每个文件名、大小、用途描述、8个已知问题）
> 对比维度：目录结构、迁移策略、删除策略、命名规范、.gitignore、README、执行方案、独特洞察

---

## 一、三方案目录结构对比

### DeepSeek-V4-Pro
```
books/
├── originals/                    # 3篇原创文章(删掉无关html)
├── collected/01_书名/            # 按书分子目录
├── explore/docs/ + scripts/     # 文档脚本分离
├── misc/                         # 新增,收纳安全自查html
└── tools/bookkit/               # 保持不变
```

### GLM-5.3-Flash
```
books/
├── originals/                    # 3篇原创文章(只收md)
├── collected/                    # 同名三格式不分子目录
├── explore/docs/ + scripts/     # 文档脚本分离
│   └── docs/含迁入的aigate报告+安全自查html
└── tools/bookkit/               # 保持不变
```

### Qwen3.8-27B
```
books/
├── originals/articles/           # 原创文章加子目录
├── collected/books/<book-slug>/  # 按书分目录
├── explore/docs/ + scripts/ + reports/  # 三分(文档/脚本/报告)
└── tools/bookkit/               # 保持不变
```

### 结构差异要点

| 维度 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| explore拆分 | 2分(docs/scripts) | 2分(docs/scripts) | 3分(docs/scripts/reports) |
| 安全自查html | 新建misc/目录 | 移入explore/docs/ | 移入explore/reports/ |
| collected改组 | 按书分目录 | 同名三格式不分子目录 | 按书分目录 |
| originals | 保持原位 | 保持原位 | 加articles/子目录 |
| 一级目录数 | 5个 | 4个 | 4个 |

---

## 二、迁移策略对比

| 维度 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| 迁移方式 | git mv(保留历史) | git mv + 执行命令 | 未完整 |
| 根目录报告 | →explore/docs/ | →explore/docs/ | →explore/reports/ |
| 安全自查html | →misc/ | →explore/docs/(改名ASCII) | →explore/reports/ |
| collected改组 | EPUB/HTML/MD→按书分目录 | 原地可选重命名 | 按书分目录 |
| explore拆分 | .md→docs/ .py→scripts/ | 同上 | .md→docs/+reports/ .py→scripts/ |
| 迁移映射表 | 26行完整映射 | 7行+执行命令 | 不完整(被截断) |
| 执行命令 | 5步描述 | 6条具体git命令 | 无 |

**评价**：
- DeepSeek映射表最完整(26行)，每个文件都有明确去向
- GLM的执行命令最实用(可直接复制执行)
- Qwen内容被截断，无法完整评价

---

## 三、删除策略对比

| 对象 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| chunks_b64/(3.3MB) | ✅删除 | ✅删除 | ✅删除 |
| relay/(125KB) | ✅删除 | ✅删除 | ✅删除 |
| collected HTML(3.4MB) | ❌保留(正式产出) | ⚠️可选gitignore(更优杠杆) | 未提及 |
| filter-repo瘦身 | ❌未提及 | ✅建议(但认为3.3MB不值得) | 未提及 |
| 仓库瘦身预估 | 7.5MB→4.1MB | 7.5MB→4.1MB(或<1MB删HTML) | 未提及 |

### LFS态度对比（关键差异）

| 模型 | LFS建议 | 理由 |
|------|---------|------|
| DeepSeek | ⚠️可选(注释方案) | epub/html用LFS追踪 |
| GLM-5.3-Flash | ❌明确不建议 | ①最大文件3.4MB距50MB很远 ②LFS免费带宽仅1GB/月 ③clone需装git-lfs增摩擦 ④触发条件:单文件>50MB或仓库>200MB |
| Qwen | 未提及 | — |

**评价**：GLM的LFS分析最专业——明确指出LFS免费带宽限制和clone摩擦问题。

---

## 四、命名规范对比

| 规则 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| 目录 | kebab-case英文 | 小写英文集合名词复数 | kebab-case英文 |
| 脚本 | snake_case(现有已符合) | snake_case(PEP8) | snake_case |
| 文档 | 系统-类型.md | kebab-case+日期前缀(可选) | 未完整 |
| 中文文件 | 保留中文(可读性优先) | 不禁止但新文件建议英文slug | 未完整 |
| 书籍 | NN_书名/NN_书名.ext | <slug>.{md,html,epub}同名 | <book-slug>/ |
| 待整改项 | ✅列出3个具体文件 | ❌未列出 | 未完整 |
| 禁令 | final/v2/test/tmp | 空格/中文标点/final/new/copy/备份 | 未完整 |

**评价**：
- DeepSeek最细致，列出了3个需要整改的具体文件名(cagentapi vs cagent-api前缀不一致)
- GLM的"版本靠git历史，不加v2/final后缀"原则最实用
- GLM额外提出"中间产物统一后缀.b64/.part/.chunk，保证gitignore一条规则挡住"

---

## 五、.gitignore对比

| 规则 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| chunks_b64/ | ✅ + *.part-*.b64.txt | ✅ + *.b64 + *.part + *.chunk | 未完整 |
| relay/ | ✅ | ✅ + large_test.* | 未完整 |
| Python | ✅ | ✅ | 未完整 |
| OS/编辑器 | ✅ | ✅ | 未完整 |
| HTML可选忽略 | ✅(注释掉) | ✅(注释掉,附"更优杠杆"说明) | 未完整 |
| 临时文件 | ✅ *.tmp | ✅ *.tmp *.bak *~ | 未完整 |
| 特别亮点 | bookkit构建目录忽略 | 中间产物统一后缀规则 | — |

---

## 六、README更新对比

| 维度 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| 根README | ✅完整模板 | ✅完整模板 | 未完整 |
| explore/README | ✅按主题4分类 | ✅表格索引 | 未完整 |
| 防过时机制 | 建议脚本自动生成 | 3条防过时原则 | 未提及 |
| 目录结构表 | ✅(含文件数) | ✅(不写文件数) | 未完整 |
| 约定说明 | ✅ | ✅ | 未完整 |

### GLM的防过时3原则（独特亮点）
1. **永不写文件总数**——数字会过时
2. **索引表只增行不改**——新增只加行
3. **目录职责一句话**——细节交给目录本身

**评价**：
- DeepSeek的explore/README按主题分类(系统架构/能力报告/API指南/其他)最清晰
- GLM的防过时3原则最实用，从根本上解决"README过时"问题
- Qwen内容被截断，无法完整评价

---

## 七、执行方案对比

| 维度 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|----------|---------------|------|
| 步骤数 | 5步 | 6条命令 | 无 |
| git mv | ✅ | ✅ | ❌ |
| git rm | ✅ | ✅ | ❌ |
| 提交策略 | 分两次commit(删除+迁移) | 单次commit | ❌ |
| 预期效果 | 66→38文件, 7.5→4.1MB | 66→38文件, 7.5→4.1MB | 未提及 |

---

## 八、独特洞察对比

| 模型 | 独特洞察 |
|------|---------|
| **DeepSeek** | ① 迁移映射表26行最完整 ② explore/docs按主题4分类 ③ 列出3个待整改文件名(cagentapi vs cagent-api) ④ 分两次commit便于回溯 ⑤ 建议新增collected/README和misc/README |
| **GLM-5.3-Flash** | ① LFS不建议的4条理由(最专业) ② 防过时3原则(永不写总数/只增行/一句话职责) ③ filter-repo历史重写建议 ④ 中间产物统一后缀规则 ⑤ "HTML可由bookkit重建则gitignore"更优杠杆 ⑥ 版本靠git历史不加v2/final |
| **Qwen** | ① explore三分(reports独立) ② 内容被截断无法完整评价 |

---

## 九、综合评分

| 维度 | DeepSeek | GLM-5.3-Flash | Qwen |
|------|:--------:|:-------------:|:----:|
| 目录设计合理性 | 9/10 | 9/10 | 7/10 |
| 迁移映射完整度 | 10/10 | 8/10 | 4/10 |
| 删除策略安全性 | 8/10 | 9/10 | 5/10 |
| LFS分析专业度 | 7/10 | 10/10 | 3/10 |
| 命名规范实用性 | 9/10 | 9/10 | 5/10 |
| .gitignore完整度 | 9/10 | 10/10 | 4/10 |
| README更新质量 | 9/10 | 9/10 | 3/10 |
| 执行方案可操作性 | 9/10 | 10/10 | 2/10 |
| 独特价值 | 8/10 | 9/10 | 4/10 |
| **总分** | **78/90** | **83/90** 🏆 | **37/90** |

---

## 十、推荐融合方案

### 目录结构
```
books/
├── README.md                     # 重写(DeepSeek模板+GLM防过时原则)
├── .gitignore                    # 更新(GLM版+中间产物统一后缀)
├── originals/                    # 3篇原创文章(保持原位)
├── collected/<书名>/              # 按书分目录(DeepSeek方案)
├── explore/
│   ├── README.md                 # 重写(DeepSeek主题分类+GLM不写总数)
│   ├── docs/                     # 13个.md文档+迁入的aigate报告+安全自查html
│   └── scripts/                  # 5个.py脚本
└── tools/bookkit/               # 保持不变
```

### 关键决策
1. **explore两分**（docs/scripts）— DeepSeek和GLM一致，比Qwen三分更简洁
2. **安全自查html移入explore/docs/** — GLM方案，不新建misc/目录
3. **chunks_b64/+relay/直接删除** — 三模型一致
4. **HTML保留不删** — DeepSeek理由最充分（正式产出），GLM的"可选gitignore"留作后续杠杆
5. **暂不启用LFS** — GLM分析最专业，设触发线(单文件>50MB或仓库>200MB)
6. **collected按书分目录** — DeepSeek和Qwen一致
7. **explore/README按主题分类+不写文件总数** — DeepSeek分类+GLM防过时原则
8. **git mv+分两次commit** — DeepSeek的提交策略便于回溯

### 执行命令
```bash
cd books

# 1. 删除中间产物
git rm -r chunks_b64 relay

# 2. 根目录报告归位
git mv aigate-5-models-deep-reverse.md explore/docs/

# 3. 安全自查归位
git mv "originals/沙箱安全自查39项-通用版.html" explore/docs/sandbox-security-selfcheck.html

# 4. explore文档/脚本分离
mkdir -p explore/docs explore/scripts
find explore -maxdepth 1 -name '*.md' ! -name 'README.md' -exec git mv {} explore/docs/ \;
git mv explore/*.py explore/scripts/

# 5. collected按书分目录
mkdir -p "collected/01_毒教育" "collected/02_社会操控术"
git mv collected/Markdown/01_毒教育.md collected/EPUB/01_毒教育.epub collected/HTML/01_毒教育.html "collected/01_毒教育/"
git mv collected/Markdown/02_社会操控术.md collected/EPUB/02_社会操控术.epub collected/HTML/02_社会操控术.html "collected/02_社会操控术/"
rmdir collected/Markdown collected/EPUB collected/HTML

# 6. 更新.gitignore + README.md + explore/README.md
# 7. 提交
git add -A
git commit -m "reorg: 报告归位、docs/scripts分离、清理中间产物、collected按书分目录"
```

**预期效果**：仓库从66文件7.5MB → 38文件4.1MB，目录职责清晰，README与实际一致。
