#!/usr/bin/env python3
"""bookkit —— OCR 文本到可读电子书的一条流水线。

用法：
    python3 bookkit.py <spec.yml> --src <原文.md> --out <输出目录> [--no-html] [--no-epub]

输入：一份 OCR 出来的 Markdown（长段落粘连、带水印）+ 一份书规格（章节结构、清洗规则、人工修正）。
输出：<书名>-精排版.md / <书名>-精排版-正文.md / <书名>.html（内嵌字体）/ <书名>.epub

规格字段见 README.md；范例见 specs/毒教育.yml。
"""
import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # 允许无 pyyaml 时用 JSON 规格
    yaml = None

HERE = Path(__file__).resolve().parent

NOISE_LINES = set()
NOISE_SUBSTR = []
MANUAL = {}
FIX_MAP = []
CHAPTERS = []
MANUAL_START = {}
BOOK_TITLE = ""
BOOK_SUBTITLE = ""
AUTHOR = ""
LANG = "zh-CN"
PACK_LO, PACK_HI = 170, 330
MD_PACK_LO, MD_PACK_HI = 170, 150  # 仅 md 交付版使用：桌面阅读器无版心，靠薄段控节奏
PREFACE = ""
SENT_END = "。！？"
CLOSE = "」』”’）)》"


def apply_spec(spec: dict) -> None:
    """把规格里的键灌进模块级全局，供 build()/render_md() 使用。"""
    global NOISE_LINES, NOISE_SUBSTR, MANUAL, FIX_MAP, CHAPTERS, MANUAL_START
    global BOOK_TITLE, BOOK_SUBTITLE, AUTHOR, LANG, PACK_LO, PACK_HI, PREFACE

    book = spec.get("book", {})
    BOOK_TITLE = book.get("title", "未命名")
    BOOK_SUBTITLE = book.get("subtitle", "")
    AUTHOR = book.get("author", "")
    LANG = book.get("lang", "zh-CN")

    NOISE_LINES = set(int(x) for x in spec.get("noise_lines", []))
    NOISE_SUBSTR = list(spec.get("noise_substr", []))
    MANUAL = {int(k): v for k, v in (spec.get("manual") or {}).items()}
    FIX_MAP = [tuple(x) for x in spec.get("fix_map", [])]
    MANUAL_START = {int(k): int(v) for k, v in (spec.get("manual_start") or {}).items()}

    chapters = []
    for ch in spec["chapters"]:
        secs = []
        for s in ch.get("sections", []):
            idx, name = int(s[0]), s[1]
            lead = s[2] if len(s) > 2 else ""
            secs.append((idx, name, lead))
        chapters.append((ch["title"], secs))
    CHAPTERS = chapters

    pack = spec.get("pack") or {}
    PACK_LO = int(pack.get("lo", 170))
    PACK_HI = int(pack.get("hi", 330))
    PREFACE = spec.get("preface") or f"本文为《{BOOK_TITLE}》的排版重制版：原文经 OCR 识别，本版只做断句、分段、章节分层、标点统一与错字替换，不改动作者原意。"


def load_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yml", ".yaml"):
        if yaml is None:
            sys.exit("需要 pyyaml 才能读 YAML 规格：pip install pyyaml")
        return yaml.safe_load(text)
    return json.loads(text)

LINES = []

