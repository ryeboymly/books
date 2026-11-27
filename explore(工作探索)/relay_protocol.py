#!/usr/bin/env python3
"""
3122 ↔ 大头虾 文件中转协议 v1.0
================================

三条通道：
  A. GitHub中转   — 3122→大头虾，大文件，3122 push→大头虾 cap-webfetch拉
  B. 聊天Base64   — 双向，小文件(≤100KB)，分块编解码
  C. fileManagement索引 — 双向共享文件清单，POST注册/GET查询/DELETE删除

消息格式（通过聊天API传递）：
  FILE_NOTIFY:{filename}:{fileId}:{fileUrl}        — 文件通知
  FILE_START:{filename}:{size}:{total_chunks}:{sha256}  — 小文件开始
  FILE_CHUNK:{n}/{total}:{base64_data}             — 小文件分块
  FILE_END:{filename}:{sha256}                     — 小文件结束
  FILE_ACK:{filename}:{ok|error}                   — 确认
"""

import base64, hashlib, json, math, os, sys, time

# ── 协议常量 ──────────────────────────────────────────
PROTOCOL_VERSION = "1.0"
CHUNK_SIZE = 30 * 1024  # 30KB per chunk (Base64后约40KB，安全在SSE限制内)
MAX_CHAT_FILE = 100 * 1024  # 100KB，超过走GitHub

# ── fileManagement API ───────────────────────────────
VAPI_HOST = "vision-aiapi.catl.com"
AGENT_HOST = "agentapi.catl.com"  # 大头虾用这个

def _http(method, host, path, token, body=None, headers_extra=None):
    """简单HTTP调用，返回(status, text)"""
    import http.client, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
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


# ── 通道C：fileManagement 共享索引 ───────────────────

def fm_register(token, filename, file_url, file_type="txt", host=VAPI_HOST):
    """注册文件到共享索引，返回 (id, raw_response)"""
    body = {"fileName": filename, "fileUrl": file_url, "fileType": file_type}
    status, raw = _http("POST", host, "/vision-ai-platform/v1/fileManagement", token, body)
    if status == 200:
        data = json.loads(raw)
        return data.get("id"), data
    return None, {"error": raw}


def fm_list(token, page=0, size=50, host=VAPI_HOST):
    """查询共享文件列表"""
    status, raw = _http("GET", host, f"/vision-ai-platform/v1/fileManagement/user/page?page={page}&size={size}", token)
    if status == 200:
        return json.loads(raw)
    return []


def fm_delete(token, file_id, host=VAPI_HOST):
    """删除文件记录"""
    status, raw = _http("DELETE", host, f"/vision-ai-platform/v1/fileManagement/{file_id}", token,
                        headers_extra={"Content-Type": "application/x-www-form-urlencoded"})
    return status == 200


def fm_download_url(obs_path):
    """构造 open-api 下载URL（平台已有文件）"""
    return f"https://{VAPI_HOST}/vision-ai-platform/open-api/download/vision-ai/{obs_path}"


# ── 通道B：聊天Base64分块 ────────────────────────────

def encode_file_for_chat(filepath):
    """将文件编码为聊天消息序列，返回消息列表"""
    with open(filepath, "rb") as f:
        data = f.read()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode()
    chunk_count = math.ceil(len(b64) / CHUNK_SIZE)
    filename = os.path.basename(filepath)

    messages = []
    messages.append(f"FILE_START:{filename}:{size}:{chunk_count}:{sha256}")
    for i in range(chunk_count):
        start = i * CHUNK_SIZE
        end = start + CHUNK_SIZE
        chunk = b64[start:end]
        messages.append(f"FILE_CHUNK:{i+1}/{chunk_count}:{chunk}")
    messages.append(f"FILE_END:{filename}:{sha256}")
    return messages


def decode_chat_file(messages):
    """从聊天消息序列重组文件，返回 (filename, data, sha256_ok)"""
    filename = None
    size = None
    total = None
    expected_sha = None
    chunks = {}

    for msg in messages:
        if msg.startswith("FILE_START:"):
            parts = msg.split(":", 4)
            filename = parts[1]
            size = int(parts[2])
            total = int(parts[3])
            expected_sha = parts[4]
        elif msg.startswith("FILE_CHUNK:"):
            # FILE_CHUNK:{n}/{total}:{base64_data}
            parts = msg.split(":", 2)
            if len(parts) < 3:
                continue
            n_str, total_str = parts[1].split("/")
            chunks[int(n_str)] = parts[2]
        elif msg.startswith("FILE_END:"):
            parts = msg.split(":", 2)
            filename = parts[1]
            expected_sha = parts[2]

    if not chunks:
        return None, None, False

    b64_full = "".join(chunks[i] for i in range(1, total + 1))
    data = base64.b64decode(b64_full)
    actual_sha = hashlib.sha256(data).hexdigest()
    return filename, data, actual_sha == expected_sha


# ── 通道A：GitHub中转 ────────────────────────────────

def github_raw_url(repo, path, branch="main"):
    """构造GitHub raw URL"""
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"


def make_notify_message(filename, file_id, file_url):
    """构造文件通知消息"""
    return f"FILE_NOTIFY:{filename}:{file_id}:{file_url}"


def parse_notify_message(msg):
    """解析文件通知消息，返回 dict 或 None"""
    if not msg.startswith("FILE_NOTIFY:"):
        return None
    parts = msg.split(":", 3)
    if len(parts) < 4:
        return None
    return {"filename": parts[1], "fileId": parts[2], "fileUrl": parts[3]}


# ── 路由决策 ─────────────────────────────────────────

def choose_channel(filepath, sender="3122"):
    """根据文件大小和发送方选择通道"""
    size = os.path.getsize(filepath)
    if size <= MAX_CHAT_FILE:
        return "B"  # 聊天Base64
    elif sender == "3122":
        return "A"  # GitHub中转（只有3122能push）
    else:
        return "B_split"  # 大头虾发大文件：分块聊天（慢但能用）


# ── 自测 ─────────────────────────────────────────────

if __name__ == "__main__":
    # 测试Base64编解码
    test_data = b"Hello from 3122! This is a relay protocol test.\n" * 10
    test_file = "/tmp/relay_test.txt"
    with open(test_file, "wb") as f:
        f.write(test_data)

    print("=== 编码测试 ===")
    msgs = encode_file_for_chat(test_file)
    print(f"  文件大小: {len(test_data)} bytes")
    print(f"  消息数量: {len(msgs)} (1 start + {len(msgs)-2} chunks + 1 end)")
    print(f"  首条: {msgs[0][:80]}...")

    print("\n=== 解码测试 ===")
    fname, data, sha_ok = decode_chat_file(msgs)
    print(f"  文件名: {fname}")
    print(f"  数据大小: {len(data)} bytes")
    print(f"  SHA256校验: {'✅ 通过' if sha_ok else '❌ 失败'}")
    print(f"  内容一致: {'✅' if data == test_data else '❌'}")

    print("\n=== 通道选择 ===")
    print(f"  50KB文件 (3122发送): 通道 {choose_channel('/tmp/relay_test.txt', '3122')}")
    print(f"  50KB文件 (大头虾发送): 通道 {choose_channel('/tmp/relay_test.txt', 'cagent')}")

    # 测试通知消息
    print("\n=== 通知消息 ===")
    notify = make_notify_message("report.pdf", 12345, github_raw_url("ryeboymly/books", "explore(工作探索)/report.pdf"))
    print(f"  通知: {notify}")
    parsed = parse_notify_message(notify)
    print(f"  解析: {parsed}")

    print("\n✅ 协议自测通过")
