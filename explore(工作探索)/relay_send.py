#!/usr/bin/env python3
"""
3122 侧文件中转发送工具
用法:
  python3 relay_send.py <文件路径> [--note "备注"]
  python3 relay_send.py --list
  python3 relay_send.py --check   # 检查大头虾有没有回复
"""
import base64, hashlib, json, math, os, sys, time, http.client, ssl

# ── 配置 ──
VAPI_HOST = "vision-aiapi.catl.com"
AGENT_HOST = "agentapi.catl.com"
VAPI_TOKEN = "e88063d6-0a1b-4ae2-9b81-e89ce226029d_3"
CAGENT_HOST = "cagentapi.catl.com"
CAGENT_TOKEN = "a4bd924d-6bf8-46ce-a888-1bdde99d13bc_3"
CAGENT_AGENT_ID = "14008331"
MAX_CHAT_FILE = 100 * 1024  # 100KB
CHUNK_SIZE = 30 * 1024

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


def fm_register(filename, file_url, file_type="txt"):
    body = {"fileName": filename, "fileUrl": file_url, "fileType": file_type}
    status, raw = _http("POST", VAPI_HOST, "/vision-ai-platform/v1/fileManagement", VAPI_TOKEN, body)
    if status == 200:
        return json.loads(raw).get("id"), json.loads(raw)
    return None, {"error": raw}


def fm_list():
    status, raw = _http("GET", VAPI_HOST, "/vision-ai-platform/v1/fileManagement/user/page?page=0&size=50", VAPI_TOKEN)
    if status == 200:
        return json.loads(raw)
    return []


def fm_delete(file_id):
    status, _ = _http("DELETE", VAPI_HOST, f"/vision-ai-platform/v1/fileManagement/{file_id}", VAPI_TOKEN,
                      headers_extra={"Content-Type": "application/x-www-form-urlencoded"})
    return status == 200


def cagent_send(content):
    """通过cagentapi发消息给大头虾，返回大头虾的回复"""
    # 创建会话
    _, raw = _http("POST", CAGENT_HOST, "/c-agent/v1/chat/sessions", CAGENT_TOKEN,
                   {"agentId": CAGENT_AGENT_ID, "content": "relay"})
    sid = json.loads(raw).get("id", "")
    if not sid:
        return "ERROR: 无法创建cagent会话"
    time.sleep(1)

    # 发消息（流式）
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
    return full


def send_small_file(filepath, note=""):
    """通道B：聊天Base64发送小文件"""
    with open(filepath, "rb") as f:
        data = f.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode()
    chunk_count = math.ceil(len(b64) / CHUNK_SIZE)
    filename = os.path.basename(filepath)

    # 注册到fileManagement
    relay_name = f"relay_{filename}"
    file_id, _ = fm_register(relay_name, f"chat://relay/{filename}")

    # 构建消息
    msgs = [f"FILE_START:{filename}:{size}:{chunk_count}:{sha256}"]
    for i in range(chunk_count):
        start = i * CHUNK_SIZE
        chunk = b64[start:start + CHUNK_SIZE]
        msgs.append(f"FILE_CHUNK:{i+1}/{chunk_count}:{chunk}")
    msgs.append(f"FILE_END:{filename}:{sha256}")

    note_str = f"\n备注: {note}" if note else ""
    prompt = f"""[文件中转协议] 3122发来一个文件，请解析处理。

{chr(10).join(msgs)}

请：
1. 解析FILE_START，提取文件名、大小、分块数、sha256
2. 拼接所有FILE_CHUNK的base64数据，解码
3. 计算SHA256校验
4. 回复 FILE_ACK:{filename}:ok 或 FILE_ACK:{filename}:error:原因
5. 保存文件到 /tmp/{filename}{note_str}"""

    reply = cagent_send(prompt)
    return file_id, reply


def send_large_file(filepath, note=""):
    """通道A：GitHub中转发送大文件（需要先push到GitHub）"""
    filename = os.path.basename(filepath)
    relay_name = f"relay_{filename}"
    # fileUrl 需要是GitHub raw URL，这里只注册元数据
    # 实际使用时需要先git push
    raw_url = f"https://raw.githubusercontent.com/ryeboymly/books/main/relay/{filename}"
    file_id, resp = fm_register(relay_name, raw_url, filename.split(".")[-1] if "." in filename else "bin")

    note_str = f"\n备注: {note}" if note else ""
    prompt = f"""[文件中转协议] 3122在fileManagement注册了一个大文件，请处理。

FILE_NOTIFY:{filename}:{file_id}:{raw_url}

请：
1. 通过 cap-webfetch 下载 {raw_url}
2. 回复 FILE_ACK:{filename}:ok 或 FILE_ACK:{filename}:error:原因{note_str}"""

    reply = cagent_send(prompt)
    return file_id, reply


def send_file(filepath, note=""):
    """自动选择通道发送文件"""
    size = os.path.getsize(filepath)
    if size <= MAX_CHAT_FILE:
        return send_small_file(filepath, note)
    else:
        return send_large_file(filepath, note)


def check_replies():
    """检查fileManagement中大头虾注册的回复文件"""
    files = fm_list()
    replies = [f for f in files if isinstance(f, dict) and str(f.get("fileName", "")).startswith("relay_reply_")]
    return replies


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 relay_send.py <文件路径> [--note '备注']")
        print("  python3 relay_send.py --list")
        print("  python3 relay_send.py --check")
        sys.exit(1)

    if sys.argv[1] == "--list":
        files = fm_list()
        relay_files = [f for f in files if isinstance(f, dict) and str(f.get("fileName", "")).startswith("relay_")]
        if not relay_files:
            print("没有relay文件")
        for f in relay_files:
            print(f"  id={f.get('id')} name={f.get('fileName')} url={str(f.get('fileUrl',''))[:60]}")
        return

    if sys.argv[1] == "--check":
        replies = check_replies()
        if not replies:
            print("没有新回复")
        for r in replies:
            print(f"  id={r.get('id')} name={r.get('fileName')} url={str(r.get('fileUrl',''))[:80]}")
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
    print(f"fileManagement ID: {file_id}")
    print(f"大头虾回复:\n{reply}")


if __name__ == "__main__":
    main()
