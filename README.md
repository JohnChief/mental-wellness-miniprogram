# 心语轻疗愈小程序

原生微信小程序 + Flask + MySQL 的活动报名 MVP，部署目标为微信云托管。

## 项目结构

```text
.
├── pages/              原生小程序页面
├── utils/api.js        云托管 API 封装
├── utils/mock.js       未部署后端时的预览数据
├── config.js           环境与服务配置
├── backend/            Flask 云托管服务
└── docs/               产品、架构与上线资料
```

当前配置：

- 小程序 AppID：`wxbe032d60211a517d`
- 云开发环境：`prod-d6g7im3ft632062b9`
- 云托管服务：`flask-ytaf`
- 数据库：MySQL，默认库名 `flask_demo`

## 本地预览

用微信开发者工具打开仓库根目录。当前 `config.js` 使用真实云托管接口。
如需离线预览，可临时将 `useMock` 改为 `true`。

## 接入真实后端

1. 按 [backend/README.md](backend/README.md) 部署 `backend` 目录。
2. 在云端调试验证 `GET /health`。
3. 确认 `config.js` 中的 `useMock` 为 `false`。
4. 在开发者工具中测试首页、OpenID 登录、活动详情、报名、我的报名和注销。
5. 访问云托管公网域名的 `/admin/login` 测试运营后台。

## 当前范围

已完成：

- 用户端活动浏览、OpenID 登录、手动填写手机号报名、取消报名和账号注销。
- Flask + MySQL 核心 API、名额与重复报名保护。
- Admin 数据概览、活动管理、报名筛选与签到、用户搜索排序和 VIP 管理。
- Admin Session 登录、CSRF、防误操作确认、Toast 提示和操作审计。
- 受环境变量保护的测试数据与报名状态重置工具。

当前小程序账号不具备微信手机号组件权限，因此 MVP 在报名页由用户手动填写手机号。
动态二维码签到、正式运营素材、多管理员角色和已验证手机号留待后续阶段。

数据库结构见 [docs/数据库表结构.md](docs/数据库表结构.md)。
