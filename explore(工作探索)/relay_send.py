#!/usr/bin/env python3
"""
3122 侧文件中转发送工具 v2
修复: 小文件不再注册假URL, fileManagement改用agentapi, 增加重试

用法:
  python3 relay_send.py <文件路径> [--note "备注"]
  python3 relay_send.py --list          # 查看fileManagement中的relay文件
  python3 relay_send.py --check         # 检查大头虾回复
  python3 relay_send.py --msg "消息"    # 发纯文本消息（不发文件）
"""
import base64, hashlib, json, math, os, sys, time, http.client, ssl

# ── 配置 ──
# fileManagement: 用agentapi（大头虾也能访问）
FM_HOST = "agentapi.catl.com"
FM_TOKEN = "e88063d6-0a1b-4ae2-9b81-e89ce226029d_3"
FM_BASE = "/vision-ai-platform/v1/fileManagement"

# cagentapi: 3122→大头虾 聊天通道
CAGENT_HOST = "cagentapi.catl.com"
CAGENT_TOKEN = "a4bd924d-6bf8-46ce-a888-1bdde99d13bc_3"
CAGENT_AGENT_ID = "14008331"

# GitHub: 大文件中转
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ryeboymly/books/main/relay"

MAX_CHAT_FILE = 100 * 1024  # 100KB以下走聊天Base64
CHUNK_SIZE = 30 * 1024      # Base64分块大小

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


# ── fileManagement 操作（agentapi域名）──

def fm_register(filename, file_url, file_type="txt"):
    """注册文件到fileManagement，返回(id, resp_dict)"""
    body = {"fileName": filename, "fileUrl": file_url, "fileType": file_type}
    status, raw = _http("POST", FM_HOST, FM_BASE, FM_TOKEN, body)
    if status == 200:
        d = json.loads(raw)
        return d.get("id"), d
    return None, {"error": f"HTTP {status}: {raw[:200]}"}


def fm_list():
    """查询fileManagement文件列表"""
    status, raw = _http("GET", FM_HOST, f"{FM_BASE}/user/page?page=0&size=50", FM_TOKEN)
    if status == 200:
        return json.loads(raw)
    return []


def fm_delete(file_id):
    """删除fileManagement记录"""
    status, _ = _http("DELETE", FM_HOST, f"{FM_BASE}/{file_id}", FM_TOKEN,
                      headers_extra={"Content-Type": "application/x-www-form-urlencoded"})
    return status == 200


# ── cagentapi 聊天（3122→大头虾）──

def cagent_send(content, max_retries=2):
    """通过cagentapi发消息给大头虾，返回大头虾的回复。
    token可能间歇性403，自动重试。"""
    for attempt in range(max_retries + 1):
        try:
            # 1. 创建session
            status, raw = _http("POST", CAGENT_HOST, "/c-agent/v1/chat/sessions", CAGENT_TOKEN,
                                {"agentId": CAGENT_AGENT_ID, "content": "relay"})
            if status != 200 and status != 201:
                if attempt < max_retries:
                    print(f"  [重试 {attempt+1}/{max_retries}] session创建失败 HTTP {status}")
                    time.sleep(3)
                    continue
                return f"ERROR: session创建失败 HTTP {status}: {raw[:200]}"

            sid = json.loads(raw).get("id", "")
            if not sid:
                if attempt < max_retries:
                    print(f"  [重试 {attempt+1}/{max_retries}] 无session id")
                    time.sleep(3)
                    continue
                return "ERROR: 无法获取session id"

            time.sleep(1)

            # 2. 发消息（流式）
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
                    print(f"  [重试 {attempt+1}/{max_retries}] stream失败 HTTP {resp.status}")
                    time.sleep(3)
                    continue
                return f"ERROR: stream失败 HTTP {resp.status}: {raw2[:200]}"

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
                print(f"  [重试 {attempt+1}/{max_retries}] 异常: {e}")
                time.sleep(3)
                continue
            return f"ERROR: {e}"

    return "ERROR: 重试耗尽"


# ── 发送函数 ──