def clean_line(text: str) -> str:
    for pat in NOISE_SUBSTR:
        text = re.sub(pat, "", text)
    for a, b in FIX_MAP:
        text = text.replace(a, b)
    text = text.replace("，,", "，").replace("。。", "。")
    text = text.replace("。，", "。").replace("，。", "。")
    text = text.replace("，，", "，").replace("。。", "。")
    text = text.replace("、，", "，").replace("，、", "，")
    text = text.replace("。—", "。")
    text = text.lstrip("。，、；：")
    if text.endswith("：\u201c"):
        text = text[:-2]
    text = text.lstrip("\u201d")
    text = re.sub(r"[ \t]+", " ", text)
    # 数字/英文与中文之间补半角空格
    text = re.sub(r"(?<=[\u4e00-\u9fa5])([0-9A-Za-z])", r" \1", text)
    text = re.sub(r"([0-9A-Za-z])(?=[\u4e00-\u9fa5])", r"\1 ", text)
    # 中文语境里的半角标点转全角
    text = re.sub(r"(?<=[\u4e00-\u9fa5]),(?=[\u4e00-\u9fa5])", "，", text)
    text = re.sub(r"(?<=[\u4e00-\u9fa5])!(?=[\u4e00-\u9fa5])", "！", text)
    text = re.sub(r"(?<=[\u4e00-\u9fa5])\?(?=[\u4e00-\u9fa5])", "？", text)
    text = re.sub(r"(?<=[\u4e00-\u9fa5]):(?=[\u4e00-\u9fa5])", "：", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    out, buf, depth = [], "", 0
    for ch in text:
        buf += ch
        if ch in "「『“‘（(《":
            depth += 1
        elif ch in "」』”’）)》":
            depth = max(0, depth - 1)
        if ch in SENT_END and depth == 0:
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    return [s for s in out if s]


def cut_long(s: str, hi: int = 340) -> list[str]:
    if len(s) <= hi:
        return [s]
    out, buf = [], ""
    for piece in re.split(r"(?<=[，；：])", s):
        if len(buf) + len(piece) > hi and buf:
            out.append(buf)
            buf = piece
        else:
            buf += piece
    if buf.strip():
        out.append(buf)
    return [x.strip() for x in out if x.strip()]


def pack(sentences: list[str], lo=None, hi=None) -> list[str]:
    lo = PACK_LO if lo is None else lo
    hi = PACK_HI if hi is None else hi
    sentences = [piece for s in sentences for piece in cut_long(s, hi=max(hi - 20, 280))]
    paras, buf = [], ""
    for s in sentences:
        cand = buf + s
        if len(cand) > hi and buf:
            paras.append(buf)
            buf = s
        else:
            buf = cand
            if len(buf) >= lo:
                paras.append(buf)
                buf = ""
    if buf:
        paras.append(buf)
    return [p.strip() for p in paras if p.strip()]


def is_dialogue(text: str) -> bool:
    return text.startswith("——“") or text.startswith("——\"") or text.startswith("——") or text.startswith("问：") or text.startswith("答：")


def is_list_item(text: str) -> bool:
    return bool(re.match(r"^(\d+[、，,.]|[①②③④⑤⑥⑦⑧⑨]|•|- )", text))


def build():
    lines = [MANUAL.get(i, l) for i, l in enumerate(LINES)]

    # 计算每章行区间
    bounds = []
    for ci, (title, secs) in enumerate(CHAPTERS):
        starts = [item[0] for item in secs]
        end = starts[0] if starts else None
        bounds.append(None)
    # 章起点 = 第一个小节行；无小节则用人工指定起点表
    manual_start = dict(MANUAL_START)
    body_start = 2

    chapters = []
    starts = []
    for ci, (title, secs) in enumerate(CHAPTERS):
        if secs:
            starts.append(min(item[0] for item in secs))
        else:
            starts.append(manual_start[ci])
    starts[0] = body_start
    for ci, v in manual_start.items():
        if ci != 0:
            starts[ci] = v
    ends = [starts[i + 1] - 1 if i + 1 < len(starts) else len(lines) - 1 for i in range(len(starts))]

    sec_map = {}
    for _, secs in CHAPTERS:
        for item in secs:
            idx, name = item[0], item[1]
            lead = item[2] if len(item) > 2 else ""
            sec_map[idx] = (name, lead)

    for ci, (title, secs) in enumerate(CHAPTERS):
        blocks = []
        cur_para: list[str] = []
        cur_kind = "para"

        def flush():
            nonlocal cur_para
            if not cur_para:
                return
            joined = "".join(cur_para)
            for p in pack(split_sentences(joined)):
                blocks.append(("para", p))
            cur_para = []

        i = starts[ci]
        while i <= ends[ci]:
            raw = lines[i].strip()
            i += 1
            if not raw or i - 1 in NOISE_LINES or i - 1 == 0:
                continue
            line_no = i - 1
            if line_no in NOISE_LINES:
                continue
            text = clean_line(raw)
            if not text:
                continue
            if line_no in sec_map:
                flush()
                name, lead = sec_map[line_no]
                blocks.append(("h3", name))
                if lead:
                    lead = clean_line(lead)
                    for para in pack(split_sentences(lead)):
                        blocks.append(("para", para))
                elif text.startswith(name):
                    rest = text[len(name):].lstrip(" 　，、。；：")
                    if rest:
                        cur_para.append(rest)
                continue
            if "‖‖" in text:
                head, text = text.split("‖‖", 1)
                flush()
                blocks.append(("h3", head.strip()))
                text = text.strip()
            if text.startswith("‖e‖"):
                rest = text[3:]
                parts = rest.split("‖p‖")
                flush()
                blocks.append(("epigraph", parts[0].strip()))
                for part in parts[1:]:
                    for para in pack(split_sentences(part.strip())):
                        blocks.append(("para", para))
                continue
            if "⁂" in text:
                parts = [x.strip() for x in text.split("⁂") if x.strip()]
                flush()
                for part in parts:
                    if part.startswith("- ") or re.match(r"^(\d+[、，,.]|[①②③④⑤⑥⑦⑧⑨])", part):
                        body = part[2:] if part.startswith("- ") else part
                        blocks.append(("li", re.sub(r"^(\d+[、，,.]|[①②③④⑤⑥⑦⑧⑨])\s*", "", body)))
                    else:
                        for para in pack(split_sentences(part)):
                            blocks.append(("para", para))
                continue
            if "‖p‖" in text:
                parts = [x.strip() for x in text.split("‖p‖") if x.strip()]
                flush()
                for part in parts:
                    for para in pack(split_sentences(part)):
                        blocks.append(("para", para))
                continue
            if "‖" in text:
                parts = [x.strip() for x in text.split("‖") if x.strip()]
                flush()
                if parts:
                    blocks.append(("epigraph", parts[0]))
                for part in parts[1:]:
                    for para in pack(split_sentences(part)):
                        blocks.append(("para", para))
                continue
            if line_no == 2:                     # 题记英文
                flush()
                blocks.append(("epigraph", text))
                continue
            if text.startswith("问：") and "答：" not in text:
                flush()
                blocks.append(("q", text[2:].strip()))
                continue
            if text.startswith("答："):
                flush()
                blocks.append(("a", text[2:].strip()))
                continue
            if is_list_item(text):
                flush()
                blocks.append(("li", re.sub(r"^(\d+[、，,.]|[①②③④⑤⑥⑦⑧⑨])\s*", "", text)))
                continue
            if is_dialogue(text):
                flush()
                blocks.append(("dialog", text))
                continue
            cur_para.append(text)

        flush()
        chapters.append({"title": title, "blocks": blocks})

    # 去掉相邻重复段（OCR 重复行）
    for ch in chapters:
        seen, dedup = None, []
        for kind, text in ch["blocks"]:
            if kind == "para" and text == seen:
                continue
            dedup.append((kind, text))
            seen = text if kind == "para" else None
        ch["blocks"] = dedup

    return chapters


def render_md(chapters, style="html") -> str:
    """style="html" 保持旧结构（供 HTML/EPUB 的中间正文）；
    style="md" 为桌面阅读优化版：书名 H1/章 H2/节 H3 + 目录锚点链接 + 更薄的段长。"""
    md_mode = style == "md"
    out = [
        "---",
        f'title: "{BOOK_TITLE}"',
        f'subtitle: "{BOOK_SUBTITLE}"',
        f'author: "{AUTHOR}"',
        f"lang: {LANG}",
        "---",
        "",
        f"# {BOOK_TITLE}",
        "",
        f"**{BOOK_SUBTITLE}**",
        "",
        f"> {PREFACE}",
        "",
        "## 目录",
        "",
    ]
    for ci, ch in enumerate(chapters, 1):
        if md_mode:
            out.append(f"- [第 {ci} 章　{ch['title']}](#ch{ci:02d})")
            sj = 0
            for kind, text in ch["blocks"]:
                if kind == "h3":
                    sj += 1
                    out.append(f"  - [{text}](#ch{ci:02d}-s{sj:02d})")
        else:
            out.append(f"{ci}. {ch['title']}")
            for kind, text in ch["blocks"]:
                if kind == "h3":
                    out.append(f"   - {text}")
    out.append("")
    for ci, ch in enumerate(chapters, 1):
        sj = 0
        if md_mode:
            out += [f'<a id="ch{ci:02d}"></a>', "", f"## 第 {ci} 章　{ch['title']}", ""]
        else:
            out += [f"# 第 {ci} 章　{ch['title']}", ""]
        list_open = False
        for kind, text in ch["blocks"]:
            if kind == "h3":
                if list_open:
                    out.append("")
                    list_open = False
                if md_mode:
                    sj += 1
                    out += [f'<a id="ch{ci:02d}-s{sj:02d}"></a>', "", f"### {text}", ""]
                else:
                    out += [f"## {text}", ""]
            elif kind == "epigraph":
                parts = text.split("\n")
                first = True
                for pt in parts:
                    if not first:
                        out.append(">")
                    out.append(f"> {pt}")
                    first = False
                out.append("")
            elif kind == "q":
                if list_open:
                    out.append("")
                    list_open = False
                out += [f"> **问**：{text}", ""]
            elif kind == "a":
                if list_open:
                    out.append("")
                    list_open = False
                out += [f"**答**：{text}", ""]
            elif kind == "li":
                out.append(f"- {text}")
                list_open = True
            elif kind == "dialog":
                if list_open:
                    out.append("")
                    list_open = False
                out += [text, ""]
            else:
                if list_open:
                    out.append("")
                    list_open = False
                if md_mode:
                    for p in pack(split_sentences(text), lo=MD_PACK_LO, hi=MD_PACK_HI):
                        out += [p, ""]
                else:
                    out += [text, ""]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def subset_fonts(chars: str, outdir: Path, serif_ttc: str, sans_ttc: str) -> dict:
    """按正文用字子集化字体，返回 {serif:/path, sans:/path}；字体缺失或 pyftsubset 缺失时返回空。"""
    outdir.mkdir(parents=True, exist_ok=True)
    res = {"serif": outdir / "serif.woff2", "sans": outdir / "sans-bold.woff2"}
    if not Path(serif_ttc).exists():
        return {}
    chars_file = outdir / "_chars.txt"
    chars_file.write_text(chars, encoding="utf-8")
    cmds = [
        [sys.executable, "-m", "fontTools.subset", serif_ttc, "--font-number=2",
         f"--text-file={chars_file}", "--flavor=woff2", "--layout-features=*",
         "--no-hinting", f"--output-file={res['serif']}"],
    ]
    if Path(sans_ttc).exists():
        res["sans"] = outdir / "sans-bold.woff2"
        cmds.append([sys.executable, "-m", "fontTools.subset", sans_ttc, "--font-number=2",
                     f"--text-file={chars_file}", "--flavor=woff2", "--layout-features=*",
                     "--no-hinting", f"--output-file={res['sans']}"])
    else:
        res.pop("sans")
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True)
        if r.returncode != 0:
            print("字体子集化失败：", r.stderr.strip()[:300], file=sys.stderr)
            return {}
    chars_file.unlink(missing_ok=True)
    return res


