#!/usr/bin/env python3
"""
V盘2.0 (sdrivesmm.catl.com) API CLI工具
逆向自前端JS (index.0a11ac05.js + list-ent/service-upload chunks)

用法:
  python vdrive_api.py list   --path-type ent --neid 1 --nsid 1
  python vdrive_api.py meta   --path-type ent --neid 1 --nsid 1
  python vdrive_api.py projects --nsid 1
  python vdrive_api.py upload --path-type ent --neid 1 --nsid 1 --file ./test.txt
"""

import argparse
import json
import os
import sys
import time
import requests
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
BASE_URL = "https://sdrivesmm.catl.com"
UID = 1518959
ACCOUNT_ID = 1

# Cookie - 从浏览器复制完整Cookie字符串
COOKIE = (
    "ETEAMSID=INTUNIFYAUTHUNIFIEDAUTH_cd17bce249179077cc0544be11a8096d-9JHMO4JM4FB4N; "
    "langType=zh_CN; "
    "uaa_session_id=przgh2xs109fjqhrbis8n65kwk948kd9; "
    "graph.jd.com=XPfeLEJHiAdAhNPNMRhlvuskhivebsWI; "
    "language=zh; "
    "X-LENOVO-TFA-ID=c6fb8267a2744073a14a7b63f27a376a_1_1518959_app1; "
    "X-LENOVO-SESS-ID=c6fb8267a2744073a14a7b63f27a376a_1_1518959_app1; "
    "theme=white; "
    "JSESSIONID=FA504A46EEEC542FC8FF7ABA86D0B769"
)