def send_small_file(filepath, note=""):
    """通道B: 聊天Base64发送小文件（不注册fileManagement，避免假URL问题）"""
    with open(filepath, "rb") as f:
        data = f.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode()
    chunk_count = math.ceil(len(b64) / CHUNK_SIZE)
    filename = os.path.basename(filepath)

    # 构建消息（不注册fileManagement，直接在聊天里发）
    msgs = [f"FILE_START:{filename}:{size}:{chunk_count}:{sha256}"]
    for i in range(chunk_count):
        start = i * CHUNK_SIZE
        chunk = b64[start:start + CHUNK_SIZE]
        msgs.append(f"FILE_CHUNK:{i+1}/{chunk_count}:{chunk}")
    msgs.append(f"FILE_END:{filename}:{sha256}")

    note_str = f"\n备注: {note}" if note else ""
    prompt = f"""[文件中转协议v2] 3122发来一个文件，请解析处理。

{chr(10).join(msgs)}

请：
1. 解析FILE_START，提取文件名、大小、分块数、sha256
2. 拼接所有FILE_CHUNK的base64数据，解码
3. 计算SHA256校验，确认与FILE_START中的一致
4. 回复 FILE_ACK:{filename}:ok 或 FILE_ACK:{filename}:error:原因
5. 保存文件到 /tmp/{filename}{note_str}"""

    reply = cagent_send(prompt)
    return None, reply  # 小文件不注册fileManagement，返回None


def send_large_file(filepath, note=""):
    """通道A: GitHub中转发送大文件。
    前提: 文件已push到GitHub books仓 relay/ 目录。
    fileManagement注册真实GitHub raw URL，大头虾用cap-webfetch下载。"""
    filename = os.path.basename(filepath)
    relay_name = f"relay_{filename}"
    ext = filename.split(".")[-1] if "." in filename else "bin"
    raw_url = f"{GITHUB_RAW_BASE}/{filename}"

    file_id, resp = fm_register(relay_name, raw_url, ext)
    if not file_id:
        return None, f"ERROR: fileManagement注册失败: {resp}"

    note_str = f"\n备注: {note}" if note else ""
    prompt = f"""[文件中转协议v2] 3122在fileManagement注册了一个大文件，请处理。

FILE_NOTIFY:{filename}:{file_id}:{raw_url}

请：
1. 通过 cap-webfetch 下载 {raw_url}
2. 下载成功后回复 FILE_ACK:{filename}:ok
3. 下载失败回复 FILE_ACK:{filename}:error:原因
4. 处理完后删除fileManagement记录: DELETE {FM_HOST}{FM_BASE}/{file_id}{note_str}"""

    reply = cagent_send(prompt)
    return file_id, reply


def send_file(filepath, note=""):
    """自动选择通道发送文件"""
    size = os.path.getsize(filepath)
    if size <= MAX_CHAT_FILE:
        return send_small_file(filepath, note)
    else:
        return send_large_file(filepath, note)


def send_message(text):
    """发送纯文本消息（不发文件）"""
    return cagent_send(text)


# ── 检查回复 ──

def check_replies():
    """检查fileManagement中大头虾注册的回复文件。
    注意: 大头虾也可能通过COME3.0 bot消息回复，此方法只查fileManagement。"""
    files = fm_list()
    replies = [f for f in files if isinstance(f, dict) and str(f.get("fileName", "")).startswith("relay_reply_")]
    return replies


# ── CLI ──

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 relay_send.py <文件路径> [--note '备注']  # 发送文件")
        print("  python3 relay_send.py --msg '消息内容'            # 发纯文本消息")
        print("  python3 relay_send.py --list                      # 查看relay文件")
        print("  python3 relay_send.py --check                     # 检查大头虾回复")
        sys.exit(1)

    if sys.argv[1] == "--list":
        files = fm_list()
        relay_files = [f for f in files if isinstance(f, dict) and str(f.get("fileName", "")).startswith("relay_")]
        if not relay_files:
            print("没有relay文件")
        for f in relay_files:
            print(f"  id={f.get('id')} name={f.get('fileName')} url={str(f.get('fileUrl',''))[:80]}")
        return

    if sys.argv[1] == "--check":
        replies = check_replies()
        if not replies:
            print("没有新回复（大头虾也可能通过COME3.0 bot消息回复）")
        for r in replies:
            print(f"  id={r.get('id')} name={r.get('fileName')} url={str(r.get('fileUrl',''))[:80]}")
        return

    if sys.argv[1] == "--msg":
        if len(sys.argv) < 3:
            print("请提供消息内容")
            sys.exit(1)
        text = sys.argv[2]
        print(f"发送消息: {text[:50]}...")
        reply = send_message(text)
        print(f"大头虾回复:\n{reply}")
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
    channel = "B(聊天Base64)" if size <= MAX_CHAT_FILE else "A(GitHub中转)"
    print(f"发送: {filepath} ({size} bytes) via {channel}")

    file_id, reply = send_file(filepath, note)
    if file_id:
        print(f"fileManagement ID: {file_id}")
    else:
        print("fileManagement: 未注册（小文件走聊天直发）")
    print(f"大头虾回复:\n{reply}")


if __name__ == "__main__":
    main()
