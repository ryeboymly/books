# V盘 2.0 API 逆向

> 逆向自 `sdrivesmm.catl.com` 前端 JS + 浏览器抓包验证
> 覆盖：文件列表、目录元数据、项目列表、权限查询、文件上传

## 端点

| 功能 | 方法 | URL | 验证方式 |
|---|---|---|---|
| 文件列表 | GET | `/v2/metadata/databox` | 浏览器抓包 |
| 项目列表 | GET | `/v2/project/list` | 已验证 |
| 权限列表 | GET | `/v2/auth/list_by_resource` | 已验证 |
| 上传冲突检查 | POST | `/v2/fileops/upload_config/check` | JS 逆向 |
| 文件上传 | POST | `/v2/fileops/auth_upload/databox` | JS 逆向 |
| 额外元数据 | POST | `/v2/extra_meta` | 已验证 |

## 认证

Cookie 认证，关键字段：`ETEAMSID`（主会话）、`X-LENOVO-TFA-ID`（双因子）、`X-LENOVO-SESS-ID`（上传时需放进 form data）、`JSESSIONID`（会变化，需定期更新）。

URL 固定携带 `account_id=1&uid={UID}&_={timestamp}`。

## 1. 文件列表 `GET /v2/metadata/databox`

`GET`，参数全部在 query string：

```
path_type=ent      # ent=企业 | team=团队 | share_in=共享给我 | share_out=我共享的
sort=desc
orderby=name       # 默认 name，也可 mtime
limit=50
offset=0
include_deleted=false
neid=1             # 目录节点 ID，从 URL /v/list/ent/{neid} 获取
nsid=1
account_id=1
uid={UID}
_={ms}
```

响应：

```json
{"result":"success","path":"/","content":[{"file_name":"文档.txt","is_dir":false,
"neid":"12345","nsid":1,"size":"1.2 KB","mtime":1675190674000,"path":"/文档.txt"}],
"content_size":1,"is_dir":true,"owner":"管理员","neid":"1"}
```

限制：`path_type=self` 与 `share_out`（个人空间）返回 403 `personal_document_cannot_access`，是 CATL 服务端策略。

## 2. 项目列表 `GET /v2/project/list`

参数：`nsid`、`account_id`、`uid`、`_`。

## 3. 权限列表 `GET /v2/auth/list_by_resource`

参数：`path_type`、`neid`、`nsid`、`account_id`、`uid`、`_`。

## 4. 上传冲突检查 `POST /v2/fileops/upload_config/check`

```
fileNames=[{"name":"文件名.txt"}]   # JSON 数组
neid=1
nsid=1
path_type=ent
```

## 5. 文件上传 `POST /v2/fileops/auth_upload/databox`

multipart/form-data：

```
path_type=ent
language=zh
from=
prefix_neid=
X-LENOVO-SESS-ID={从 Cookie 提取}
nsid=1
account_id=1
uid={UID}
forceRename=false
path=/
```

文件字段名 `file`。

## 调度器机制

前端用 webpack 模块 13106 作 API 调度器，导出 `postData` / `getData`：`getData` 走 GET（带 neid 时），`postData` 走 POST（带 path 时）。

action 名到 URL 不是简单驼峰转下划线：`getMetadata` → `GET /v2/metadata/databox`（不是 `/v2/get_metadata`）；`extraMeta` → `POST /v2/extra_meta`。

## 使用

```bash
python vdrive_api.py list --path-type ent --neid 1 --nsid 1    # 企业空间根目录
python vdrive_api.py list --path-type team --neid 1 --nsid 1   # 团队空间
python vdrive_api.py meta --path-type ent --neid 1 --nsid 1    # 目录元数据
python vdrive_api.py projects --nsid 1                          # 可访问项目
python vdrive_api.py upload --path-type ent --neid 1 --nsid 1 --file ./test.txt
```

## 已知限制

1. 个人空间封锁：`path_type=self` / `share_out` 返回 403（服务端策略）。
2. `neid` / `nsid` 需从浏览器 URL `/v/list/{path_type}/{neid}` 或文件列表响应中取。
3. Cookie 有时效，`JSESSIONID` 会变化，需定期从浏览器更新。