HEADERS = {
    "Cookie": COOKIE,
    "Origin": BASE_URL,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def _ts():
    return f"{int(time.time() * 1000)}"


def _query_params(**extra):
    params = {"account_id": ACCOUNT_ID, "uid": UID, "_": _ts()}
    params.update(extra)
    return params


# ── API: 文件列表 ────────────────────────────────────
def list_files(path_type="ent", neid=1, nsid=1, limit=50, offset=0):
    """POST /v2/metadata/get - 获取目录下文件列表"""
    url = f"{BASE_URL}/v2/metadata/get"
    params = _query_params()
    data = {
        "path_type": path_type,
        "include_deleted": "false",
        "limit": limit,
        "offset": offset,
        "sort": "desc",
        "orderby": "mtime",
        "neid": neid,
        "nsid": nsid,
    }
    resp = requests.post(url, params=params, data=data, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()

    if result.get("result") != "success":
        print(f"API返回异常: {json.dumps(result, ensure_ascii=False)[:200]}")
        return

    content = result.get("content", [])
    print(f"目录: {result.get('path', '?')}  (共 {len(content)} 项)")
    print("-" * 60)
    for item in content:
        name = item.get("file_name", "?")
        is_dir = item.get("is_dir", False)
        size = item.get("size", "")
        neid_val = item.get("neid", "")
        nsid_val = item.get("nsid", "")
        icon = "📁" if is_dir else "📄"
        print(f"  {icon} {name}")
        print(f"     neid={neid_val} nsid={nsid_val} size={size}")
    return result


# ── API: 目录元数据 ──────────────────────────────────
def get_meta(path_type="ent", neid=1, nsid=1):
    """POST /v2/metadata/databox - 获取目录元数据"""
    url = f"{BASE_URL}/v2/metadata/databox"
    params = _query_params(path_type=path_type, nsid=nsid)
    data = {"path": "/"}
    resp = requests.post(url, params=params, data=data, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


# ── API: 项目列表 ────────────────────────────────────
def list_projects(nsid=1):
    """GET /v2/project/list - 获取可访问的项目/团队空间"""
    url = f"{BASE_URL}/v2/project/list"
    params = _query_params(nsid=nsid)
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    if isinstance(result, dict):
        content = result.get("content", [])
        print(f"项目数: {len(content)}")
        for item in content:
            print(f"  - {item.get('name', '?')} | neid={item.get('neid')} | nsid={item.get('nsid')}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


# ── API: 权限列表 ────────────────────────────────────
def list_auth(path_type="ent", neid=1, nsid=1):
    """GET /v2/auth/list_by_resource - 获取目录权限列表"""
    url = f"{BASE_URL}/v2/auth/list_by_resource"
    params = _query_params(path_type=path_type, neid=neid, nsid=nsid)
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


# ── API: 上传文件 ────────────────────────────────────
def upload_file(path_type="ent", neid=1, nsid=1, file_path="", force_rename=False):
    """
    两步上传:
    1. POST /v2/fileops/upload_config/check - 检查文件名冲突
    2. POST /v2/fileops/auth_upload/databox - 上传文件
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    print(f"准备上传: {file_name} ({file_size} bytes)")

    # Step 1: 检查冲突
    check_url = f"{BASE_URL}/v2/fileops/upload_config/check"
    check_params = _query_params()
    check_data = {
        "fileNames": json.dumps([{"name": file_name}]),
        "neid": neid,
        "nsid": nsid,
        "path_type": path_type,
    }
    resp = requests.post(check_url, params=check_params, data=check_data, headers=HEADERS)
    resp.raise_for_status()
    check_result = resp.json()
    print(f"冲突检查: {json.dumps(check_result, ensure_ascii=False)[:200]}")

    # Step 2: 上传
    upload_url = f"{BASE_URL}/v2/fileops/auth_upload/databox"
    upload_params = _query_params()
    sess_id = ""
    for part in COOKIE.split(";"):
        part = part.strip()
        if part.startswith("X-LENOVO-SESS-ID="):
            sess_id = part.split("=", 1)[1]
            break

    form_data = {
        "path_type": path_type,
        "language": "zh",
        "from": "",
        "prefix_neid": "",
        "X-LENOVO-SESS-ID": sess_id,
        "nsid": nsid,
        "account_id": ACCOUNT_ID,
        "uid": UID,
        "forceRename": "true" if force_rename else "false",
        "path": "/",
    }

    with open(file_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        upload_headers = {k: v for k, v in HEADERS.items() if k != "Content-Type"}
        resp = requests.post(
            upload_url, params=upload_params, data=form_data,
            files=files, headers=upload_headers
        )

    print(f"上传响应: HTTP {resp.status_code}")
    try:
        result = resp.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        print(resp.text[:500])
    return resp


# ── CLI ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="V盘2.0 API CLI")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="列出文件")
    p_list.add_argument("--path-type", default="ent", choices=["ent", "team", "share_in", "share_out"])
    p_list.add_argument("--neid", default="1")
    p_list.add_argument("--nsid", default="1")
    p_list.add_argument("--limit", type=int, default=50)

    p_meta = sub.add_parser("meta", help="目录元数据")
    p_meta.add_argument("--path-type", default="ent")
    p_meta.add_argument("--neid", default="1")
    p_meta.add_argument("--nsid", default="1")

    p_proj = sub.add_parser("projects", help="项目列表")
    p_proj.add_argument("--nsid", default="1")

    p_auth = sub.add_parser("auth", help="权限列表")
    p_auth.add_argument("--path-type", default="ent")
    p_auth.add_argument("--neid", default="1")
    p_auth.add_argument("--nsid", default="1")

    p_upload = sub.add_parser("upload", help="上传文件")
    p_upload.add_argument("--path-type", default="ent")
    p_upload.add_argument("--neid", default="1")
    p_upload.add_argument("--nsid", default="1")
    p_upload.add_argument("--file", required=True)
    p_upload.add_argument("--force-rename", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        list_files(args.path_type, args.neid, args.nsid, args.limit)
    elif args.command == "meta":
        get_meta(args.path_type, args.neid, args.nsid)
    elif args.command == "projects":
        list_projects(args.nsid)
    elif args.command == "auth":
        list_auth(args.path_type, args.neid, args.nsid)
    elif args.command == "upload":
        upload_file(args.path_type, args.neid, args.nsid, args.file, args.force_rename)


if __name__ == "__main__":
    main()