def build_html(body_html: str, toc_html: str, spec: dict, fonts: dict) -> str:
    css = (HERE / "book.css").read_text(encoding="utf-8")
    if fonts:
        serif_b64 = base64.b64encode(fonts["serif"].read_bytes()).decode()
        css = css.replace("{{SERIF}}", serif_b64)
        if fonts.get("sans"):
            css = css.replace("{{SANS}}", base64.b64encode(fonts["sans"].read_bytes()).decode())
        else:
            css = css.replace("{{SANS}}", serif_b64)
    else:
        css = re.sub(r"@font-face\{[^}]*\}\n?", "", css)

    tpl = (HERE / "book.html").read_text(encoding="utf-8")
    sub = spec.get("book", {}).get("subtitle", "")
    if len(sub) > 8:
        tpl = tpl.replace('<div class="cv-side"><span class="sub">{{SUBTITLE}}</span></div>',
                          '<div class="cv-side sub-long-wrap"><span class="sub-long">{{SUBTITLE}}</span></div>')
    return (tpl.replace("{{CSS}}", css)
                .replace("{{TOC}}", toc_html)
                .replace("{{BODY}}", body_html)
                .replace("{{TITLE}}", spec.get("book", {}).get("title", ""))
                .replace("{{SUBTITLE}}", spec.get("book", {}).get("subtitle", ""))
                .replace("{{AUTHOR}}", spec.get("book", {}).get("author", ""))
                .replace("{{LANG}}", spec.get("book", {}).get("lang", "zh-CN")))


