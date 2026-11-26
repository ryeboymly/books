# V盘2.0 API 逆向指南

> 逆向自 `sdrivesmm.catl.com` 前端 JS + 浏览器抓包验证
> 涵盖文件列表、目录元数据、项目列表、权限查询、文件上传

## 已验证的 API 端点

| 功能 | 方法 | URL | 状态 |
|------|------|-----|------|
| 文件列表 | **GET** | `/v2/metadata/databox` | ✅ 浏览器抓包验证 |
| 项目列表 | GET | `/v2/project/list` | ✅ 已验证 |
| 权限列表 | GET | `/v2/auth/list_by_resource` | ✅ 已验证 |
| 上传冲突检查 | POST | `/v2/fileops/upload_config/check` | ✅ JS逆向验证 |
| 文件上传 | POST | `/v2/fileops/auth_upload/databox` | ✅ JS逆向验证 |
| 额外元数据 | POST | `/v2/extra_meta` | ✅ 已验证 |

## 认证

所有请求通过 Cookie 认证，关键 Cookie 字段:
- `ETEAMSID` - 主会话令牌
- `X-LENOVO-TFA-ID` - 双因子认证
- `X-LENOVO-SESS-ID` - 会话ID (上传时需放入 form data)
- `JSESSIONID` - Java 会话 (会变化，需定期更新)

URL 查询参数固定携带: `account_id=1&uid={UID}&_={timestamp}`

## API 详情

### 1. 文件列表 - GET /v2/metadata/databox

获取指定目录下的文件和子目录列表。

**重要:** 方法是 **GET**，所有参数在 query string 中。

**Query Parameters:**
```
path_type=ent            # ent=企业, team=团队, share_in=共享给我, share_out=我共享的
sort=desc
orderby=name             # 按名称排序 (不是mtime)
limit=50
offset=0
include_deleted=false
neid=1                   # 目录节点ID (从URL /v/list/ent/{neid} 获取)
nsid=1                   # 命名空间ID
account_id=1
uid=1518959
_={timestamp}            # 毫秒时间戳
```

**响应示例:**
```json
{
  "result": "success",
  "path": "/",
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
  "content_size": 1,
  "is_dir": true,
  "owner": "管理员",
  "neid": "1"
}
```

**注意:**
- `path_type=self` 和 `path_type=share_out` (个人空间) 返回 403 `personal_document_cannot_access`，这是 CATL 服务器端安全策略
- `orderby` 默认为 `name`，也可用 `mtime` (修改时间)

### 2. 项目列表 - GET /v2/project/list

获取当前用户可访问的团队空间/项目列表。

**Query Parameters:** `nsid`, `account_id`, `uid`, `_`

### 3. 权限列表 - GET /v2/auth/list_by_resource

获取指定目录的权限分配列表。

**Query Parameters:** `path_type`, `neid`, `nsid`, `account_id`, `uid`, `_`

### 4. 上传冲突检查 - POST /v2/fileops/upload_config/check

上传前检查文件名是否冲突。

**Form Data:**
```
fileNames=[{"name":"文件名.txt"}]   # JSON数组
neid=1
nsid=1
path_type=ent
```

### 5. 文件上传 - POST /v2/fileops/auth_upload/databox

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

前端使用 webpack 模块 13106 作为 API 调度器，导出 `postData` / `getData` 方法。

- `getData` -> HTTP **GET** (有 neid 参数时使用)
- `postData` -> HTTP **POST** (有 path 参数时使用)

action 名到 URL 的映射不是简单的驼峰转下划线:
- `getMetadata` -> `GET /v2/metadata/databox` (不是 `/v2/get_metadata`)
- `extraMeta` -> `POST /v2/extra_meta`

## 使用方法

```bash
# 列出企业空间根目录文件
python vdrive_api.py list --path-type ent --neid 1 --nsid 1

# 列出团队空间文件
python vdrive_api.py list --path-type team --neid 1 --nsid 1

# 查看目录元数据
python vdrive_api.py meta --path-type ent --neid 1 --nsid 1

# 查看可访问的项目列表
python vdrive_api.py projects --nsid 1

# 上传文件
python vdrive_api.py upload --path-type ent --neid 1 --nsid 1 --file ./test.txt
```

## 已知限制

1. **个人空间封锁**: `path_type=self` 和 `path_type=share_out` 被 CATL 服务器端策略封锁 (403)
2. **neid/nsid 获取**: 需从浏览器 URL `/v/list/{path_type}/{neid}` 或文件列表响应中获取
3. **Cookie 过期**: Cookie 有时效性，JSESSIONID 会变化，需定期从浏览器更新
