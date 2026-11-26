#!/usr/bin/env python3
"""
KHM 知识中心文件上传工具（v2 - 文档注册版）

v1 用 file/add 只存文件不注册文档，页面上看不到。
v2 改用 knowledge/single/upload 一步到位：上传文件 + 注册文档到空间。

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
# 密级说明：1=公开, 2=内部, 3=秘密, 4=机密, 5=绝密
# 前端UI会拦截秘密及以上，但后端API不拦截，可直接传5
# 私人空间中所有密级都显示为"个人"
SECURITY_LEVEL = 5  # 5=绝密（私人空间中自动显示为"个人"）
COOKIE = "ETEAMSID=INTUNIFYAUTHUNIFIEDAUTH_cd17bce249179077cc0544be11a8096d-9JHMO4JM4FB4N; langType=zh_CN; uaa_session_id=przgh2xs109fjqhrbis8n65kwk948kd9; graph.jd.com=XPfeLEJHiAdAhNPNMRhlvuskhivebsWI"
SPACE_CODE = "P_8853"
DIR_ID = 1043232
PROJECT_ID = 1
AUTHOR_NAME = "本杰明"
BASE_URL = "https://khm.catl.com"
# =========================================================

HEADERS = {
    "Cookie": COOKIE,
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/knowledge-center",
}

# 文件扩展名 -> docFormat 数字（1=文档类，其他格式待补充）
EXT_FORMAT_MAP = {
    "md": 1, "txt": 1,
    "doc": 1, "docx": 1,
    "pdf": 1,
    "html": 1, "htm": 1,
    "ppt": 1, "pptx": 1,
    "xls": 1, "xlsx": 1, "csv": 1,
    "png": 1, "jpg": 1, "jpeg": 1,
}


def upload_file(filepath):
    """上传单个文件到 KHM 私人空间（文件 + 文档注册一步完成）"""
    p = Path(filepath)
    if not p.is_file():
        print(f"[SKIP] {filepath} 不是文件")
        return None

    ext = p.suffix.lstrip(".").lower()
    doc_format = EXT_FORMAT_MAP.get(ext, 1)

    # docInfoList: 文档元数据，决定文件在空间里怎么显示
    doc_info = {
        "docRealName": p.name,
        "docFormat": doc_format,
        "securityLevel": SECURITY_LEVEL,
        "spaceCode": SPACE_CODE,
        "dirId": DIR_ID,
        "authorInfoList": [{"author": AUTHOR_NAME, "authorType": "1"}],
    }

    with open(p, "rb") as f:
        files = {"files": (p.name, f)}
        data = {"docInfoList": json.dumps([doc_info])}
        try:
            resp = requests.post(
                f"{BASE_URL}/api-poc/knowledge/single/upload/{PROJECT_ID}/0/0",
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
        doc_codes = result.get("content", [])
        code_str = ", ".join(doc_codes) if doc_codes else "无"
        print(f"[OK]   {p.name} -> docCode={code_str}")
        return result
    else:
        msg = result.get("message", "未知错误")
        if "登录失效" in msg or "重新登录" in msg:
            print(f"[FAIL] {p.name} -> Cookie 过期，请更新脚本中的 COOKIE")
        elif "没有权限" in msg:
            print(f"[FAIL] {p.name} -> 无权限，检查空间配置")
        elif "作者不能为空" in msg:
            print(f"[FAIL] {p.name} -> authorInfoList 缺失，检查脚本配置")
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