def md_to_html_body(md_text: str) -> str:
    r = subprocess.run(["pandoc", "-f", "markdown", "-t", "html5", "--section-divs"],
                       input=md_text, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("pandoc 转换失败：" + r.stderr)
    body = r.stdout

    def split_h1(m):
        text = m.group(1)
        parts = re.split("　", text, maxsplit=1)
        if len(parts) == 2:
            return f'<h1 class="chapter"><span class="kicker">{parts[0]}</span><span class="ctitle">{parts[1]}</span></h1>'
        return f'<h1 class="chapter"><span class="ctitle">{text}</span></h1>'

    return re.sub(r"<h1[^>]*>(.*?)</h1>", split_h1, body, flags=re.S)


def build_toc(body_html: str) -> str:
    items = []
    for m in re.finditer(r'<h([12])(?: id="([^"]*)")?[^>]*>(.*?)</h\1>', body_html, flags=re.S):
        level, hid, raw = m.group(1), m.group(2), m.group(3)
        txt = re.sub(r"<[^>]+>", "", raw).replace("　", " ").strip()
        items.append((level, hid, txt))

    groups = []
    for lvl, hid, txt in items:
        if lvl == "1":
            groups.append({"id": hid, "title": txt, "subs": []})
        elif groups:
            groups[-1]["subs"].append((hid, txt))

    def split_num(title):
        m = re.match(r"^(第\s*\d+\s*章)\s*(.*)$", title)
        if m:
            return m.group(1).replace(" ", ""), m.group(2).strip()
        return "", title

    rows = ['<nav class="toc" id="toc"><h2 class="toc-title">目录</h2><ol class="toc-list">']
    for g in groups:
        num, tt = split_num(g["title"])
        num_html = f'<span class="num">{num}</span>' if num else ""
        rows.append(f'<li class="lvl1"><a href="#{g["id"]}">{num_html}<span class="tt">{tt}</span></a>')
        if g["subs"]:
            rows.append('<ol class="sub">')
            for hid, txt in g["subs"]:
                rows.append(f'<li class="lvl2"><a href="#{hid}">{txt}</a></li>')
            rows.append("</ol>")
        rows.append("</li>")
    rows.append("</ol></nav>")
    return "\n".join(rows)


def run_pandoc_epub(md_body: Path, out: Path, spec: dict) -> None:
    book = spec.get("book", {})
    cmd = ["pandoc", str(md_body), "-o", str(out),
           "--css", str(HERE / "epub.css"),
           "--epub-title-page=true",
           "-M", f"title={book.get('title','')}",
           "-M", f"author={book.get('author','')}",
           "-M", f"lang={book.get('lang','zh-CN')}",
           "--toc-depth=2", "-M", "toc-title=目录"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("EPUB 生成失败：" + r.stderr)
    print("EPUB", out, out.stat().st_size, "B")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--src", required=True, help="OCR 原文 Markdown")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--slug", default=None, help="输出文件名（默认取书名）")
    ap.add_argument("--no-html", action="store_true")
    ap.add_argument("--no-epub", action="store_true")
    ap.add_argument("--serif-ttc", default="/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc")
    ap.add_argument("--sans-ttc", default="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
    args = ap.parse_args()

    spec = load_spec(Path(args.spec))
    apply_spec(spec)
    src = Path(args.src)
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    slug = args.slug or spec.get("book", {}).get("title", "book")

    lines = [x.rstrip("\n") for x in src.read_text(encoding="utf-8").split("\n")]
    global LINES
    LINES = lines

    chapters = build()
    md = render_md(chapters, style="md")          # 交付给阅读器的 md
    md_strict = render_md(chapters, style="html")  # HTML/EPUB 的中间正文，保持旧结构
    md_path = outdir / f"{slug}-精排版.md"
    md_path.write_text(md, encoding="utf-8")
    preface = spec.get("front_matter") or ""
    body_md = ((preface + "\n\n") if preface else "") + (md_strict[md_strict.index("# 第 1 章"):] if "# 第 1 章" in md_strict else md_strict)
    body_path = outdir / f"{slug}-精排版-正文.md"
    body_path.write_text(body_md, encoding="utf-8")

    stats = {
        "章": len(chapters),
        "节": sum(1 for ch in chapters for k, _ in ch["blocks"] if k == "h3"),
        "段": sum(1 for ch in chapters for k, _ in ch["blocks"] if k == "para"),
        "列表项": sum(1 for ch in chapters for k, _ in ch["blocks"] if k == "li"),
        "字数": len(re.sub(r"\s", "", md_strict)),
        "最长段": max((len(t) for ch in chapters for k, t in ch["blocks"] if k == "para"), default=0),
    }
    print("排版", md_path, md_path.stat().st_size, "B", json.dumps(stats, ensure_ascii=False))

    if not args.no_html:
        body_html = md_to_html_body(body_md)
        toc = build_toc(body_html)
        chars = "".join(sorted(set(md_strict))) + "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz，。！？、；：“”‘’（）《》【】…—·　％"
        fonts = subset_fonts(chars, outdir / "fonts", args.serif_ttc, args.sans_ttc)
        html = build_html(body_html, toc, spec, fonts)
        html_path = outdir / f"{slug}.html"
        html_path.write_text(html, encoding="utf-8")
        print("HTML", html_path, html_path.stat().st_size, "B")

    if not args.no_epub:
        run_pandoc_epub(body_path, outdir / f"{slug}.epub", spec)


if __name__ == "__main__":
    main()
