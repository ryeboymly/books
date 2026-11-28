#!/usr/bin/env python3
"""
V盘2.0 (sdrivesmm.catl.com) API CLI工具
逆向自前端JS + 浏览器抓包验证

用法:
  python vdrive_api.py list     --path-type ent --neid 1 --nsid 1
  python vdrive_api.py meta     --path-type ent --neid 1 --nsid 1
  python vdrive_api.py projects --nsid 1
  python vdrive_api.py auth     --path-type ent --neid 1 --nsid 1
  python vdrive_api.py upload   --path-type ent --neid 1 --nsid 1 --file ./test.txt
"""

import argparse
import json
import os
import sys
import time
import requests

# ── 配置 ──────────────────────────────────────────────
BASE_URL = "https://sdrivesmm.catl.com"
UID = 1518959
ACCOUNT_ID = 1

# Cookie - 从浏览器复制完整Cookie字符串
COOKIE = (
    "ETEAMSID=INTUNIFYAUTHUNIFIEDAUTH_cd17bce249179077cc0544be11a8096d-9JHMO4JM4FB4N; "
    "langType=zh_CN; "
    "graph.jd.com=XPfeLEJHiAdAhNPNMRhlvuskhivebsWI; "
    "language=zh; "
    "X-LENOVO-TFA-ID=c6fb8267a2744073a14a7b63f27a376a_1_1518959_app1; "
    "X-LENOVO-SESS-ID=c6fb8267a2744073a14a7b63f27a376a_1_1518959_app1; "
    "theme=white; "
    "JSESSIONID=3D1366BF8F47D72C1F26C6E38F1660DA"
)

HEADERS = {
    "Cookie": COOKIE,
    "Accept": "application/json, text/plain, */*",
    "Origin": BASE_URL,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def _ts():
    return f"{int(time.time() * 1000)}"


def _params(path_type=None, neid=None, nsid=None, **extra):
    """构建查询参数 - 所有参数都在query string里"""
    params = {
        "account_id": ACCOUNT_ID,
        "uid": UID,
        "_": _ts(),
        "sort": "desc",
        "orderby": "name",
        "limit": 50,
        "offset": 0,
        "include_deleted": "false",
    }
    if path_type:
        params["path_type"] = path_type
    if neid:
        params["neid"] = neid
    if nsid:
        params["nsid"] = nsid
    params.update(extra)
    return params


# ── API: 文件列表 ────────────────────────────────────
def list_files(path_type="ent", neid=1, nsid=1, limit=50, offset=0):
    """
    GET /v2/metadata/databox - 获取目录下文件列表
    所有参数在query string中，方法为GET
    """
    url = f"{BASE_URL}/v2/metadata/databox"
    params = _params(
        path_type=path_type, neid=neid, nsid=nsid,
        limit=limit, offset=offset,
    )
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()

    if result.get("result") != "success":
        msg = result.get("message", "")
        print(f"API返回异常: {msg or json.dumps(result, ensure_ascii=False)[:200]}")
        return

    content = result.get("content", [])
    path = result.get("path", "?")
    print(f"目录: {path}  (共 {len(content)} 项)")
    print("-" * 60)
    for item in content:
        name = item.get("file_name", "?")
        is_dir = item.get("is_dir", False)
        size = item.get("size", "")
        neid_val = item.get("neid", "")
        nsid_val = item.get("nsid", "")
        icon = "[DIR] " if is_dir else "[FILE]"
        print(f"  {icon} {name}")
        print(f"         neid={neid_val} nsid={nsid_val} size={size}")
    return result


# ── API: 目录元数据 ──────────────────────────────────
def get_meta(path_type="ent", neid=1, nsid=1):
    """
    GET /v2/metadata/databox - 获取目录本身元数据
    与list_files相同端点，返回目录自身信息+content数组
    """
    url = f"{BASE_URL}/v2/metadata/databox"
    params = _params(path_type=path_type, neid=neid, nsid=nsid)
    resp = requests.get(url, params=params, headers=HEADERS)
    resp.raise_for_status()
    result = resp.json()
    # 只显示目录自身信息，不显示content
    meta = {k: v for k, v in result.items() if k != "content"}
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return result


# ── API: 项目列表 ────────────────────────────────────
def list_projects(nsid=1):
    """GET /v2/project/list - 获取可访问的项目/团队空间"""
    url = f"{BASE_URL}/v2/project/list"
    params = {"account_id": ACCOUNT_ID, "uid": UID, "nsid": nsid, "_": _ts()}
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
    params = {
        "account_id": ACCOUNT_ID, "uid": UID, "_": _ts(),
        "path_type": path_type, "neid": neid, "nsid": nsid,
    }
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
    2. POST /v2/fileops/auth_upload/databox - 上传文件(multipart)
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    print(f"准备上传: {file_name} ({file_size} bytes)")

    # Step 1: 检查冲突
    check_url = f"{BASE_URL}/v2/fileops/upload_config/check"
    check_params = {"account_id": ACCOUNT_ID, "uid": UID, "_": _ts()}
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
    upload_params = {"account_id": ACCOUNT_ID, "uid": UID, "_": _ts()}
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
        "bytes": str(file_size),
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
    p_list.add_argument("--path-type", default="ent",
                        choices=["ent", "team", "share_in", "share_out"])
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
