#!/usr/bin/env python3
"""
KHM 知识中心文件上传工具
用法:
  python khm_upload.py <文件路径>          # 上传单个文件
  python khm_upload.py <目录路径>          # 批量上传目录下所有文件

Cookie 过期后需重新从浏览器获取，替换下面的 COOKIE 值。
"""

import requests
import json
import sys
from pathlib import Path

# ========== 凭证配置（直接写死，过期了来这里换） ==========
COOKIE = "ETEAMSID=INTUNIFYAUTHUNIFIEDAUTH_cd17bce249179077cc0544be11a8096d-9JHMO4JM4FB4N; langType=zh_CN; uaa_session_id=r8bh8fxonlfcibtxj3as7udyikvib0pz; graph.jd.com=cXsDbIIPtJnihIObPJeITXCfzMJJbpFX"
SPACE_CODE = "P_8853"
DIR_ID = 1043232
PROJECT_ID = 1
BASE_URL = "https://khm.catl.com"
# =========================================================

HEADERS = {
    "Cookie": COOKIE,
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/knowledge-center",
}

def upload_file(filepath):
    """上传单个文件到 KHM 私人空间"""
    p = Path(filepath)
    if not p.is_file():
        print(f"[SKIP] {filepath} 不是文件")
        return None

    with open(p, "rb") as f:
        files = {"file": (p.name, f)}
        data = {"spaceInfo": json.dumps({"spaceCode": SPACE_CODE, "dirId": DIR_ID})}
        try:
            resp = requests.post(
                f"{BASE_URL}/api-poc/cpd/file/add/{PROJECT_ID}",
                headers=HEADERS,
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
        print(f"[OK]   {p.name} -> id={content.get('id')} preview={BASE_URL}/api-poc/cpd/file/is/{PROJECT_ID}/{content.get('id')}")
        return result
    else:
        msg = result.get("message", "未知错误")
        if "登录失效" in msg:
            print(f"[FAIL] {p.name} -> Cookie 过期，请更新脚本中的 COOKIE")
        elif "没有权限" in msg:
            print(f"[FAIL] {p.name} -> 无权限，检查空间配置")
        else:
            print(f"[FAIL] {p.name} -> {msg}")
        return None

def batch_upload(directory):
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
        result = upload_file(str(f))
        if result:
            success += 1
        else:
            fail += 1

    print(f"\n完成: 成功 {success}, 失败 {fail}")

def main():
    if len(sys.argv) < 2:
        print("用法: python khm_upload.py <文件或目录路径>")
        sys.exit(1)

    path = sys.argv[1]

    if Path(path).is_dir():
        batch_upload(path)
    elif Path(path).is_file():
        upload_file(path)
    else:
        print(f"[ERROR] 路径不存在: {path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
