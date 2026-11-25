# KHM 知识中心文件上传 API 指南

> 逆向自 https://khm.catl.com 前端 JS（umi.1036901b.js, 4.7MB）
> 整理日期：2026-11-25

---

## 一、认证机制

KHM 使用 SSO 单点登录，登录后通过 Cookie 维持会话。

### 获取 Cookie

1. 在浏览器打开 https://khm.catl.com 并登录
2. 按 F12 打开开发者工具
3. Network 面板 → 随便点一个请求
4. 复制 Request Headers 中的 `cookie` 值

需要的 Cookie 字段：

```
ETEAMSID=...; langType=zh_CN; uaa_session_id=...; graph.jd.com=...
```

### 验证 Cookie 是否有效

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: <你的完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/graph/v3/space/docSearch/1/1/10" \
  -d '{"keyword":"","spaceCode":"","sortField":"createdTime","dirId":0,"sortOrder":"desc"}'
```

返回 `code: 1` 且 message 不是"登录失效" = Cookie 有效。

---

## 二、查询用户空间

### 获取私人空间信息

```bash
curl -s \
  -H "Cookie: <你的完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/graph/v3/space/getUserSpace/1/0"
```

返回 JSON 中找 `content.privateDirs`，关键字段：

| 字段 | 说明 | 示例值 |
|------|------|--------|
| id | 目录ID（上传时用） | 1043232 |
| code | 空间编码 | P_8853 |
| name | 空间名称 | 私人空间 |
| dirType | 目录类型（2=私人） | 2 |
| spacePerm.uploadFile | 是否有上传权限 | 1 |

### 获取部门空间信息

```bash
curl -s \
  -H "Cookie: <你的完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/graph/v3/space/getUserDeptSpace/1"
```

---

## 三、上传文件（核心）

### 接口信息

| 项目 | 值 |
|------|-----|
| URL | `POST /api-poc/cpd/file/add/1` |
| Content-Type | multipart/form-data |
| 认证 | Cookie |

### 请求参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| file | File | 要上传的文件（二进制） |
| spaceInfo | JSON String | 空间信息，JSON 序列化后作为表单字段 |

### spaceInfo JSON 结构

```json
{
  "spaceCode": "P_8853",
  "dirId": 1043232
}
```

- `spaceCode`：从 getUserSpace 返回的 privateDirs[].code
- `dirId`：从 getUserSpace 返回的 privateDirs[].id

### 完整 curl 命令

```bash
curl -s -X POST \
  -H "Cookie: <你的完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/cpd/file/add/1" \
  -F "file=@/path/to/yourfile.md" \
  -F 'spaceInfo={"spaceCode":"P_8853","dirId":1043232}'
```

### 成功返回

```json
{
  "code": 0,
  "message": "操作成功",
  "content": {
    "id": 1000643,
    "name": "yourfile.md",
    "ext": "md",
    "size": 73,
    "path": "graph/knowledge/map//xxx/yourfile.md",
    "previewUrl": "https://khm.catl.com/api-poc/cpd/file/is/1/1000643",
    "createdBy": 2143475270,
    "sourceSystem": 0
  }
}
```

### 失败排查

| 错误 | 原因 | 解决 |
|------|------|------|
| "登录失效，请重新登录!" | Cookie 过期 | 重新从浏览器抓 Cookie |
| "你没有权限访问！" | 空间权限不足 | 确认 spacePerm.uploadFile = 1 |
| code 非 0 | 参数缺失 | 检查 file 和 spaceInfo 是否都传了 |

---

## 四、Python 批量上传脚本

```python
import requests
import json
from pathlib import Path

KHM_BASE = "https://khm.catl.com"
COOKIE = "ETEAMSID=...; langType=zh_CN; uaa_session_id=...; graph.jd.com=..."
SPACE_CODE = "P_8853"
DIR_ID = 1043232

HEADERS = {
    "Cookie": COOKIE,
    "Origin": KHM_BASE,
    "Referer": f"{KHM_BASE}/knowledge-center",
}

def upload_file(filepath: str) -> dict:
    """上传单个文件到 KHM 私人空间"""
    p = Path(filepath)
    with open(p, "rb") as f:
        files = {"file": (p.name, f)}
        data = {"spaceInfo": json.dumps({"spaceCode": SPACE_CODE, "dirId": DIR_ID})}
        resp = requests.post(
            f"{KHM_BASE}/api-poc/cpd/file/add/1",
            headers=HEADERS,
            files=files,
            data=data,
            timeout=30,
        )
    result = resp.json()
    if result.get("code") == 0:
        print(f"[OK] {p.name} -> id={result['content']['id']}")
    else:
        print(f"[FAIL] {p.name} -> {result.get('message')}")
    return result

def batch_upload(directory: str):
    """批量上传目录下所有文件"""
    for p in sorted(Path(directory).iterdir()):
        if p.is_file():
            upload_file(str(p))

if __name__ == "__main__":
    # 单个文件
    # upload_file("/path/to/file.md")
    
    # 批量上传
    # batch_upload("/path/to/directory")
    pass
```

---

## 五、注意事项

1. **Cookie 有效期**：Session cookie 有时效，长时间不用需要重新获取
2. **支持的文件格式**：pdf, xls, xlsx, csv, xlsm, doc, docx, ppt, pptx, md, txt, vsdx, vsd, png, jpg, jpeg
3. **projectId**：URL 中的 `/1` 是 projectId，生产环境固定为 1
4. **空间选择**：私人空间（dirType=2）只有自己能看到；部门空间其他人可见
5. **文件大小**：未在 JS 中发现明确限制，建议单文件不超过 50MB

---

## 六、逆向过程记录

1. 下载首页 HTML → 发现 SPA 空壳，JS 动态渲染
2. 下载 umi.js（4.7MB）→ grep 搜索 upload/file/add 关键词
3. 找到 API 路径：`/api-poc/cpd/file/add/{projectId}`
4. 找到空间查询 API：`/api-poc/graph/v3/space/getUserSpace/1/0`
5. 从 getUserSpace 返回中提取 privateDirs 获取 spaceCode 和 dirId
6. 用 Cookie 认证 + FormData 暴力测试上传 → 成功
7. 关键发现：spaceInfo 需要作为 JSON 字符串传入 FormData，不是嵌套对象
