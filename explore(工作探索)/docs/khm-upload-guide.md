# KHM 知识中心上传 API

> 逆向自 `khm.catl.com` 前端 JS（umi.1036901b.js，4.7MB）；2026-11-25，v2 文档注册版

## 一、认证

SSO 登录后靠 Cookie 维持会话。浏览器登录 khm.catl.com → F12 → Network 任一请求 → 复制 Request Headers 的 `cookie`。

需要的字段：`ETEAMSID`、`langType=zh_CN`、`uaa_session_id`、`graph.jd.com`。

## 二、查用户空间

```bash
curl -s -H "Cookie: <完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/graph/v3/space/getUserSpace/1/0"
```

返回里取 `content.privateDirs`：`id`（目录 ID，上传要用）、`code`（空间编码）、`name`（空间名）。

## 三、上传（核心）

两个 API 的区别：

| API | 作用 | 页面可见 |
|---|---|---|
| `POST /api-poc/cpd/file/add/{projectId}` | 只存到存储层 | ❌ |
| `POST /api-poc/knowledge/single/upload/{projectId}/{isProcessFlag}/{docCode}` | 上传 + 注册文档 | ✅ |

v1 的坑就在这里：用 `file/add` 传完文件在服务器上，但页面看不到，缺注册步骤。v2 直接用 `knowledge/single/upload` 一步到位。

**接口**：`POST /api-poc/knowledge/single/upload/1/0/0`，`multipart/form-data`，Cookie 认证。

路径参数：`projectId` 固定 1（生产）；`isProcessFlag` 0=直接上传、1=提交审核；`docCode` 0=新建、非 0=编辑已有。

**表单字段**：`files`（File，注意是复数）、`docInfoList`（JSON 字符串）。

`docInfoList` 结构（`spaceCode` / `dirId` 从 getUserSpace 取）：

```json
[{"docRealName":"文件名.md","docFormat":1,"securityLevel":1,
  "spaceCode":"<spaceCode>","dirId":<dirId>,
  "authorInfoList":[{"author":"作者名","authorType":"1"}]}]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| docRealName | String | 显示名，含扩展名 |
| docFormat | Integer | 必须整数，1=文档类 |
| securityLevel | Integer | 密级，1=公开 |
| spaceCode | String | 空间编码 |
| dirId | Integer | 目录 ID |
| authorInfoList | Array | 不传报"作者不能为空"；authorType "1"=内部员工 |

**完整 curl**：

```bash
curl -s -X POST -H "Cookie: <完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/knowledge/single/upload/1/0/0" \
  -F "files=@/path/to/file.md" \
  -F 'docInfoList=[{"docRealName":"file.md","docFormat":1,"securityLevel":1,"spaceCode":"<spaceCode>","dirId":<dirId>,"authorInfoList":[{"author":"你的名字","authorType":"1"}]}]'
```

**成功返回**：`{"code":0,"message":"操作成功","content":["<docCode>"]}`。`content` 是 docCode 数组，可用它查详情：

```bash
curl -s -X POST -H "Cookie: <完整cookie>" -H "Content-Type: application/json" \
  "https://khm.catl.com/api-poc/action/doc/stat/detail" \
  -d '{"projectId":1,"docCode":"<docCode>"}'
```

**失败排查**：

| 错误 | 原因 | 解决 |
|---|---|---|
| 登录失效，请重新登录 | Cookie 过期 | 重抓 Cookie |
| 作者不能为空 | 缺 authorInfoList | 补上 |
| Cannot deserialize Integer from String | docFormat 传了字符串 | 改整数 1 |
| 你没有权限访问 | 空间权限不足 | 确认上传权限 |

## 四、脚本

`khm_upload.py` 在同目录，Cookie 与空间配置写在脚本顶部。

```bash
python khm_upload.py /path/to/file.md        # 单文件
python khm_upload.py /path/to/directory/     # 批量
```

Cookie 过期时改脚本顶部 `COOKIE` 变量。

## 五、补充注意

- `files` 是复数，字段名不能写成 `file`。
- 上传成功后 `docSearch` 可能短时搜不到，但 docCode 详情可查（索引延迟）。
- `projectId` 是 URL 里的 `/1`，生产固定 1。

## 六、怎么找到的

首页 HTML 是 SPA 空壳 → 下 umi.js（4.7MB）grep `upload`/`file/add` → 先命中 `file/add`（能传但不可见）→ 搜 `docInfoList` 找到真正的上传函数 `knowledge/single/upload` → 试 `docFormat` 报 Integer 错误、加 `authorInfoList` 报作者字段、逐个补齐后成功 → docCode 详情确认已注册。关键结论：`file/add` 只存文件，`knowledge/single/upload` 才注册到空间。
