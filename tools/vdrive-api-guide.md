# V盘2.0 API 逆向指南

> 逆向自 `sdrivesmm.catl.com` 前端 JS (webpack hash: `0a11ac05`)
> 涵盖文件列表、目录元数据、项目列表、权限查询、文件上传

## 已验证的 API 端点

| 功能 | 方法 | URL | 状态 |
|------|------|-----|------|
| 文件列表 | POST | `/v2/metadata/get` | ✅ 已验证 |
| 目录元数据 | POST | `/v2/metadata/databox` | ✅ 已验证 |
| 额外元数据 | POST | `/v2/extra_meta` | ✅ 已验证 |
| 项目列表 | GET | `/v2/project/list` | ✅ 已验证 |
| 权限列表 | GET | `/v2/auth/list_by_resource` | ✅ 已验证 |
| 上传冲突检查 | POST | `/v2/fileops/upload_config/check` | ✅ 已验证 |
| 文件上传 | POST | `/v2/fileops/auth_upload/databox` | ✅ 已验证 |

## 认证

所有请求通过 Cookie 认证，关键 Cookie 字段:
- `ETEAMSID` - 主会话令牌
- `X-LENOVO-TFA-ID` - 双因子认证
- `X-LENOVO-SESS-ID` - 会话ID (上传时需放入 form data)
- `JSESSIONID` - Java 会话

URL 查询参数固定携带: `account_id=1&uid={UID}&_={timestamp}`

## API 详情

### 1. 文件列表 - POST /v2/metadata/get

获取指定目录下的文件和子目录列表。

**查询参数:** `account_id`, `uid`, `_` (时间戳)

**Form Data:**
```
path_type=ent          # ent=企业, team=团队, share_in=共享给我, share_out=我共享的
include_deleted=false
limit=50
offset=0
sort=desc
orderby=mtime
neid=1                 # 目录节点ID (从URL /v/list/ent/{neid} 获取)
nsid=1                 # 命名空间ID
```

**响应示例:**
```json
{
  "result": "success",
  "content": [
    {
      "file_name": "文档.txt",
      "is_dir": false,
      "neid": "12345",
      "nsid": 1,
      "size": "1.2 KB",
      "mtime": 1675190674000,
      "path": "/文档.txt"
    }
  ],
  "content_size": 1
}
```

**注意:** `path_type=self` (个人空间) 返回 403 `personal_document_cannot_access`，这是 CATL 服务器端安全策略，非 API 问题。

### 2. 目录元数据 - POST /v2/metadata/databox

获取目录本身的元数据 (不含子文件)。

**查询参数:** `path_type`, `nsid`, `account_id`, `uid`, `_`

**Form Data:** `path=/`

### 3. 额外元数据 - POST /v2/extra_meta

批量获取文件的额外元数据 (标签、描述等)。

**Form Data:** `neids=1,2,3` (复数，逗号分隔)

### 4. 项目列表 - GET /v2/project/list

获取当前用户可访问的团队空间/项目列表。

**查询参数:** `nsid`, `account_id`, `uid`, `_`

### 5. 权限列表 - GET /v2/auth/list_by_resource

获取指定目录的权限分配列表。

**查询参数:** `path_type`, `neid`, `nsid`, `account_id`, `uid`, `_`

### 6. 上传冲突检查 - POST /v2/fileops/upload_config/check

上传前检查文件名是否冲突。

**Form Data:**
```
fileNames=[{"name":"文件名.txt"}]   # JSON数组
neid=1
nsid=1
path_type=ent
```

### 7. 文件上传 - POST /v2/fileops/auth_upload/databox

实际上传文件 (multipart/form-data)。

**Form Data:**
```
path_type=ent
language=zh
from=
prefix_neid=
X-LENOVO-SESS-ID={从Cookie提取}
nsid=1
account_id=1
uid={UID}
forceRename=false
path=/
```

**File field:** `file` (文件二进制)

## API 调度器机制

前端使用 webpack 模块 13106 作为 API 调度器，导出 `postData` / `getData` / `getDataAbort` 方法。

action 名到 URL 的映射不是简单的驼峰转下划线:
- `getMetadata` -> `/v2/metadata/get` (不是 `/v2/get_metadata`)
- `extraMeta` -> `/v2/extra_meta`
- `usualSearch` -> `/v2/usual_search` (推测)

`getData` 使用 GET 方法 (有 neid 参数时)，`postData` 使用 POST 方法 (有 path 参数时)。

## 使用方法

```bash
# 列出企业空间根目录文件
python vdrive_api.py list --path-type ent --neid 1 --nsid 1

# 查看目录元数据
python vdrive_api.py meta --path-type ent --neid 1 --nsid 1

# 查看可访问的项目列表
python vdrive_api.py projects --nsid 1

# 上传文件
python vdrive_api.py upload --path-type ent --neid 1 --nsid 1 --file ./test.txt
```

## 已知限制

1. **个人空间封锁**: `path_type=self` 被 CATL 服务器端策略封锁 (403)
2. **neid/nsid 获取**: 需从浏览器 URL `/v/list/{path_type}/{neid}` 或文件列表响应中获取
3. **Cookie 过期**: Cookie 有时效性，需定期从浏览器更新
