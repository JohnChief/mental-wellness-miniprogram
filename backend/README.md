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
# 本地开发也可使用 DATABASE_URL=sqlite:///local.db
SECRET_KEY=<长随机字符串>
ADMIN_API_KEY=<另一条长随机字符串>
ADMIN_USERNAME=<管理后台账号>
ADMIN_PASSWORD_HASH=<Werkzeug 生成的密码哈希>
WECHAT_APP_ID=<小程序 AppID>
WECHAT_APP_SECRET=<小程序 AppSecret>
AUTO_INIT_DB=true
SEED_SAMPLE_DATA=true
ALLOW_DEV_OPENID=false
SESSION_COOKIE_SECURE=true
```

部署后访问 `/admin/login` 进入运营管理后台。后台包含数据概览、活动管理、
报名签到与用户 VIP 管理。开发环境可临时使用 `ADMIN_PASSWORD` 明文密码，
正式环境应只配置 `ADMIN_PASSWORD_HASH`，可通过以下命令生成：

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('替换为强密码'))"
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
- 首次登录只要求手机号授权；昵称和头像可选，未填写时系统随机分配，登录后可再次修改。
- 手机号授权 code 由后端调用微信接口换取。
- `WECHAT_APP_SECRET` 只能配置在云托管环境变量中，禁止写入代码或提交到 Git。
- 管理接口要求 `X-ADMIN-KEY`，目前仅用于开发期联调。
- 正式上线管理端前还需增加管理员账号、密码哈希、会话、CSRF、限速和更完整的操作审计。
- 报名备注明确限制为非健康敏感信息。
