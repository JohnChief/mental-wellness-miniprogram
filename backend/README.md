# 心语轻疗愈后端

基于 Flask、MySQL 和微信云托管。小程序通过 `wx.cloud.callContainer` 调用，用户身份只信任云托管注入的 `X-WX-OPENID` 请求头。

## 云托管部署

在 `flask-ytaf` 服务中创建新版本，代码目录选择本仓库的 `backend` 目录，容器端口为 `80`。

保留模板已经配置的：

- `MYSQL_ADDRESS`
- `MYSQL_USERNAME`
- `MYSQL_PASSWORD`

新增环境变量：

```text
MYSQL_DATABASE=flask_demo
SECRET_KEY=<长随机字符串>
ADMIN_API_KEY=<另一条长随机字符串>
AUTO_INIT_DB=true
SEED_SAMPLE_DATA=true
ALLOW_DEV_OPENID=false
```

首次启动会自动建表并写入三条演示活动。确认业务数据已由管理流程维护后，将 `SEED_SAMPLE_DATA` 改为 `false`。

## 健康检查

部署完成后在云端调试中请求：

```text
GET /health
```

成功响应：

```json
{"code": 0, "data": {"status": "healthy"}}
```

## 安全边界

- 小程序用户接口不接受前端提交的 OpenID。
- 管理接口要求 `X-ADMIN-KEY`，目前仅用于开发期联调。
- 正式上线管理端前还需增加管理员账号、密码哈希、会话、CSRF、限速和更完整的操作审计。
- 报名备注明确限制为非健康敏感信息。
