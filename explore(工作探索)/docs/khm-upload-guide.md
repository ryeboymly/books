# KHM 知识中心文件上传 API 指南

> 逆向自 https://khm.catl.com 前端 JS（umi.1036901b.js, 4.7MB）
> 整理日期：2026-11-25 | 更新：2026-11-25（v2 - 文档注册版）

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

---

## 三、上传文件（核心）

### 两个 API 的区别

| API | 作用 | 文件可见？ |
|-----|------|-----------|
| `POST /api-poc/cpd/file/add/{projectId}` | 只存文件到存储层 | 不可见 |
| `POST /api-poc/knowledge/single/upload/{projectId}/{isProcessFlag}/{docCode}` | 上传文件 + 注册文档到空间 | 可见 |

v1 踩坑：用 `file/add` 上传后文件在服务器上但页面看不到，因为缺少文档注册步骤。
v2 方案：直接用 `knowledge/single/upload` 一步到位。

### 接口信息

| 项目 | 值 |
|------|-----|
| URL | `POST /api-poc/knowledge/single/upload/1/0/0` |
| Content-Type | multipart/form-data |
| 认证 | Cookie |

URL 路径参数：
- `projectId`：固定 1（生产环境）
- `isProcessFlag`：0=直接上传，1=提交审核
- `docCode`：0=新建文档，非0=编辑已有文档

### 请求参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| files | File | 要上传的文件（注意是复数 files） |
| docInfoList | JSON String | 文档元数据数组，JSON 序列化后作为表单字段 |

### docInfoList JSON 结构

```json
[
  {
    "docRealName": "文件名.md",
    "docFormat": 1,
    "securityLevel": 1,
    "spaceCode": "P_8853",
    "dirId": 1043232,
    "authorInfoList": [
      {"author": "作者名", "authorType": "1"}
    ]
  }
]
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| docRealName | String | 是 | 文档显示名称（含扩展名） |
| docFormat | Integer | 是 | 文件格式（必须整数，1=文档类） |
| securityLevel | Integer | 是 | 密级（1=公开） |
| spaceCode | String | 是 | 空间编码，从 getUserSpace 获取 |
| dirId | Integer | 是 | 目录ID，从 getUserSpace 获取 |
| authorInfoList | Array | 是 | 作者信息（不传会报"作者不能为空"） |
| authorInfoList[].author | String | 是 | 作者姓名 |
| authorInfoList[].authorType | String | 是 | 作者类型（"1"=内部员工） |

### 完整 curl 命令

```bash
curl -s -X POST \
  -H "Cookie: <你的完整cookie>" \
  -H "Origin: https://khm.catl.com" \
  -H "Referer: https://khm.catl.com/knowledge-center" \
  "https://khm.catl.com/api-poc/knowledge/single/upload/1/0/0" \
  -F "files=@/path/to/yourfile.md" \
  -F 'docInfoList=[{"docRealName":"yourfile.md","docFormat":1,"securityLevel":1,"spaceCode":"P_8853","dirId":1043232,"authorInfoList":[{"author":"你的名字","authorType":"1"}]}]'
```

### 成功返回

```json
{
  "code": 0,
  "message": "操作成功",
  "content": ["e1d474c056f3c298e670c2039d9963ad"]
}
```

`content` 是 docCode 数组，用这个 code 可以查文档详情：

```bash
curl -s -X POST \
  -H "Cookie: <你的完整cookie>" \
  -H "Content-Type: application/json" \
  "https://khm.catl.com/api-poc/action/doc/stat/detail" \
  -d '{"projectId":1,"docCode":"e1d474c056f3c298e670c2039d9963ad"}'
```

### 失败排查

| 错误 | 原因 | 解决 |
|------|------|------|
| "登录失效，请重新登录!" | Cookie 过期 | 重新从浏览器抓 Cookie |
| "作者不能为空" | 缺少 authorInfoList | 检查 docInfoList 中是否包含 authorInfoList |
| "Cannot deserialize Integer from String" | docFormat 传了字符串 | docFormat 必须是整数，不能是 "md" |
| "你没有权限访问！" | 空间权限不足 | 确认空间上传权限 |

---

## 四、Python 上传脚本

完整脚本见同目录下 `khm_upload.py`，cookie 和空间配置直接写在脚本顶部。

### 使用方法

```bash
# 上传单个文件
python khm_upload.py /path/to/file.md

# 批量上传目录
python khm_upload.py /path/to/directory/
```

### Cookie 过期更新

打开 `khm_upload.py`，替换顶部 `COOKIE` 变量的值即可。

---

## 五、注意事项

1. **Cookie 有效期**：Session cookie 有时效，过期后重新从浏览器获取
2. **docFormat 必须是整数**：传字符串会报 Jackson 反序列化错误
3. **authorInfoList 必填**：不传会报"作者不能为空"
4. **files 是复数**：表单字段名是 `files` 不是 `file`
5. **搜索索引延迟**：上传成功后 docSearch 可能暂时搜不到，但 docCode 详情可查
6. **projectId**：URL 中的 `/1` 是 projectId，生产环境固定为 1

---

## 六、逆向过程记录

1. 下载首页 HTML → 发现 SPA 空壳，JS 动态渲染
2. 下载 umi.js（4.7MB）→ grep 搜索 upload/file/add 关键词
3. v1: 找到 `file/add` API → 上传成功但文件不可见（只存存储层）
4. 在 JS 中搜索 `docInfoList` → 发现真正的上传函数
5. 找到 `knowledge/single/upload/{projectId}/{isProcessFlag}/{docCode}` API
6. 暴力测试 docFormat：字符串报错要 Integer → 传整数 1 通过
7. 报"作者不能为空" → 在 JS 中找到 `authorInfoList` 字段 → 加上后成功
8. docCode 详情 API 确认文档已注册（code=0）
9. 关键发现：`file/add` 只存文件，`knowledge/single/upload` 才注册文档到空间
