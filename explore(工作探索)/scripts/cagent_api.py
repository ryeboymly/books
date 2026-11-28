#!/usr/bin/env python3
"""
CATL C-Agent (cagent.catl.com) 对话 API 客户端
完整调用链: 创建会话 -> 发消息(SSE流式) -> 读历史 -> 反馈

用法:
  python3 cagent_api.py "你好"
  python3 cagent_api.py --session 14098810 "1+1等于几"
  python3 cagent_api.py --list
  python3 cagent_api.py --history 14098810
"""

import json
import sys
import requests

# ============ 配置 ============
API_HOST = "https://cagentapi.catl.com"
TOKEN = "fff950d6-8116-489e-bd3f-1f50e36073a7_3"
AGENT_ID = "14008331"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
}

SSE_HEADERS = {
    **HEADERS,
    "Accept": "text/event-stream",
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}


def create_session(content="你好"):
    """创建新会话, 返回 sessionId"""
    url = f"{API_HOST}/c-agent/v1/chat/sessions"
    resp = requests.post(url, headers=HEADERS, json={"agentId": AGENT_ID, "content": content}, timeout=15)
    print(f"[创建会话] HTTP {resp.status_code}")
    data = resp.json()
    sid = data.get("data", {}).get("id") or data.get("id")
    print(f"  sessionId = {sid}")
    return sid


def send_message(session_id, content):
    """发送消息并解析SSE流式响应, 返回完整回复文本"""
    url = f"{API_HOST}/c-agent/v1/chat/stream"
    body = {"sessionId": int(session_id), "content": content, "agentId": AGENT_ID}
    print(f"[发送消息] -> {content}")

    full_text = ""
    resp = requests.post(url, headers=SSE_HEADERS, json=body, stream=True, timeout=120)
    print(f"[SSE流] HTTP {resp.status_code}")

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            print("\n[SSE流] 完成")
            break
        try:
            chunk = json.loads(payload)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            piece = delta.get("content", "")
            if piece:
                full_text += piece
                print(piece, end="", flush=True)
            reason = chunk.get("choices", [{}])[0].get("finishReason")
            if reason == "stop":
                print()
        except json.JSONDecodeError:
            pass

    return full_text


def list_sessions():
    """列出所有会话"""
    url = f"{API_HOST}/c-agent/v1/chat/sessions"
    params = {"agentId": AGENT_ID}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    print(f"[会话列表] HTTP {resp.status_code}")
    data = resp.json()
    sessions = data.get("data", {}).get("list", data.get("data", []))
    if isinstance(sessions, list):
        for s in sessions:
            sid = s.get("id", "?")
            title = s.get("title", s.get("lastMessage", "?"))[:40]
            print(f"  [{sid}] {title}")
    return data


def get_history(session_id, page=1, size=50):
    """获取会话消息历史"""
    url = f"{API_HOST}/c-agent/v1/chat/sessions/{session_id}/messages"
    params = {"pageNum": page, "pageSize": size}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    print(f"[消息历史] HTTP {resp.status_code}")
    data = resp.json()
    msgs = data.get("data", {}).get("list", data.get("data", []))
    if isinstance(msgs, list):
        for m in msgs:
            role = m.get("role", "?")
            content = m.get("content", "")[:100]
            print(f"  [{role}] {content}")
    return data


def get_feedbacks(session_id):
    """获取会话反馈"""
    url = f"{API_HOST}/c-agent/v1/chat/sessions/{session_id}/feedbacks"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    print(f"[反馈] HTTP {resp.status_code}")
    return resp.json()


def chat(content, session_id=None):
    """一站式对话: 可选创建会话 -> 发消息"""
    if not session_id:
        session_id = create_session(content)
    reply = send_message(session_id, content)
    return reply


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    if args[0] == "--list":
        list_sessions()
    elif args[0] == "--history" and len(args) > 1:
        get_history(args[1])
    elif args[0] == "--feedback" and len(args) > 1:
        print(json.dumps(get_feedbacks(args[1]), ensure_ascii=False, indent=2))
    elif args[0] == "--session" and len(args) > 2:
        send_message(args[1], args[2])
    elif args[0] == "--create" and len(args) > 1:
        create_session(args[1])
    else:
        # 默认: 一站式对话
        content = args[0]
        reply = chat(content)
        print(f"\n=== 完整回复 ===\n{reply}")
