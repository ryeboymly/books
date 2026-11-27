#!/usr/bin/env python3
"""
3122 侧文件中转发送工具 v3.2
================================
通道B: ≤4KB  单条聊天Base64（实测安全上限）
通道A: >4KB  gzip→split(100KB)→base64→GitHub push→聊天发FILE_NOTIFY
         大头虾用cap-webfetch逐块抓取→解码拼接→gunzip
v3.2: session从服务器查询复用，不依赖本地文件，沙箱重置无影响
"""
import base64, hashlib, json, math, os, subprocess, sys, time, http.client, ssl, tempfile, shutil

# ── 配置 ──
FM_HOST = "agentapi.catl.com"
FM_TOKEN = "e88063d6-0a1b-4ae2-9b81-e89ce226029d_3"
FM_BASE = "/vision-ai-platform/v1/fileManagement"
CAGENT_HOST = "cagentapi.catl.com"
CAGENT_TOKEN = "a4bd924d-6bf8-46ce-a888-1bdde99d13bc_3"
CAGENT_AGENT_ID = "14008331"
GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
GITHUB_REPO = "ryeboymly/books"
GITHUB_BRANCH = "main"
GITHUB_CHUNKS_DIR = "chunks_b64"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_CHUNKS_DIR}"

MAX_CHAT_FILE = 4 * 1024      # 4KB以下走单条聊天Base64
SPLIT_SIZE = 100 * 1024       # gzip后按100KB分块

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def _http(method, host, path, token, body=None, headers_extra=None):
    conn = http.client.HTTPSConnection(host, context=ctx)
    headers = {"Authorization": f"bearer {token}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if headers_extra:
        headers.update(headers_extra)
    data = json.dumps(body).encode() if body else None
    conn.request(method, path, body=data, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", "ignore")
    conn.close()
    return resp.status, raw


# ── cagentapi 聊天（session从服务器查询复用，不依赖本地文件）──
# 沙箱重置后也能从服务器找回旧session，不会新开窗口

def _find_latest_session():
    """从cagentapi服务器查询最新的relay session"""
    status, raw = _http("GET", CAGENT_HOST,
                        f"/c-agent/v1/chat/sessions?agentId={CAGENT_AGENT_ID}&page=0&size=5",
                        CAGENT_TOKEN)
    if status == 200:
        data = json.loads(raw)
        sessions = data.get("list", [])
        if sessions:
            return sessions[0].get("id")
    return None

def _create_session(title="relay"):
    status, raw = _http("POST", CAGENT_HOST, "/c-agent/v1/chat/sessions", CAGENT_TOKEN,
                        {"agentId": CAGENT_AGENT_ID, "content": title})
    if status in (200, 201):
        return json.loads(raw).get("id", "")
    return None

def _get_session():
    """先从服务器查已有session，没有才创建新的"""
    sid = _find_latest_session()
    if sid:
        return sid
    return _create_session()


def _stream_message(sid, content, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            conn = http.client.HTTPSConnection(CAGENT_HOST, context=ctx)
            body = json.dumps({"sessionId": sid, "content": content, "agentId": int(CAGENT_AGENT_ID)})
            conn.request("POST", "/c-agent/v1/chat/stream", body=body, headers={
                "Authorization": f"Bearer {CAGENT_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            })
            resp = conn.getresponse()
            if resp.status != 200:
                raw2 = resp.read().decode("utf-8", "ignore")
                conn.close()
                if attempt < max_retries:
                    time.sleep(3)
                    continue
                return f"ERROR: HTTP {resp.status}: {raw2[:200]}"
            full = ""
            for line in resp:
                line = line.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                p = line[5:].strip()
                if p == "[DONE]":
                    break
                try:
                    c = json.loads(p)
                    piece = c.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if piece:
                        full += piece
                except:
                    pass
            conn.close()
            return full if full else "(空回复)"
        except Exception as e:
            if attempt < max_retries:
                time.sleep(3)
                continue
            return f"ERROR: {e}"
    return "ERROR: 重试耗尽"


def cagent_send(content, max_retries=2):
    """发送消息，复用持久化session。失效时自动重建。"""
    for attempt in range(max_retries + 1):
        sid = _get_session()
        if not sid:
            if attempt < max_retries:
                print(f"  [重试 {attempt+1}/{max_retries}] session创建失败")
                time.sleep(3)
                continue
            return "ERROR: 无法创建session"
        reply = _stream_message(sid, content)
        if reply.startswith("ERROR") and attempt < max_retries:
            print(f"  [重试 {attempt+1}/{max_retries}] {reply[:80]}")
            time.sleep(3)
            continue
        return reply
    return "ERROR: 重试耗尽"


# ── 通道B: 小文件聊天Base64 ──

def send_small_file(filepath, note=""):
    with open(filepath, "rb") as f:
        data = f.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode()
    filename = os.path.basename(filepath)

    note_str = f"\n备注: {note}" if note else ""
    prompt = f"""[文件中转协议v3] 3122发来一个小文件，请解析处理。

FILE_START:{filename}:{size}:{sha256}
FILE_DATA:{b64}
FILE_END:{filename}:{sha256}

请：
1. 解码FILE_DATA的base64
2. 计算SHA256校验，确认与FILE_START一致
3. 回复 FILE_ACK:{filename}:ok 或 FILE_ACK:{filename}:error:原因
4. 保存到 workspace/.tmp/{filename}{note_str}"""

    reply = cagent_send(prompt)
    return None, reply


# ── 通道A: 大文件 gzip+split+GitHub ──

def send_large_file(filepath, note=""):
    """大文件: gzip→split(100KB)→base64→push GitHub→聊天发FILE_NOTIFY
    大头虾用cap-webfetch逐块抓取→解码拼接→gunzip"""
    filename = os.path.basename(filepath)
    ascii_name = filename.encode("ascii", "ignore").decode() or "file"
    with open(filepath, "rb") as f:
        data = f.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()

    # 1. gzip压缩
    print(f"  1/4 gzip压缩...", end=" ", flush=True)
    tmpdir = tempfile.mkdtemp()
    gz_path = os.path.join(tmpdir, f"{ascii_name}.gz")
    import gzip
    with gzip.open(gz_path, "wb") as gz:
        gz.write(data)
    gz_size = os.path.getsize(gz_path)
    print(f"{size}→{gz_size} bytes ({gz_size*100//size}%)")

    # 2. split分块 + base64编码
    print(f"  2/4 split+base64...", end=" ", flush=True)
    with open(gz_path, "rb") as gf:
        gz_data = gf.read()
    parts = []
    for i in range(0, len(gz_data), SPLIT_SIZE):
        chunk = gz_data[i:i + SPLIT_SIZE]
        b64_chunk = base64.b64encode(chunk).decode()
        part_name = f"{ascii_name}.gz.part-{chr(ord('a') + i // SPLIT_SIZE // 26)}{chr(ord('a') + i // SPLIT_SIZE % 26)}.b64.txt"
        parts.append((part_name, b64_chunk))
    total_parts = len(parts)
    print(f"{total_parts} 块")

    # 3. push到GitHub
    print(f"  3/4 push到GitHub...", end=" ", flush=True)
    repo_dir = os.path.join(tmpdir, "repo")
    clone_url = f"https://x-access-token:{GITHUB_PAT}@github.com/{GITHUB_REPO}.git"
    r = subprocess.run(["git", "clone", "--depth", "1", clone_url, repo_dir],
                       capture_output=True, timeout=30)
    if r.returncode != 0:
        return None, f"ERROR: git clone失败: {r.stderr.decode()[:200]}"

    chunks_dir = os.path.join(repo_dir, GITHUB_CHUNKS_DIR)
    os.makedirs(chunks_dir, exist_ok=True)
    # 清理旧的同名分块
    for old in os.listdir(chunks_dir):
        if old.startswith(f"{ascii_name}.gz.part-"):
            os.remove(os.path.join(chunks_dir, old))
    # 写入新分块
    for part_name, b64_data in parts:
        with open(os.path.join(chunks_dir, part_name), "w") as pf:
            pf.write(b64_data)

    subprocess.run(["git", "config", "user.email", "60401094@catl.com"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.name", "ryeboymly"], cwd=repo_dir)
    subprocess.run(["git", "add", "-A"], cwd=repo_dir)
    r2 = subprocess.run(["git", "commit", "-m", f"relay: {ascii_name} ({total_parts} chunks)"], cwd=repo_dir, capture_output=True)
    if r2.returncode != 0 and "nothing to commit" not in r2.stderr.decode():
        return None, f"ERROR: git commit失败: {r2.stderr.decode()[:200]}"
    r3 = subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True, timeout=30)
    if r3.returncode != 0:
        return None, f"ERROR: git push失败: {r3.stderr.decode()[:200]}"
    print("done")

    # 4. 聊天发FILE_NOTIFY（<4KB）
    print(f"  4/4 发送FILE_NOTIFY通知...", end=" ", flush=True)
    raw_url = f"{GITHUB_RAW_BASE}/{ascii_name}.gz.part-aa.b64.txt"
    note_str = f"\n备注: {note}" if note else ""
    notify = f"""[文件中转协议v3-大文件] 3122发来文件 {filename}，已分块推送到GitHub。

FILE_NOTIFY:{filename}:{size}:{sha256}:{total_parts}:{ascii_name}

请用cap-webfetch逐块抓取以下URL（每块约55秒）:
{GITHUB_RAW_BASE}/{ascii_name}.gz.part-XX.b64.txt
分块名: aa, ab, ac... 到 {chr(ord('a')+(total_parts-1)//26)}{chr(ord('a')+(total_parts-1)%26)}

处理步骤:
1. cap-webfetch抓取每个分块URL，提取base64内容
2. 逐块base64解码，二进制拼接（不能先拼base64再统一解码）
3. gunzip解压拼接后的数据
4. 计算SHA256，应为: {sha256}
5. 保存到 workspace/.tmp/{filename}
6. 回复 FILE_ACK:{filename}:ok 或 FILE_ACK:{filename}:error:原因{note_str}"""

    reply = cagent_send(notify)
    print("sent")

    # 清理临时目录
    shutil.rmtree(tmpdir, ignore_errors=True)
    return None, reply


# ── 路由 ──

def send_file(filepath, note=""):
    size = os.path.getsize(filepath)
    if size <= MAX_CHAT_FILE:
        return send_small_file(filepath, note)
    else:
        return send_large_file(filepath, note)


def send_message(text):
    return cagent_send(text)


# ── CLI ──

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 relay_send.py <文件> [--note '备注']   # 发送文件")
        print("  python3 relay_send.py --msg '消息'             # 发纯文本")
        print("  python3 relay_send.py --list                   # 查看relay文件")
        sys.exit(1)

    if sys.argv[1] == "--list":
        status, raw = _http("GET", FM_HOST, f"{FM_BASE}/user/page?page=0&size=50", FM_TOKEN)
        files = json.loads(raw) if status == 200 else []
        relay = [f for f in files if isinstance(f, dict) and str(f.get("fileName", "")).startswith("relay_")]
        if not relay:
            print("没有relay文件")
        for f in relay:
            print(f"  id={f.get('id')} name={f.get('fileName')}")
        return

    if sys.argv[1] == "--msg":
        if len(sys.argv) < 3:
            print("请提供消息内容")
            sys.exit(1)
        print(f"发送消息: {sys.argv[2][:50]}...")
        reply = send_message(sys.argv[2])
        print(f"回复:\n{reply}")
        return

    filepath = sys.argv[1]
    note = ""
    if "--note" in sys.argv:
        idx = sys.argv.index("--note")
        note = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""

    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        sys.exit(1)

    size = os.path.getsize(filepath)
    channel = "B(聊天Base64)" if size <= MAX_CHAT_FILE else "A(gzip+split+GitHub)"
    print(f"发送: {filepath} ({size} bytes) via {channel}")

    file_id, reply = send_file(filepath, note)
    print(f"\n大头虾回复:\n{reply}")


if __name__ == "__main__":
    main()
