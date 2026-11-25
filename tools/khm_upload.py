#!/usr/bin/env python3
"""
KHM 知识中心文件上传工具
用法:
  python khm_upload.py <文件路径>          # 上传单个文件
  python khm_upload.py <目录路径>          # 批量上传目录下所有文件
  python khm_upload.py <文件路径> --dept   # 上传到部门空间(默认私人空间)

凭证存放在私有仓 mly 的 ops(环境运维)/khm-credentials.toml 中。
首次使用前: export KHM_CREDS=/path/to/khm-credentials.toml
"""

import requests
import json
import sys
import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def load_config():
    """从 toml 凭证文件加载配置"""
    creds_path = os.environ.get("KHM_CREDS")
    if not creds_path:
        # 尝试默认路径
        creds_path = os.path.expanduser("~/mly/ops(环境运维)/khm-credentials.toml")
    if not os.path.exists(creds_path):
        print(f"[ERROR] 凭证文件不存在: {creds_path}")
        print("请设置环境变量 KHM_CREDS 指向 khm-credentials.toml")
        sys.exit(1)
    with open(creds_path, "rb") as f:
        return tomllib.load(f)["khm"]

def upload_file(filepath, config, use_dept=False):
    """上传单个文件到 KHM"""
    p = Path(filepath)
    if not p.is_file():
        print(f"[SKIP] {filepath} 不是文件")
        return None

    base_url = config["base_url"]
    cookie = config["cookie"]
    project_id = config["project_id"]

    if use_dept:
        space_code = config.get("dept_space_code", "")
        dir_id = config.get("dept_dir_id", 0)
    else:
        space_code = config["space_code"]
        dir_id = config["dir_id"]

    headers = {
        "Cookie": cookie,
        "Origin": base_url,
        "Referer": f"{base_url}/knowledge-center",
    }

    with open(p, "rb") as f:
        files = {"file": (p.name, f)}
        data = {"spaceInfo": json.dumps({"spaceCode": space_code, "dirId": dir_id})}
        try:
            resp = requests.post(
                f"{base_url}/api-poc/cpd/file/add/{project_id}",
                headers=headers,
                files=files,
                data=data,
                timeout=30,
            )
            result = resp.json()
        except Exception as e:
            print(f"[FAIL] {p.name} -> 请求异常: {e}")
            return None

    if result.get("code") == 0:
        content = result.get("content", {})
        print(f"[OK]   {p.name} -> id={content.get('id')} url={base_url}/api-poc/cpd/file/is/{project_id}/{content.get('id')}")
        return result
    else:
        msg = result.get("message", "未知错误")
        if "登录失效" in msg:
            print(f"[FAIL] {p.name} -> Cookie 过期，请重新获取")
        elif "没有权限" in msg:
            print(f"[FAIL] {p.name} -> 无权限，检查空间配置")
        else:
            print(f"[FAIL] {p.name} -> {msg}")
        return None

def batch_upload(directory, config, use_dept=False):
    """批量上传目录下所有文件"""
    d = Path(directory)
    if not d.is_dir():
        print(f"[ERROR] {directory} 不是目录")
        sys.exit(1)

    files = sorted([f for f in d.iterdir() if f.is_file()])
    print(f"找到 {len(files)} 个文件\n")

    success = 0
    fail = 0
    for f in files:
        result = upload_file(str(f), config, use_dept)
        if result:
            success += 1
        else:
            fail += 1

    print(f"\n完成: 成功 {success}, 失败 {fail}")

def main():
    if len(sys.argv) < 2:
        print("用法: python khm_upload.py <文件或目录路径> [--dept]")
        sys.exit(1)

    path = sys.argv[1]
    use_dept = "--dept" in sys.argv

    config = load_config()

    if Path(path).is_dir():
        batch_upload(path, config, use_dept)
    elif Path(path).is_file():
        upload_file(path, config, use_dept)
    else:
        print(f"[ERROR] 路径不存在: {path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
